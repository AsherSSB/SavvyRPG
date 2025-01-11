import psycopg2
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import custom.playable_character as pc
import custom.stattable as origins
import asyncio
import json
from custom.gear import Item, Loadout
import jsonpickle


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

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                user_id BIGINT PRIMARY KEY,
                name TEXT NOT NULL,
                gender TEXT NOT NULL,
                race TEXT NOT NULL,
                origin TEXT NOT NULL,
                strength INTEGER NOT NULL,
                will INTEGER NOT NULL,
                dexterity INTEGER NOT NULL,
                intelligence INTEGER NOT NULL,
                attunement INTEGER NOT NULL,
                xp INTEGER NOT NULL,
                gold INTEGER NOT NULL
            );
        """)

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                user_id BIGINT NOT NULL,
                slot_id INTEGER NOT NULL,
                item_data JSONB NOT NULL,
                PRIMARY KEY (user_id, slot_id)
            );
        """)

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS equipment (
                user_id BIGINT NOT NULL,
                slot_type TEXT NOT NULL,
                item_data JSONB NOT NULL,
                PRIMARY KEY (user_id, slot_type)
            );
        """)
        self.conn.commit()

    def save_inventory(self, user_id: int, items: list[Item]):
        # Clear existing inventory
        self.cur.execute("DELETE FROM inventory WHERE user_id = %s;", (user_id,))

        # PICKLE EVERYTHING
        for slot_id, item in enumerate(items):
            item_json = jsonpickle.encode(item)
        # Insert new items
            self.cur.execute("""
                    INSERT INTO inventory (user_id, slot_id, item_data)
                    VALUES (%s, %s, %s);
                """, (user_id, slot_id, json.dumps(item_json)))
        self.conn.commit()

    def load_inventory(self, user_id: int) -> list[Item]:
        self.cur.execute("""
            SELECT item_data FROM inventory
            WHERE user_id = %s
            ORDER BY slot_id;
        """, (user_id,))

        items = []
        for row in self.cur.fetchall():
            item = jsonpickle.decode(row[0])
            items.append(item)
        return items

    def save_equipment(self, user_id: int, loadout: Loadout):
        # Clear existing equipment
        self.cur.execute("DELETE FROM equipment WHERE user_id = %s;", (user_id,))

        # Save each equipment piece
        for slot_type, gear in vars(loadout).items():
            if gear is not None:
                gear_json = jsonpickle.encode(gear)
                self.cur.execute("""
                    INSERT INTO equipment (user_id, slot_type, item_data)
                    VALUES (%s, %s, %s);
                """, (user_id, slot_type, json.dumps(gear_json)))
        self.conn.commit()

    def load_equipment(self, user_id: int) -> Loadout:
        gear_pieces = {
            "head": None,
            "chest": None,
            "hands": None,
            "legs": None,
            "feet": None
        }

        self.cur.execute("""
            SELECT slot_type, item_data FROM equipment
            WHERE user_id = %s;
        """, (user_id,))

        for row in self.cur.fetchall():
            slot_type, data = row[0], jsonpickle.decode(row[1])

            gear_pieces[slot_type] = data

        return Loadout(**gear_pieces)

    async def delete_character(self, interaction:discord.Interaction):
        self.cur.execute("DELETE FROM characters WHERE user_id = %s;", (interaction.user.id,))
        self.conn.commit()
        await interaction.response.send_message("Character deleted")
        await asyncio.sleep(2.0)
        await interaction.delete_original_response()

    def add_character(self, uid, character):
        self.cur.execute("""
            INSERT INTO characters (user_id, name, gender, race, origin, strength, will, dexterity, intelligence, attunement, xp, gold)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (uid, character.name, character.gender, str(character.race), str(character.origin),
              character.stats.str, character.stats.wil, character.stats.dex,
              character.stats.int, character.stats.att, character.xp, character.gold))
        self.conn.commit()

    def user_exists(self, user_id):
        self.cur.execute("""
            SELECT EXISTS(SELECT 1 FROM characters WHERE user_id = %s);
        """, (user_id,))
        return self.cur.fetchone()[0]

    def get_character(self, uid):
        self.cur.execute("""
            SELECT name, gender, race, origin, strength, will, dexterity, intelligence, attunement, xp, gold
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
                xp=row[9],
                gold=row[10]
            )
        return None

    def add_gold(self, user_id, amount):
        self.cur.execute("""
            UPDATE characters
            SET gold = gold + %s
            WHERE user_id = %s;
        """, (amount, user_id))
        self.conn.commit()

    def add_xp(self, user_id, amount):
        self.cur.execute("""
            UPDATE characters
            SET xp = xp + %s
            WHERE user_id = %s;
        """, (amount, user_id))
        self.conn.commit()

    def set_gold(self, user_id, amount):
        if amount is not None:
            self.cur.execute("""
                UPDATE characters
                SET gold = %s
                WHERE user_id = %s
            """, (amount, user_id))
            self.conn.commit()

    def set_xp(self, user_id, amount):
        if amount is not None:
            self.cur.execute("""
                UPDATE characters
                SET xp = %s
                WHERE user_id = %s
            """, (amount, user_id))
            self.conn.commit()


async def setup(bot):
    await bot.add_cog(Database(bot))

