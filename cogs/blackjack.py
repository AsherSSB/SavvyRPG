import discord
from discord.ext import commands
import random
import asyncio

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
        self.ace_count:bool = 0
        self.can_split:bool = False

    def add_card(self, card:Card) -> None:
        self.hand.cards.append(card)
        self.hand.value += card.value
        if card.rank == "Ace": self.ace_count += 1
        
    def can_burn_ace(self) -> bool:
        if self.ace_count > 0: return True
        else: return False

    def burn_ace(self) -> None:
        self.ace_count -= 1
        self.hand.value-= 10

    def check_split(self) -> None:
        if len(self.hand.cards) == 2 and self.hand.cards[0].rank == self.hand.cards[1].rank:
            self.can_split = True


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

    @discord.app_commands.command(name="play_blackjack")
    async def play_blackjack(self, interaction:discord.Interaction):
        player = self.deal_in_player()
        if player.hand.value != 21:
            await self.play_hand(interaction, player)
        else:
            await interaction.response.send_message(f"{player.hand}\n\n Blackjack!")

    async def play_hand(self, interaction:discord.Interaction, player:Player):
        dealer = self.deal_in_player()
        player.check_split()
        view = GameView(player.can_split)
        content = str(player.hand) + f"\n\nThe Dealer's Card is {self.stringify_draw(dealer.hand.cards[0])}"
        await interaction.response.send_message(content=content, view=view)
        await view.wait()
        choice = view.choice

        while choice == 0:
            player.add_card(self.draw_card())
            content = str(player.hand) + f"\n\nThe Dealer's Card is {self.stringify_draw(dealer.hand.cards[0])}"
            await interaction.delete_original_response()
            interaction = view.interaction
            view = GameView(can_split=False)
            await interaction.response.send_message(content=content, view=view)
            await view.wait()

            

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


async def setup(bot):
    await bot.add_cog(Blackjack(bot))

