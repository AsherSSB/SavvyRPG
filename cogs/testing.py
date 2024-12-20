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


# currently used by both players and enemies, should maybe change that later
class Cooldown():
    def __init__(self, name, emoji, stats: WeaponStatTable, active, acted):
        self.name: str = name
        self.emoji: str = emoji
        self.stats: WeaponStatTable = stats
        self.active: Callable = active
        self.acted: str = acted

    def in_range(self, mypos, targetpos) -> bool:
        if abs(targetpos - mypos) <= self.stats.rng:
            return True
        return False

    def miss(self) -> bool:
        if random.random() < self.stats.acc:
            return False
        return True

    def calculate_crit(self) -> int:
        if random.random() < self.stats.cc:
            return self.stats.cm
        return 1.0
    
    # only applicable to PLAYERS do NOT call for enemy cooldowns
    def scale_damage(self, player:PlayableCharacter):
        playerstats = player.stats.to_dict()
        playerstats = playerstats[self.stats.stat]
        if playerstats > 10:
            self.stats.dmg = int(self.stats.dmg * self.stats.scalar * playerstats)

@dataclass
class Weapon(Item):
    cooldown: Cooldown
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


class EnemyCooldown(Cooldown):
    def __init__(self, name, emoji, stats, active, acted):
        super().__init__(name, emoji, stats, active, acted)

    def attack(self, player: PlayableCharacter, playerhealthpools: list[int], playerindex: int) -> str:
        if self.miss():
            return f"missed {self.name}"
        mult = self.calculate_crit()
        hit = f"crit {self.acted}" if mult > 1.0 else self.acted
        dmg = int(self.stats.dmg * mult)
        playerhealthpools[playerindex] -= dmg
        return f"{hit} {player.name} for {dmg} damage"


class Enemy():
    def __init__(self, name:str, stats:NPCStatTable, drops:Drops, attack:EnemyCooldown, position:int):
        self.name = name
        self.stats = stats
        self.drops = drops
        self.attack = attack
        self.position = position


class SingleTargetAttack(Cooldown):
    def __init__(self, name, emoji, stats, acted):
        super().__init__(name=name, emoji=emoji, stats=stats, acted=acted, active=self.attack)

    def attack(self, enemy:Enemy) -> str:
        if self.miss():
            return f"missed {self.name}"
        mult = self.calculate_crit()
        hit = f"crit {self.acted}" if mult > 1.0 else self.acted
        dmg = int(self.stats.dmg * mult)
        enemy.stats.hp = enemy.stats.hp - dmg
        return f"{hit} {enemy.name} for {dmg} damage"


# TODO: implement range logic for cooldowns
# TODO: implement range logic for enemies
# TODO: give weapons knockback 
# TODO: implement knockback logic to use cooldown function
# TODO: implement target selection for cooldowns
# TODO: implement enemy dodge and resistance logic
# TODO: run probability should be the difference between player and enemy spd
# TODO: implement status effects
class CombatInstance():
    def __init__(self, players:list[PlayableCharacter], cooldowns:list[list[Cooldown]], enemies:list[Enemy], bounds:tuple[int]):
        self.bounds = bounds
        self.players = players
        self.cooldowns = cooldowns
        self.playerhealthpools:list[int] = self.initialize_player_healthpools()
        self.playerpositions = self.initialize_player_positions()
        self.enemies = enemies
        self.enemy_tasks = []
        self.scale_cooldown_damages(self.cooldowns, self.characters)
        # TODO: broken, pass correct values
        self.embed = CombatEmbed(self.pc, self.pchp, self.enemy)
        self.logcount = 0

    # TODO: REFACTOR THIS NIGHTMARE
    async def combat(self, interaction: discord.Interaction):
        choice = 0
        # TODO: replace temp indexing of cooldowns with specific player when implementing multiplayer
        # TODO: move view to instance
        view = self.initialize_combat_view(interaction, self.cooldowns[0])
        await interaction.response.send_message("Combat", view=view, embed=self.embed)
        # TODO: move enemy tasks to instance
        self.enemy_tasks = self.initialize_enemy_tasks(interaction)
       
        while self.enemy.stats.hp > 0:
            # if player hp < 1
            if self.pchp <= 0:
                self.stop_tasks_and_views(view)
                return
            
            # check before and after input if player died
            # TODO: refactor to literally anything else
            try:
                await asyncio.wait_for(view.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                continue  # Continue the loop if timeout occurs

            if self.pchp <= 0:
                self.stop_tasks_and_views(view)
                return
                    
            # TODO: refactor run to a cooldown
            choice = view.choice
            if choice == -1:
                if self.try_run():
                    self.stop_tasks_and_views(view)
                    return
                
                else:
                    view.children[0].disabled = True
                    self.embed = self.embed.insert_field_at(-2, name="Failed to Run", value="Run option disabled", inline=False)
                    self.logcount += 1
                    self.trim_embed()
                    await self.fix_embed_players(interaction)
                    await interaction.edit_original_response(view=view)
            else:
                # TODO: select enemy to attack if there is more than 1 enemy
                # TODO: do attack here
                # if not in range tell user
                # else call cooldown.attack and use cooldown
                await self.use_cooldown(cds[choice], self.enemy, interaction)
                self.logcount += 1

            view.event = asyncio.Event()
            
        self.stop_tasks_and_views(view)

    def stop_tasks_and_views(self, view:discord.ui.View):
        view.stop()
        view.clear_items()
        self.kill_all_enemy_tasks()

    def kill_all_enemy_tasks(self):
        for task in self.enemy_tasks:
            task.cancel()

    def initialize_enemy_tasks(self, interaction):
        [asyncio.create_task(self.enemy_attack(interaction)) for _ in self.enemies]

    def initialize_player_positions(self):
        return [self.bounds[0] for _ in self.players]

    def initialize_player_healthpools(self):
        return [self.calculate_player_hp(player) for player in self.players]

    def scale_cooldown_damages(self, all_players_cooldowns: list[list[Cooldown]], players: list[PlayableCharacter]):
        for i, player in enumerate(players):
            for cooldown in all_players_cooldowns[i]:
                cooldown.scale_damage(player)

    async def use_cooldown(self, message, interaction:discord.Interaction):
        self.embed = self.embed.insert_field_at(-2, name=f"{self.pc.name} ", value=message, inline=False)
        self.trim_embed()
        await self.fix_embed_players(interaction)

    def initialize_combat_view(self, interaction, cds:tuple[Cooldown]):
        view = CombatView(interaction)
        for i, cd in enumerate(cds):
            view.add_item(CooldownButton(cd.name, i, cd.stats.spd, cd.emoji))
        return view

    async def enemy_attack(self, interaction:discord.Interaction):
        while self.enemy.stats.hp > 0 and self.pchp > 0:
            await asyncio.sleep(self.enemy.weapon.stats.spd)
            self.pchp -= self.enemy.weapon.stats.dmg
            self.embed = self.embed.insert_field_at(-2, name=f"{self.enemy.name} struck {self.pc.name}", value=f"for {self.enemy.weapon.stats.dmg} damage", inline=False)
            self.logcount += 1
            self.trim_embed()
            await self.fix_embed_players(interaction)
            if self.pchp <= 0:
                return

    async def fix_embed_players(self, interaction:discord.Interaction):
        self.embed.set_field_at(-1, name=self.enemy.name, value=f"hp: {self.enemy.stats.hp}")
        self.embed.set_field_at(-2, name=self.pc.name, value=f"hp {self.pchp}")
        await interaction.edit_original_response(embed=self.embed)

    def trim_embed(self):
        if self.logcount > 10:
            self.embed = self.embed.remove_field(0)

    def try_run(self):
        # prob = self.calculate_run_probability()
        prob = 0.5
        return random.random() < prob
    
    def calculate_run_probability(self):
        advantage = self.pc.stats.att - self.enemy.stats.speed
        return 0.5 + 0.05 * advantage
    
    def calculate_player_hp(self, player:PlayableCharacter):
        return int((10 + (player.level * 2)) * (player.stats.wil * .1))


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

class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        punchcd = SingleTargetAttack("Punch", "👊", WeaponStatTable(
            dmg=10, spd=3.5, rng=1, cc=0.2, cm=1.5, acc=.9, scalar=.1, stat="str"
        ), acted="punched")

        pummelcd = SingleTargetAttack("Pummel", "✊", WeaponStatTable(
            dmg=30, spd=7.5, rng=0, cc=0.2, cm=1.5, acc=0.9, scalar=0.1, stat="str" 
        ), acted="pummeled")    

        pc:PlayableCharacter = PlayableCharacter(
            "Player", "test", sts.Human(), sts.Barbarian(), xp=0, gold=0)

        enemy:Enemy = Enemy("Training Dummy", 
                    NPCStatTable(120, 0, 0), 
                    Drops(1, 1, None),
                    Weapon(name="Stick Arms", value=0, 
                        stats=WeaponStatTable(dmg=1, spd=2.5, rng=1, cc=.1, cm=1.5, acc=.25, scalar=0, stat="str"),
                        scale="str"))
    
    @discord.app_commands.command(name="combat")
    async def test_combat(self, interaction:discord.Interaction):
        instance = CombatInstance()
        interaction = await self.send_testing_view(interaction)
        await instance.test_combat(interaction)
        await interaction.edit_original_response(content="Combat Over", view=None)
        await asyncio.sleep(8.0)
        await interaction.delete_original_response()

    async def send_testing_view(self, interaction:discord.Interaction):
        view = TestingView()
        await interaction.response.send_message("## Combat Test\nThis test is for demonstration purposes only and is not representative of any finished product.", view=view)
        await view.wait()
        await interaction.delete_original_response()
        return view.interaction

async def setup(bot):
    await bot.add_cog(Testing(bot))