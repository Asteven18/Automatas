from transicion import EPSILON, Transicion

class Automata:
    #constructor
    def __init__(self):
        self.estadoInicial = None        # (q₀) estado inicial
        self.estadosAceptacion = []      # (F) estados donde puede finalizar 
        self.listaEstados = []           # (Q) todos los estados del autómata
        self.listaTransiciones = []      # (δ) todas las transiciones (objetos Transicion)
        self.alfabeto = set()            # (Σ) símbolos usados (sin incluir epsilon)

    # métodos
    def agregarEstado(self, estado):
        if estado not in self.listaEstados:
            self.listaEstados.append(estado)
        if estado.esAceptacion and estado not in self.estadosAceptacion:
            self.estadosAceptacion.append(estado)
        return estado

    def agregarTransicion(self, origen, destino, simbolo):
        t = Transicion(origen, destino, simbolo)
        self.listaTransiciones.append(t)
        if simbolo != EPSILON:
            self.alfabeto.add(simbolo)
        return t

    # consultas
    def transicionesDesde(self, estado, simbolo=None):
        """Devuelve las transiciones que salen de 'estado' (filtradas por símbolo si se indica)."""
        resultado = []
        for t in self.listaTransiciones:
            if t.estadoOrigen == estado and (simbolo is None or t.simbolo == simbolo):
                resultado.append(t)
        return resultado

    # representacion visual
    def __repr__(self):
        return (f"Automata(inicial={self.estadoInicial}, "
                f"aceptacion={self.estadosAceptacion}, "
                f"#estados={len(self.listaEstados)}, "
                f"#transiciones={len(self.listaTransiciones)})")
