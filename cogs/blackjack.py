import discord
from discord.ext import commands
import random
import asyncio
from cogs.database import Database

class Card:
    def __init__(self, suit, rank, value):
        self.suit:str = suit
        self.rank:str = rank
        self.value:int = value

    def __str__(self):
        return f"{self.rank} of {self.suit}"


class Hand:
    def __init__(self):
        self.cards:list[Card] = []
        self.value:int = 0

    def __str__(self):
        strhand = "Current Hand:"
        for cards in self.cards:
            strhand += f"\n{cards}"
        strhand += f"\nTotal Value: {self.value}"
        return strhand


class Player:
    def __init__(self):
        self.hand = Hand()
        self.ace_count:int = 0
        self.can_split:bool = False

    def add_card(self, card:Card) -> None:
        self.hand.cards.append(card)
        self.hand.value += card.value
        if card.rank == "Ace": 
            self.ace_count += 1
        
    def can_burn_ace(self) -> bool:
        return self.ace_count > 0

    def burn_ace(self) -> None:
        self.ace_count -= 1
        self.hand.value -= 10

    def check_split(self) -> None:
        if len(self.hand.cards) == 2 and self.hand.cards[0].rank == self.hand.cards[1].rank:
            self.can_split = True

# TODO: detect when timout and subtract player gold from db
class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.values = {
            "Ace": 11, "Two": 2, "Three": 3, "Four": 4, "Five": 5, "Six": 6,
            "Seven": 7, "Eight": 8, "Nine": 9, "Ten": 10, "Jack": 10, "Queen": 10, "King": 10
        }
        self.suits = ["Hearts", "Spades", "Clubs", "Diamonds"]
        self.ranks = ["Ace", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Jack", "Queen", "King"]
        random.seed()

    # TODO: delete after integration with RPG
    @discord.app_commands.command(name="blackjacktest")
    async def test_blackjack(self, interaction:discord.Interaction):
        await self.play_blackjack(interaction)

    async def play_blackjack(self, interaction:discord.Interaction):
        # TODO: player gold connection
        view = BetView()
        await interaction.response.send_message("Place Your Bet", view=view)
        await view.wait()
        interaction = view.interaction
        if view.choice == -1:
            # TODO: go back to tavern menu
            pass
        elif view.choice == 0:
            # TODO: send modal for bet placement and retrieve new interaction
            await self.start_blackjack_game(interaction=interaction)
        else:
            self.db.add_gold(interaction.user.id, 100)
            self.play_blackjack(interaction)
            pass

    async def start_blackjack_game(self, interaction:discord.Interaction):
        player = self.deal_in_player()
        if player.hand.value != 21:
            player_won = await self.play_hand(interaction, player)
        else:
            player_won = True
            await interaction.response.send_message(f"{player.hand}\n\n Blackjack! You Win!")
        # TODO: payout player based on win
        await asyncio.sleep(2.0)
        view = ContinueView()
        await interaction.edit_original_response(content="Play Again?", view=view)
        await view.wait()
        if view.choice: 
            await interaction.delete_original_response()
            await self.start_blackjack_game(interaction=view.interaction)
        # TODO: placeholder for navigation back to main menu
        else: 
            await view.interaction.response.defer()
            await interaction.delete_original_response()

    async def try_burn_ace(self, interaction:discord.Interaction, player:Player):
        if player.can_burn_ace():
            player.burn_ace()
            return True
        return False

    async def play_hand(self, interaction:discord.Interaction, player:Player) -> bool:
        dealer = self.deal_in_player()
        player.check_split()
        view = GameView(player.can_split)
        content = str(player.hand) + f"\n\nThe Dealer's Card is {self.stringify_draw(dealer.hand.cards[0])}"
        await interaction.response.send_message(content=content, view=view)
        await view.wait()
        choice = view.choice
        await view.interaction.response.defer()

        if choice == 2:
            player:Player = await self.play_split(interaction, player, dealer)
        if player.hand.value == 21:
            return True

        while choice == 0 and player.hand.value < 21:
            player.add_card(self.draw_card())
            if player.hand.value > 21:
                if not await self.try_burn_ace(interaction, player):
                    await interaction.edit_original_response(content=f"{player.hand}\n\nYou Drew Over 21. You Lose.", view=None)
                    return False
                else:
                    await interaction.edit_original_response(content=f"{player.hand}\n\nAce Set to 1 to Avoid Bust")
            if player.hand.value == 21:
                await interaction.edit_original_response(content=f"{player.hand}\n\n Blackjack! You Win!", view=None)
                return True
            content = str(player.hand) + f"\n\nThe Dealer's Card is {self.stringify_draw(dealer.hand.cards[0])}"
            view = GameView(can_split=False)
            await interaction.edit_original_response(content=content, view=view)
            await view.wait()
            choice = view.choice
            await view.interaction.response.defer()

        await self.play_dealers_turn(interaction, dealer)
        await asyncio.sleep(2.0)

        if dealer.hand.value > player.hand.value and dealer.hand.value <= 21:
            content = f"The Dealer's {dealer.hand.value} is Greater Than Your {player.hand.value}\nYou Lose"
            result = False
        elif dealer.hand.value > 21:
            content = "The Dealer Busted Out.\nYou Win!"
            result = True
        elif dealer.hand.value == player.hand.value:
            content = f"Your {player.hand.value} is Equal to The Dealer's {dealer.hand.value}\nDraw."
            result = False
        else:
            content = f"Your {player.hand.value} is Greater Than The Dealer's {dealer.hand.value}\nYou Win!"
            result = True

        await interaction.edit_original_response(content=content)
        return result

    async def play_split(self, interaction:discord.Interaction, player:Player, dealer:Player) -> Player:
        player.can_split = False
        hand1 = player
        hand2 = Player()
        hand2.add_card(hand1.hand.cards.pop(1))
        hand1.hand.value -= hand1.hand.cards[0].value
        if hand2.hand.cards[0].value == 11:
            hand1.ace_count -= 1
        firstvalue = await self.play_split_hand(interaction, hand1, dealer, "First")
        if firstvalue == 21: 
            return hand1
        secondvalue = await self.play_split_hand(interaction, hand2, dealer, "Second") 
        if secondvalue == 21: 
            return hand2
        if firstvalue >= secondvalue: 
            return hand1
        else: 
            return hand2
        
    async def play_split_hand(self, interaction:discord.Interaction, hand:Player, dealer:Player, handcnt):
        content = f"Playing {handcnt} Hand \n{hand.hand}\nDealer Card: {dealer.hand.cards[0]}"
        view = GameView(False)
        await interaction.edit_original_response(content=content, view=view)
        await view.wait()
        choice = view.choice
        while choice == 0 and hand.hand.value < 21:
            hand.add_card(self.draw_card())
            if hand.hand.value > 21 and not await self.try_burn_ace(interaction, hand):
                await interaction.edit_original_response(content=f"{hand.hand}\n\nYou Drew Over 21. Moving to Next Hand", view=None)
                await view.interaction.response.defer()
                await asyncio.sleep(1.0)
                return 0
            if hand.hand.value == 21:
                await interaction.edit_original_response(content=f"{hand.hand}\n\n Blackjack! You Win!", view=None)
                await view.interaction.response.defer()
                await asyncio.sleep(1.0)
                return 21
            content = str(hand.hand) + f"\n\nThe Dealer's Card is {self.stringify_draw(dealer.hand.cards[0])}"
            await view.interaction.response.defer()
            view = GameView(can_split=False)
            await interaction.edit_original_response(content=content, view=view)
            await view.wait()
            choice = view.choice
        await view.interaction.response.defer()
        return hand.hand.value

    async def play_dealers_turn(self, interaction:discord.Interaction, dealer:Player):
        content = f"The Dealer's {dealer.hand}"
        await interaction.edit_original_response(content=content, view=None)
        while dealer.hand.value < 17:
            await asyncio.sleep(2.0)
            dealer.add_card(self.draw_card())
            content = f"The Dealer's {dealer.hand}"
            await interaction.edit_original_response(content=content)
            if dealer.hand.value > 21:
                await self.try_burn_ace(interaction, dealer)
            
    def stringify_draw(self, card:Card) -> str:
        article = "a"
        if card.rank in ["Ace", "Eight"]:
            article += "n"
        return f"{article} {card.rank} of {card.suit}"

    def deal_in_player(self) -> Player:
        player = Player()
        self.deal_hand(player)
        return player

    def deal_hand(self, player:Player) -> None:
        player.add_card(self.draw_card())
        player.add_card(self.draw_card())
        if player.hand.cards[0].rank == player.hand.cards[1].rank:
            player.can_split = True

    def draw_card(self) -> str:
        suit = self.get_random_suit()
        rank = self.get_random_rank()
        value = self.get_rank_value(rank)
        return Card(suit, rank, value)
    
    def get_random_suit(self) -> str:
        return random.choice(self.suits)

    def get_random_rank(self) -> str:
        return random.choice(self.ranks)

    def get_rank_value(self, rank) -> int:
        return self.values[rank]


class GameView(discord.ui.View):
    def __init__(self, can_split:bool):
        super().__init__()
        self.event = asyncio.Event()
        self.choice:int
        if can_split: 
            split_button = SplitButton()
            self.add_item(split_button)
        self.interaction:discord.Interaction
        

    @discord.ui.button(label="Hit")
    async def hit_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        self.choice = 0
        self.interaction = interaction
        self.event.set()

    @discord.ui.button(label="Stand")
    async def stand_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        self.choice = 1
        self.interaction = interaction
        self.event.set()

    async def wait(self):
        await self.event.wait()


class SplitButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Split")

    async def callback(self, interaction:discord.Interaction):
        self.view.choice = 2
        self.view.interaction = interaction
        self.view.event.set()


class ContinueView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.event = asyncio.Event()
        self.choice:bool
        self.interaction:discord.Interaction
    
    @discord.ui.button(label="Continue")
    async def continue_button(self, interaction, button):
        self.choice = True
        self.interaction = interaction
        self.event.set()

    @discord.ui.button(label="Back")
    async def back_button(self, interaction, button):
        self.choice = False
        self.interaction = interaction
        self.event.set()

    async def wait(self):
        await self.event.wait()


class BetView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.interaction:discord.Interaction
        self.event = asyncio.Event()
        self.choice:int
        self.add_item(BackButton())
    
    @discord.ui.button(label="Bet", style=discord.ButtonStyle.green)
    async def bet_button(self, interaction:discord.Interaction, button):
        self.choice = 0
        self.interaction = interaction
        self.event.set()
    
    @discord.ui.button(label="Give Money", style=discord.ButtonStyle.blurple)
    async def money_button(self, interaction:discord.Interaction, button):
        self.choice = 1
        self.interaction = interaction
        self.event.set()

    async def wait(self):
        await self.event.wait()


class BackButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="Back")

    async def callback(self, interaction: discord.Interaction):
        self.view.choice = -1
        self.view.interaction = interaction
        self.view.event.set()


async def setup(bot):
    await bot.add_cog(Blackjack(bot))

