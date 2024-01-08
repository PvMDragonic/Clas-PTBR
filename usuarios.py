from discord.ext import commands
from discord import utils
from time import sleep
import requests
import psycopg2

def nomes_clans() -> list:
    """
    Retorna lista com nomes dos clãs do Ranks PT-BR.

    Retorna:
        list:
            
    """

    try:
        ranks_ptbr_db = psycopg2.connect(
                host = 'localhost', 
                database = 'clansptbr', 
                user = 'postgres',  
                password = 123456
            )

        cur = ranks_ptbr_db.cursor()
        cur.execute("""
            SELECT DISTINCT ON (id_clan) id_clan, nome
            FROM nomes
            ORDER BY id_clan, data_alterado DESC
        """)

        return cur.fetchall()
    finally:
        ranks_ptbr_db.close()

async def atualizar_cargos(bot: commands.Bot, id_disc: int) -> list[str]:
    """
    Atualiza o cargo das pessoas no servidor, de acordo com o clã em que estiverem.

    Retorna:
        list:
            Lista com o(s) nome(s) daquele(s) que não foi(ram) localizado(s), seja por não ter(em) mais clã/ter(em) mudado de nome.
    """

    coletado = [] # Lista com 3 dimensões.
    falhado = []

    clans = nomes_clans()
    for clan in clans:
        sleep(0.25) # Evita de spammar a API.

        res = requests.get(f"http://services.runescape.com/m=clan-hiscores/members_lite.ws?clanName={clan}")
        if res.status_code != 200:
            continue
        
        coletado.append(
            [
                clan,
                res.content.decode('utf-8', errors='replace').replace('\ufffd', ' ').split('\n')[1:]
            ]
        )

    clans_disc = bot.get_guild(id_disc)
    membros_sv = [member for member in clans_disc.members]
    membro_encontrado = False

    for membro in membros_sv:
        membro_encontrado = False
        nome_sv = membro.nick if membro.nick else membro.name

        for (clan_nome, clan_lista) in coletado:
            for pessoa in clan_lista:
                # Não é a pessoa certa.
                if nome_sv != pessoa:
                    continue

                # O cargo da pessoa já tá certo.
                if clan_nome in [role.name for role in membro.roles]:
                    continue

                cargo_clan = utils.get(bot.guild.roles, name = clan_nome)
                if not cargo_clan:
                    cargo_clan = await clans_disc.create_role(name = clan)
                    await membro.add_roles(cargo_clan)
                else:
                    # O cargo do clã fica sempre em último na lista de cargos da pessoa.
                    cargo_a_remover = min(membro.roles, key = lambda role: role.position)
                    await membro.remove_roles(cargo_a_remover)
                    await membro.add_roles(cargo_clan)

                membro_encontrado = True
                break

            if membro_encontrado:
                break

        if not membro_encontrado:
            falhado.append(nome_sv)

    return falhado

# Precisa ser asyncrono pro discord não desconectar o bot.
async def buscar_clan(nome: str) -> list[str] | None:
    """
    Retorna o clã ao qual dado jogador pertence.

    Retorna:
        list: 
            Lista no formato '[Nome do clã, rank dentro do clã]'.
        None:
            Caso não tenha clã.
    """

    try:
        clans = nomes_clans()

        for clan in clans:
            res = requests.get(f"http://services.runescape.com/m=clan-hiscores/members_lite.ws?clanName={clan}")
            if res.status_code != 200:
                continue
            
            jogadores = res.content.decode('utf-8', errors='replace').replace('\ufffd', ' ')
            if nome in jogadores:
                membros = jogadores.split('\n')
                for membro in membros:
                    pessoa, rank, _, _ = membro.split(',')
                    if pessoa == nome:
                        return [clan, rank]
            
        return None
    except Exception as erro:
        print(erro)
        return None