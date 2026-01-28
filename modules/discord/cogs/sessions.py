import discord
from discord.ext import commands
from modules.utils.db_manager import get_db_session, save_db_session, delete_db_session
import time
import asyncio

class SessionManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def auto_delete_loop(self, channel, user_id):
        while True:
            await asyncio.sleep(60)
            db_s = get_db_session(user_id)
            if not db_s: break
            if (time.time() - db_s.updated_at) >= 1800:
                try:
                    delete_db_session(channel.id)
                    await channel.delete()
                except: pass
                break

    async def get_or_create(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        db_s = get_db_session(user_id)
        now = time.time()

        if db_s and db_s.updated_at and (now - db_s.updated_at) < 1800:
            channel = interaction.guild.get_channel(db_s.channel_id)
            if channel:
                try:
                    await channel.set_permissions(interaction.user,
                        view_channel=True,
                        send_messages=True,
                        use_application_commands=True,
                        read_message_history=True,
                        embed_links=True,
                        attach_files=True
                    )
                except: pass
                return channel
            delete_db_session(db_s.channel_id)
        elif db_s:
            delete_db_session(db_s.channel_id)

        category = discord.utils.get(interaction.guild.categories, name="sessions")
        
        ch_name = f"session-{interaction.user.name.lower()}"
        existing_ch = discord.utils.get(interaction.guild.text_channels, name=ch_name)
        if existing_ch:
            save_db_session(user_id, existing_ch.id)
            return existing_ch

        if not category:
            cat_overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
            category = await interaction.guild.create_category("sessions", overwrites=cat_overwrites)

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, use_application_commands=True,
                read_message_history=True, embed_links=True, attach_files=True
            ),
            interaction.guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, attach_files=True,
                embed_links=True, read_message_history=True, manage_channels=True
            )
        }
        channel = await interaction.guild.create_text_channel(
            name=ch_name,
            overwrites=overwrites, category=category
        )
        save_db_session(user_id, channel.id)
        self.bot.loop.create_task(self.auto_delete_loop(channel, user_id))
        return channel

async def setup(bot):
    await bot.add_cog(SessionManager(bot))
