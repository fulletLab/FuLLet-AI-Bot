import discord
from discord.ext import commands
import os

class AdminTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            existing = discord.utils.get(guild.text_channels, name="admin-tools")
            if existing: continue
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
            await guild.create_text_channel("admin-tools", overwrites=overwrites)

    @commands.command(name="sync", hidden=True)
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx):
        if ctx.channel.name != "admin-tools": return
        self.bot.tree.copy_global_to(guild=ctx.guild)
        synced = await self.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"Sincronizados {len(synced)} comandos localmente.")

    @commands.command(name="clearall", hidden=True)
    @commands.has_permissions(administrator=True)
    async def clearall(self, ctx):
        if ctx.channel.name != "admin-tools": return
        self.bot.tree.clear_commands(guild=ctx.guild)
        await self.bot.tree.sync(guild=ctx.guild)
        self.bot.tree.clear_commands(guild=None)
        await self.bot.tree.sync()
        await ctx.send("Cache global y local limpio.")

    @commands.command(name="getid", hidden=True)
    @commands.has_permissions(administrator=True)
    async def getid(self, ctx):
        if ctx.channel.name != "admin-tools": return
        await ctx.send(f"ID: `{ctx.guild.id}`")


async def setup(bot):
    await bot.add_cog(AdminTools(bot))
