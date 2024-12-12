import discord
from discord.ext import commands
from custom.database import Database

class Controller(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()


    @discord.app_commands.command(name="dbtestt")
    async def dbtestt(self, interaction: discord.Interaction):
        try:
            self.db.cur.execute("SELECT 1")
            await interaction.response.send_message("Database connection is good!")
        except Exception as e:
            await interaction.response.send_message(f"Database connection failed: {e}")

    async def cleanup(self):
        self.db.conn.close
        self.db.cur.close


    async def cog_unload(self):
        await self.cleanup()


async def setup(bot):
    await bot.add_cog(Controller(bot))

