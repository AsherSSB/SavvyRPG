import discord
from discord.ext import commands
from cogs.database import Database
from custom.gear import HandGear, HeadGear, GearStatTable, Item, BonusStatsTable


class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(self.bot)

    @discord.app_commands.command(name="insertitem")
    async def dbinserttest(self, interaction: discord.Interaction):
        inventory = []
        # Create a HandGear item
        gloves = HandGear(
            name="Steel Gauntlets",
            emoji="🧤",
            value=200,
            rarity="Common",
            stats=GearStatTable(
                resist=0.05,  # 5% damage resistance
                maxhp=30,     # +30 max HP
                dodge=0.03,   # 3% dodge chance
                bonus_stats=BonusStatsTable(
                    strength=2,
                    dexterity=1
                )
            ),
            critmult=0.2,    # 20% bonus crit multiplier
            attacks=1        # +1 attacks per turn
        )
        health_potion = Item(
            name="Health Potion",
            emoji="❤️",
            value=50,
            stack_size=99,
            quantity=1
        )

        # Piece of gear (HeadGear)
        magic_helmet = HeadGear(
            name="Mage's Hood",
            emoji="🎭",
            value=1000,
            rarity="Rare",
            stats=GearStatTable(
                resist=0.15,  # 15% damage resistance
                maxhp=50,     # +50 max HP
                dodge=0.05,   # 5% dodge chance
                bonus_stats=BonusStatsTable(
                    intelligence=5,
                    attunement=3
                )
            ),
            critchance=0.10,  # 10% crit chance
            multicast=0.05    # 5% multicast chance
        )

        inventory.append(health_potion)
        inventory.append(magic_helmet)
        inventory.append(gloves)
        self.db.save_inventory(interaction.user.id, inventory)
        await interaction.response.send_message("saved")

    @discord.app_commands.command(name="retrieveinventory")
    async def test_inv_retrieval(self, interaction: discord.Interaction):
        inventory = self.db.load_inventory(interaction.user.id)
        await interaction.response.send_message(content=inventory)

    @discord.app_commands.command(name="deleteinventory")
    async def test_inv_deletion(self, interaction: discord.Interaction):
        self.db.save_inventory(interaction.user.id, [])
        await interaction.response.send_message("reset")

    async def cleanup(self):
        self.db.conn.close
        self.db.cur.close

    async def cog_unload(self):
        await self.cleanup()


async def setup(bot):
    await bot.add_cog(Testing(bot))
