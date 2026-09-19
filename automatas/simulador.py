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
