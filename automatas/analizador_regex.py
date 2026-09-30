# Operadores soportados:
# | (unión), . (concatenación implícita), * (cerradura de Kleene), + (cierre positivo), ( ) agrupación

OPERADORES_BINARIOS = {"|": 1, ".": 2}
OPERADORES_UNARIOS = {"*": 3, "+": 3}
PRECEDENCIA = {**OPERADORES_BINARIOS, **OPERADORES_UNARIOS}


class AnalizadorRegex:

    def esOperando(self, c):
        return c not in "|.*+()"

    def insertarConcatenacion(self, regex):
        """
        Inserta el punto de concatenación explícito.
        Ej: "ab(c|d)e" -> "a.b.(c|d).e"
        """
        resultado = []
        for i, c in enumerate(regex):
            resultado.append(c)
            if i + 1 < len(regex):
                actual, siguiente = c, regex[i + 1]
                necesita_punto = (
                    (self.esOperando(actual) or actual in ")*+")
                    and (self.esOperando(siguiente) or siguiente == "(")
                )
                if necesita_punto:
                    resultado.append(".")
        return "".join(resultado)

    def aPostfijo(self, regex):
        regex = self.insertarConcatenacion(regex)
        salida = []
        pila = []

        for c in regex:
            if self.esOperando(c):
                salida.append(c)
            elif c == "(":
                pila.append(c)
            elif c == ")":
                while pila and pila[-1] != "(":
                    salida.append(pila.pop())
                if not pila:
                    raise ValueError("Paréntesis desbalanceados en la expresión regular.")
                pila.pop()
            elif c in PRECEDENCIA:
                while (pila and pila[-1] != "(" and
                       PRECEDENCIA.get(pila[-1], 0) >= PRECEDENCIA[c]):
                    salida.append(pila.pop())
                pila.append(c)
            else:
                raise ValueError(f"Símbolo no soportado en la expresión: '{c}'")

        while pila:
            op = pila.pop()
            if op == "(":
                raise ValueError("Paréntesis desbalanceados en la expresión regular.")
            salida.append(op)

        return "".join(salida)