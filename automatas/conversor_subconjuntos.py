from estado import Estado
from automata import Automata
from transicion import EPSILON


class ConversorSubconjuntos:
    def _init_(self):
        self.pasos = []
        self.pasos_detallados = []
        self.tabla_subconjuntos = []
        self.mapeo_subconjuntos = {}  # id_afd -> list of ids_afn

    def epsilonClausura(self, estados, afn):
        # Solo transiciones epsilon, no se mueve con simbolos
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
        self.pasos_detallados = []
        self.mapeo_subconjuntos = {}
        self.tabla_subconjuntos = []

        afd = Automata()
        afd.alfabeto = set(afn.alfabeto)

        contador_id = 0
        conjuntos_vistos = {}  # (ids AFN) -> Estado del AFD

        def obtener_o_crear_estado_afd(conjunto_frozenset, conjunto_estados_afn):
            nonlocal contador_id
            if conjunto_frozenset in conjuntos_vistos:
                return conjuntos_vistos[conjunto_frozenset], False
            es_aceptacion = any(e.esAceptacion for e in conjunto_estados_afn)
            nuevo = Estado(contador_id, es_aceptacion)
            self.mapeo_subconjuntos[nuevo.id] = sorted(e.id for e in conjunto_estados_afn)
            contador_id += 1
            conjuntos_vistos[conjunto_frozenset] = nuevo
            afd.agregarEstado(nuevo)
            return nuevo, True

        clausura_inicial = self.epsilonClausura({afn.estadoInicial}, afn)
        clave_inicial = frozenset(e.id for e in clausura_inicial)
        estado_inicial_afd, _ = obtener_o_crear_estado_afd(clave_inicial, clausura_inicial)
        afd.estadoInicial = estado_inicial_afd

        sorted_inicial_afn = sorted(e.id for e in clausura_inicial)
        str_clausura_inicial = "{" + ", ".join(f"q{i}" for i in sorted_inicial_afn) + "}"
        tag_aceptacion_inicial = " (*)" if estado_inicial_afd.esAceptacion else ""
        texto_inicial = (
            f"Estado inicial del AFD = ε-clausura(q{afn.estadoInicial.id}) = "
            f"{str_clausura_inicial} -> q{estado_inicial_afd.id}{tag_aceptacion_inicial}"
        )
        self.pasos.append(texto_inicial)
        self.pasos_detallados.append({
            "tipo": "inicio",
            "paso": 0,
            "estado_afd": estado_inicial_afd.id,
            "es_aceptacion": estado_inicial_afd.esAceptacion,
            "afn_inicial": afn.estadoInicial.id,
            "conjunto_afn": sorted_inicial_afn,
            "texto": texto_inicial
        })

        pendientes = [(clave_inicial, clausura_inicial)]
        procesados = set()

        # Recorremos los conjuntos de estados pendientes para procesarlos y generar las transiciones del AFD
        while pendientes:
            clave_actual, conjunto_actual = pendientes.pop(0)
            if clave_actual in procesados:
                continue
            procesados.add(clave_actual)
            estado_actual_afd = conjuntos_vistos[clave_actual]
            sorted_actual_afn = sorted(e.id for e in conjunto_actual)
            str_actual_afn = "{" + ", ".join(f"q{i}" for i in sorted_actual_afn) + "}"

            # Recorremos cada simbolo del alfabeto para generar las transiciones del AFD
            for simbolo in sorted(afd.alfabeto):
                movidos = self.mover(conjunto_actual, simbolo, afn)
                if not movidos:
                    continue
                clausura = self.epsilonClausura(movidos, afn)
                clave_nueva = frozenset(e.id for e in clausura)

                estado_destino_afd, nuevo_es_nuevo = obtener_o_crear_estado_afd(clave_nueva, clausura)
                afd.agregarTransicion(estado_actual_afd, estado_destino_afd, simbolo)

                sorted_movidos = sorted(e.id for e in movidos)
                sorted_clausura = sorted(e.id for e in clausura)

                str_movidos = "{" + ", ".join(f"q{i}" for i in sorted_movidos) + "}"
                str_clausura = "{" + ", ".join(f"q{i}" for i in sorted_clausura) + "}"

                tag_nuevo = "  [ESTADO NUEVO]" if nuevo_es_nuevo else ""
                asterisco_final = "(*)" if estado_destino_afd.esAceptacion else ""

                texto_paso = (
                    f"mover({str_actual_afn}, '{simbolo}') "
                    f"-> mover = {str_movidos} "
                    f"-> ε-clausura = {str_clausura} "
                    f"=> q{estado_actual_afd.id} --{simbolo}--> q{estado_destino_afd.id}{asterisco_final}"
                    + tag_nuevo
                )
                self.pasos.append(texto_paso)

                self.pasos_detallados.append({
                    "tipo": "transicion",
                    "paso": len(self.pasos_detallados),
                    "origen_afd": estado_actual_afd.id,
                    "origen_conjunto": sorted_actual_afn,
                    "simbolo": simbolo,
                    "movidos": sorted_movidos,
                    "clausura": sorted_clausura,
                    "destino_afd": estado_destino_afd.id,
                    "destino_conjunto": sorted_clausura,
                    "es_nuevo": nuevo_es_nuevo,
                    "es_aceptacion": estado_destino_afd.esAceptacion,
                    "texto": texto_paso
                })

                if clave_nueva not in procesados:
                    pendientes.append((clave_nueva, clausura))

        # Construir tabla de subconjuntos para la visualización formal (Tabla)
        for estado in afd.listaEstados:
            fila = {
                "id_afd": estado.id,
                "conjunto_afn": self.mapeo_subconjuntos.get(estado.id, []),
                "es_aceptacion": estado.esAceptacion,
                "es_inicial": (estado.id == estado_inicial_afd.id),
                "transiciones": {}
            }
            for t in afd.transicionesDesde(estado):
                fila["transiciones"][t.simbolo] = t.estadoDestino.id
            self.tabla_subconjuntos.append(fila)

        return afd