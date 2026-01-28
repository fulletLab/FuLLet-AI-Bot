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
        job = Job(priority, prompt, context, user_id, is_edit, input_image_bytes, input_filename, model_type)
        await self.queue.put(job)
        return self.queue.qsize()

    async def start_worker(self, processor_callback):
        self.is_running = True
        while self.is_running:
            job = await self.queue.get()
            try:
                await processor_callback(job)
            except Exception as e:
                print(f"Error: {e}")
            finally:
                self.queue.task_done()

queue_manager = QueueManager()
