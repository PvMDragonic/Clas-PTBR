import json

class Servidor():
    def __init__(self):
        try:
            with open('dados.json', 'r') as arqv:
                self.__dict__.update(json.load(arqv))
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo 'dados.json' não foi encontrado.")

    def salvar_dados(self): 
        with open('dados.json', 'w') as arqv:
            json.dump(self.__dict__, arqv, indent = 4)

    def boas_vindas(self, mention: str):
        return self.msg_bem_vindos.replace("{}", mention)