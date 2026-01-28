import torch
import math

def get_lcm(a, b):
    return abs(a * b) // math.gcd(a, b)

def get_lcm_list(numbers):
    if not numbers: return 1
    res = numbers[0]
    for n in numbers[1:]:
        res = get_lcm(res, n)
    return res

class CLIPTextEncodeBatch:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "clip": ("CLIP", ),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 64}),
                "text_1": ("STRING", {"multiline": True}),
                "text_2": ("STRING", {"multiline": True}),
                "text_3": ("STRING", {"multiline": True}),
                "text_4": ("STRING", {"multiline": True}),
            }
        }
    RETURN_TYPES = ("CONDITIONING",)
    FUNCTION = "encode"
    CATEGORY = "conditioning_batch"

    def encode(self, clip, batch_size, text_1, text_2, text_3="", text_4=""):
        all_texts = [text_1, text_2, text_3, text_4]
        target_size = max(1, batch_size)
        texts = all_texts[:target_size]
        
        while len(texts) < target_size:
            texts.append("")
            
        conds = []
        pooleds = []
        num_tokens = []
        
        for text in texts:
            tokens = clip.tokenize(text if text is not None else "")
            cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
            conds.append(cond)
            pooleds.append(pooled)
            num_tokens.append(cond.shape[1])
        
        if not conds:
            tokens = clip.tokenize("")
            cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
            return ([[cond, {"pooled_output": pooled}]], )

        lcm_val = get_lcm_list(num_tokens)
        final_conds = []
        for cond, num in zip(conds, num_tokens):
            repeat = lcm_val // num if num > 0 else 1
            final_conds.append(cond.repeat(1, repeat, 1))
            
        conds_tensor = torch.cat(final_conds)
        
        valid_pooled = [p for p in pooleds if p is not None]
        if len(valid_pooled) == len(pooleds):
            pooleds_tensor = torch.cat(pooleds)
            return ([[conds_tensor, {"pooled_output": pooleds_tensor}]], )
        elif len(valid_pooled) > 0:

            pooleds_tensor = torch.cat(valid_pooled)
            return ([[conds_tensor, {"pooled_output": pooleds_tensor}]], )
        else:
            return ([[conds_tensor, {}]], )

class StringInput:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"text": ("STRING", {"multiline": True})}}
    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_text"
    CATEGORY = "conditioning_batch"
    def get_text(self, text): return (text, )

class BatchString:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {}}
    RETURN_TYPES = ("BATCH_STRING",)
    FUNCTION = "get_batch"
    CATEGORY = "conditioning_batch"
    def get_batch(self, **kwargs):
        return ([kwargs[f"text{i+1}"] for i in range(len(kwargs))], )

NODE_CLASS_MAPPINGS = {
    "CLIP Text Encode (Batch)": CLIPTextEncodeBatch,
    "String Input": StringInput,
    "Batch String": BatchString
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CLIP Text Encode (Batch)": "CLIP Text Encode Batch (FuLLet)",
    "String Input": "String Input (FuLLet)",
    "Batch String": "Batch String (FuLLet)"
}
