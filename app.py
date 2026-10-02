import sys
import os
import json
import socket
import webbrowser
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

# Agregar carpeta automatas al PATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTOMATAS_DIR = os.path.join(BASE_DIR, "automatas")
GUI_DIR = os.path.join(BASE_DIR, "gui")

if AUTOMATAS_DIR not in sys.path:
    sys.path.insert(0, AUTOMATAS_DIR)

from analizador_regex import AnalizadorRegex
from generador_thompson import GeneradorThompson
from conversor_subconjuntos import ConversorSubconjuntos
from simulador import Simulador
from graficador import Graficador
from transicion import EPSILON

analizador = AnalizadorRegex()
graficador = Graficador()
simulador = Simulador()

# Caché en memoria para simulación
cache_analisis = {}


def extraer_datos_automata(automata, titulo="Autómata", highlight_nodes=None):
    if highlight_nodes is None:
        highlight_nodes = []

    estados = [{"id": e.id, "esAceptacion": e.esAceptacion} for e in automata.listaEstados]
    transiciones = [
        {
            "origen": t.estadoOrigen.id,
            "destino": t.estadoDestino.id,
            "simbolo": t.simbolo,
            "esEpsilon": (t.simbolo == EPSILON)
        }
        for t in automata.listaTransiciones
    ]
    alfabeto = sorted(list(automata.alfabeto))
    inicial = automata.estadoInicial.id if automata.estadoInicial else None
    aceptacion = [e.id for e in automata.estadosAceptacion]

    svg = graficador.generar_svg(automata, titulo=titulo, highlight_nodes=highlight_nodes)
    dot = graficador.generar_dot(automata, titulo=titulo, highlight_nodes=highlight_nodes).source

    # Definición formal de 5-tupla
    q_str = "{" + ", ".join(f"q{e['id']}" for e in estados) + "}"
    sigma_str = "{" + ", ".join(alfabeto) + "}"
    f_str = "{" + ", ".join(f"q{i}" for i in aceptacion) + "}"
    tupla_texto = f"M = (Q, Σ, δ, q{inicial}, F)\nDonde:\n  Q = {q_str}\n  Σ = {sigma_str}\n  q₀ = q{inicial}\n  F = {f_str}"

    return {
        "inicial": inicial,
        "aceptacion": aceptacion,
        "estados": estados,
        "transiciones": transiciones,
        "alfabeto": alfabeto,
        "svg": svg,
        "dot": dot,
        "tupla": tupla_texto
    }


class AutomatasHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=GUI_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


    def _responder_json(self, data, status_code=200):
        cuerpo = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            self._responder_json({
                "status": "online",
                "python": sys.version.split()[0],
                "sistema": sys.platform
            })
            return

        if parsed.path == "/" or parsed.path == "":
            self.path = "/index.html"

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        longitud = int(self.headers.get("Content-Length", 0))
        cuerpo_bytes = self.rfile.read(longitud)

        try:
            datos = json.loads(cuerpo_bytes.decode("utf-8")) if cuerpo_bytes else {}
        except Exception as e:
            self._responder_json({"success": False, "error": f"JSON inválido: {e}"}, 400)
            return

        if parsed.path == "/api/analizar":
            self._handle_analizar(datos)
        elif parsed.path == "/api/simular":
            self._handle_simular(datos)
        elif parsed.path == "/api/render-svg":
            self._handle_render_svg(datos)
        else:
            self.send_error(404, "Endpoint no encontrado")

    def _handle_analizar(self, datos):
        regex = (datos.get("regex") or "").strip()
        if not regex:
            self._responder_json({"success": False, "error": "La expresión regular no puede estar vacía."}, 400)
            return

        try:
            concat = analizador.insertarConcatenacion(regex)
            postfijo = analizador.aPostfijo(regex)

            gen_thompson = GeneradorThompson()
            afn = gen_thompson.construir(postfijo)

            conversor = ConversorSubconjuntos()
            afd = conversor.nfaToDfa(afn)

            cache_analisis[regex] = {
                "afn": afn,
                "afd": afd,
                "conversor": conversor
            }

            datos_afn = extraer_datos_automata(afn, titulo=f"AFN: {regex}")
            datos_afn["pasos"] = gen_thompson.pasos

            datos_afd = extraer_datos_automata(afd, titulo=f"AFD: {regex}")
            datos_afd["pasos"] = conversor.pasos
            datos_afd["pasosDetallados"] = conversor.pasos_detallados
            datos_afd["tablaSubconjuntos"] = conversor.tabla_subconjuntos
            datos_afd["mapeoSubconjuntos"] = conversor.mapeo_subconjuntos

            self._responder_json({
                "success": True,
                "infijo": regex,
                "concat": concat,
                "postfijo": postfijo,
                "afn": datos_afn,
                "afd": datos_afd
            })
        except Exception as e:
            self._responder_json({"success": False, "error": str(e)}, 400)

    def _handle_simular(self, datos):
        regex = (datos.get("regex") or "").strip()
        cadena = datos.get("cadena", "")
        tipo = datos.get("tipo", "afd").lower()

        if regex not in cache_analisis:
            try:
                concat = analizador.insertarConcatenacion(regex)
                postfijo = analizador.aPostfijo(regex)
                afn = GeneradorThompson().construir(postfijo)
                conversor = ConversorSubconjuntos()
                afd = conversor.nfaToDfa(afn)
                cache_analisis[regex] = {"afn": afn, "afd": afd, "conversor": conversor}
            except Exception as e:
                self._responder_json({"success": False, "error": f"Error al procesar la expresión: {e}"}, 400)
                return

        cached = cache_analisis[regex]
        try:
            if tipo == "afn":
                aceptada, pasos = simulador.simular_estructurado_nfa(cached["afn"], cadena, cached["conversor"])
            else:
                aceptada, pasos = simulador.simular_estructurado_afd(cached["afd"], cadena)

            self._responder_json({
                "success": True,
                "tipo": tipo,
                "cadena": cadena,
                "aceptada": aceptada,
                "pasos": pasos
            })
        except Exception as e:
            self._responder_json({"success": False, "error": str(e)}, 500)

    def _handle_render_svg(self, datos):
        regex = (datos.get("regex") or "").strip()
        tipo = datos.get("tipo", "afd").lower()
        highlight_nodes = datos.get("highlight_nodes", [])

        if regex not in cache_analisis:
            self._responder_json({"success": False, "error": "Expresión no encontrada en memoria."}, 404)
            return

        automata = cache_analisis[regex]["afn"] if tipo == "afn" else cache_analisis[regex]["afd"]
        svg = graficador.generar_svg(automata, titulo=f"{tipo.upper()}: {regex}", highlight_nodes=highlight_nodes)
        self._responder_json({"success": True, "svg": svg})


def encontrar_puerto_libre(inicio=5000):
    puerto = inicio
    while puerto < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", puerto)) != 0:
                return puerto
            puerto += 1
    return inicio


def iniciar_servidor():
    puerto = encontrar_puerto_libre(5000)
    servidor = HTTPServer(("127.0.0.1", puerto), AutomatasHandler)
    url = f"http://127.0.0.1:{puerto}/"

    print(f"Servidor iniciado en {url}")
    print("Presiona Ctrl + C para detenerlo.")

    threading.Timer(0.7, lambda: webbrowser.open(url)).start()

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        servidor.server_close()


if __name__ == "__main__":
    iniciar_servidor()
