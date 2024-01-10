from discord.ext.commands.errors import MissingRequiredArgument, BadArgument
from discord.ext.commands import CommandNotFound
from discord.ext import commands
from asyncio import sleep
import discord

from dados import Servidor
from usuarios import buscar_clan, atualizar_cargos

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.roles = True
bot = commands.Bot(command_prefix = commands.when_mentioned, intents = intents)    

config_disc = Servidor()

ID_DISC = 375656099321479170
ID_BOASVINDAS = 375701166614380555

# Lista de pessoas com resposta pendente sobre vivar representante em votações.
para_votar = set()

async def loop_semanal():
    while True:
        await sleep(604800) # Uma semana.
        sem_atualizar = await atualizar_cargos(bot, ID_DISC)
        config_disc.sem_atualizar = sem_atualizar
        config_disc.salvar_dados()

async def validar_nome(message):
    # Nomes no rune só vão até 12 caracteres.
    if len(message.content) > 12:
        return
    
    AUTOR = message.author

    # Pessoa já tem cargo(s), então não precisa receber de novo.
    if AUTOR.user.roles:
        return
    
    # 'message.content' é para ser o RSN da pessoa, dito por ela mesma.
    clan, rank = await buscar_clan(message.content)
    if not clan:
        return await message.channel.send(
            f'O seu clã não foi encontrado dentre os luso-brasileiros. Entre em contato com alguém da moderação para resolver este problema! {AUTOR.mention}'
        )

    DISC_CLANS = bot.get_guild(ID_DISC)
    
    for member in DISC_CLANS.members:
        if member == AUTOR:
            continue
        if member.name in message.content or member.display_name in message.content:
            return await message.channel.send(
                f'Já existe alguém com este nome no servidor. Entre em contato com alguém da moderação para resolver este problema! {AUTOR.mention}'
            )

    cargo_clan = None

    for role in DISC_CLANS.roles:
        if role.name == clan:
            await AUTOR.add_roles(role)
            cargo_clan = role

    # O clã da pessoa ainda não existe no Discord dos Clãs.
    if not AUTOR.user.roles:
        cargo_clan = await DISC_CLANS.create_role(name = clan)
        await AUTOR.add_roles(cargo_clan)

    if rank in ('Owner', 'Deputy Owner', 'Overseer', 'Coordinator'):
        # Cargo de 'Líder de Clã'.
        await AUTOR.add_roles(DISC_CLANS.get_role(721503125822898226))

    membros_mesmo_clan = [member for member in DISC_CLANS.members if cargo_clan in member.roles]
    cargo_votar = await DISC_CLANS.get_role(721503125822898226)
    para_votar = [member for member in membros_mesmo_clan if discord.utils.get(member.roles, name = cargo_votar)]
    if not para_votar:
        para_votar.add(AUTOR)
        await message.channel.send(
            f'Não há ninguém responsável por participar de votações em nome de seu clã, {AUTOR.mention}. Você gostaria de ser o responsável? Responda "Sim" para confirmar. '
        )

    # Cargo de 'Ativos'.
    await AUTOR.add_roles(DISC_CLANS.get_role(375666393758040065))

    await AUTOR.edit(nick = message.content)

@bot.command()
async def membros(ctx):
    nomes = '\n'.join(config_disc.sem_atualizar)
    await ctx.message.channel.send(
        f"A seguir estão o(s) nome(s) daquele(s) cujo cargo de clã está(ão) errado(s) {ctx.message.author.mention}:\n\n{nomes}"
    )

@bot.event
async def on_member_join(member):
    if config_disc.enviar_boas_vindas:
        await bot.get_guild(ID_DISC).get_channel(ID_BOASVINDAS).send(
            config_disc.boas_vindas(member.mention)
        )

@bot.event
async def on_ready():
    await bot.change_presence(activity = discord.Game(name = 'em mundo BR.'))
    print(f'>> {bot.user} on-line!')

    # Deixar aqui rodando eternamente.
    await loop_semanal()

@bot.event
async def on_message(message):            
    if message.author.bot:
        return

    if not message.author.guild_permissions.administrator:
        return
    
    if message.channel.id == ID_BOASVINDAS:
        AUTOR = message.author.display_name
        if AUTOR in para_votar:
            lower = message.content.lower
            if "sim" in lower:
                cargo_votar = await bot.get_guild(ID_DISC).get_role(721503125822898226)
                AUTOR.add_roles(cargo_votar)
                para_votar.remove(AUTOR)
                
                await message.channel.send(
                    f'Você foi colocado como responsável por votar em nome de seu clã, {AUTOR.mention}!'
                )
        else:
            await validar_nome(message)

    await bot.process_commands(message)

if __name__ == '__main__':
    bot.run(config_disc.token)