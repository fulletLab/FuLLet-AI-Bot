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
                "text_1": ("STRING", {"multiline": True}),
                "text_2": ("STRING", {"multiline": True}),
            },
            "optional": {
                "text_3": ("STRING", {"multiline": True}),
                "text_4": ("STRING", {"multiline": True}),
            }
        }
    RETURN_TYPES = ("CONDITIONING",)
    FUNCTION = "encode"
    CATEGORY = "conditioning_batch"

    def encode(self, clip, text_1, text_2, text_3="", text_4=""):
        texts = [t for t in [text_1, text_2, text_3, text_4] if t.strip()]
        conds = []
        pooleds = []
        num_tokens = []
        
        for text in texts:
            tokens = clip.tokenize(text)
            cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
            conds.append(cond)
            pooleds.append(pooled)
            num_tokens.append(cond.shape[1])
        
        lcm_val = get_lcm_list(num_tokens)
        final_conds = []
        for cond, num in zip(conds, num_tokens):
            repeat = lcm_val // num
            final_conds.append(cond.repeat(1, repeat, 1))
            
        conds_tensor = torch.cat(final_conds)
        pooleds_tensor = torch.cat(pooleds)
        return ([[conds_tensor, {"pooled_output": pooleds_tensor}]], )

NODE_CLASS_MAPPINGS = {
    "CLIPTextEncodeBatch": CLIPTextEncodeBatch
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CLIPTextEncodeBatch": "CLIP Text Encode Batch (FuLLet)"
}
