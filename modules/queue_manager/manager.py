import asyncio
import time

class Job:
    def __init__(self, priority, prompt, context, user_id, is_edit=False, input_image_bytes=None, input_filename=None, model_type="flux"):
        self.priority = priority
        self.prompt = prompt
        self.context = context
        self.user_id = user_id
        self.is_edit = is_edit
        self.input_image_bytes = input_image_bytes
        self.input_filename = input_filename
        self.model_type = model_type
        self.timestamp = time.time()
        self.start_time = 0

    def __lt__(self, other):
        if self.priority == other.priority:
            return self.timestamp < other.timestamp
        return self.priority < other.priority

class QueueManager:
    def __init__(self):
        self.queue = asyncio.PriorityQueue()
        self.is_running = False

    async def add_job(self, priority, prompt, context, user_id, is_edit=False, input_image_bytes=None, input_filename=None, model_type="flux"):
        user_id_str = str(user_id)
        active_count = 0
        
        tmp_queue = []
        while not self.queue.empty():
            item = await self.queue.get()
            if str(item.user_id) == user_id_str:
                active_count += 1
            tmp_queue.append(item)
            
        for item in tmp_queue:
            await self.queue.put(item)
            
        if active_count >= 2:
            return -1

        job = Job(priority, prompt, context, user_id, is_edit, input_image_bytes, input_filename, model_type)
        await self.queue.put(job)
        return self.queue.qsize()

    async def start_worker(self, processor_callback):
        self.is_running = True
        while self.is_running:
            jobs = []
            job = await self.queue.get()
            jobs.append(job)
            
            start_wait = time.time()
            while len(jobs) < 4:
                remaining = 2.0 - (time.time() - start_wait)
                if remaining <= 0:
                    break
                try:
                    next_job = await asyncio.wait_for(self.queue.get(), timeout=remaining)
                    jobs.append(next_job)
                except asyncio.TimeoutError:
                    break
            
            try:
                await processor_callback(jobs)
            except Exception as e:
                print(f"Error: {e}")
            finally:
                for _ in range(len(jobs)):
                    self.queue.task_done()

queue_manager = QueueManager()
