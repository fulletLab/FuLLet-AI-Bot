import os
import asyncio
import aiohttp
from dataclasses import dataclass, field
from typing import Optional, List, Dict
import time


VRAM_REQUIREMENTS = {
    "flux": 4.0,
    "flux_edit": 5.0,
    "z-image": 5.0
}

DEFAULT_VRAM_GB = 16.0
MIN_FREE_VRAM = float(os.getenv("MIN_FREE_VRAM", "4.0"))


@dataclass
class GPUInstance:
    url: str
    api_key: str
    total_vram: float
    used_vram: float = 0.0
    active_jobs: int = 0
    is_healthy: bool = True
    last_check: float = 0.0
    
    @property
    def free_vram(self) -> float:
        return self.total_vram - self.used_vram
    
    def can_accept(self, model_type: str) -> bool:
        if not self.is_healthy:
            return False
        required = VRAM_REQUIREMENTS.get(model_type, 4.0)
        return self.free_vram >= required
    
    def reserve(self, model_type: str):
        required = VRAM_REQUIREMENTS.get(model_type, 4.0)
        self.used_vram += required
        self.active_jobs += 1
    
    def release(self, model_type: str):
        required = VRAM_REQUIREMENTS.get(model_type, 4.0)
        self.used_vram = max(0, self.used_vram - required)
        self.active_jobs = max(0, self.active_jobs - 1)


class GPUPool:
    def __init__(self):
        self.gpus: List[GPUInstance] = []
        self.lock = asyncio.Lock()
        self._initialize()
    
    def _initialize(self):
        urls_str = os.getenv("COMFY_URLS", "").strip()
        vram_str = os.getenv("GPU_VRAM_GB", "").strip()
        api_key = os.getenv("COMFY_API_KEY", "")
        
        if urls_str:
            urls = [u.strip() for u in urls_str.split(",") if u.strip()]
            vrams = [float(v.strip()) for v in vram_str.split(",") if v.strip()] if vram_str else []
            
            for i, url in enumerate(urls):
                vram = vrams[i] if i < len(vrams) else DEFAULT_VRAM_GB
                self.gpus.append(GPUInstance(url=url, api_key=api_key, total_vram=vram))
        else:
            single_url = os.getenv("COMFY_URL", "http://127.0.0.1:8188")
            self.gpus.append(GPUInstance(url=single_url, api_key=api_key, total_vram=DEFAULT_VRAM_GB))
    
    async def get_best_gpu(self, model_type: str) -> Optional[GPUInstance]:
        async with self.lock:
            available = [gpu for gpu in self.gpus if gpu.can_accept(model_type)]
            if not available:
                return None
            return max(available, key=lambda g: g.free_vram)
    
    async def reserve_gpu(self, gpu: GPUInstance, model_type: str):
        async with self.lock:
            gpu.reserve(model_type)
    
    async def release_gpu(self, gpu: GPUInstance, model_type: str):
        async with self.lock:
            gpu.release(model_type)
    
    async def health_check(self, gpu: GPUInstance) -> bool:
        try:
            headers = {"Authorization": f"Bearer {gpu.api_key}"} if gpu.api_key else {}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{gpu.url}/system_stats", headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    gpu.is_healthy = response.status == 200
        except:
            gpu.is_healthy = False
        gpu.last_check = time.time()
        return gpu.is_healthy
    
    async def wait_for_available_gpu(self, model_type: str, timeout: float = 60.0) -> Optional[GPUInstance]:
        start = time.time()
        while time.time() - start < timeout:
            gpu = await self.get_best_gpu(model_type)
            if gpu:
                return gpu
            await asyncio.sleep(1.0)
        return None
    
    def get_status(self) -> List[Dict]:
        return [
            {
                "url": gpu.url,
                "total_vram": gpu.total_vram,
                "free_vram": gpu.free_vram,
                "active_jobs": gpu.active_jobs,
                "is_healthy": gpu.is_healthy
            }
            for gpu in self.gpus
        ]


gpu_pool = GPUPool()
