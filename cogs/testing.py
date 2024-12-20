import discord
from discord.ext import commands
import asyncio 
import custom.stattable as sts
from custom.playable_character import PlayableCharacter
import random
from dataclasses import dataclass, field
from typing import Callable

@dataclass
class Item():
    name: str
    value: int = field(default=0, kw_only=True)
    stack_size: int = field(default=1, kw_only=True)
    quantity: int = field(default=1, kw_only=True)


@dataclass
class WeaponStatTable():
    dmg: int
    spd: float
    rng: int
    cc: float
    cm: float
    acc: float
    scalar: float
    stat: str


@dataclass
class Weapon(Item):
    stats: WeaponStatTable
    scale: str
    slots: int = field(default=2, kw_only=True)


@dataclass
class Drops():
    xp: int
    gold: int
    item: Item | None


@dataclass
class NPCStatTable():
    hp: int
    resist: float
    speed: int


class Enemy():
    def __init__(self, name:str, stats:NPCStatTable, drops:Drops, weapon:Weapon):
        self.name = name
        self.stats = stats
        self.drops = drops
        self.weapon = weapon



class Cooldown():
    def __init__(self, name, emoji, stats: WeaponStatTable, active):
        self.name: str = name
        self.emoji: str = emoji
        self.stats: WeaponStatTable = stats
        self.active: Callable = active
        self.acted: str | None = None

    def miss(self) -> bool:
        if random.random < self.stats.acc:
            return False
        return True

    def calculate_crit(self) -> int:
        if random.random < self.stats.cc:
            return self.stats.cm
        return 1.0
    
    def scale_damage(self, player:PlayableCharacter):
        playerstats = player.stats.to_dict()
        playerstats = playerstats[self.stats.stat]
        if playerstats > 10:
            self.stats.dmg = self.stats.dmg * self.stats.scalar * playerstats
        
def punch_active(enemy:Enemy, cd:Cooldown):
    if cd.miss():
        return "missed Punch"
    mult = cd.calculate_crit()
    hit = "crit punched" if mult > 1.0 else "punched"
    dmg = cd.stats.dmg * mult
    enemy.stats.hp = enemy.stats.hp - dmg
    return f"{hit} {enemy.name} for {dmg}"

punchcd = Cooldown("Punch", "👊", WeaponStatTable(
    dmg=10, spd=3.5, rng=1, cc=0.2, cm=1.5, acc=.9, scalar=.1, stat="str"
), punch_active)

def pummel_active(enemy:Enemy, cd:Cooldown):
    if cd.miss():
        return "missed Pummel"
    mult = cd.calculate_crit()
    hit = "crit pummeled" if mult > 1.0 else "pummeled"
    dmg = cd.stats.dmg * mult
    enemy.stats.hp = enemy.stats.hp - dmg
    return f"{hit} {enemy.name} for {dmg}"

pummelcd = Cooldown("Pummel", "✊", WeaponStatTable(
    dmg=30, spd=7.5, rng=0, cc=0.2, cm=1.5, acc=0.9, scalar=0.1, stat="str" 
), pummel_active)    


class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pc:PlayableCharacter = PlayableCharacter(
            "Player", "test", sts.Human(), sts.Barbarian(), xp=0, gold=0)
        
        self.pcweapon:Weapon = Weapon(name="Fists", value=0, scale="str",
                               stats=WeaponStatTable(5, 1.0, 1, .2, 1.5, .95))
        
        self.enemy:Enemy = Enemy("Training Dummy", 
                         NPCStatTable(120, 0, 0), 
                         Drops(1, 1, None),
                         Weapon(name="Stick Arms", value=0, 
                                stats=WeaponStatTable(1, 2.5, 1, .1, 1.5, .25),
                                scale="str"))
        
        self.pcdmg = self.calculate_player_damage()
        self.pchp: int = 0
        # init embed with player and enemy info
        self.embed = CombatEmbed(self.pc, self.pchp, self.enemy)
        self.logcount = 0

    @discord.app_commands.command(name="combat")
    async def test_combat(self, interaction:discord.Interaction):

        self.pchp = self.calculate_player_hp()
        self.enemy.stats.hp = 120
        self.logcount = 0
        interaction = await self.send_testing_view(interaction)
        await self.combat(interaction)
        await interaction.edit_original_response(content="Combat Over", view=None, embed=None)
        await asyncio.sleep(8.0)
        await interaction.delete_original_response()

    async def send_testing_view(self, interaction:discord.Interaction):
        view = TestingView()
        await interaction.response.send_message("## Combat Test\nThis test is for demonstration purposes only and is not representative of any finished product.", view=view)
        await view.wait()
        await interaction.delete_original_response()
        return view.interaction

    # TODO: CLEAN THIS SHIT UP
    async def combat(self, interaction: discord.Interaction):
        self.embed = CombatEmbed(self.pc, self.pchp, self.enemy)
        choice = 0

        def punch_active(enemyhp):
            if random.random() < .2:
                return ((enemyhp - 15), 15)
            return ((enemyhp - 10), 10)
        punchcd = Cooldown("Punch", "👊", 3.5, punch_active)

        def pummel_active(enemyhp):
            if random.random() < .2:
                return ((enemyhp - 45), 45)
            return ((enemyhp - 30), 30)
        pummelcd = Cooldown("Pummel", "✊", 7.5, pummel_active)

        cds = (punchcd, pummelcd)

        view = self.initialize_combat_view(interaction, cds)
        
        await interaction.response.send_message("Combat", view=view, embed=self.embed)
        
        enemy_task = asyncio.create_task(self.enemy_attack(interaction))

       
        while self.enemy.stats.hp > 0:
            await interaction.edit_original_response(embed=self.embed)
            # if player hp < 1
            if self.pchp <= 0:
                view.stop()
                view.clear_items()
                enemy_task.cancel()
                return
            
            # TODO: fix players able to attack twice on 1 cooldown
            try:
                await asyncio.wait_for(view.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                continue  # Continue the loop if timeout occurs

            # check player hp again after waiting for input
            if self.pchp <= 0:
                enemy_task.cancel()
                view.stop()
                view.clear_items()
                return
                    
            choice = view.choice
            if choice == -1:
                if self.try_run():
                    enemy_task.cancel()
                    view.stop()
                    view.clear_items()
                    return
                
                else:
                    # TODO: can autoclick run, update to be normal cooldown
                    view.children[0].disabled = True
                    self.embed = self.embed.insert_field_at(-2, name="Failed to Run", value="Run option disabled", inline=False)
                    self.logcount += 1
                    self.trim_embed()
                    self.fix_embed_players()
                    await interaction.edit_original_response(view=view)
            else:
                self.enemy.stats.hp = cds[choice].active(self.enemy.stats.hp)
                self.logcount += 1

            view.event = asyncio.Event()
            
        view.stop()
        view.clear_items()
        enemy_task.cancel()
        
    def use_cooldown(self, cooldown: Cooldown, target, targetstat):
        targetstat, dealt = cooldown.active(target)
        self.embed = self.embed.insert_field_at(-2, name=f"{self.pc.name} struck {self.enemy.name}", value=f"for {dealt} damage", inline=False)
        self.trim_embed()
        self.fix_embed_players()


    def initialize_combat_view(self, interaction, cds:tuple[Cooldown]):
        view = CombatView(interaction)
        for i, cd in enumerate(cds):
            view.add_item(CooldownButton(cd.name, i, cd.time, cd.emoji))
        return view

    async def enemy_attack(self, interaction:discord.Interaction):
        while self.enemy.stats.hp > 0 and self.pchp > 0:
            await asyncio.sleep(self.enemy.weapon.stats.spd)
            self.pchp -= self.enemy.weapon.stats.dmg
            self.embed = self.embed.insert_field_at(-2, name=f"{self.enemy.name} struck {self.pc.name}", value=f"for {self.enemy.weapon.stats.dmg} damage", inline=False)
            self.logcount += 1
            self.trim_embed()
            self.fix_embed_players()
            await interaction.edit_original_response(embed=self.embed)
            if self.pchp <= 0:
                return

    def punch(self):
        mult = self.calculate_crit()
        final_dmg = int(self.pcdmg * mult)
        self.enemy.stats.hp -= final_dmg
        self.embed = self.embed.insert_field_at(-2, name=f"{self.pc.name} struck {self.enemy.name}", value=f"for {final_dmg} damage", inline=False)
        self.trim_embed()
        self.fix_embed_players()

    def pummel(self):
        mult = self.calculate_crit()
        final_dmg = int(30 * mult)
        self.enemy.stats.hp -= final_dmg
        self.embed = self.embed.insert_field_at(-2, name=f"{self.pc.name} pummeled {self.enemy.name}", value=f"for {final_dmg} damage", inline=False)
        self.trim_embed()
        self.fix_embed_players()

    def fix_embed_players(self):
        self.embed.set_field_at(-1, name=self.enemy.name, value=f"hp: {self.enemy.stats.hp}")
        self.embed.set_field_at(-2, name=self.pc.name, value=f"hp {self.pchp}")

    def trim_embed(self):
        if self.logcount > 10:
            self.embed = self.embed.remove_field(0)


    def calculate_crit(self):
        if self.try_crit():
            return self.pcweapon.stats.cm
        return 1

    def try_crit(self):
        return random.random() < self.pcweapon.stats.cc

    def try_run(self):
        # prob = self.calculate_run_probability()
        prob = 0.5
        return random.random() < prob
    
    def calculate_run_probability(self):
        advantage = self.pc.stats.att - self.enemy.stats.speed
        return 0.5 + 0.05 * advantage

    def attack(self):
        pass

    def calculate_player_damage(self):
        base = self.pcweapon.stats.dmg
        scales = {
            "str" : self.scale_with_str,
            "dex" : self.scale_with_dex,
            "int" : self.scale_with_int
        }
        return base * scales[self.pcweapon.scale]()
    
    def calculate_player_hp(self):
        return int((10 + (self.pc.level * 2)) * (self.pc.stats.wil * .1))
    
    def scale_with_str(self):
        stat = self.pc.stats.str
        if stat >= 10:
            return int(1 + 0.2 * (stat - 10))
        else:
            return int(1 + 0.1 * (stat - 10))

    def scale_with_dex(self):
        stat = self.pc.stats.dex
        if stat >= 10:
            return int(1 + 0.2 * (stat - 10))
        else:
            return int(1 + 0.1 * (stat - 10))

    def scale_with_int(self):
        stat = self.pc.stats.int
        if stat >= 10:
            return int(1 + 0.2 * (stat - 10))
        else:
            return int(1 + 0.1 * (stat - 10))


class CombatEmbed(discord.Embed):
    def __init__(self, pc:PlayableCharacter, pchp, enemy:Enemy):
        super().__init__(color=None, title="Combat", description=None)
        self.add_field(name=pc.name, value=f"hp: {pchp}", inline=True)
        self.add_field(name=enemy.name, value=f"hp: {enemy.stats.hp}", inline=True)


class CooldownButton(discord.ui.Button):
    def __init__(self, label, choiceid, cooldowntime, emoji):
        super().__init__(style=discord.ButtonStyle.blurple, label=label, emoji=discord.PartialEmoji(name=emoji))
        self.disabled = False
        self.choiceid = choiceid
        self.cd = cooldowntime

    async def callback(self, interaction):
        self.disabled = True
        await self.view.interaction.edit_original_response(view=self.view)
        self.view.choice = self.choiceid
        await interaction.response.defer()
        self.view.event.set()
        await asyncio.sleep(self.cd)
        self.disabled = False
        await self.view.interaction.edit_original_response(view=self.view)


class CombatView(discord.ui.View):
    def __init__(self, interaction:discord.Interaction):
        super().__init__()
        self.event = asyncio.Event()
        self.choice:int
        self.interaction = interaction

    @discord.ui.button(label="Run", style=discord.ButtonStyle.red)
    async def run_button(self, interaction:discord.Interaction, button):
        self.choice = -1
        await interaction.response.defer()
        self.event.set()

    async def wait(self):
        await self.event.wait()


class TestingView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.event = asyncio.Event()
        self.interaction:discord.Interaction

    @discord.ui.button(label="Begin Combat Test", style=discord.ButtonStyle.green)
    async def test_button(self, interaction:discord.Interaction, button):
        self.interaction = interaction
        self.event.set()

    async def wait(self):
        await self.event.wait()

async def setup(bot):
    await bot.add_cog(Testing(bot))