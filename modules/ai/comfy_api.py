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


async def process_image_gen(prompt, input_image_bytes=None, input_filename=None, model_type="flux"):
    vram_type = get_model_type_for_vram(model_type, input_image_bytes is not None)
    
    gpu = await gpu_pool.wait_for_available_gpu(vram_type, timeout=120.0)
    if not gpu:
        return {"status": "error", "message": "No GPU available"}
    
    await gpu_pool.reserve_gpu(gpu, vram_type)
    
    try:
        if model_type == "z-image":
            workflow_file = "z-image_imagine.json"
        else:
            workflow_file = "flux_edit.json" if input_image_bytes else "flux_image.json"
        
        try:
            workflow = load_workflow(workflow_file)
        except Exception as e:
            return {"status": "error", "message": f"Workflow error: {e}"}
        
        if model_type == "z-image":
            if "6" in workflow: workflow["6"]["inputs"]["text"] = prompt
            seed = random.randint(1, 10**15)
            if "32" in workflow: workflow["32"]["inputs"]["noise_seed"] = seed
            if "33" in workflow: workflow["33"]["inputs"]["noise_seed"] = seed
        else:
            if "75:74" in workflow: workflow["75:74"]["inputs"]["text"] = prompt
            if "75:73" in workflow: workflow["75:73"]["inputs"]["noise_seed"] = random.randint(1, 10**15)
        
        if input_image_bytes and model_type != "z-image" and "103" in workflow:
            try:
                upload_result = await upload_image(input_image_bytes, input_filename, gpu.url, gpu.api_key)
                workflow["103"]["inputs"]["image"] = upload_result["name"]
            except Exception as e:
                return {"status": "error", "message": "Image upload failed"}
        
        try:
            response = await queue_prompt(workflow, gpu.url, gpu.api_key)
            prompt_id = response.get("prompt_id")
        except Exception as e:
            return {"status": "error", "message": "Connection error"}
        
        if not prompt_id:
            return {"status": "error", "message": "Queue full"}

        history_entry = await wait_for_image(prompt_id, gpu.url, gpu.api_key)
        
        if history_entry:
            try:
                outputs = history_entry.get("outputs", {})
                for node_id, node_output in outputs.items():
                    if "images" in node_output:
                        image_data = node_output["images"][0]
                        image_bytes = await get_image(
                            image_data["filename"], 
                            image_data["subfolder"], 
                            image_data["type"],
                            gpu.url,
                            gpu.api_key
                        )
                        return {
                            "status": "success", 
                            "image_bytes": image_bytes, 
                            "filename": image_data["filename"],
                            "gpu_url": gpu.url
                        }
            except: 
                pass
                    
        return {"status": "error", "message": "Generation failed"}
    
    finally:
        await gpu_pool.release_gpu(gpu, vram_type)

