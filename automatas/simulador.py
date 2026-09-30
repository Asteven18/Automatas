from transicion import EPSILON

class Simulador:
    def validarCadena(self, afd, cadena):
        """Simulación sobre el Determinista. Devuelve (aceptada: bool, traza: list[str])."""
        estado_actual = afd.estadoInicial
        traza = [f"Inicio en {estado_actual}"]

        for simbolo in cadena:
            transiciones = afd.transicionesDesde(estado_actual, simbolo)
            if not transiciones:
                traza.append(f"No hay transición con '{simbolo}' desde {estado_actual} = RECHAZADO")
                return False, traza
            estado_actual = transiciones[0].estadoDestino
            traza.append(f"Consume '{simbolo}' -> {estado_actual}")

        aceptada = estado_actual.esAceptacion
        traza.append(
            f"Cadena terminada en {estado_actual} "
            f"({'ACEPTACIÓN' if aceptada else 'NO es estado de aceptación'})"
        )
        return aceptada, traza

    def validarCadenaNFA(self, afn, cadena, conversor):
        """ Simulación directa sobre No determinista  """
        activos = conversor.epsilonClausura({afn.estadoInicial}, afn)
        traza = [f"Estados activos iniciales: {activos}"]

        for simbolo in cadena:
            movidos = conversor.mover(activos, simbolo, afn)
            activos = conversor.epsilonClausura(movidos, afn)
            traza.append(f"Tras consumir '{simbolo}': {activos}")
            if not activos:
                traza.append("Conjunto de estados vacío -> RECHAZA")
                return False, traza

        aceptada = any(e.esAceptacion for e in activos)
        traza.append("ACEPTACIÓN" if aceptada else "RECHAZA (ningún estado activo es de aceptación)")
        return aceptada, traza

    def simular_estructurado_afd(self, afd, cadena):
        """Simulación paso a paso sobre el AFD con objetos estructurados para la UI."""
        estado_actual = afd.estadoInicial
        pasos = [{
            "tipo": "inicio",
            "indice_simbolo": -1,
            "simbolo": None,
            "estado_id": estado_actual.id,
            "estado_ids": [estado_actual.id],
            "texto": f"Inicio en el estado q{estado_actual.id}",
            "es_aceptacion": estado_actual.esAceptacion,
            "es_final": False,
            "rechazo": False
        }]

        for idx, simbolo in enumerate(cadena):
            transiciones = afd.transicionesDesde(estado_actual, simbolo)
            if not transiciones:
                pasos.append({
                    "tipo": "rechazo_sin_transicion",
                    "indice_simbolo": idx,
                    "simbolo": simbolo,
                    "estado_id": estado_actual.id,
                    "estado_ids": [estado_actual.id],
                    "texto": f"Sin transición con '{simbolo}' desde q{estado_actual.id} → RECHAZADA",
                    "es_aceptacion": False,
                    "es_final": True,
                    "rechazo": True
                })
                return False, pasos

            origen = estado_actual
            estado_actual = transiciones[0].estadoDestino
            pasos.append({
                "tipo": "transicion",
                "indice_simbolo": idx,
                "simbolo": simbolo,
                "origen_id": origen.id,
                "estado_id": estado_actual.id,
                "estado_ids": [estado_actual.id],
                "texto": f"Consume '{simbolo}': q{origen.id} ──({simbolo})──> q{estado_actual.id}",
                "es_aceptacion": estado_actual.esAceptacion,
                "es_final": False,
                "rechazo": False
            })

        aceptada = estado_actual.esAceptacion
        pasos.append({
            "tipo": "fin",
            "indice_simbolo": len(cadena),
            "simbolo": None,
            "estado_id": estado_actual.id,
            "estado_ids": [estado_actual.id],
            "texto": f"Fin de cadena en q{estado_actual.id} (" + ("ACEPTADA (Estado de Aceptación)" if aceptada else "RECHAZADA (No es de aceptación)") + ")",
            "es_aceptacion": aceptada,
            "es_final": True,
            "rechazo": not aceptada
        })
        return aceptada, pasos

    def simular_estructurado_nfa(self, afn, cadena, conversor):
        """Simulación paso a paso sobre el AFN (conjunto de estados activos concurrentes)."""
        activos = conversor.epsilonClausura({afn.estadoInicial}, afn)
        ids_activos = sorted(e.id for e in activos)
        pasos = [{
            "tipo": "inicio",
            "indice_simbolo": -1,
            "simbolo": None,
            "estado_ids": ids_activos,
            "texto": f"Estados iniciales activos (ε-clausura): {{{', '.join(f'q{i}' for i in ids_activos)}}}",
            "es_aceptacion": any(e.esAceptacion for e in activos),
            "es_final": False,
            "rechazo": False
        }]

        for idx, simbolo in enumerate(cadena):
            movidos = conversor.mover(activos, simbolo, afn)
            activos = conversor.epsilonClausura(movidos, afn)
            ids_activos = sorted(e.id for e in activos)

            if not activos:
                pasos.append({
                    "tipo": "rechazo_sin_transicion",
                    "indice_simbolo": idx,
                    "simbolo": simbolo,
                    "estado_ids": [],
                    "texto": f"Al leer '{simbolo}': conjunto vacío de estados activos → RECHAZADA",
                    "es_aceptacion": False,
                    "es_final": True,
                    "rechazo": True
                })
                return False, pasos

            pasos.append({
                "tipo": "transicion",
                "indice_simbolo": idx,
                "simbolo": simbolo,
                "estado_ids": ids_activos,
                "texto": f"Tras leer '{simbolo}': estados activos = {{{', '.join(f'q{i}' for i in ids_activos)}}}",
                "es_aceptacion": any(e.esAceptacion for e in activos),
                "es_final": False,
                "rechazo": False
            })

        aceptada = any(e.esAceptacion for e in activos)
        pasos.append({
            "tipo": "fin",
            "indice_simbolo": len(cadena),
            "simbolo": None,
            "estado_ids": ids_activos,
            "texto": "Fin de cadena: " + ("ACEPTADA (Al menos un estado activo es de aceptación)" if aceptada else "RECHAZADA (Ningún estado activo es de aceptación)"),
            "es_aceptacion": aceptada,
            "es_final": True,
            "rechazo": not aceptada
        })
        return aceptada, pasos