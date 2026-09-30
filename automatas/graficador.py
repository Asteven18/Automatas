from graphviz import Digraph
from transicion import EPSILON

class Graficador:
    def imprimirTabla(self, automata, titulo="Autómata"):
        print(f"\n___ Tabla de transiciones: {titulo} ___")
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
        dot.node("_inicio_", shape="none", label="")
        dot.edge("_inicio_", str(automata.estadoInicial.id))

        for estado in automata.listaEstados:
            forma = "doublecircle" if estado.esAceptacion else "circle"
            dot.node(str(estado.id), label=f"q{estado.id}", shape=forma)

        for t in automata.listaTransiciones:
            dot.edge(str(t.estadoOrigen.id), str(t.estadoDestino.id), label=t.simbolo)

        ruta = dot.render(filename=nombre_archivo, cleanup=True)
        return ruta

    def generar_dot(self, automata, titulo="Autómata", highlight_nodes=None):
        """Genera un objeto Digraph con estilo técnico y limpio."""
        if highlight_nodes is None:
            highlight_nodes = set()
        elif isinstance(highlight_nodes, (list, tuple)):
            highlight_nodes = set(highlight_nodes)

        dot = Digraph(name=titulo, format="svg", encoding="utf-8")
        dot.attr(rankdir="LR", bgcolor="transparent", margin="0.2", nodesep="0.45", ranksep="0.65")
        dot.attr("node", fontname="system-ui, -apple-system, sans-serif", fontsize="11", penwidth="2")
        dot.attr("edge", fontname="system-ui, -apple-system, sans-serif", fontsize="10", penwidth="1.6")

        # Entrada al estado inicial
        dot.node("_inicio_", shape="none", label="", width="0", height="0")
        dot.edge("_inicio_", f"q{automata.estadoInicial.id}", color="#38bdf8", penwidth="2")

        for estado in automata.listaEstados:
            es_activo = estado.id in highlight_nodes
            forma = "doublecircle" if estado.esAceptacion else "circle"

            if es_activo:
                fill = "#fef08a"
                borde = "#eab308"
                color_texto = "#0f172a"
            elif estado.esAceptacion:
                fill = "#1e293b"
                borde = "#f59e0b"
                color_texto = "#f8fafc"
            else:
                fill = "#0f172a"
                borde = "#38bdf8"
                color_texto = "#f8fafc"

            dot.node(
                f"q{estado.id}",
                label=f"q{estado.id}",
                shape=forma,
                style="filled",
                fillcolor=fill,
                color=borde,
                fontcolor=color_texto
            )

        # Agrupar transiciones entre el mismo origen y destino para fusionar etiquetas
        grupos = {}
        for t in automata.listaTransiciones:
            clave = (t.estadoOrigen.id, t.estadoDestino.id)
            if clave not in grupos:
                grupos[clave] = []
            grupos[clave].append(t.simbolo)

        for (orig, dest), simbolos in grupos.items():
            es_eps = all(s == EPSILON for s in simbolos)
            etiqueta = ", ".join(simbolos)
            if es_eps:
                dot.edge(
                    f"q{orig}",
                    f"q{dest}",
                    label=etiqueta,
                    style="dashed",
                    color="#a78bfa",
                    fontcolor="#c4b5fd"
                )
            else:
                dot.edge(
                    f"q{orig}",
                    f"q{dest}",
                    label=etiqueta,
                    color="#38bdf8",
                    fontcolor="#94a3b8"
                )

        return dot

    def generar_svg(self, automata, titulo="Autómata", highlight_nodes=None):
        """Genera el contenido SVG en formato string."""
        dot = self.generar_dot(automata, titulo=titulo, highlight_nodes=highlight_nodes)
        try:
            svg = dot.pipe(format="svg").decode("utf-8")
            return svg
        except Exception as e:
            return f"<!-- Error generando SVG con Graphviz: {e} -->"