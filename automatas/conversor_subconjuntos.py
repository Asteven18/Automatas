from estado import Estado
from automata import Automata
from transicion import EPSILON


class ConversorSubconjuntos:
    def __init__(self):
        self.pasos = []

    def epsilonClausura(self, estados, afn):
        #Solo trancisiones epsilon, no se mueve con simbolos
        clausura = set(estados)
        pila = list(estados)

        while pila:
            estado = pila.pop()
            for t in afn.transicionesDesde(estado, EPSILON):
                if t.estadoDestino not in clausura:
                    clausura.add(t.estadoDestino)
                    pila.append(t.estadoDestino)

        return clausura

    def mover(self, conjuntoEstados, simbolo, afn):
        """Movimiento de estados con un simbolo."""
        destino = set()
        for estado in conjuntoEstados:
            for t in afn.transicionesDesde(estado, simbolo):
                destino.add(t.estadoDestino)
        return destino

    def nfaToDfa(self, afn):
        """Algoritmo de subconjuntos completo: AFN -> AFD."""
        self.pasos = []
        afd = Automata()
        afd.alfabeto = set(afn.alfabeto)

        contador_id = 0
        conjuntos_vistos = {}  # (ids AFN) -> Estado del AFD

        def obtener_o_crear_estado_afd(conjunto_frozenset, conjunto_estados_afn):
            nonlocal contador_id
            if conjunto_frozenset in conjuntos_vistos:
                return conjuntos_vistos[conjunto_frozenset]
            es_aceptacion = any(e.esAceptacion for e in conjunto_estados_afn)
            nuevo = Estado(contador_id, es_aceptacion)
            contador_id += 1
            conjuntos_vistos[conjunto_frozenset] = nuevo
            afd.agregarEstado(nuevo)
            return nuevo

        clausura_inicial = self.epsilonClausura({afn.estadoInicial}, afn)
        clave_inicial = frozenset(e.id for e in clausura_inicial)
        estado_inicial_afd = obtener_o_crear_estado_afd(clave_inicial, clausura_inicial)
        afd.estadoInicial = estado_inicial_afd

        self.pasos.append(
            f"Estado inicial del AFD = ε-clausura({afn.estadoInicial}) = "
            f"{{{', '.join(str(e) for e in clausura_inicial)}}} -> {estado_inicial_afd}"
        )

        pendientes = [(clave_inicial, clausura_inicial)]
        procesados = set()
        
        #Recorremos los conjuntos de estados pendientes para procesarlos y generar las transiciones del AFD
        while pendientes:
            clave_actual, conjunto_actual = pendientes.pop(0)
            #Si ya procesamos este conjunto, lo saltamos
            if clave_actual in procesados:
                continue
            procesados.add(clave_actual)
            estado_actual_afd = conjuntos_vistos[clave_actual]

            #Recorremos cada simbolo del alfabeto para generar las transiciones del AFD
            for simbolo in sorted(afd.alfabeto):
                movidos = self.mover(conjunto_actual, simbolo, afn)
                if not movidos:
                    continue
                clausura = self.epsilonClausura(movidos, afn)
                clave_nueva = frozenset(e.id for e in clausura)

                nuevo_es_nuevo = clave_nueva not in conjuntos_vistos
                estado_destino_afd = obtener_o_crear_estado_afd(clave_nueva, clausura)
                afd.agregarTransicion(estado_actual_afd, estado_destino_afd, simbolo)

                self.pasos.append(
                    f"mover({{{', '.join(str(e) for e in conjunto_actual)}}}, '{simbolo}') "
                    f"-> ε-clausura = {{{', '.join(str(e) for e in clausura)}}} "
                    f"=> {estado_actual_afd} --{simbolo}--> {estado_destino_afd}"
                    + ("  [ESTADO NUEVO]" if nuevo_es_nuevo else "")
                )

                if clave_nueva not in procesados:
                    pendientes.append((clave_nueva, clausura))

        return afd