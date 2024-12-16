import psycopg2
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import custom.playable_character as pc
import custom.stattable as origins


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        load_dotenv()
        password = os.getenv('DB_PASS')
        self.conn = psycopg2.connect(database="SavvyRPG",
                                    host="localhost",
                                    user="postgres",
                                    password=f"{password}",
                                    port="5432")
        self.cur = self.conn.cursor()

    @discord.app_commands.command(name="deletechar")
    async def delete_character(self, interaction:discord.Interaction):
        self.cur.execute("DELETE FROM characters WHERE user_id = %s;", (interaction.user.id,))
        self.conn.commit()
        await interaction.response.send_message("Character deleted")

    def add_character(self, uid, character):
        self.cur.execute("""
            INSERT INTO characters (user_id, name, gender, race, origin, strength, will, dexterity, intelligence, attunement, xp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (uid, character.name, character.gender, str(character.race), str(character.origin),
              character.stats.str, character.stats.wil, character.stats.dex,
              character.stats.int, character.stats.att, character.xp))
        self.conn.commit()

    def user_exists(self, user_id):
        self.cur.execute("""
            SELECT EXISTS(SELECT 1 FROM characters WHERE user_id = %s);
        """, (user_id,))
        return self.cur.fetchone()[0]


    def get_character(self, uid):
        self.cur.execute("""
            SELECT name, gender, race, origin, strength, will, dexterity, intelligence, attunement, xp
            FROM characters
            WHERE user_id = %s;
        """, (uid,))
        row = self.cur.fetchone()
        if row:
            
            return pc.PlayableCharacter(
                name=row[0],
                gender=row[1],
                race=row[2],
                origin=row[3],
                stats=origins.StatTable(
                    row[4],
                    row[5],
                    row[6],
                    row[7],
                    row[8]
                ),
                xp=row[9]
            )
        return None

async def setup(bot):
    await bot.add_cog(Database(bot))
