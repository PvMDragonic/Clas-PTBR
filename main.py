from discord.ext.commands import CommandNotFound
from discord.ext import commands
from datetime import datetime
from asyncio import sleep
import discord

from dados import Servidor
from logger import Logger
from usuarios import buscar_clan, atualizar_cargos, buscar_blacklist

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix = commands.when_mentioned, intents = intents)    

config_disc = Servidor()
para_votar = set()

ID_DISC = 375656099321479170
ID_BOASVINDAS = 375701166614380555

async def loop_semanal(tempo: int):
    while True:
        await sleep(tempo)
        config_disc.sem_atualizar = await atualizar_cargos(bot, ID_DISC)
        config_disc.tempo_loop = tempo = int(datetime.timestamp(datetime.now()))
        config_disc.salvar_dados()
        Logger.adicionar('Loop semanal concluído.')

async def validar_nome(message):
    # Nomes no rune só vão até 12 caracteres.
    if len(message.content) > 12:
        return
    
    AUTOR = message.author

    # Pessoa já tem cargo(s), então não precisa receber de novo.
    if AUTOR.user.roles:
        return
    
    if config_disc.verificar_bl:
        meliantes = await buscar_blacklist()
        if any(nome in meliantes for nome in [AUTOR.name, AUTOR.display_name, message.content]):
            return await message.channel.send(f'O seu nome consta na black-list dos clãs. Entre em contato com alguém da moderação para resolver este problema! {AUTOR.mention}')

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

    membros_mesmo_clan = [member for member in DISC_CLANS.members if cargo_clan in member.roles]

    if rank in ('Owner', 'Deputy Owner', 'Overseer', 'Coordinator'):
        cargo_lider = await DISC_CLANS.get_role(375692963248078848)
        quantia_lideres = [member for member in membros_mesmo_clan if member.role == cargo_lider]
        if config_disc.quantia_lideres > len(quantia_lideres):
            # Cargo de 'Líder de Clã'.
            await AUTOR.add_roles(DISC_CLANS.get_role(375692963248078848))

    cargo_votar = await DISC_CLANS.get_role(721503125822898226)
    pessoa_para_votar = [member for member in membros_mesmo_clan if member.role == cargo_votar]
    if not pessoa_para_votar:
        para_votar.add(AUTOR)
        await message.channel.send(
            f'Não há ninguém responsável por participar de votações em nome de seu clã, {AUTOR.mention}. Você gostaria de ser o responsável? Responda "Sim" para confirmar. '
        )

    # Cargo de 'Ativos'.
    await AUTOR.add_roles(DISC_CLANS.get_role(375666393758040065))
    await AUTOR.edit(nick = message.content)
    Logger.adicionar(f'{AUTOR.name} entrou pelo clã {clan}.')

async def enviar_comandos(message):
    embed = discord.Embed(
        title = "COMANDOS CLÃS PT-BR",
        description = "Lista de comandos do bot.\n\n᲼᲼",
        color = 0x7a8ff5
    )

    comandos = [
        ("@Clãs PT-BR membros", "O bot envia uma lista com os nomes daqueles que estão com o cargo de clã incorreto, seja porque mudaram de clã ou de nome.\n᲼᲼"),
        ("@Clãs PT-BR lideres [número]", "Define um limite de líderes de clã para um único clã. \
            Ao atingir o limite definido, novos membros daquele clã (mesmo que tenham cargo alto) não receberão o cargo de líder.\n᲼᲼"),
        ("@Clãs PT-BR blacklist", "Ativa/desativa a verificação de nomes listados na black-list dos clãs na hora da identificação.\n᲼᲼"),
        ("@Clãs PT-BR boasvindas", "Atualiza a mensagem de boas-vindas para quem entrar no servidor. Use `{}` para indicar onde a marcação da pessoa deve ficar na mensagem.\n᲼᲼"),
        ("@Clãs PT-BR teste", "Testa a mensagem de boas-vindas, enviando-a como se a pessoa tivesse acabado de entrar.\n᲼᲼"),
    ]

    for cmd, descricao in comandos:
        embed.add_field(name = cmd, value = descricao, inline = False)

    embed.set_footer(text = "OBS.: Não usar [ ] nos comandos; é apenas para demonstrar os parâmetros.")

    await message.channel.send(embed = embed)

@bot.command()
async def lideres(ctx, *args):
    quantos = args[0]
    config_disc.quantos_lideres = quantos
    config_disc.salvar_dados()
    Logger.adicionar(f'Limite de líderes por clã atualizado para {quantos} por {ctx.message.author.name}')

    await ctx.message.channel.send(
        f"O número máximo de líderes de clã por clã foi alterado para `{quantos}`! {ctx.message.author.mention}"
    )

@bot.command()
async def membros(ctx):
    nomes = '\n'.join(config_disc.sem_atualizar)
    await ctx.message.channel.send(
        f"A seguir estão o(s) nome(s) daquele(s) cujo cargo de clã está(ão) errado(s) {ctx.message.author.mention}:\n\n{nomes}"
    )

@bot.command()
async def blacklist(ctx):
    config_disc.verificar_bl = not config_disc.verificar_bl
    config_disc.salvar_dados()

    status = 'ativada' if config_disc.verificar_bl else 'desativada'
    Logger.adicionar(f'Verificação da black-list {status} por {ctx.message.author.name}.')

    await ctx.message.channel.send(
        f"A verificação de meliantes da black-list dos clãs foi `{status}`! {ctx.message.author.mention}"
    )

@bot.command()
async def boasvindas(ctx, *args):
    config_disc.msg_bem_vindos = " ".join(args)
    config_disc.salvar_dados()

    await ctx.message.channel.send(
        f"A mensagem de boas-vindas foi atualizada; use `@Clãs PT-BR teste` para testar como ela ficou! {ctx.message.author.mention}"
    )

@bot.command()
async def teste(ctx):
    await ctx.message.channel.send(
        config_disc.boas_vindas(ctx.message.author.mention)
    )

@bot.event
async def on_member_join(member):
    Logger.adicionar(f'Usuário {member.name} entrou para o servidor.')
    if config_disc.enviar_boas_vindas:
        await bot.get_guild(ID_DISC).get_channel(ID_BOASVINDAS).send(
            config_disc.boas_vindas(member.mention)
        )

@bot.event
async def on_member_remove(member):
    Logger.adicionar(f'Usuário {member.name} deixou o servidor.')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return await ctx.message.channel.send(
            f"Esse comando não existe! {ctx.message.author.mention}"
        )
    if isinstance(error, discord.Forbidden):
        pass
    raise error

@bot.event
async def on_ready():
    await bot.change_presence(activity = discord.Game(name = 'em mundo BR.'))
    print(f'>> {bot.user} on-line!')

    unix_atual = int(datetime.timestamp(datetime.now()))
    if config_disc.tempo_loop == 0:
        config_disc.tempo_loop = restante = unix_atual
    else:
        config_disc.tempo_loop = unix_atual
        tempo_passado = unix_atual - config_disc.tempo_loop
        restante = 604800 - tempo_passado

    config_disc.salvar_dados()

    # Deixar aqui rodando eternamente.
    await loop_semanal(restante)

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

                Logger.adicionar(f'{AUTOR} recebeu cargo para votar.')
                await message.channel.send(
                    f'Você foi colocado como responsável por votar em nome de seu clã, {AUTOR.mention}!'
                )
        else:
            await validar_nome(message)

    if message.content == '<@1196492724526923786>':
        return await enviar_comandos(message)

    await bot.process_commands(message)

if __name__ == '__main__':
    bot.run(config_disc.token)