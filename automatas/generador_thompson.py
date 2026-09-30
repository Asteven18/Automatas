from estado import Estado
from automata import Automata
from transicion import EPSILON

class GeneradorThompson:
    def __init__(self):
        self._contador_id = 0
        self.pasos = []

    def _nuevoEstado(self, es_aceptacion=False):
        e = Estado(self._contador_id, es_aceptacion)
        self._contador_id += 1
        return e

    def crearBase(self, simbolo):
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
        frag = Automata()
        inicio = self._nuevoEstado(False)
        fin = self._nuevoEstado(True)
        frag.agregarEstado(inicio)
        frag.agregarEstado(fin)
        frag.agregarTransicion(inicio, fin, EPSILON)
        frag.estadoInicial = inicio
        return frag

    def _fusionar(self, *fragmentos):
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
        nuevo = self._fusionar(a1, a2)
        fin_a1 = a1.estadosAceptacion[0]
        self._desactivarAceptacion(fin_a1)
        nuevo.agregarTransicion(fin_a1, a2.estadoInicial, EPSILON)
        nuevo.estadoInicial = a1.estadoInicial
        nuevo.estadosAceptacion = [a2.estadosAceptacion[0]]
        self.pasos.append(f"Concatenación: une {fin_a1} -> {a2.estadoInicial} con ε")
        return nuevo

    def crearUnion(self, a1, a2):
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
        nuevo = self._fusionar(a)
        nuevo_inicio = self._nuevoEstado(False)
        nuevo_fin = self._nuevoEstado(True)
        nuevo.agregarEstado(nuevo_inicio)
        nuevo.agregarEstado(nuevo_fin)

        fin_a = a.estadosAceptacion[0]
        self._desactivarAceptacion(fin_a)

        nuevo.agregarTransicion(nuevo_inicio, a.estadoInicial, EPSILON)
        nuevo.agregarTransicion(nuevo_inicio, nuevo_fin, EPSILON)
        nuevo.agregarTransicion(fin_a, a.estadoInicial, EPSILON)
        nuevo.agregarTransicion(fin_a, nuevo_fin, EPSILON)

        nuevo.estadoInicial = nuevo_inicio
        nuevo.estadosAceptacion = [nuevo_fin]
        self.pasos.append(f"Estrella de Kleene sobre fragmento con inicio {a.estadoInicial}")
        return nuevo

    def crearMasCierre(self, a):
        clon = self._clonar(a)
        estrella = self.crearEstrellaKleene(clon)
        return self.crearConcatenacion(a, estrella)

    def _clonar(self, a):
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

    def construir(self, postfijo):
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
            else:
                pila.append(self.crearBase(token))

        if len(pila) != 1:
            raise ValueError("Expresión regular mal formada (no se redujo a un solo AFN).")

        afn = pila.pop()
        return afn