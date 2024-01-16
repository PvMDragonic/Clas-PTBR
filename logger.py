from datetime import datetime

class Logger():
    """
        Responsável por fazer o log das atividades do bot.

        Funciona de maneira estática because why not.
    """

    @classmethod
    def adicionar(txt: str) -> None:
        with open('log.txt', 'a') as arqv:
            log = f'[{datetime.now().strftime("%d/%m/%Y, %H:%M")}] {txt}'
            arqv.writelines('log\n')
            print(log)