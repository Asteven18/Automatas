EPSILON = "ε"

class Transicion:
    #constructor
    def __init__(self, estado_origen, estado_destino, simbolo):
        self.estadoOrigen = estado_origen
        self.estadoDestino = estado_destino
        self.simbolo = simbolo

    #compara si el simbolo es igual a epsilon
    def es_epsilon(self):
        return self.simbolo == EPSILON

    #representacion visual
    def __repr__(self):
        return f"({self.estadoOrigen} --{self.simbolo}--> {self.estadoDestino})"
