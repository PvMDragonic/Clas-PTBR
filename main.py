from discord.ext.commands.errors import MissingRequiredArgument, BadArgument
from discord.ext.commands import CommandNotFound
from discord.ext import commands
import discord

from dados import Servidor

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix = commands.when_mentioned, intents = intents)    

clans = Servidor()

ID_DISC = 375656099321479170
ID_BOASVINDAS = 375701166614380555

@bot.event
async def on_member_join(member):
    if clans.enviar_boas_vindas:
        await bot.get_guild(ID_DISC).get_channel(ID_BOASVINDAS).send(
            clans.boas_vindas(member.mention)
        )