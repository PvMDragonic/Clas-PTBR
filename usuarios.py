import requests
import psycopg2

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
        nomes_clans = cur.fetchall()
        ranks_ptbr_db.close()

        for clan in nomes_clans:
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