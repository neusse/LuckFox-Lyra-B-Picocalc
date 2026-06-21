#!/usr/bin/env python3
# ------------------------------------------------------------
# PicoEdit
# Editor de texto compacto para terminal 53x22.
#
# Archivo autocontenido
#
# Uso:
#     python3 picoedit.py
#     python3 picoedit.py archivo.py
# ------------------------------------------------------------

import builtins
import curses
import gzip
import keyword
import os
import signal
import shutil
import subprocess
import sys


AN = 53
AL = 26
MIN_AN = 1
MIN_AL = 3

C_NORMAL = 1
C_TITULO = 2
C_RESALTA = 3
C_ERROR = 4
C_ESTADO = 5
C_RESULT = 6
C_DESTACA = 7
C_CARPETA = 8
C_KEYWORD = 9
C_NUMERO = 10
C_STRING = 11
C_COMENTARIO = 12
C_VARIABLE = 13
C_VENTANA = 14
C_VENTANA_BORDE = 15
C_VENTANA_SEL = 16
C_VENTANA_DIR = 17
C_VENTANA_ESTADO = 18
C_FUNCION = 19

ULTIMO_PAR_COLOR_EDITOR = 19

CTRL_C = 3
CTRL_D = 4
CTRL_F = 6
CTRL_G = 7
CTRL_N = 14
CTRL_O = 15
CTRL_R = 18
CTRL_S = 19
CTRL_V = 22
CTRL_X = 24

TECLA_ALT_MENU = ord("m")
TECLA_ALT_UNDO = ord("z")
TECLA_ALT_UNDO_ALT = ord("u")
TECLA_ALT_REDO = ord("y")
TECLA_ALT_COPY = ord("c")
TECLA_ALT_CUT = ord("x")
TECLA_ALT_PASTE = ord("v")
TECLA_ALT_DUP = ord("d")
TECLA_ALT_SAVE = ord("s")
TECLA_ALT_OPEN = ord("o")
TECLA_ALT_RUN = ord("r")
TECLA_ALT_FIND = ord("f")
TECLA_ALT_FIND_NEXT = ord("n")

MAX_UNDO = 10
ESPERA_ALT_MS = 40
ESPERA_CONSOLA_MS = 250
MAX_FUENTES_PANEL = 200

DIRECTORIOS_FUENTES_CONSOLA = (
    "/usr/share/consolefonts",
    "/usr/share/kbd/consolefonts",
    "/lib/kbd/consolefonts",
    "/usr/lib/kbd/consolefonts",
)

RUTAS_HERRAMIENTAS_CONSOLA = (
    "/usr/sbin",
    "/sbin",
    "/usr/bin",
    "/bin",
)

EXTENSIONES_FUENTES_CONSOLA = (
    ".psf",
    ".psf.gz",
    ".psfu",
    ".psfu.gz",
)


PY_KEYWORDS = set(keyword.kwlist)
PY_BUILTINS = set(dir(builtins))

PALETA_ANTERIOR = {}


# ------------------------------------------------------------
# Guardado y restauracion de paleta de colores
# ------------------------------------------------------------
def guardar_paleta_actual():
    global PALETA_ANTERIOR

    PALETA_ANTERIOR = {}

    for par in range(1, ULTIMO_PAR_COLOR_EDITOR + 1):
        if par >= curses.COLOR_PAIRS:
            continue

        try:
            PALETA_ANTERIOR[par] = curses.pair_content(par)
        except curses.error:
            pass


def restaurar_paleta_anterior():
    if not PALETA_ANTERIOR:
        return

    for par, colores in PALETA_ANTERIOR.items():
        if par >= curses.COLOR_PAIRS:
            continue

        try:
            fg, bg = colores
            curses.init_pair(par, fg, bg)
        except curses.error:
            pass


# ------------------------------------------------------------
# Inicializacion de curses
# ------------------------------------------------------------
def actualizar_tamano(stdscr):
    global AN, AL

    try:
        alto, ancho = stdscr.getmaxyx()
    except curses.error:
        return

    AN = max(MIN_AN, int(ancho))
    AL = max(MIN_AL, int(alto))


def cursor_visible(visible):
    try:
        curses.curs_set(1 if visible else 0)
        return True
    except curses.error:
        return False


def usar_colores_por_defecto():
    try:
        curses.use_default_colors()
        return True
    except curses.error:
        return False


def terminal_necesita_linux(term):
    return not term or term in ("dumb", "unknown") or term.startswith("vt")


def es_ruta_consola_fisica(ruta):
    return ruta == "/dev/console" or ruta.startswith("/dev/tty")


def detectar_consola_fisica():
    if os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_TTY"):
        return False

    try:
        ruta = os.ttyname(sys.stdin.fileno())
    except OSError:
        ruta = ""

    return es_ruta_consola_fisica(ruta)


def preparar_terminal_consola():
    if detectar_consola_fisica() and terminal_necesita_linux(os.environ.get("TERM")):
        os.environ["TERM"] = "linux"


def color_seguro(color, respaldo=0):
    colores = getattr(curses, "COLORS", 0)

    if colores <= 0:
        return 0

    if 0 <= color < colores:
        return color

    if 0 <= respaldo < colores:
        return respaldo

    return 0


def init_pair_seguro(par, fg, bg):
    if not curses.has_colors():
        return False

    if par >= curses.COLOR_PAIRS:
        return False

    try:
        curses.init_pair(
            par,
            color_seguro(fg, curses.COLOR_WHITE),
            color_seguro(bg, curses.COLOR_BLACK),
        )
        return True
    except (curses.error, ValueError):
        return False


def color_necesita_brillo(color):
    return color in (
        C_ERROR,
        C_ESTADO,
        C_DESTACA,
        C_NUMERO,
        C_FUNCION,
        C_VENTANA_BORDE,
        C_VENTANA_DIR,
        C_VENTANA_ESTADO,
    )


def decodificar_secuencia_escape(secuencia):
    mapa = {
        (ord("["), ord("A")): curses.KEY_UP,
        (ord("["), ord("B")): curses.KEY_DOWN,
        (ord("["), ord("C")): curses.KEY_RIGHT,
        (ord("["), ord("D")): curses.KEY_LEFT,
        (ord("["), ord("H")): curses.KEY_HOME,
        (ord("["), ord("F")): curses.KEY_END,
        (ord("O"), ord("A")): curses.KEY_UP,
        (ord("O"), ord("B")): curses.KEY_DOWN,
        (ord("O"), ord("C")): curses.KEY_RIGHT,
        (ord("O"), ord("D")): curses.KEY_LEFT,
        (ord("O"), ord("H")): curses.KEY_HOME,
        (ord("O"), ord("F")): curses.KEY_END,
        (ord("["), ord("1"), ord("~")): curses.KEY_HOME,
        (ord("["), ord("2"), ord("~")): curses.KEY_IC,
        (ord("["), ord("3"), ord("~")): curses.KEY_DC,
        (ord("["), ord("4"), ord("~")): curses.KEY_END,
        (ord("["), ord("5"), ord("~")): curses.KEY_PPAGE,
        (ord("["), ord("6"), ord("~")): curses.KEY_NPAGE,
    }

    return mapa.get(tuple(secuencia), -1)


def leer_secuencia_prefijada(stdscr, prefijo, espera_ms=ESPERA_ALT_MS):
    stdscr.timeout(espera_ms)

    try:
        secuencia = [prefijo]

        while len(secuencia) < 8:
            parte = stdscr.getch()

            if parte == -1:
                break

            secuencia.append(parte)

            if 64 <= parte <= 126:
                break

        return decodificar_secuencia_escape(secuencia), secuencia
    finally:
        stdscr.timeout(-1)


def leer_escape_terminal(stdscr, espera_ms=ESPERA_ALT_MS):
    stdscr.timeout(espera_ms)

    try:
        siguiente = stdscr.getch()

        if siguiente == -1:
            return "escape", None

        if siguiente in (ord("["), ord("O")):
            valor, _secuencia = leer_secuencia_prefijada(stdscr, siguiente, espera_ms)
            return "secuencia", valor

        return "alt", siguiente
    finally:
        stdscr.timeout(-1)


class TecladoSSH:
    modo = "ssh"

    def __init__(self, stdscr):
        self.stdscr = stdscr

    def leer_evento(self):
        tecla = self.stdscr.getch()

        if tecla != 27:
            return "tecla", tecla

        tipo, valor = leer_escape_terminal(self.stdscr)

        if tipo == "escape":
            return "tecla", 27

        if tipo == "secuencia":
            return "tecla", valor

        return "alt", valor

    def leer_tecla(self):
        tipo, valor = self.leer_evento()

        if tipo == "tecla":
            return valor

        if valor is not None:
            curses.ungetch(valor)

        return 27


class TecladoConsola(TecladoSSH):
    modo = "console"

    def leer_evento(self):
        tecla = self.stdscr.getch()

        if tecla == 27:
            tipo, valor = leer_escape_terminal(self.stdscr, ESPERA_CONSOLA_MS)

            if tipo == "escape":
                return "tecla", 27

            if tipo == "secuencia":
                return "tecla", valor

            return "alt", valor

        # PicoCalc console can drop the leading ESC and deliver [D, [C, [4~, etc.
        if tecla in (ord("["), ord("O")):
            valor, secuencia = leer_secuencia_prefijada(self.stdscr, tecla, ESPERA_CONSOLA_MS)

            if valor != -1:
                return "tecla", valor

            for parte in reversed(secuencia[1:]):
                curses.ungetch(parte)

        return "tecla", tecla


def crear_teclado(stdscr):
    if detectar_consola_fisica():
        return TecladoConsola(stdscr)

    return TecladoSSH(stdscr)


def leer_tecla_terminal(stdscr):
    return TecladoSSH(stdscr).leer_tecla()


def iniciar_curses(stdscr):
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.nodelay(False)
    actualizar_tamano(stdscr)
    cursor_visible(False)

    curses.start_color()
    usar_colores_por_defecto()
    guardar_paleta_actual()

    # Editor principal
    init_pair_seguro(C_NORMAL, curses.COLOR_WHITE, curses.COLOR_BLACK)
    init_pair_seguro(C_TITULO, curses.COLOR_BLACK, curses.COLOR_WHITE)
    init_pair_seguro(C_RESALTA, curses.COLOR_BLUE, curses.COLOR_WHITE)
    init_pair_seguro(C_ERROR, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    init_pair_seguro(C_ESTADO, curses.COLOR_YELLOW, curses.COLOR_BLUE)
    init_pair_seguro(C_RESULT, curses.COLOR_WHITE, curses.COLOR_BLUE)
    init_pair_seguro(C_DESTACA, curses.COLOR_YELLOW, curses.COLOR_BLUE)
    init_pair_seguro(C_CARPETA, curses.COLOR_CYAN, curses.COLOR_BLUE)

    # Sintaxis Python.
    init_pair_seguro(C_KEYWORD, curses.COLOR_WHITE, curses.COLOR_BLACK)
    init_pair_seguro(C_NUMERO, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    init_pair_seguro(C_STRING, curses.COLOR_GREEN, curses.COLOR_BLACK)
    init_pair_seguro(C_COMENTARIO, curses.COLOR_GREEN, curses.COLOR_BLACK)
    init_pair_seguro(C_VARIABLE, curses.COLOR_CYAN, curses.COLOR_BLACK)
    init_pair_seguro(C_FUNCION, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    # Ventanas flotantes
    init_pair_seguro(C_VENTANA, curses.COLOR_WHITE, curses.COLOR_BLACK)
    init_pair_seguro(C_VENTANA_BORDE, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    init_pair_seguro(C_VENTANA_SEL, curses.COLOR_BLACK, curses.COLOR_WHITE)
    init_pair_seguro(C_VENTANA_DIR, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    init_pair_seguro(C_VENTANA_ESTADO, curses.COLOR_YELLOW, curses.COLOR_BLACK)


# ------------------------------------------------------------
# Primitivas de pantalla
# ------------------------------------------------------------
def escribir(stdscr, x, y, texto, color=C_NORMAL):
    if y < 0 or y >= AL:
        return
    if x < 0 or x >= AN:
        return

    try:
        attr = curses.color_pair(color)

        if color_necesita_brillo(color):
            attr = attr | curses.A_BOLD

        stdscr.addstr(y, x, str(texto)[:AN - x], attr)
    except curses.error:
        pass


def escribir_color(stdscr, x, y, char, color=C_NORMAL):
    if y < 0 or y >= AL:
        return
    if x < 0 or x >= AN:
        return

    try:
        attr = curses.color_pair(color)

        if color_necesita_brillo(color):
            attr = attr | curses.A_BOLD

        stdscr.addstr(y, x, char, attr)
    except curses.error:
        pass


def escribir_attr(stdscr, x, y, texto, color=C_NORMAL, attr=0):
    if y < 0 or y >= AL:
        return
    if x < 0 or x >= AN:
        return

    try:
        if color_necesita_brillo(color):
            attr = attr | curses.A_BOLD

        stdscr.addstr(y, x, str(texto)[:AN - x], curses.color_pair(color) | attr)
    except curses.error:
        pass


def limpiar_area(stdscr):
    for y in range(AL):
        escribir(stdscr, 0, y, " " * AN, C_NORMAL)


def linea_h(stdscr, y):
    escribir(stdscr, 0, y, "─" * AN, C_TITULO)


def normalizar_ruta(ruta):
    if not ruta:
        return None
    return os.path.abspath(os.path.expanduser(ruta))


def es_fuente_consola(ruta):
    nombre = ruta.lower()
    return any(nombre.endswith(ext) for ext in EXTENSIONES_FUENTES_CONSOLA)


def nombre_fuente_consola(ruta):
    nombre = os.path.basename(ruta)

    for ext in sorted(EXTENSIONES_FUENTES_CONSOLA, key=len, reverse=True):
        if nombre.lower().endswith(ext):
            return nombre[:-len(ext)]

    return nombre


def listar_fuentes_consola(directorios=DIRECTORIOS_FUENTES_CONSOLA):
    fuentes = []
    vistos = set()

    for directorio in directorios:
        if not os.path.isdir(directorio):
            continue

        try:
            nombres = os.listdir(directorio)
        except OSError:
            continue

        for nombre in nombres:
            ruta = os.path.join(directorio, nombre)

            if not os.path.isfile(ruta) or not es_fuente_consola(ruta):
                continue

            real = os.path.abspath(ruta)

            if real in vistos:
                continue

            vistos.add(real)
            fuentes.append({
                "nombre": nombre_fuente_consola(real),
                "ruta": real,
            })

    fuentes.sort(key=lambda item: item["nombre"].lower())
    return fuentes[:MAX_FUENTES_PANEL]


def buscar_herramienta_consola(nombre):
    ruta = shutil.which(nombre)

    if ruta:
        return ruta

    for directorio in RUTAS_HERRAMIENTAS_CONSOLA:
        ruta = os.path.join(directorio, nombre)

        if os.path.isfile(ruta) and os.access(ruta, os.X_OK):
            return ruta

    return None


def cargador_fuente_consola_disponible():
    picofont = buscar_herramienta_consola("picofont")

    if os.geteuid() != 0 and picofont is not None:
        return "picofont", picofont

    setfont = buscar_herramienta_consola("setfont")

    if setfont is not None:
        return "setfont", setfont

    loadfont = buscar_herramienta_consola("loadfont")

    if loadfont is not None:
        return "loadfont", loadfont

    return None


def leer_bytes_fuente_consola(ruta):
    if ruta.lower().endswith(".gz"):
        with gzip.open(ruta, "rb") as archivo:
            return archivo.read()

    with open(ruta, "rb") as archivo:
        return archivo.read()


def alto_fuente_terminus(nombre):
    base = nombre.lower()

    for sufijo in ("b", "n"):
        if base.endswith(sufijo):
            base = base[:-1]
            break

    digitos = ""

    for ch in reversed(base):
        if not ch.isdigit():
            break
        digitos = ch + digitos

    return int(digitos) if digitos else None


def tamano_terminal_para_fuente(nombre):
    nombre_base = nombre.lower()

    if nombre_base == "kernel-6x8":
        return 40, 53

    if nombre_base.startswith("ter-v12"):
        return 26, 53

    alto_fuente = alto_fuente_terminus(nombre)

    if not alto_fuente:
        return None

    return max(1, 320 // alto_fuente), 40


def eleccion_picofont_para_fuente(nombre):
    nombre_base = nombre.lower()

    if nombre_base == "kernel-6x8":
        return "original"

    if nombre_base.startswith("ter-v12"):
        return "small"

    alto_fuente = alto_fuente_terminus(nombre)

    if alto_fuente in (14, 16, 18, 20):
        return "40" if alto_fuente == 16 else str(alto_fuente)

    return None


# ------------------------------------------------------------
# Entrada para uso integrado
# ------------------------------------------------------------
def ejecutar(stdscr, ruta_archivo=None):
    iniciar_curses(stdscr)

    try:
        editor = PicoEdit(stdscr, ruta_archivo)
        editor.bucle()
    finally:
        restaurar_paleta_anterior()
        stdscr.refresh()


class PicoEdit:
    def __init__(self, stdscr, ruta_archivo=None):
        self.stdscr = stdscr
        self.teclado = crear_teclado(stdscr)
        self.ruta_archivo = normalizar_ruta(ruta_archivo)
        self.carpeta_actual = os.getcwd()

        if self.ruta_archivo:
            self.carpeta_actual = os.path.dirname(self.ruta_archivo) or os.getcwd()

        self.lineas = []
        self.cursor_fila = 0
        self.cursor_col = 0
        self.offset_fila = 0
        self.offset_col = 0

        self.modificado = False
        self.insertar = True
        self.portapapeles = ""
        self.busqueda = ""
        self.mensaje = ""

        self.undo_stack = []
        self.redo_stack = []

        if self.ruta_archivo:
            self.cargar_archivo()
        else:
            self.lineas = [""]

        if not self.lineas:
            self.lineas = [""]

    # ------------------------------------------------------------
    # Propiedades auxiliares
    # ------------------------------------------------------------
    def nombre_archivo(self):
        if self.ruta_archivo:
            return os.path.basename(self.ruta_archivo)
        return "new"

    def ruta_para_guardar_defecto(self):
        if self.ruta_archivo:
            return os.path.basename(self.ruta_archivo)
        return ""

    # ------------------------------------------------------------
    # Carga y guardado
    # ------------------------------------------------------------
    def cargar_archivo(self):
        if not self.ruta_archivo or not os.path.exists(self.ruta_archivo):
            self.lineas = [""]
            return

        try:
            with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                self.lineas = f.read().splitlines()
        except UnicodeDecodeError:
            with open(self.ruta_archivo, "r", encoding="latin-1") as f:
                self.lineas = f.read().splitlines()
        except Exception as e:
            self.lineas = [f"Error opening file: {e}"]

    def guardar_archivo_directo(self):
        if not self.ruta_archivo:
            return self.guardar_como()

        try:
            carpeta = os.path.dirname(self.ruta_archivo)
            if carpeta:
                os.makedirs(carpeta, exist_ok=True)

            with open(self.ruta_archivo, "w", encoding="utf-8") as f:
                for i, linea in enumerate(self.lineas):
                    f.write(linea)
                    if i < len(self.lineas) - 1:
                        f.write("\n")

            self.modificado = False
            self.mensaje = "Saved."
            return True
        except Exception as e:
            self.mensaje = f"Error: {e}"
            return False

    def guardar_archivo(self):
        if self.ruta_archivo:
            return self.guardar_archivo_directo()

        return self.guardar_como()

    def guardar_como(self):
        inicial = self.ruta_para_guardar_defecto()

        nombre = self.input_barra("Save as: ", inicial)

        if nombre is None:
            self.mensaje = "Save canceled."
            return False

        nombre = nombre.strip()

        if not nombre:
            self.mensaje = "Empty filename."
            return False

        if os.path.isabs(nombre):
            ruta = normalizar_ruta(nombre)
        else:
            ruta = normalizar_ruta(os.path.join(self.carpeta_actual, nombre))

        if os.path.exists(ruta):
            if not self.confirmar_simple(f"Overwrite {os.path.basename(ruta)}? Y/N"):
                self.mensaje = "Not overwritten."
                return False

        ruta_anterior = self.ruta_archivo
        carpeta_anterior = self.carpeta_actual

        self.ruta_archivo = ruta
        self.carpeta_actual = os.path.dirname(ruta) or self.carpeta_actual

        if self.guardar_archivo_directo():
            return True

        self.ruta_archivo = ruta_anterior
        self.carpeta_actual = carpeta_anterior
        return False

    # ------------------------------------------------------------
    # Geometria de pantalla
    # ------------------------------------------------------------
    def area_texto(self):
        y_ini = 1
        y_fin = AL - 2
        alto = y_fin - y_ini + 1
        return y_ini, y_fin, alto

    # ------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------
    def dibujar(self):
        limpiar_area(self.stdscr)
        self.dibujar_barra_superior()
        self.dibujar_texto()
        self.dibujar_barra_inferior()
        self.asegurar_cursor_visible()
        self.posicionar_cursor()
        self.stdscr.refresh()

    def dibujar_barra_superior(self):
        marca = "*" if self.modificado else " "
        nombre = self.nombre_archivo()
        menu = " File  Edit  Search  Run  Help "
        info = f"{marca} {nombre}"

        libre = AN - len(menu) - len(info)

        if libre < 1:
            titulo = menu[:AN]
        else:
            titulo = menu + " " * libre + info

        escribir(self.stdscr, 0, 0, titulo[:AN].ljust(AN), C_TITULO)

    def dibujar_barra_inferior(self):
        modo = "INS" if self.insertar else "REP"
        estado = f"Ln {self.cursor_fila + 1} Col {self.cursor_col + 1} {modo}"
        izquierda = "[ESC] Menu"

        escribir(self.stdscr, 0, AL - 1, " " * AN, C_TITULO)
        escribir(self.stdscr, 0, AL - 1, izquierda[:AN], C_TITULO)

        x_estado = max(0, AN - len(estado))
        escribir(self.stdscr, x_estado, AL - 1, estado[:AN], C_TITULO)


    def dibujar_texto(self):
        y_ini, y_fin, alto = self.area_texto()

        for y in range(y_ini, y_fin + 1):
            escribir(self.stdscr, 0, y, " " * AN, C_NORMAL)

        fin = min(len(self.lineas), self.offset_fila + alto)

        for i in range(self.offset_fila, fin):
            y = y_ini + (i - self.offset_fila)
            linea = self.lineas[i]
            self.dibujar_linea_codigo(y, linea)

    def dibujar_linea_codigo(self, y, linea):
        estilos = self.estilos_sintaxis(linea)

        frag = linea[self.offset_col:self.offset_col + AN]
        estilos_frag = estilos[self.offset_col:self.offset_col + AN]

        if self.offset_col > 0 and AN > 1:
            if frag:
                frag = "←" + frag[1:]
                estilos_frag = [C_ESTADO] + estilos_frag[1:]
            else:
                frag = "←"
                estilos_frag = [C_ESTADO]

        if len(linea) > self.offset_col + AN and AN > 1:
            if len(frag) >= AN:
                frag = frag[:AN - 1] + "→"
                estilos_frag = estilos_frag[:AN - 1] + [C_ESTADO]
            else:
                frag += "→"
                estilos_frag.append(C_ESTADO)

        frag = frag[:AN]
        estilos_frag = estilos_frag[:AN]

        for x, ch in enumerate(frag):
            color_ch = estilos_frag[x] if x < len(estilos_frag) else C_NORMAL
            escribir_color(self.stdscr, x, y, ch, color_ch)

    def es_llamada_funcion(self, linea, pos):
        i = pos
        n = len(linea)

        while i < n and linea[i].isspace():
            i += 1

        return i < n and linea[i] == "("

    def estilos_sintaxis(self, linea):
        estilos = [C_NORMAL for _ in linea]
        n = len(linea)
        i = 0

        while i < n:
            ch = linea[i]

            if ch == "#":
                for j in range(i, n):
                    estilos[j] = C_COMENTARIO
                break

            if ch in ("'", '"'):
                quote = ch
                inicio = i
                triple = i + 2 < n and linea[i:i + 3] == quote * 3

                if triple:
                    i += 3
                    while i < n:
                        if i + 2 < n and linea[i:i + 3] == quote * 3:
                            i += 3
                            break
                        i += 1
                else:
                    i += 1
                    escape = False
                    while i < n:
                        if escape:
                            escape = False
                        elif linea[i] == "\\":
                            escape = True
                        elif linea[i] == quote:
                            i += 1
                            break
                        i += 1

                for j in range(inicio, min(i, n)):
                    estilos[j] = C_STRING
                continue

            if ch.isdigit() or (
                ch == "."
                and i + 1 < n
                and linea[i + 1].isdigit()
            ):
                inicio = i
                i += 1

                while i < n and (
                    linea[i].isdigit()
                    or linea[i] in ".xXabcdefABCDEF_"
                    or linea[i] in "eEjJ+-"
                ):
                    if linea[i] in "+-" and linea[i - 1] not in "eE":
                        break
                    i += 1

                for j in range(inicio, min(i, n)):
                    estilos[j] = C_NUMERO
                continue

            if ch.isalpha() or ch == "_":
                inicio = i
                i += 1

                while i < n and (linea[i].isalnum() or linea[i] == "_"):
                    i += 1

                palabra = linea[inicio:i]

                if palabra in PY_KEYWORDS:
                    color_palabra = C_KEYWORD
                elif palabra in PY_BUILTINS or self.es_llamada_funcion(linea, i):
                    color_palabra = C_FUNCION
                else:
                    color_palabra = C_VARIABLE

                for j in range(inicio, i):
                    estilos[j] = color_palabra

                continue

            i += 1

        return estilos

    def asegurar_cursor_visible(self):
        _, _, alto = self.area_texto()

        if self.cursor_fila < self.offset_fila:
            self.offset_fila = self.cursor_fila
        elif self.cursor_fila >= self.offset_fila + alto:
            self.offset_fila = self.cursor_fila - alto + 1

        if self.cursor_col < self.offset_col:
            self.offset_col = self.cursor_col
        elif self.cursor_col >= self.offset_col + AN:
            self.offset_col = self.cursor_col - AN + 1

        self.offset_fila = max(0, self.offset_fila)
        self.offset_col = max(0, self.offset_col)

    def posicionar_cursor(self):
        y_ini, y_fin, _ = self.area_texto()
        y = y_ini + (self.cursor_fila - self.offset_fila)
        x = self.cursor_col - self.offset_col

        y = max(y_ini, min(y, y_fin))
        x = max(0, min(x, AN - 1))

        try:
            self.stdscr.move(y, x)
        except curses.error:
            pass

    # ------------------------------------------------------------
    # Bucle principal
    # ------------------------------------------------------------
    def bucle(self):
        cursor_visible(True)

        try:
            while True:
                actualizar_tamano(self.stdscr)
                self.dibujar()
                tecla = self.leer_tecla_principal()
                self.mensaje = ""

                if tecla == curses.KEY_RESIZE:
                    actualizar_tamano(self.stdscr)
                    self.asegurar_cursor_visible()
                    continue

                if tecla == CTRL_C:
                    if self.confirmar_salida():
                        break
                elif tecla == "menu":
                    accion = self.menu_superior()

                    if accion == "salir":
                        break
                elif tecla == "undo":
                    self.deshacer()
                elif tecla == "redo":
                    self.rehacer()
                elif tecla == "copy":
                    self.copiar_linea()
                elif tecla == "cut":
                    self.cortar_linea()
                elif tecla == "paste":
                    self.pegar_linea()
                elif tecla == "duplicate":
                    self.duplicar_linea()
                elif tecla == "save":
                    self.guardar_archivo()
                elif tecla == "open":
                    self.abrir_desde_panel()
                elif tecla == "run":
                    self.ejecutar_programa()
                elif tecla == "find":
                    self.buscar()
                elif tecla == "find_next":
                    self.buscar_siguiente()
                elif tecla == curses.KEY_F1 or tecla == CTRL_G:
                    self.mostrar_ayuda()
                elif tecla == curses.KEY_F2 or tecla == CTRL_S:
                    self.guardar_archivo()
                elif tecla == curses.KEY_F3 or tecla == CTRL_F:
                    self.buscar()
                elif tecla == curses.KEY_F4 or tecla == CTRL_N:
                    self.buscar_siguiente()
                elif tecla == curses.KEY_F5 or tecla == curses.KEY_IC:
                    self.insertar = not self.insertar
                elif tecla == curses.KEY_F6 or tecla == CTRL_O:
                    self.abrir_desde_panel()
                elif tecla == curses.KEY_F7:
                    self.guardar_como()
                elif tecla == curses.KEY_F8 or tecla == CTRL_R:
                    self.ejecutar_programa()
                elif tecla == 27:
                    accion = self.menu_superior()

                    if accion == "salir":
                        break
                else:
                    self.manejar_tecla_edicion(tecla)
        except KeyboardInterrupt:
            pass
        finally:
            cursor_visible(False)
            limpiar_area(self.stdscr)
            self.stdscr.refresh()

    # ------------------------------------------------------------
    # Undo / Redo
    # ------------------------------------------------------------
    def crear_estado_editor(self):
        return {
            "lineas": list(self.lineas),
            "cursor_fila": self.cursor_fila,
            "cursor_col": self.cursor_col,
            "offset_fila": self.offset_fila,
            "offset_col": self.offset_col,
            "modificado": self.modificado,
            "insertar": self.insertar,
        }

    def restaurar_estado_editor(self, estado):
        self.lineas = list(estado["lineas"])

        if not self.lineas:
            self.lineas = [""]

        self.cursor_fila = max(0, min(estado["cursor_fila"], len(self.lineas) - 1))
        self.cursor_col = max(0, min(estado["cursor_col"], len(self.lineas[self.cursor_fila])))

        self.offset_fila = max(0, estado["offset_fila"])
        self.offset_col = max(0, estado["offset_col"])
        self.modificado = estado["modificado"]
        self.insertar = estado["insertar"]

    def guardar_undo(self):
        estado = self.crear_estado_editor()

        if self.undo_stack and self.undo_stack[-1] == estado:
            return

        self.undo_stack.append(estado)

        if len(self.undo_stack) > MAX_UNDO:
            self.undo_stack.pop(0)

        self.redo_stack.clear()

    def limpiar_undo_redo(self):
        self.undo_stack.clear()
        self.redo_stack.clear()

    def deshacer(self):
        if not self.undo_stack:
            self.mensaje = "Nothing to undo."
            return None

        estado_actual = self.crear_estado_editor()
        estado_anterior = self.undo_stack.pop()

        self.redo_stack.append(estado_actual)

        if len(self.redo_stack) > MAX_UNDO:
            self.redo_stack.pop(0)

        self.restaurar_estado_editor(estado_anterior)
        self.mensaje = "Undo."

        return None

    def rehacer(self):
        if not self.redo_stack:
            self.mensaje = "Nothing to redo."
            return None

        estado_actual = self.crear_estado_editor()
        estado_siguiente = self.redo_stack.pop()

        self.undo_stack.append(estado_actual)

        if len(self.undo_stack) > MAX_UNDO:
            self.undo_stack.pop(0)

        self.restaurar_estado_editor(estado_siguiente)
        self.mensaje = "Redo."

        return None


    # ------------------------------------------------------------
    # Menu superior
    # ------------------------------------------------------------
    def leer_tecla_principal(self):
        mapa_alt = {
            TECLA_ALT_MENU: "menu",
            ord("M"): "menu",
            TECLA_ALT_UNDO: "undo",
            ord("Z"): "undo",
            TECLA_ALT_UNDO_ALT: "undo",
            ord("U"): "undo",
            TECLA_ALT_REDO: "redo",
            ord("Y"): "redo",
            TECLA_ALT_COPY: "copy",
            ord("C"): "copy",
            TECLA_ALT_CUT: "cut",
            ord("X"): "cut",
            TECLA_ALT_PASTE: "paste",
            ord("V"): "paste",
            TECLA_ALT_DUP: "duplicate",
            ord("D"): "duplicate",
            TECLA_ALT_SAVE: "save",
            ord("S"): "save",
            TECLA_ALT_OPEN: "open",
            ord("O"): "open",
            TECLA_ALT_RUN: "run",
            ord("R"): "run",
            TECLA_ALT_FIND: "find",
            ord("F"): "find",
            TECLA_ALT_FIND_NEXT: "find_next",
            ord("N"): "find_next",
        }

        tipo, siguiente = self.teclado.leer_evento()

        if tipo == "tecla":
            return siguiente

        if siguiente in mapa_alt:
            return mapa_alt[siguiente]

        if siguiente is not None:
            curses.ungetch(siguiente)

        return 27


    def opciones_menu_superior(self):
        return [
            {
                "titulo": "File",
                "x": 1,
                "opciones": [
                    ("New", self.nuevo_archivo),
                    ("Open", self.abrir_desde_panel),
                    ("Save", self.guardar_archivo),
                    ("Save as", self.guardar_como),
                    ("Exit", self.salir_desde_menu),
                ],
            },
            {
                "titulo": "Edit",
                "x": 7,
                "opciones": [
                    ("Undo", self.deshacer),
                    ("Redo", self.rehacer),
                    ("Cut line", self.cortar_linea),
                    ("Copy line", self.copiar_linea),
                    ("Paste line", self.pegar_linea),
                    ("Duplicate", self.duplicar_linea),
                    ("Ins/Rep", self.alternar_insertar),
                ],
            },
            {
                "titulo": "Search",
                "x": 13,
                "opciones": [
                    ("Find", self.buscar),
                    ("Find next", self.buscar_siguiente),
                ],
            },
            {
                "titulo": "Run",
                "x": 21,
                "opciones": [
                    ("Run file", self.ejecutar_programa),
                ],
            },
            {
                "titulo": "Help",
                "x": 26,
                "opciones": [
                    ("Help", self.mostrar_ayuda),
                    ("Console font", self.seleccionar_fuente_consola),
                    ("About", self.mostrar_acerca_de),
                ],
            },
        ]

    def menu_superior(self):
        menus = self.opciones_menu_superior()
        menu_sel = 0
        item_sel = 0

        cursor_visible(False)

        while True:
            actualizar_tamano(self.stdscr)
            self.dibujar()
            self.dibujar_menu_superior(menus, menu_sel, item_sel)
            self.stdscr.refresh()

            tecla = self.teclado.leer_tecla()

            if tecla in (27, CTRL_C):
                cursor_visible(True)
                return None

            if tecla == curses.KEY_RESIZE:
                actualizar_tamano(self.stdscr)
                continue

            if tecla == curses.KEY_LEFT:
                menu_sel = (menu_sel - 1) % len(menus)
                item_sel = 0
                continue

            if tecla == curses.KEY_RIGHT:
                menu_sel = (menu_sel + 1) % len(menus)
                item_sel = 0
                continue

            opciones = menus[menu_sel]["opciones"]

            if tecla == curses.KEY_UP:
                item_sel = (item_sel - 1) % len(opciones)
                continue

            if tecla == curses.KEY_DOWN:
                item_sel = (item_sel + 1) % len(opciones)
                continue

            if tecla in (10, 13, curses.KEY_ENTER):
                funcion = opciones[item_sel][1]
                resultado = funcion()
                cursor_visible(True)
                return resultado

            if 32 <= tecla <= 126:
                letra = chr(tecla).lower()

                for i, (nombre, funcion) in enumerate(opciones):
                    if nombre and nombre[0].lower() == letra:
                        item_sel = i
                        resultado = funcion()
                        cursor_visible(True)
                        return resultado

    def dibujar_menu_superior(self, menus, menu_sel, item_sel):
        menu = menus[menu_sel]

        for i, dato in enumerate(menus):
            color = C_RESALTA if i == menu_sel else C_TITULO
            escribir(
                self.stdscr,
                dato["x"],
                0,
                " " + dato["titulo"] + " ",
                color
            )

        ancho = max(len(nombre) for nombre, _ in menu["opciones"]) + 4
        alto = len(menu["opciones"]) + 2
        x = menu["x"]
        y = 1

        if ancho > AN:
            ancho = AN

        if x + ancho >= AN:
            x = max(0, AN - ancho)

        self.dibujar_ventana(x, y, ancho, alto, menu["titulo"])

        for i, (nombre, _) in enumerate(menu["opciones"]):
            color = C_VENTANA_SEL if i == item_sel else C_VENTANA
            self.escribir_en_ventana(
                x + 2,
                y + 1 + i,
                ancho - 4,
                nombre,
                color
            )

    def nuevo_archivo(self):
        if self.modificado:
            r = self.confirmar_tres_opciones("Unsaved changes. Save first? Y/N/ESC")

            if r == "esc":
                return None

            if r == "y":
                if not self.guardar_archivo():
                    return None

        self.ruta_archivo = None
        self.lineas = [""]
        self.cursor_fila = 0
        self.cursor_col = 0
        self.offset_fila = 0
        self.offset_col = 0
        self.modificado = False
        self.limpiar_undo_redo()
        self.mensaje = "New file."

        return None

    def alternar_insertar(self):
        self.insertar = not self.insertar
        return None

    def salir_desde_menu(self):
        if self.confirmar_salida():
            return "salir"

        return None

    def mostrar_acerca_de(self):
        lineas = [
            "PicoEdit",
            "",
            "Compact editor for PicoCalc Linux.",
            "",
            "ALT+M opens the top menu.",
            "Exit is located under File > Exit.",
            "",
            "Ariel Palazzesi 2026",
        ]

        ancho = 43
        alto = 10
        x = (AN - ancho) // 2
        y = (AL - alto) // 2

        self.dibujar()
        self.dibujar_ventana(x, y, ancho, alto, "About")

        for i, linea in enumerate(lineas):
            self.escribir_en_ventana(x + 2, y + 2 + i, ancho - 4, linea, C_VENTANA)

        self.stdscr.refresh()

        while True:
            tecla = self.teclado.leer_tecla()

            if tecla in (27, 10, 13, curses.KEY_ENTER):
                return None


    def seleccionar_fuente_consola(self):
        cargador = cargador_fuente_consola_disponible()

        if cargador is None:
            self.mensaje = "setfont/loadfont not found. Install console font tools."
            return None

        fuentes = listar_fuentes_consola()

        if not fuentes:
            self.mensaje = "No PSF console fonts found."
            return None

        seleccion = 0
        offset = 0

        while True:
            actualizar_tamano(self.stdscr)
            ancho = min(max(30, AN - 4), AN)
            alto = min(max(8, AL - 4), AL)
            x = max(0, (AN - ancho) // 2)
            y = max(0, (AL - alto) // 2)
            alto_lista = max(1, alto - 5)

            seleccion = max(0, min(seleccion, len(fuentes) - 1))

            if seleccion < offset:
                offset = seleccion
            elif seleccion >= offset + alto_lista:
                offset = seleccion - alto_lista + 1

            self.dibujar()
            self.dibujar_ventana(x, y, ancho, alto, "Console font")

            fin = min(len(fuentes), offset + alto_lista)

            for i in range(offset, fin):
                fila = y + 2 + (i - offset)
                nombre = fuentes[i]["nombre"]
                color = C_VENTANA_SEL if i == seleccion else C_VENTANA
                self.escribir_en_ventana(x + 2, fila, ancho - 4, nombre, color)

            pie = "ENTER apply  ESC cancel"
            self.escribir_en_ventana(x + 2, y + alto - 2, ancho - 4, pie, C_VENTANA_ESTADO)
            self.stdscr.refresh()

            tecla = self.teclado.leer_tecla()

            if tecla in (27, CTRL_C):
                self.mensaje = "Font selection canceled."
                return None

            if tecla == curses.KEY_RESIZE:
                actualizar_tamano(self.stdscr)
                continue

            if tecla == curses.KEY_UP:
                seleccion = max(0, seleccion - 1)
                continue

            if tecla == curses.KEY_DOWN:
                seleccion = min(len(fuentes) - 1, seleccion + 1)
                continue

            if tecla == curses.KEY_PPAGE:
                seleccion = max(0, seleccion - alto_lista)
                continue

            if tecla == curses.KEY_NPAGE:
                seleccion = min(len(fuentes) - 1, seleccion + alto_lista)
                continue

            if tecla in (10, 13, curses.KEY_ENTER):
                self.aplicar_fuente_consola(fuentes[seleccion])
                return None

    def aplicar_fuente_consola(self, fuente):
        curses.def_prog_mode()
        curses.endwin()
        cargador = cargador_fuente_consola_disponible()

        try:
            if cargador is not None and cargador[0] == "picofont":
                eleccion = eleccion_picofont_para_fuente(fuente["nombre"])

                if eleccion is None:
                    resultado = subprocess.CompletedProcess(
                        [cargador[1]],
                        1,
                        stdout="",
                        stderr="picofont supports only Terminus VGA 14/16/18/20"
                    )
                else:
                    resultado = subprocess.run(
                        [cargador[1], eleccion],
                        check=False,
                        capture_output=True,
                        text=True
                    )
            elif cargador is not None and cargador[0] == "setfont":
                resultado = subprocess.run(
                    [cargador[1], fuente["ruta"]],
                    check=False,
                    capture_output=True,
                    text=True
                )
            elif cargador is not None and cargador[0] == "loadfont":
                resultado = subprocess.run(
                    [cargador[1]],
                    input=leer_bytes_fuente_consola(fuente["ruta"]),
                    check=False,
                    capture_output=True
                )
            else:
                resultado = subprocess.CompletedProcess(
                    ["setfont/loadfont"],
                    1,
                    stdout=b"",
                    stderr=b"setfont/loadfont not found"
                )

            if resultado.returncode == 0:
                self.ajustar_tamano_por_fuente(fuente)
        finally:
            curses.reset_prog_mode()
            cursor_visible(True)
            actualizar_tamano(self.stdscr)

        if resultado.returncode == 0:
            self.mensaje = f"Font: {fuente['nombre']}"
            return

        error = (resultado.stderr or resultado.stdout or b"console font load failed")

        if isinstance(error, bytes):
            error = error.decode("utf-8", "replace")

        error = error.strip()
        self.mensaje = error.splitlines()[0][:AN] if error else "console font load failed"

    def ajustar_tamano_por_fuente(self, fuente):
        tamano = tamano_terminal_para_fuente(fuente["nombre"])

        if not tamano:
            return

        filas, columnas = tamano
        subprocess.run(
            ["stty", "rows", str(filas), "cols", str(columnas)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )


    # ------------------------------------------------------------
    # Edicion
    # ------------------------------------------------------------
    def manejar_tecla_edicion(self, tecla):
        if tecla == curses.KEY_UP:
            self.mover_arriba()
        elif tecla == curses.KEY_DOWN:
            self.mover_abajo()
        elif tecla == curses.KEY_LEFT:
            self.mover_izquierda()
        elif tecla == curses.KEY_RIGHT:
            self.mover_derecha()
        elif tecla == curses.KEY_HOME:
            self.cursor_col = 0
        elif tecla == curses.KEY_END:
            self.cursor_col = len(self.lineas[self.cursor_fila])
        elif tecla == curses.KEY_PPAGE:
            self.page_up()
        elif tecla == curses.KEY_NPAGE:
            self.page_down()
        elif tecla in (curses.KEY_BACKSPACE, 127, 8):
            self.backspace()
        elif tecla == curses.KEY_DC:
            self.delete()
        elif tecla in (10, 13, curses.KEY_ENTER):
            self.insertar_salto_linea()
        elif tecla == 9:
            self.insertar_texto("    ")
        elif tecla == CTRL_X:
            self.cortar_linea()
        elif tecla == CTRL_V:
            self.pegar_linea()
        elif tecla == CTRL_D:
            self.duplicar_linea()
        elif 32 <= tecla <= 126:
            self.insertar_texto(chr(tecla))

    def mover_arriba(self):
        if self.cursor_fila > 0:
            self.cursor_fila -= 1
            self.ajustar_columna()

    def mover_abajo(self):
        if self.cursor_fila < len(self.lineas) - 1:
            self.cursor_fila += 1
            self.ajustar_columna()

    def mover_izquierda(self):
        if self.cursor_col > 0:
            self.cursor_col -= 1
        elif self.cursor_fila > 0:
            self.cursor_fila -= 1
            self.cursor_col = len(self.lineas[self.cursor_fila])

    def mover_derecha(self):
        if self.cursor_col < len(self.lineas[self.cursor_fila]):
            self.cursor_col += 1
        elif self.cursor_fila < len(self.lineas) - 1:
            self.cursor_fila += 1
            self.cursor_col = 0

    def page_up(self):
        _, _, alto = self.area_texto()
        self.cursor_fila = max(0, self.cursor_fila - alto)
        self.ajustar_columna()

    def page_down(self):
        _, _, alto = self.area_texto()
        self.cursor_fila = min(len(self.lineas) - 1, self.cursor_fila + alto)
        self.ajustar_columna()

    def ajustar_columna(self):
        self.cursor_col = min(self.cursor_col, len(self.lineas[self.cursor_fila]))

    def insertar_texto(self, texto):
        self.guardar_undo()

        for ch in texto:
            linea = self.lineas[self.cursor_fila]

            if self.insertar or self.cursor_col >= len(linea):
                self.lineas[self.cursor_fila] = linea[:self.cursor_col] + ch + linea[self.cursor_col:]
            else:
                self.lineas[self.cursor_fila] = linea[:self.cursor_col] + ch + linea[self.cursor_col + 1:]

            self.cursor_col += 1

        self.modificado = True

    def insertar_salto_linea(self):
        self.guardar_undo()

        linea = self.lineas[self.cursor_fila]
        izquierda = linea[:self.cursor_col]
        derecha = linea[self.cursor_col:]

        self.lineas[self.cursor_fila] = izquierda

        indent = ""
        for ch in izquierda:
            if ch in (" ", "\t"):
                indent += ch
            else:
                break

        if self.nombre_archivo().endswith(".py") and izquierda.strip().endswith(":"):
            indent += "    "

        self.lineas.insert(self.cursor_fila + 1, indent + derecha)
        self.cursor_fila += 1
        self.cursor_col = len(indent)
        self.modificado = True

    def backspace(self):
        if self.cursor_col > 0:
            self.guardar_undo()
            linea = self.lineas[self.cursor_fila]
            self.lineas[self.cursor_fila] = linea[:self.cursor_col - 1] + linea[self.cursor_col:]
            self.cursor_col -= 1
            self.modificado = True
            return

        if self.cursor_fila > 0:
            self.guardar_undo()
            actual = self.lineas[self.cursor_fila]
            anterior = self.lineas[self.cursor_fila - 1]
            self.cursor_col = len(anterior)
            self.lineas[self.cursor_fila - 1] = anterior + actual
            del self.lineas[self.cursor_fila]
            self.cursor_fila -= 1
            self.modificado = True

    def delete(self):
        linea = self.lineas[self.cursor_fila]

        if self.cursor_col < len(linea):
            self.guardar_undo()
            self.lineas[self.cursor_fila] = linea[:self.cursor_col] + linea[self.cursor_col + 1:]
            self.modificado = True
            return

        if self.cursor_fila < len(self.lineas) - 1:
            self.guardar_undo()
            self.lineas[self.cursor_fila] += self.lineas[self.cursor_fila + 1]
            del self.lineas[self.cursor_fila + 1]
            self.modificado = True

    def copiar_linea(self):
        self.portapapeles = self.lineas[self.cursor_fila]
        self.mensaje = "Line copied."

    def cortar_linea(self):
        self.guardar_undo()

        self.portapapeles = self.lineas[self.cursor_fila]

        if len(self.lineas) == 1:
            self.lineas[0] = ""
            self.cursor_col = 0
        else:
            del self.lineas[self.cursor_fila]
            self.cursor_fila = min(self.cursor_fila, len(self.lineas) - 1)
            self.ajustar_columna()

        self.modificado = True
        self.mensaje = "Line cut."

    def pegar_linea(self):
        self.guardar_undo()

        self.lineas.insert(self.cursor_fila + 1, self.portapapeles)
        self.cursor_fila += 1
        self.cursor_col = len(self.portapapeles)
        self.modificado = True
        self.mensaje = "Line pasted."

    def duplicar_linea(self):
        self.guardar_undo()

        linea = self.lineas[self.cursor_fila]
        self.lineas.insert(self.cursor_fila + 1, linea)
        self.cursor_fila += 1
        self.cursor_col = min(self.cursor_col, len(linea))
        self.modificado = True
        self.mensaje = "Line duplicated."

    # ------------------------------------------------------------
    # Ejecutar el programa actual
    # ------------------------------------------------------------
    def ejecutar_programa(self):
        if not self.ruta_archivo:
            self.mensaje = "Save the file before running."
            if not self.guardar_como():
                return

        if self.modificado:
            r = self.confirmar_tres_opciones("Save before running? Y/N/ESC")

            if r == "esc":
                self.mensaje = "Execution canceled."
                return

            if r == "y":
                if not self.guardar_archivo_directo():
                    return

        if not self.ruta_archivo:
            self.mensaje = "No file to run."
            return

        if not self.ruta_archivo.endswith(".py"):
            if not self.confirmar_simple("Not a .py file. Run anyway? Y/N"):
                return

        carpeta = os.path.dirname(self.ruta_archivo) or os.getcwd()

        curses.def_prog_mode()
        curses.endwin()

        try:
            print()
            print("Running:", self.ruta_archivo)
            print("-----------------------------------------------------")
            resultado = subprocess.run(
                [sys.executable, self.ruta_archivo],
                cwd=carpeta,
                check=False
            )
            print("-----------------------------------------------------")
            print(f"Process finished. Code: {resultado.returncode}")
            input("Press ENTER to return to PicoEdit...")
        except Exception as e:
            print()
            print("Error while running:")
            print(e)
            input("Press ENTER to return to PicoEdit...")
        finally:
            curses.reset_prog_mode()
            cursor_visible(True)
            self.mensaje = "Execution finished."
            self.stdscr.refresh()


    # ------------------------------------------------------------
    # Busqueda
    # ------------------------------------------------------------
    def buscar(self):
        termino = self.input_barra("Search: ", self.busqueda)

        if termino is None:
            return

        self.busqueda = termino
        self.buscar_siguiente(desde_inicio=True)

    def buscar_siguiente(self, desde_inicio=False):
        if not self.busqueda:
            self.mensaje = "No search query active."
            return

        total = len(self.lineas)

        if desde_inicio:
            fila = 0
            col = 0
        else:
            fila = self.cursor_fila
            col = self.cursor_col + 1

        inicio = (fila, col)

        while True:
            idx = self.lineas[fila].find(self.busqueda, col)

            if idx != -1:
                self.cursor_fila = fila
                self.cursor_col = idx
                self.mensaje = "Found."
                return

            fila += 1
            col = 0

            if fila >= total:
                fila = 0

            if (fila, col) == inicio:
                self.mensaje = "Not found."
                return

    # ------------------------------------------------------------
    # Ventanas simples con borde ASCII
    # ------------------------------------------------------------
    def dibujar_ventana(self, x, y, ancho, alto, titulo_txt=""):
        ancho = max(4, min(ancho, AN - max(0, x)))
        alto = max(3, min(alto, AL - max(0, y)))

        borde_sup = "╔" + "═" * (ancho - 2) + "╗"
        borde_inf = "╚" + "═" * (ancho - 2) + "╝"
        borde_med = "║" + " " * (ancho - 2) + "║"

        escribir_attr(self.stdscr, x, y, borde_sup, C_VENTANA_BORDE, curses.A_BOLD)

        for fila in range(1, alto - 1):
            escribir(self.stdscr, x, y + fila, borde_med, C_VENTANA)
            escribir_attr(self.stdscr, x, y + fila, "║", C_VENTANA_BORDE, curses.A_BOLD)
            escribir_attr(self.stdscr, x + ancho - 1, y + fila, "║", C_VENTANA_BORDE, curses.A_BOLD)

        escribir_attr(self.stdscr, x, y + alto - 1, borde_inf, C_VENTANA_BORDE, curses.A_BOLD)

        if titulo_txt:
            titulo_visible = " " + titulo_txt[:ancho - 6] + " "
            escribir_attr(self.stdscr, x + 2, y, titulo_visible, C_VENTANA_BORDE, curses.A_BOLD)


    def escribir_en_ventana(self, x, y, ancho, texto, color=C_VENTANA):
        escribir(self.stdscr, x, y, texto[:ancho].ljust(ancho), color)

    # ------------------------------------------------------------
    # Panel para abrir archivos
    # ------------------------------------------------------------
    def listar_panel(self, carpeta):
        entradas = []

        padre = os.path.abspath(os.path.join(carpeta, os.pardir))
        entradas.append({
            "nombre": "..",
            "ruta": padre,
            "tipo": "dir",
        })

        try:
            nombres = os.listdir(carpeta)
        except Exception:
            return entradas

        dirs = []
        archivos = []

        for nombre in nombres:
            ruta = os.path.join(carpeta, nombre)

            if os.path.isdir(ruta) and not nombre.startswith("."):
                dirs.append(nombre)
            elif os.path.isfile(ruta) and nombre.endswith(".py"):
                archivos.append(nombre)

        for nombre in sorted(dirs, key=str.lower):
            entradas.append({
                "nombre": nombre + "/",
                "ruta": os.path.join(carpeta, nombre),
                "tipo": "dir",
            })

        for nombre in sorted(archivos, key=str.lower):
            entradas.append({
                "nombre": nombre,
                "ruta": os.path.join(carpeta, nombre),
                "tipo": "file",
            })

        return entradas

    def abrir_desde_panel(self):
        if self.modificado:
            r = self.confirmar_tres_opciones(
                "Unsaved changes. Save first? Y/N/ESC"
            )

            if r == "esc":
                return

            if r == "y":
                if not self.guardar_archivo():
                    return

        ruta = self.panel_archivos(self.carpeta_actual)

        if ruta is None:
            self.mensaje = "Open canceled."
            return

        self.ruta_archivo = normalizar_ruta(ruta)
        self.carpeta_actual = os.path.dirname(self.ruta_archivo) or self.carpeta_actual
        self.cargar_archivo()

        if not self.lineas:
            self.lineas = [""]

        self.cursor_fila = 0
        self.cursor_col = 0
        self.offset_fila = 0
        self.offset_col = 0
        self.modificado = False
        self.limpiar_undo_redo()
        self.mensaje = "File opened."

    def panel_archivos(self, carpeta_inicial):
        carpeta = normalizar_ruta(carpeta_inicial) or os.getcwd()
        seleccion = 0
        offset = 0

        while True:
            actualizar_tamano(self.stdscr)
            ventana_an = max(18, AN - 6)
            ventana_al = max(8, AL - 4)
            vx = min(3, max(0, AN - ventana_an))
            vy = min(2, max(0, AL - ventana_al))

            entradas = self.listar_panel(carpeta)

            if not entradas:
                entradas = [{"nombre": "..", "ruta": os.path.dirname(carpeta), "tipo": "dir"}]

            seleccion = max(0, min(seleccion, len(entradas) - 1))

            alto_lista = ventana_al - 6

            if seleccion < offset:
                offset = seleccion
            elif seleccion >= offset + alto_lista:
                offset = seleccion - alto_lista + 1

            self.dibujar()
            self.dibujar_ventana(vx, vy, ventana_an, ventana_al, "Open Python file")

            ruta_visible = carpeta[-(ventana_an - 4):]
            self.escribir_en_ventana(vx + 2, vy + 1, ventana_an - 4, ruta_visible, C_VENTANA_ESTADO)

            fin_lista = min(len(entradas), offset + alto_lista)

            for i in range(offset, fin_lista):
                y = vy + 3 + (i - offset)
                entrada = entradas[i]
                nombre = entrada["nombre"]

                pref = "[D] " if entrada["tipo"] == "dir" else "    "
                texto = (pref + nombre)[:ventana_an - 4]

                if i == seleccion:
                    self.escribir_en_ventana(vx + 2, y, ventana_an - 4, texto, C_VENTANA_SEL)
                elif entrada["tipo"] == "dir":
                    self.escribir_en_ventana(vx + 2, y, ventana_an - 4, texto, C_VENTANA_DIR)
                else:
                    self.escribir_en_ventana(vx + 2, y, ventana_an - 4, texto, C_VENTANA)

            pie = "ENTER open  ESC cancel"
            self.escribir_en_ventana(vx + 2, vy + ventana_al - 2, ventana_an - 4, pie, C_VENTANA_ESTADO)

            self.stdscr.refresh()
            tecla = self.teclado.leer_tecla()

            if tecla in (27, CTRL_C):
                return None

            if tecla == curses.KEY_UP:
                seleccion = max(0, seleccion - 1)
            elif tecla == curses.KEY_DOWN:
                seleccion = min(len(entradas) - 1, seleccion + 1)
            elif tecla == curses.KEY_PPAGE:
                seleccion = max(0, seleccion - alto_lista)
            elif tecla == curses.KEY_NPAGE:
                seleccion = min(len(entradas) - 1, seleccion + alto_lista)
            elif tecla in (10, 13, curses.KEY_ENTER):
                entrada = entradas[seleccion]

                if entrada["tipo"] == "dir":
                    carpeta = normalizar_ruta(entrada["ruta"])
                    seleccion = 0
                    offset = 0
                else:
                    return entrada["ruta"]

    # ------------------------------------------------------------
    # Entrada editable en barra inferior
    # ------------------------------------------------------------
    def input_barra(self, prompt, inicial=""):
        texto = list(inicial)
        pos = len(texto)
        offset = 0

        cursor_visible(True)

        while True:
            actualizar_tamano(self.stdscr)
            ancho_input = max(1, AN - len(prompt))

            if pos < offset:
                offset = pos
            elif pos > offset + ancho_input:
                offset = pos - ancho_input

            frag = "".join(texto[offset:offset + ancho_input])
            visible = prompt + frag

            escribir(self.stdscr, 0, AL - 1, " " * AN, C_TITULO)

            if offset > 0 and len(prompt) < AN:
                visible = prompt[:-1] + "←" + frag if prompt else "←" + frag

            if offset + ancho_input < len(texto):
                visible = visible[:AN - 1] + "→"

            escribir(self.stdscr, 0, AL - 1, visible[:AN].ljust(AN), C_TITULO)

            cursor_x = len(prompt) + (pos - offset)
            cursor_x = max(0, min(cursor_x, AN - 1))

            try:
                self.stdscr.move(AL - 1, cursor_x)
            except curses.error:
                pass

            self.stdscr.refresh()
            tecla = self.teclado.leer_tecla()

            if tecla in (10, 13, curses.KEY_ENTER):
                return "".join(texto)

            if tecla == 27:
                return None

            if tecla == curses.KEY_LEFT:
                pos = max(0, pos - 1)
                continue

            if tecla == curses.KEY_RIGHT:
                pos = min(len(texto), pos + 1)
                continue

            if tecla == curses.KEY_HOME:
                pos = 0
                continue

            if tecla == curses.KEY_END:
                pos = len(texto)
                continue

            if tecla in (curses.KEY_BACKSPACE, 127, 8):
                if pos > 0:
                    del texto[pos - 1]
                    pos -= 1
                continue

            if tecla == curses.KEY_DC:
                if pos < len(texto):
                    del texto[pos]
                continue

            if 32 <= tecla <= 126:
                texto.insert(pos, chr(tecla))
                pos += 1

    # ------------------------------------------------------------
    # Ayuda y confirmaciones
    # ------------------------------------------------------------
    def mostrar_ayuda(self):
        lineas = [
            "Main",
            "  ALT+M        open menu",
            "  ESC          open menu",
            "",
            "File",
            "  ALT+S        save",
            "  ALT+O        open",
            "",
            "Edit",
            "  ALT+U        undo",
            "  ALT+Y        redo",
            "  ALT+C/X/V    copy / cut / paste line",
            "  ALT+D        duplicate line",
            "",
            "Search / Run",
            "  ALT+F        find",
            "  ALT+N        find next",
            "  ALT+R        run file",
            "",
            "Help",
            "  Console font changes Linux console font",
        ]

        ancho = min(47, max(24, AN - 4))
        alto = min(21, max(8, AL - 4))
        x = (AN - ancho) // 2
        y = (AL - alto) // 2

        self.dibujar()
        self.dibujar_ventana(x, y, ancho, alto, "Help")

        for i, linea in enumerate(lineas[:alto - 3]):
            color = C_VENTANA_ESTADO if linea and not linea.startswith(" ") else C_VENTANA
            self.escribir_en_ventana(
                x + 2,
                y + 1 + i,
                ancho - 4,
                linea,
                color
            )

        pie = "ENTER/ESC close"
        self.escribir_en_ventana(x + 2, y + alto - 2, ancho - 4, pie, C_VENTANA_ESTADO)

        self.stdscr.refresh()

        while True:
            tecla = self.teclado.leer_tecla()

            if tecla in (27, CTRL_C, 10, 13, curses.KEY_ENTER):
                return None


    def confirmar_simple(self, mensaje):
        escribir(self.stdscr, 0, AL - 1, " " * AN, C_TITULO)
        escribir(self.stdscr, 0, AL - 1, mensaje[:AN], C_TITULO)
        self.stdscr.refresh()

        while True:
            tecla = self.teclado.leer_tecla()

            if tecla in (ord("y"), ord("Y")):
                return True

            if tecla in (ord("n"), ord("N"), 27, CTRL_C):
                return False

    def confirmar_tres_opciones(self, mensaje):
        escribir(self.stdscr, 0, AL - 1, " " * AN, C_TITULO)
        escribir(self.stdscr, 0, AL - 1, mensaje[:AN], C_TITULO)
        self.stdscr.refresh()

        while True:
            tecla = self.teclado.leer_tecla()

            if tecla in (ord("y"), ord("Y")):
                return "y"

            if tecla in (ord("n"), ord("N")):
                return "n"

            if tecla in (27, CTRL_C):
                return "esc"

    def confirmar_salida(self):
        if not self.modificado:
            return True

        r = self.confirmar_tres_opciones("Save changes before exit? Y/N/ESC")

        if r == "esc":
            return False

        if r == "n":
            return True

        # Al salir, siempre mostramos el nombre en un campo editable.
        # Si era un archivo abierto, aparece su nombre.
        # Si era un archivo nuevo, aparece vacio.
        return self.guardar_como()


def main(stdscr):
    signal.signal(signal.SIGINT, signal.default_int_handler)

    if len(sys.argv) >= 2:
        ruta = sys.argv[1]
    else:
        ruta = None

    ejecutar(stdscr, ruta)


if __name__ == "__main__":
    try:
        preparar_terminal_consola()
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
