import json

class Servidor():
    def __init__(self):
        try:
            with open('dados.json', 'r') as arqv:
                # Cria os atributos da classe com base no que tem no json.
                self.__dict__.update(json.load(arqv))
        except FileNotFoundError:
            self.msg_bem_vindos = ""
            self.sem_atualizar = []
            self.tempo_loop = 0
            self.token = ""
            self.salvar_dados()

    def salvar_dados(self): 
        with open('dados.json', 'w') as arqv:
            json.dump(self.__dict__, arqv, indent = 4)

    def boas_vindas(self, mention: str):
        return self.msg_bem_vindos.replace("{}", mention)