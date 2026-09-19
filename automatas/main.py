import os

from analizador_regex import AnalizadorRegex
from generador_thompson import GeneradorThompson
from conversor_subconjuntos import ConversorSubconjuntos
from simulador import Simulador
from graficador import Graficador

CARPETA_SALIDA = "salidas"


class Aplicacion:
    def __init__(self):
        self.analizador = AnalizadorRegex()
        self.graficador = Graficador()
        self.simulador = Simulador()
        self.expresion_actual = None
        self.postfijo_actual = None
        self.afn = None
        self.afd = None
        os.makedirs(CARPETA_SALIDA, exist_ok=True)

    # Menu principal
    def opcion_ingresar_regex(self):
        expresion = input("\nIngresa la expresión regular (ej: a(b|c)*d ): ").strip()
        if not expresion:
            print("La expresión no puede estar vacía.")
            return

        try:
            postfijo = self.analizador.aPostfijo(expresion)
        except ValueError as e:
            print(f"Error al analizar la expresión: {e}")
            return

        print(f"\nExpresión infija : {expresion}")
        print(f"Expresión postfija: {postfijo}")

        gen_thompson = GeneradorThompson()
        afn = gen_thompson.construir(postfijo)

        print("\n Pasos de la construcción de Thompson (AFN) ")
        for paso in gen_thompson.pasos:
            print(" -", paso)

        conversor = ConversorSubconjuntos()
        afd = conversor.nfaToDfa(afn)

        print("\n Pasos del algoritmo de subconjuntos (AFN -> AFD) ")
        for paso in conversor.pasos:
            print(" -", paso)

        self.expresion_actual = expresion
        self.postfijo_actual = postfijo
        self.afn = afn
        self.afd = afd
        self._conversor = conversor

        print("\n AFN y AFD generados correctamente! Usa las opciones 2 y 3 para verlos.")

    def _verificar_automatas_listos(self):
        if self.afn is None or self.afd is None:
            print("\nPrimero debes ingresar una expresión regular (opción 1).")
            return False
        return True

    def opcion_ver_afn(self):
        if not self._verificar_automatas_listos():
            return
        self.graficador.imprimirTabla(self.afn, titulo=f"AFN de '{self.expresion_actual}'")
        ruta = self.graficador.dibujar(
            self.afn, os.path.join(CARPETA_SALIDA, "afn"), titulo=f"AFN: {self.expresion_actual}"
        )
        print(f"Diagrama guardado en: {ruta}")

    def opcion_ver_afd(self):
        if not self._verificar_automatas_listos():
            return
        self.graficador.imprimirTabla(self.afd, titulo=f"AFD de '{self.expresion_actual}'")
        ruta = self.graficador.dibujar(
            self.afd, os.path.join(CARPETA_SALIDA, "afd"), titulo=f"AFD: {self.expresion_actual}"
        )
        print(f"Diagrama guardado en: {ruta}")

    def opcion_probar_cadena(self):
        if not self._verificar_automatas_listos():
            return
        cadena = input("\nIngresa la cadena a evaluar: ")

        aceptada, traza = self.simulador.validarCadena(self.afd, cadena)
        print("\n Simulación sobre el AFD ")
        for paso in traza:
            print(" -", paso)

        resultado = "SÍ pertenece" if aceptada else "NO pertenece"
        print(f"\nResultado: la cadena '{cadena}' {resultado} al lenguaje de '{self.expresion_actual}'.")

    def ejecutar(self):
        while True:
            print("\n____GENERADOR DE AUTÓMATAS FINITOS____")
            print("1. Ingresar expresión regular (genera AFN y AFD)")
            print("2. Ver AFN (tabla + diagrama)")
            print("3. Ver AFD (tabla + diagrama)")
            print("4. Probar una cadena")
            print("5. Salir")
            opcion = input("Selecciona una opción: ").strip()

            if opcion == "1":
                self.opcion_ingresar_regex()
            elif opcion == "2":
                self.opcion_ver_afn()
            elif opcion == "3":
                self.opcion_ver_afd()
            elif opcion == "4":
                self.opcion_probar_cadena()
            elif opcion == "5":
                print(" Fin del programa")
                break
            else:
                print("Opción no válida.")


if __name__ == "__main__":
    Aplicacion().ejecutar()
