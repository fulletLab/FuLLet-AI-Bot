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

async def upload_image(image_bytes: bytes, filename: str, gpu_url: str, api_key: str) -> str:
    data = aiohttp.FormData()
    data.add_field('image', image_bytes, filename=filename, content_type='image/png')
    data.add_field('overwrite', 'true')
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{gpu_url}/upload/image", data=data, headers=get_headers(api_key)) as response:
            resp = await response.json()
            return resp.get("name", filename)

async def wait_for_image(prompt_id: str, gpu_url: str, api_key: str, timeout: int = 300) -> dict:
    start_time = time.time()
    while time.time() - start_time < timeout:
        history = await get_history(prompt_id, gpu_url, api_key)
        if prompt_id in history:
            return history[prompt_id]
        await asyncio.sleep(2)
    return None

async def process_image_batch(jobs):
    if not jobs: return []
    
    edit_jobs = [j for j in jobs if j.is_edit or j.input_image_bytes]
    anima_jobs = [j for j in jobs if not j.is_edit and not j.input_image_bytes and getattr(j, 'model_type', 'flux') == 'anima']
    standard_jobs = [j for j in jobs if not j.is_edit and not j.input_image_bytes and getattr(j, 'model_type', 'flux') != 'anima']
    
    results = [None] * len(jobs)
    
    if standard_jobs:
        std_results = await process_standard_batch(standard_jobs)
        std_idx = 0
        for i, job in enumerate(jobs):
            if not job.is_edit and not job.input_image_bytes and getattr(job, 'model_type', 'flux') != 'anima':
                results[i] = std_results[std_idx]
                std_idx += 1
    
    if anima_jobs:
        for i, job in enumerate(jobs):
            if not job.is_edit and not job.input_image_bytes and getattr(job, 'model_type', 'flux') == 'anima':
                results[i] = await process_anima_job(job)
                
    if edit_jobs:
        for i, job in enumerate(jobs):
            if job.is_edit or job.input_image_bytes:
                results[i] = await process_single_edit_job(job)
                
    return results

async def process_anima_job(job):
    gpu = await gpu_pool.wait_for_available_gpu("anima", timeout=120.0)
    if not gpu: return {"status": "error", "message": "No GPU available"}
    
    await gpu_pool.reserve_gpu(gpu, "anima")
    try:
        workflow = load_workflow("anima.json")
        
        if "4" in workflow:
            workflow["4"]["inputs"]["text"] = job.prompt
        if "3" in workflow:
            workflow["3"]["inputs"]["seed"] = random.randint(1, 10**15)
            
        response = await queue_prompt(workflow, gpu.url, gpu.api_key)
        prompt_id = response.get("prompt_id")
        if not prompt_id:
            msg = response.get("error", {}).get("message", "Workflow rejected")
            return {"status": "error", "message": msg}
            
        history_entry = await wait_for_image(prompt_id, gpu.url, gpu.api_key)
        if history_entry:
            outputs = history_entry.get("outputs", {})
            if "10" in outputs and "images" in outputs["10"]:
                img_data = outputs["10"]["images"][0]
                img_bytes = await get_image(img_data["filename"], img_data["subfolder"], img_data["type"], gpu.url, gpu.api_key)
                return {"status": "success", "image_bytes": img_bytes, "filename": img_data["filename"], "user_id": job.user_id}
        return {"status": "error", "message": "Timeout or no output"}
    except aiohttp.ContentTypeError:
        return {"status": "error", "message": "GPU server unavailable"}
    except aiohttp.ClientError:
        return {"status": "error", "message": "Connection error"}
    except Exception:
        return {"status": "error", "message": "Generation failed"}
    finally:
        await gpu_pool.release_gpu(gpu, "anima")

async def process_single_edit_job(job):
    gpu = await gpu_pool.wait_for_available_gpu("flux", timeout=120.0)
    if not gpu: return {"status": "error", "message": "No GPU available"}
    
    await gpu_pool.reserve_gpu(gpu, "flux")
    try:
        try:
            workflow = load_workflow("flux_edit.json")
        except FileNotFoundError:
            return {"status": "error", "message": "Edit workflow not found"}
            
        if job.input_image_bytes:
            filename = job.input_filename or f"upload_{int(time.time())}.png"
            uploaded_name = await upload_image(job.input_image_bytes, filename, gpu.url, gpu.api_key)
        else:
            return {"status": "error", "message": "No input image for edit"}
            
        INPUT_NODE = "103"
        POS_NODE = "75:74"
        NEG_NODE = "75:67"
        
        if INPUT_NODE in workflow:
            workflow[INPUT_NODE]["inputs"]["image"] = uploaded_name
            
        if POS_NODE in workflow:
            workflow[POS_NODE]["inputs"]["text"] = job.prompt
            
        if NEG_NODE in workflow:
            workflow[NEG_NODE]["inputs"]["text"] = ""

        NOISE_NODE = "75:73"
        if NOISE_NODE in workflow:
            workflow[NOISE_NODE]["inputs"]["noise_seed"] = random.randint(1, 10**15)

        try:
            response = await queue_prompt(workflow, gpu.url, gpu.api_key)
            prompt_id = response.get("prompt_id")
            if not prompt_id:
                msg = response.get("error", {}).get("message", "Workflow rejected")
                return {"status": "error", "message": msg}
                
            history_entry = await wait_for_image(prompt_id, gpu.url, gpu.api_key)
            
            if history_entry:
                outputs = history_entry.get("outputs", {})
                save_node = "9" 
                if save_node in outputs and "images" in outputs[save_node]:
                    img_data = outputs[save_node]["images"][0]
                    img_bytes = await get_image(img_data["filename"], img_data["subfolder"], img_data["type"], gpu.url, gpu.api_key)
                    return {
                        "status": "success",
                        "image_bytes": img_bytes,
                        "filename": img_data["filename"],
                        "user_id": job.user_id
                    }
                else:
                    return {"status": "error", "message": "No output images"}
            else:
                return {"status": "error", "message": "Timeout"}
                
        except aiohttp.ContentTypeError:
            return {"status": "error", "message": "GPU server unavailable"}
        except aiohttp.ClientError:
            return {"status": "error", "message": "Connection error"}
        except Exception:
            return {"status": "error", "message": "Edit failed"}

    finally:
        await gpu_pool.release_gpu(gpu, "flux")

async def process_standard_batch(jobs):
    if not jobs: return []
    gpu = await gpu_pool.wait_for_available_gpu("flux", timeout=120.0)
    if not gpu: return [{"status": "error", "message": "No GPU available"} for _ in jobs]
    await gpu_pool.reserve_gpu(gpu, "flux")
    try:
        workflow = load_workflow("flux_image.json")
        batch_size = len(jobs)
        prompts = [j.prompt for j in jobs]
        while len(prompts) < 4: prompts.append("")

        POS_NODE = "75:74"
        NEG_NODE = "75:67"
        LATENT_NODE = "75:66"
        NOISE_NODE = "75:73"

        if POS_NODE in workflow:
            workflow[POS_NODE]["inputs"].update({
                "batch_size": batch_size,
                "text_1": prompts[0],
                "text_2": prompts[1],
                "text_3": prompts[2],
                "text_4": prompts[3]
            })
        
        if NEG_NODE in workflow:
            workflow[NEG_NODE]["inputs"].update({
                "batch_size": batch_size,
                "text_1": "",
                "text_2": "",
                "text_3": "",
                "text_4": ""
            })

        if LATENT_NODE in workflow:
            workflow[LATENT_NODE]["inputs"]["batch_size"] = batch_size

        if NOISE_NODE in workflow:
            workflow[NOISE_NODE]["inputs"]["noise_seed"] = random.randint(1, 10**15)

        try:
            response = await queue_prompt(workflow, gpu.url, gpu.api_key)
            prompt_id = response.get("prompt_id")
        except aiohttp.ContentTypeError:
            return [{"status": "error", "message": "GPU server unavailable"} for _ in jobs]
        except aiohttp.ClientError:
            return [{"status": "error", "message": "Connection error"} for _ in jobs]
        except:
            return [{"status": "error", "message": "Generation failed"} for _ in jobs]
        
        if not prompt_id:
            msg = response.get("error", {}).get("message", "Workflow rejected")
            return [{"status": "error", "message": msg} for _ in jobs]

        history_entry = await wait_for_image(prompt_id, gpu.url, gpu.api_key)
        final_responses = []
        if history_entry:
            outputs = history_entry.get("outputs", {})
            save_node = "9"
            if save_node in outputs and "images" in outputs[save_node]:
                images_list = outputs[save_node]["images"]
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
