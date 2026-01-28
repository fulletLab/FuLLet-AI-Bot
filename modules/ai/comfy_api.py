import json
import random
import time
import asyncio
import os
import aiohttp
import base64
from modules.utils.image_filter import sanitize_image
from modules.ai.gpu_pool import gpu_pool


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_headers(api_key: str) -> dict:
    headers = {"ngrok-skip-browser-warning": "69420"}
    if not api_key:
        return headers
    
    if ":" in api_key:
        encoded = base64.b64encode(api_key.encode()).decode()
        headers["Authorization"] = f"Basic {encoded}"
    else:
        headers["Authorization"] = f"Bearer {api_key}"
        
    return headers


def load_workflow(filename: str) -> dict:
    path = os.path.join(ROOT_DIR, "flujos", filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Workflow file not found at {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


async def queue_prompt(workflow: dict, gpu_url: str, api_key: str) -> dict:
    p = {"prompt": workflow}
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{gpu_url}/prompt", json=p, headers=get_headers(api_key)) as response:
            return await response.json()


async def get_history(prompt_id: str, gpu_url: str, api_key: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{gpu_url}/history/{prompt_id}", headers=get_headers(api_key)) as response:
            return await response.json()


async def get_image(filename: str, subfolder: str, folder_type: str, gpu_url: str, api_key: str) -> bytes:
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{gpu_url}/view", params=data, headers=get_headers(api_key)) as response:
            return await response.read()


async def upload_image(image_bytes: bytes, filename: str, gpu_url: str, api_key: str) -> dict:
    clean_bytes = sanitize_image(image_bytes)
    if not clean_bytes:
        raise Exception("Image sanitization failed")

    clean_filename = os.path.splitext(filename)[0] + ".jpg"
    
    data = aiohttp.FormData()
    data.add_field('image', clean_bytes, filename=clean_filename)
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{gpu_url}/upload/image", data=data, headers=get_headers(api_key)) as response:
            return await response.json()


async def wait_for_image(prompt_id: str, gpu_url: str, api_key: str, timeout: int = 300) -> dict:
    start_time = time.time()
    while time.time() - start_time < timeout:
        history = await get_history(prompt_id, gpu_url, api_key)
        if prompt_id in history:
            return history[prompt_id]
        await asyncio.sleep(2)
    return None


def get_model_type_for_vram(model_type: str, is_edit: bool) -> str:
    if model_type == "z-image":
        return "z-image"
    return "flux_edit" if is_edit else "flux"

async def process_image_batch(jobs):
    if not jobs:
        return []
    
    gpu = await gpu_pool.wait_for_available_gpu("flux", timeout=120.0)
    if not gpu:
        return [{"status": "error", "message": "No GPU available"} for _ in jobs]
    
    await gpu_pool.reserve_gpu(gpu, "flux")
    
    try:
        base_workflow = load_workflow("flux_image.json")
        merged = {}
        
        shared_loaders = ["75:72", "75:82", "75:83"]
        for nid in shared_loaders:
            if nid in base_workflow:
                merged[nid] = base_workflow[nid]

        batch_size = len(jobs)
        prompts = [j.prompt for j in jobs]
        while len(prompts) < 4:
            prompts.append("")

        merged["p_batch"] = {
            "inputs": {
                "clip": ["75:82", 0],
                "text_1": prompts[0],
                "text_2": prompts[1],
                "text_3": prompts[2],
                "text_4": prompts[3]
            },
            "class_type": "CLIPTextEncodeBatch"
        }
        
        merged["n_batch"] = {
            "inputs": {
                "clip": ["75:82", 0],
                "text_1": "",
                "text_2": "",
                "text_3": "",
                "text_4": ""
            },
            "class_type": "CLIPTextEncodeBatch"
        }

        merged["latent"] = {
            "inputs": {"width": 1024, "height": 1024, "batch_size": batch_size},
            "class_type": "EmptyFlux2LatentImage"
        }
        
        merged["scheduler"] = {
            "inputs": {"steps": 4, "width": 1024, "height": 1024},
            "class_type": "Flux2Scheduler"
        }
        
        merged["noise"] = {
            "inputs": {"noise_seed": random.randint(1, 10**15)},
            "class_type": "RandomNoise"
        }
        
        merged["guider"] = {
            "inputs": {
                "cfg": 1,
                "model": ["75:83", 0],
                "positive": ["p_batch", 0],
                "negative": ["n_batch", 0]
            },
            "class_type": "CFGGuider"
        }
        
        merged["sampler"] = {
            "inputs": {
                "noise": ["noise", 0],
                "guider": ["guider", 0],
                "sampler": ["75:61", 0],
                "sigmas": ["scheduler", 0],
                "latent_image": ["latent", 0]
            },
            "class_type": "SamplerCustomAdvanced"
        }
        
        merged["75:61"] = base_workflow["75:61"]
        
        merged["decode"] = {
            "inputs": {"samples": ["sampler", 0], "vae": ["75:72", 0]},
            "class_type": "VAEDecode"
        }
        
        merged["save"] = {
            "inputs": {"filename_prefix": "batch", "images": ["decode", 0]},
            "class_type": "SaveImage"
        }

        try:
            response = await queue_prompt(merged, gpu.url, gpu.api_key)
            prompt_id = response.get("prompt_id")
        except:
            return [{"status": "error", "message": "Connection error"} for _ in jobs]
        
        if not prompt_id:
            return [{"status": "error", "message": "Workflow rejected"} for _ in jobs]

        history_entry = await wait_for_image(prompt_id, gpu.url, gpu.api_key)
        
        final_responses = []
        if history_entry:
            outputs = history_entry.get("outputs", {})
            if "save" in outputs and "images" in outputs["save"]:
                images_list = outputs["save"]["images"]
                for i, job in enumerate(jobs):
                    if i < len(images_list):
                        img_data = images_list[i]
                        img_bytes = await get_image(img_data["filename"], img_data["subfolder"], img_data["type"], gpu.url, gpu.api_key)
                        final_responses.append({
                            "status": "success",
                            "image_bytes": img_bytes,
                            "filename": img_data["filename"],
                            "user_id": job.user_id
                        })
                    else:
                        final_responses.append({"status": "error", "message": "Index missing"})
            else:
                return [{"status": "error", "message": "No output images"} for _ in jobs]
        else:
            return [{"status": "error", "message": "Timeout"} for _ in jobs]
            
        return final_responses

    finally:
        await gpu_pool.release_gpu(gpu, "flux")


async def process_image_gen(prompt, input_image_bytes=None, input_filename=None, model_type="flux"):
    class MockJob:
        def __init__(self, p):
            self.prompt = p
            self.user_id = "single"
            self.model_type = "flux"
    
    res = await process_image_batch([MockJob(prompt)])
    return res[0]

