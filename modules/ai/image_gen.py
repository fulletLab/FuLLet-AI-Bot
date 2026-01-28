from modules.ai.comfy_api import process_image_gen as gen_logic, process_image_batch as gen_logic_batch

async def process_image_gen(prompt, input_image_bytes=None, input_filename=None, model_type="flux"):
    try:
        return await gen_logic(prompt, input_image_bytes, input_filename, model_type)
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def process_image_batch(jobs):
    try:
        return await gen_logic_batch(jobs)
    except Exception as e:
        return [{"status": "error", "message": str(e)} for _ in jobs]
