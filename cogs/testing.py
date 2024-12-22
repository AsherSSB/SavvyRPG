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
class Entity():
    name: str
    hp: int
    position: int


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
    def __init__(self, name, emoji, stats, acted):
        super().__init__(name, emoji, stats, self.attack, acted)

    def attack(self, entities: list[Entity], playerindex: int) -> str:
        if self.miss():
            return f"missed {self.name}"
        mult = self.calculate_crit()
        hit = f"crit {self.acted}" if mult > 1.0 else self.acted
        dmg = int(self.stats.dmg * mult)
        entities[playerindex].hp -= dmg
        return f"{hit} {entities[playerindex].name} for {dmg} damage"


class Enemy():
    def __init__(self, name:str, stats:NPCStatTable, drops:Drops, attack:EnemyCooldown, position:int):
        self.name = name
        self.stats = stats
        self.drops = drops
        self.attack = attack
        self.position = position


class SingleTargetAttack(Cooldown):
    def __init__(self, name, emoji, stats, acted):
        super().__init__(name, emoji, stats, self.attack, acted)

    def attack(self, enemy:Entity) -> str:
        if self.miss():
            return f"missed {self.name}"
        mult = self.calculate_crit()
        hit = f"crit {self.acted}" if mult > 1.0 else self.acted
        dmg = int(self.stats.dmg * mult)
        enemy.hp -= dmg
        return f"{hit} {enemy.name} for {dmg} damage"
    

# TODO: implement range logic for enemies
# TODO: give weapons knockback 
# TODO: implement knockback logic to use cooldown function
# TODO: implement enemy dodge and resistance logic
# TODO: run probability should be the difference between player and enemy spd
# TODO: implement status effects
# TODO: implement "practical stats" for players during combat
# TODO: buttons turn gray if out of range
class CombatInstance():
    def __init__(self, interaction:discord.Interaction, players:list[PlayableCharacter], cooldowns:list[list[Cooldown]], enemies:list[Enemy], bounds:tuple[int]):
        self.interaction = interaction
        self.bounds = bounds
        self.enemies:list[Enemy] = enemies
        self.players: list[PlayableCharacter] = players
        self.cooldowns: list[list[Cooldown]] = cooldowns
        self.entities: list[Entity] = self.initialize_entities()
        self.enemy_tasks = []
        self.scale_cooldown_damages(self.cooldowns, self.players)
        self.embed_handler = CombatEmbedHandler(self.entities, self.interaction)
        # TODO: currently only works for 1 player
        self.view = self.initialize_combat_view(interaction, self.cooldowns[0])
        self.logcount = 0
        self.result: bool | None = None
        self.initialize_enemy_cooldowns()

    async def combat(self):
        choice = 0
        await self.interaction.response.send_message("Combat", view=self.view, embed=self.embed_handler.embed)
        self.enemy_tasks = self.initialize_enemy_tasks()
       
        while len(self.enemy_tasks) > 0 and self.result == None:
            # if player hp < 1
            if self.entities[0].hp <= 0:
                self.stop_tasks_and_views()
                return
            
            # check before and after input if player died
            # TODO: refactor to literally anything else
            try:
                await asyncio.wait_for(self.view.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                continue  # Continue the loop if timeout occurs

            if self.entities[0].hp <= 0:
                self.stop_tasks_and_views()
                return
                    
            # TODO: run might be spammable?
            choice = self.view.choice
            if choice == -1:
                if self.try_run():
                    self.stop_tasks_and_views()
                    return
                await self.embed_handler.log("Failed to Run", "Run option disabled")

            else:
                # only works with 1 player
                target = self.entities[self.view.target + 1] 
                cooldown = self.cooldowns[0][choice]
                if cooldown.in_range(self.entities[0].position, target.position):
                    # TODO: this only works with singletargetattack class
                    await self.use_cooldown(cooldown.attack(target), 0)
                    if target.hp <= 0:
                        self.cleanup_enemy_task(self.view.target)
                        # TODO: fix select menu

                else:
                    await self.append_user_not_in_range(0)

            self.view.event = asyncio.Event()
            
        self.stop_tasks_and_views()

    def initialize_enemy_cooldowns(self):
        cds = []
        for enemy in self.enemies:
            cds.append(enemy.attack)
        self.cooldowns.append(cds)

    def initialize_entities(self) -> list[Entity]:
        entities: list[Entity] = []
        for player in self.players:
            entities.append(Entity(player.name, self.calculate_player_hp(player), self.bounds[0]))
        for enemy in self.enemies:
            entities.append(Entity(enemy.name, enemy.stats.hp, self.bounds[1]))
        return entities

    def cleanup_enemy_task(self, enemyindex):
        self.enemy_tasks[enemyindex].cancel()
        del self.enemy_tasks[enemyindex]
        del self.enemies[enemyindex]

    async def append_user_not_in_range(self, playerindex):
        await self.embed_handler.log(f"{self.players[playerindex].name}", "Out of Range!")

    def stop_tasks_and_views(self):
        self.view.stop()
        self.view.clear_items()
        self.kill_all_enemy_tasks()

    def kill_all_enemy_tasks(self):
        for task in self.enemy_tasks:
            task.cancel()

    def initialize_enemy_tasks(self):
        return [asyncio.create_task(self.enemy_attack(i)) for i, _ in enumerate(self.enemies)]

    def initialize_player_positions(self):
        return [self.bounds[0] for _ in self.players]

    def scale_cooldown_damages(self, all_players_cooldowns: list[list[Cooldown]], players: list[PlayableCharacter]):
        for i, player in enumerate(players):
            for cooldown in all_players_cooldowns[i]:
                cooldown.scale_damage(player)

    async def use_cooldown(self, message, playerindex):
        await self.embed_handler.log(self.players[playerindex].name, message)

    # currently initializes all cooldowns on row 1
    # errors out if the user has > 5 cooldowns
    def initialize_combat_view(self, interaction, cds:tuple[Cooldown]):
        view = CombatView(interaction, self.embed_handler)
        for i, cd in enumerate(cds):
            view.add_item(CooldownButton(cd.name, i, cd.stats.spd, cd.emoji, row=1))
        view.add_item(EnemySelectMenu([enemy.name for enemy in self.enemies]))
        view.add_item(BackButton(self.bounds, self.entities, 0))
        view.add_item(ForwardButton(self.bounds, self.entities, 0))
        return view

    # TODO: only works for 1 player and 1 enemy
    # TODO: Should use EnemyCooldown class

    async def enemy_attack(self, enemy_index: int):
        entities = self.entities
        entity_index = len(self.players) + enemy_index
        cd: EnemyCooldown = self.cooldowns[-1][enemy_index]

        while entities[entity_index].hp > 0 and entities[0].hp > 0:
            if self.enemy_in_range(entities[entity_index], entities[0], cd.stats.rng):
                await asyncio.sleep(1.5)
                if self.enemy_in_range(entities[entity_index], entities[0], cd.stats.rng):
                    message = cd.attack(entities, 0)
                    await self.embed_handler.log(entities[entity_index].name, message)
            else:
                self.move_toward_player(entities, entity_index, 0)
                await self.embed_handler.fix_embed_players()
                await asyncio.sleep(1.0)

    def enemy_in_range(self, enemy, player, range):
        return abs(enemy.position - player.position) <= range

    def move_toward_player(self, entities, enemyindex, playerindex):
        if entities[enemyindex].position < entities[playerindex].position:
            entities[enemyindex].position += 1
        elif entities[enemyindex].position > entities[playerindex].position:
            entities[enemyindex].position -= 1
#



    # always uses player 0 because run only works in single player
    def try_run(self):
        prob = self.calculate_run_probability(self.players[0])
        return random.random() < prob
    
    # TODO: properly implement once player "practical stats" are implemented
    def calculate_run_probability(self, player: PlayableCharacter):
        # advantage = self.players[playerindex] - self.enemy.stats.speed
        # return 0.5 + 0.05 * advantage
        return 0.5
    
    def calculate_player_hp(self, player:PlayableCharacter):
        return int((10 + (player.level * 2)) * (player.stats.wil * .1))


class CombatEmbed(discord.Embed):
    def __init__(self):
        super().__init__(color=None, title="Combat", description=None)


class CombatEmbedHandler():
    def __init__(self, entities: list[Entity], interaction:discord.Interaction):
        self.embed = CombatEmbed()
        self.logcount = 0
        self.entities = entities
        self.interaction = interaction
        for entity in entities:
            self.embed.add_field(name=entity.name, value=f"hp: {entity.hp}\nposition:{entity.position}", inline=True)

    async def log(self, name: str, message: str):
        self.embed = self.embed.insert_field_at(-2, name=name, value=message, inline=False)
        self.logcount += 1
        self.trim()
        await self.fix_embed_players()

    def trim(self):
        if self.logcount > 10:
            self.embed = self.embed.remove_field(0)

    async def fix_embed_players(self):
        for i in range(1, len(self.entities) + 1):
            entity = self.entities[-i]
            self.embed.set_field_at(-i, name=entity.name, value=f"hp: {entity.hp}\nposition: {entity.position}")
        await self.interaction.edit_original_response(embed=self.embed)

class CooldownButton(discord.ui.Button):
    def __init__(self, label, choiceid, cooldowntime, emoji, row):
        super().__init__(style=discord.ButtonStyle.blurple, label=label, emoji=discord.PartialEmoji(name=emoji), row=row)
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


class EnemySelectOption(discord.SelectOption):
    def __init__(self, label: str, value: int):
        super().__init__(label=label, value=str(value))


class EnemySelectMenu(discord.ui.Select):
    def __init__(self, enemies: list[str], min_values=1, max_values=1):
        self.enemies = enemies
        options = self.initialize_options(enemies)
        super().__init__(placeholder=f"targeting: {enemies[0]}", min_values=min_values, 
                         max_values=max_values, options=options, row=0)

    def initialize_options(self, enemies: list[str]):
        return [EnemySelectOption(enemy, i) for i, enemy in enumerate(enemies)]

    async def callback(self, interaction: discord.Interaction):
        selected_option = int(self.values[0])  # Convert the selected value back to integer
        self.view.target = selected_option
        self.placeholder = f"targeting: {self.enemies[selected_option]}"
        await self.view.interaction.edit_original_response(content=f"{self.view.target}", view=self.view)
        await interaction.response.defer()


class RunButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.red, label="Run", row=4)

    async def callback(self, interaction):
        self.disabled = True
        await self.view.interaction.edit_original_response(view=self.view)
        self.view.choice = -1
        await interaction.response.defer()
        self.view.event.set()


class CombatView(discord.ui.View):
    def __init__(self, interaction:discord.Interaction, embed_handler):
        super().__init__()
        self.embed_handler = embed_handler
        self.event = asyncio.Event()
        self.choice:int
        self.interaction = interaction
        self.target: int = 0
        self.add_item(RunButton())

    async def wait(self):
        await self.event.wait()


class ForwardButton(discord.ui.Button):
    def __init__(self, bounds, entities: list[Entity], entityid):
        self.entities = entities
        self.id = entityid
        self.bounds = bounds
        super().__init__(style=discord.ButtonStyle.secondary, label="", emoji=discord.PartialEmoji(name="▶"), row=2)
        
    async def callback(self, interaction):
        if self.entities[self.id].position < self.bounds[1]:
            self.entities[self.id].position += 1
            await self.view.embed_handler.fix_embed_players()
        await interaction.response.defer() # ▶ ◀


class BackButton(discord.ui.Button):
    def __init__(self, bounds, entities: list[Entity], entityid):
        self.entities = entities
        self.id = entityid
        self.bounds = bounds
        super().__init__(style=discord.ButtonStyle.secondary, label="", emoji=discord.PartialEmoji(name="◀"), row=2)
        
    async def callback(self, interaction):
        if self.entities[self.id].position > self.bounds[0]:
            self.entities[self.id].position -= 1
            await self.view.embed_handler.fix_embed_players()
        await interaction.response.defer() # ▶ ◀


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

        self.punchcd = SingleTargetAttack("Punch", "👊", WeaponStatTable(
            dmg=10, spd=3.5, rng=1, cc=0.2, cm=1.5, acc=.9, scalar=.1, stat="str"
        ), acted="punched")

        self.pummelcd = SingleTargetAttack("Pummel", "✊", WeaponStatTable(
            dmg=30, spd=7.5, rng=0, cc=0.2, cm=1.5, acc=0.9, scalar=0.1, stat="str" 
        ), acted="pummeled")    

        self.pc:PlayableCharacter = PlayableCharacter(
            "Player", "test", sts.Human(), sts.Barbarian(), xp=0, gold=0)

        # CombatInstance(interaction:discord.Interaction, players:list[PlayableCharacter], cooldowns:list[list[Cooldown]], enemies:list[Enemy], bounds:tuple[int])
    @discord.app_commands.command(name="combat")
    async def test_combat(self, interaction:discord.Interaction):
        enemy:Enemy = Enemy("Training Dummy", 
                    NPCStatTable(120, 0, 0), 
                    Drops(1, 1, None),
                    EnemyCooldown("Smack", None, WeaponStatTable(
            dmg=1, spd=7.5, rng=0, cc=0.2, cm=2.0, acc=0.9, scalar=0.1, stat="str" 
        ), "smaccd"), 0)

        interaction = await self.send_testing_view(interaction)
        instance = CombatInstance(interaction, [self.pc], [[self.punchcd, self.pummelcd]], [enemy], (0, 3))
        await instance.combat()
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