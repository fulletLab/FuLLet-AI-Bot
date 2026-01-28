import json
import urllib.request
import urllib.parse
import random
import time
import asyncio
import os
import aiohttp
from modules.utils.image_filter import sanitize_image

COMFY_URL = os.getenv("COMFY_URL")
COMFY_API_KEY = os.getenv("COMFY_API_KEY")
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_headers():
    headers = {}
    if COMFY_API_KEY:
        headers["Authorization"] = f"Bearer {COMFY_API_KEY}"
    return headers

def load_workflow(filename):
    path = os.path.join(ROOT_DIR, "flujos", filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Workflow file not found at {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

async def queue_prompt(workflow):
    p = {"prompt": workflow}
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{COMFY_URL}/prompt", json=p, headers=get_headers()) as response:
            return await response.json()

async def get_history(prompt_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{COMFY_URL}/history/{prompt_id}", headers=get_headers()) as response:
            return await response.json()

async def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{COMFY_URL}/view", params=data, headers=get_headers()) as response:
            return await response.read()

async def upload_image(image_bytes, filename):
    clean_bytes = sanitize_image(image_bytes)
    if not clean_bytes:
        raise Exception("Image sanitization failed")

    clean_filename = os.path.splitext(filename)[0] + ".jpg"
    
    data = aiohttp.FormData()
    data.add_field('image', clean_bytes, filename=clean_filename)
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{COMFY_URL}/upload/image", data=data, headers=get_headers()) as response:
            return await response.json()

async def wait_for_image(prompt_id, timeout=300):
    start_time = time.time()
    while time.time() - start_time < timeout:
        history = await get_history(prompt_id)
        if prompt_id in history:
            return history[prompt_id]
        await asyncio.sleep(2)
    return None

async def process_image_gen(prompt, input_image_bytes=None, input_filename=None, model_type="flux"):
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
            upload_result = await upload_image(input_image_bytes, input_filename)
            workflow["103"]["inputs"]["image"] = upload_result["name"]
        except Exception as e:
            return {"status": "error", "message": "Image upload failed"}
    
    try:
        response = await queue_prompt(workflow)
        prompt_id = response.get("prompt_id")
    except Exception as e:
        return {"status": "error", "message": "Connection error"}
    
    if not prompt_id:
        return {"status": "error", "message": "Queue full"}

    history_entry = await wait_for_image(prompt_id)
    
    if history_entry:
        try:
            outputs = history_entry.get("outputs", {})
            for node_id, node_output in outputs.items():
                if "images" in node_output:
                    image_data = node_output["images"][0]
                    image_bytes = await get_image(image_data["filename"], image_data["subfolder"], image_data["type"])
                    return {
                        "status": "success", 
                        "image_bytes": image_bytes, 
                        "filename": image_data["filename"]
                    }
        except: pass
                
    return {"status": "error", "message": "Generation failed"}
