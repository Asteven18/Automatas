from estado import Estado
from automata import Automata
from transicion import EPSILON

class GeneradorThompson:
    def __init__(self):
        self._contador_id = 0
        self.pasos = []  # guarda un registro textual de cada paso (para mostrarlo)

    def _nuevoEstado(self, es_aceptacion=False):
        e = Estado(self._contador_id, es_aceptacion)
        self._contador_id += 1
        return e

    def crearBase(self, simbolo):
        """(q0) --a--> (q1*)"""
        frag = Automata()
        inicio = self._nuevoEstado(False)
        fin = self._nuevoEstado(True)
        frag.agregarEstado(inicio)
        frag.agregarEstado(fin)
        frag.agregarTransicion(inicio, fin, simbolo)
        frag.estadoInicial = inicio
        self.pasos.append(f"Base '{simbolo}': {inicio} --{simbolo}--> {fin}")
        return frag

    def crearEpsilon(self):
        """(q0) --ε--> (q1*)"""
        frag = Automata()
        inicio = self._nuevoEstado(False)
        fin = self._nuevoEstado(True)
        frag.agregarEstado(inicio)
        frag.agregarEstado(fin)
        frag.agregarTransicion(inicio, fin, EPSILON)
        frag.estadoInicial = inicio
        return frag

    def _fusionar(self, *fragmentos):
        """Combina estados/transiciones de varios fragmentos en un Automata nuevo (vacío).
        fusion tiene: [q0, q1, q2, q3] y transiciones [q0--a-->q1, q2--b-->q3]
        """
        nuevo = Automata()
        for f in fragmentos:
            for e in f.listaEstados:
                if e not in nuevo.listaEstados:
                    nuevo.listaEstados.append(e)
            for t in f.listaTransiciones:
                nuevo.listaTransiciones.append(t)
                if t.simbolo != EPSILON:
                    nuevo.alfabeto.add(t.simbolo)
        return nuevo

    def _desactivarAceptacion(self, estado):
        estado.esAceptacion = False

    def crearConcatenacion(self, a1, a2):
        """AB: conecta el final de a1 con el inicio de a2 vía epsilon.
        (q0) --a--> (q1) --ε--> (q2) --b--> (q3*)"""
        nuevo = self._fusionar(a1, a2)
        fin_a1 = a1.estadosAceptacion[0]
        self._desactivarAceptacion(fin_a1)
        nuevo.agregarTransicion(fin_a1, a2.estadoInicial, EPSILON)
        nuevo.estadoInicial = a1.estadoInicial
        nuevo.estadosAceptacion = [a2.estadosAceptacion[0]]
        self.pasos.append(f"Concatenación: une {fin_a1} -> {a2.estadoInicial} con ε")
        return nuevo

    def crearUnion(self, a1, a2):
        """A|B: nuevo inicio con ε hacia ambos; nuevo final recibiendo ε de ambos."""
        nuevo = self._fusionar(a1, a2)
        nuevo_inicio = self._nuevoEstado(False)
        nuevo_fin = self._nuevoEstado(True)
        nuevo.agregarEstado(nuevo_inicio)
        nuevo.agregarEstado(nuevo_fin)

        fin_a1 = a1.estadosAceptacion[0]
        fin_a2 = a2.estadosAceptacion[0]
        self._desactivarAceptacion(fin_a1)
        self._desactivarAceptacion(fin_a2)

        nuevo.agregarTransicion(nuevo_inicio, a1.estadoInicial, EPSILON)
        nuevo.agregarTransicion(nuevo_inicio, a2.estadoInicial, EPSILON)
        nuevo.agregarTransicion(fin_a1, nuevo_fin, EPSILON)
        nuevo.agregarTransicion(fin_a2, nuevo_fin, EPSILON)

        nuevo.estadoInicial = nuevo_inicio
        nuevo.estadosAceptacion = [nuevo_fin]
        self.pasos.append(f"Unión: nuevo inicio {nuevo_inicio}, nuevo final {nuevo_fin}")
        return nuevo

    def crearEstrellaKleene(self, a):
        """A*: permite repetir A cero o más veces."""
        nuevo = self._fusionar(a)
        nuevo_inicio = self._nuevoEstado(False)
        nuevo_fin = self._nuevoEstado(True)
        nuevo.agregarEstado(nuevo_inicio)
        nuevo.agregarEstado(nuevo_fin)

        fin_a = a.estadosAceptacion[0]
        self._desactivarAceptacion(fin_a)

        nuevo.agregarTransicion(nuevo_inicio, a.estadoInicial, EPSILON)
        nuevo.agregarTransicion(nuevo_inicio, nuevo_fin, EPSILON)      # cero repeticiones
        nuevo.agregarTransicion(fin_a, a.estadoInicial, EPSILON)       # repetir
        nuevo.agregarTransicion(fin_a, nuevo_fin, EPSILON)             # salir

        nuevo.estadoInicial = nuevo_inicio
        nuevo.estadosAceptacion = [nuevo_fin]
        self.pasos.append(f"Estrella de Kleene sobre fragmento con inicio {a.estadoInicial}")
        return nuevo

    def crearMasCierre(self, a):
        """A+: una o más repeticiones = A seguido de A* (clonando A para no reusar estados)."""
        clon = self._clonar(a)
        estrella = self.crearEstrellaKleene(clon)
        return self.crearConcatenacion(a, estrella)

    def crearOpcional(self, a):
        """A?: cero o una vez = A unido con epsilon (cadena vacía)."""
        return self.crearUnion(a, self.crearEpsilon())

    def _clonar(self, a):
        """Crea una copia de un fragmento con IDs de estado nuevos (para usar en A+)."""
        mapa = {}
        clon = Automata()
        for e in a.listaEstados:
            nuevo_e = self._nuevoEstado(e.esAceptacion)
            mapa[e.id] = nuevo_e
            clon.agregarEstado(nuevo_e)
        for t in a.listaTransiciones:
            clon.agregarTransicion(mapa[t.estadoOrigen.id], mapa[t.estadoDestino.id], t.simbolo)
        clon.estadoInicial = mapa[a.estadoInicial.id]
        clon.estadosAceptacion = [mapa[e.id] for e in a.estadosAceptacion]
        return clon

    # Construccion Final

    def construir(self, postfijo):
        """Recorre la expresión en postfijo usando una pila de fragmentos Automata."""
        self.pasos = []
        pila = []

        for token in postfijo:
            if token == "|":
                b = pila.pop()
                a = pila.pop()
                pila.append(self.crearUnion(a, b))
            elif token == ".":
                b = pila.pop()
                a = pila.pop()
                pila.append(self.crearConcatenacion(a, b))
            elif token == "*":
                a = pila.pop()
                pila.append(self.crearEstrellaKleene(a))
            elif token == "+":
                a = pila.pop()
                pila.append(self.crearMasCierre(a))
            elif token == "?":
                a = pila.pop()
                pila.append(self.crearOpcional(a))
            else:
                pila.append(self.crearBase(token))

        if len(pila) != 1:
            raise ValueError("Expresión regular mal formada (no se redujo a un solo AFN).")

        afn = pila.pop()
        return afn