from PIL import Image
import io

def sanitize_image(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        output_buffer = io.BytesIO()
        img.save(output_buffer, format="JPEG", quality=95, subsampling=0)
        
        return output_buffer.getvalue()
    except Exception as e:
        print(f"Sanitization Error: {e}")
        return None
