from graphviz import Digraph
from transicion import EPSILON

class Graficador:
    def imprimirTabla(self, automata, titulo="Autómata"):
        print(f"\n______ Tabla de transiciones: {titulo} ______")
        print(f"Estado inicial      : {automata.estadoInicial}")
        print(f"Estados aceptación  : {automata.estadosAceptacion}")
        print(f"Alfabeto            : {sorted(automata.alfabeto)}")
        print(f"{'Origen':<10}{'Símbolo':<10}{'Destino':<10}")
        print("-" * 30)
        for t in sorted(automata.listaTransiciones, key=lambda x: (x.estadoOrigen.id, x.simbolo)):
            print(f"{str(t.estadoOrigen):<10}{t.simbolo:<10}{str(t.estadoDestino):<10}")
        print("=" * 45)

    def dibujar(self, automata, nombre_archivo, titulo="Autómata"):
        """Genera un archivo png con el diagrama del autómata."""
        dot = Digraph(name=titulo, format="png")
        dot.attr(rankdir="LR", label=titulo, fontsize="14")

        # nodo invisible que apunta al estado inicial
        dot.node("__inicio__", shape="none", label="")
        dot.edge("__inicio__", str(automata.estadoInicial.id))

        for estado in automata.listaEstados:
            forma = "doublecircle" if estado.esAceptacion else "circle"
            dot.node(str(estado.id), label=f"q{estado.id}", shape=forma)

        for t in automata.listaTransiciones:
            dot.edge(str(t.estadoOrigen.id), str(t.estadoDestino.id), label=t.simbolo)

        ruta = dot.render(filename=nombre_archivo, cleanup=True)
        return ruta
