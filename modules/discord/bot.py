import discord
from discord.ext import commands
from modules.queue_manager.manager import queue_manager
from modules.ai.image_gen import process_image_gen
from modules.utils.db_manager import get_db_session, save_db_session, get_next_image_index
import io
import os
import time

class ImageBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        for ext in ["modules.discord.cogs.admin", "modules.discord.cogs.image_commands", "modules.discord.cogs.sessions"]:
            await self.load_extension(ext)
        
        urls = os.getenv("COMFY_URLS", os.getenv("COMFY_URL", "")).split(",")
        num_workers = len([u for u in urls if u.strip()])
        if num_workers == 0: num_workers = 1
            
        self.loop.create_task(queue_manager.start_worker(self.process_queue_job, num_workers=num_workers))

    async def on_ready(self):
        print(f"Bot: {self.user.name}")
        allowed = os.getenv("ALLOWED_GUILD_ID")
        for guild in self.guilds:
            if allowed and str(guild.id) != allowed:
                await guild.leave()

    async def on_guild_join(self, guild):
        allowed = os.getenv("ALLOWED_GUILD_ID")
        if allowed and str(guild.id) != allowed:
            await guild.leave()

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        raise error

    async def process_queue_job(self, jobs):
        from modules.ai.image_gen import process_image_batch
        
        batch_info = []
        for job in jobs:
            channel = job.context
            db_s = get_db_session(job.user_id)
            img_bytes, img_name = job.input_image_bytes, job.input_filename
            
            if job.is_edit and not img_bytes and db_s and db_s.last_img_bytes:
                img_bytes, img_name = db_s.last_img_bytes, db_s.last_img_name

            job.start_time = time.time()
            await channel.send(f"Batch Processing: `{job.prompt}`")
            batch_info.append(job)

        results = await process_image_batch(batch_info)
        
        for i, result in enumerate(results):
            job = batch_info[i]
            channel = job.context
            
            if result["status"] == "success":
                duration = round(time.time() - job.start_time, 1)
                idx = get_next_image_index()
                name = f"{idx:02d}.jpg"
                
                export_path = os.getenv("EXPORT_PATH")
                if export_path:
                    if not os.path.exists(export_path):
                        try: os.makedirs(export_path)
                        except: pass
                    
                    if os.path.exists(export_path):
                        try:
                            with open(os.path.join(export_path, name), "wb") as f:
                                f.write(result["image_bytes"])
                        except: pass

                save_db_session(job.user_id, channel.id, result["image_bytes"], name)
                file = discord.File(io.BytesIO(result["image_bytes"]), filename=name)
                await channel.send(content=f"Done in {duration}s! <@{job.user_id}>\nPrompt: `{job.prompt}`", file=file)
            else:
                await channel.send(f"Error for `{job.prompt}`: {result.get('message', 'Failed')}")

bot = ImageBot()

def start_bot(token):
    bot.run(token)
