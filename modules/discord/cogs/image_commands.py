import discord
from discord import app_commands
from discord.ext import commands
from modules.queue_manager.manager import queue_manager
from modules.utils.db_manager import get_db_session, save_db_session

PROMPTS = ["hyperrealistic, 8k", "cyberpunk city", "fantasy landscape", "portrait", "3d render"]
PROMPTS_EDIT = ["Exactly the same image, don't change anything, but in a realistic style", "change the background", "change the lighting", "change the composition", "change the style", "change the colors"]

class ImageCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="imagine", description="Generate image")
    @app_commands.choices(model=[
        app_commands.Choice(name="Flux (Schnell)", value="flux"),
        app_commands.Choice(name="Z-Image (Turbo)", value="z-image")
    ])
    async def imagine(self, interaction: discord.Interaction, model: str, prompt: str):
        await interaction.response.defer(ephemeral=True)
        sessions = self.bot.get_cog("SessionManager")
        channel = await sessions.get_or_create(interaction)
        save_db_session(interaction.user.id, channel.id, img_bytes=None, img_name=None)
        q_pos = await queue_manager.add_job(
            priority=(0 if interaction.user.guild_permissions.administrator else 1),
            prompt=prompt, context=channel, user_id=interaction.user.id,
            is_edit=False, model_type=model
        )
        await interaction.followup.send(f"Queued (Pos: {q_pos}) in: {channel.mention}", ephemeral=True)

    @imagine.autocomplete("prompt")
    async def imagine_auto(self, interaction: discord.Interaction, current: str):
        return [app_commands.Choice(name=c, value=c) for c in PROMPTS if current.lower() in c.lower()][:25]

    @app_commands.command(name="edit", description="Edit image")
    @app_commands.choices(model=[
        app_commands.Choice(name="Flux (Schnell)", value="flux")
    ])
    async def edit(self, interaction: discord.Interaction, new_prompt: str, image: discord.Attachment = None, model: str = "flux"):
        await interaction.response.defer(ephemeral=True)
        img_bytes, img_name = None, None
        if image:
            if any(image.filename.lower().endswith(e) for e in [".png",".jpg",".jpeg",".webp"]):
                img_bytes, img_name = await image.read(), image.filename
            else:
                return await interaction.followup.send("Invalid format.", ephemeral=True)

        db_s = get_db_session(interaction.user.id)
        if not img_bytes and (not db_s or not db_s.last_img_bytes):
            return await interaction.followup.send("No image found.", ephemeral=True)

        sessions = self.bot.get_cog("SessionManager")
        channel = await sessions.get_or_create(interaction)
        q_pos = await queue_manager.add_job(
            priority=(0 if interaction.user.guild_permissions.administrator else 1),
            prompt=new_prompt, context=channel, user_id=interaction.user.id,
            is_edit=True, input_image_bytes=img_bytes, input_filename=img_name,
            model_type=model
        )
        await interaction.followup.send(f"Queued (Pos: {q_pos}) in: {channel.mention}", ephemeral=True)

    @edit.autocomplete("new_prompt")
    async def edit_auto(self, interaction: discord.Interaction, current: str):
        return [app_commands.Choice(name=c, value=c) for c in PROMPTS_EDIT if current.lower() in c.lower()][:25]

async def setup(bot):
    await bot.add_cog(ImageCommands(bot))
