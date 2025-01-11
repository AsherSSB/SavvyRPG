import discord
from discord.ext import commands
from cogs.database import Database
from custom.playable_character import PlayableCharacter


class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(self.bot)

    @discord.app_commands.command(name="checkgoldandxp")
    async def check_gold_and_xp(self, interaction: discord.Interaction):
        player: PlayableCharacter = self.db.get_character(interaction.user.id)
        await interaction.response.send_message(f"gold:{player.gold}, xp:{player.xp}")

    async def cleanup(self):
        self.db.conn.close
        self.db.cur.close

    async def cog_unload(self):
        await self.cleanup()


async def setup(bot):
    await bot.add_cog(Testing(bot))
