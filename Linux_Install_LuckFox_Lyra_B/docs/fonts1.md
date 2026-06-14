# Cambiar la fuente de consola en PicoCalc con Luckfox Lyra B y Linux

<span><img src="https://img.shields.io/badge/PicoCalc-LuckFox%20%2B%20Linux-5E81AC?style=for-the-badge&logo=linux&logoColor=white"/></span>
<span><img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black"/></span>
<span><img src="https://img.shields.io/badge/Ubuntu-24.04.2-E95420?style=for-the-badge&logo=ubuntu&logoColor=white"/></span>

Este documento explica cómo cambiar la fuente utilizada por la consola de Linux en una **PicoCalc** modificada con una **[Luckfox Lyra B](https://github.com/VintaBytes/LuckFox-Lyra-B-Picocalc/blob/main/Linux_Install_LuckFox_Lyra_B/readme.md)**.

El procedimiento está pensado para una instalación de Linux en modo consola, sin entorno gráfico, donde la PicoCalc se usa principalmente como una pequeña computadora portátil para terminal, edición de texto, programación y ejecución de scripts.

La fuente de consola es importante en este dispositivo porque la pantalla es pequeña. Una fuente demasiado grande, demasiado ancha o poco legible puede hacer que entren pocas columnas y pocas líneas, dificultando el uso real de la terminal.

---

## Objetivo

El objetivo de este procedimiento es cambiar la fuente de texto usada por la consola Linux para mejorar la legibilidad y aprovechar mejor el espacio disponible en pantalla.

En particular, se busca poder elegir una fuente más cómoda para la PicoCalc, por ejemplo una variante de **Terminus**, que suele funcionar bien en pantallas pequeñas por ser clara, compacta y legible.

---

## Contexto

En una instalación normal de Linux para escritorio, la fuente suele configurarse desde el entorno gráfico.

Pero en este caso estamos trabajando con la PicoCalc usando Linux directamente en consola. Por eso, la fuente que nos interesa no es una fuente de escritorio como las que se usan en LibreOffice, Firefox o VS Code, sino una **fuente de consola**.

Estas fuentes suelen estar ubicadas en:

```bash
/usr/share/consolefonts/
```

Y se pueden configurar usando herramientas como:

```bash
sudo apt install console-setup
sudo dpkg-reconfigure console-setup
```

También es posible probar fuentes manualmente con el comando:

```bash
setfont
```

---

## Requisitos previos

Antes de comenzar, se asume que ya tenés:

* [Una PicoCalc funcionando con una Luckfox Lyra B](https://github.com/VintaBytes/LuckFox-Lyra-B-Picocalc/blob/main/Linux_Install_LuckFox_Lyra_B/readme.md).
* Linux instalado y arrancando correctamente.
* Acceso a una terminal.
* Conexión a internet en el dispositivo, o acceso por ADB desde una computadora.
* Permisos de usuario con `sudo`.

Si todavía no configuraste la red, es posible que algunos comandos como `apt install` no funcionen hasta resolver primero la conexión.

---

## Instalar las herramientas necesarias

Para configurar la fuente de consola, primero instalamos el paquete `console-setup`.

Ejecutá:

```bash
sudo apt update
sudo apt install console-setup
```

Este paquete instala las herramientas necesarias para configurar el teclado, el mapa de caracteres y la fuente usada por la consola.

---

## Configurar la fuente con dpkg-reconfigure

Una vez instalado el paquete, podemos lanzar el asistente de configuración:

```bash
sudo dpkg-reconfigure console-setup
```

Este comando abre un asistente en modo texto. Las opciones exactas pueden variar un poco según la imagen de Linux instalada, pero en general permite elegir:

* Codificación de caracteres.
* Juego de caracteres.
* Familia de fuente.
* Tamaño de fuente.

Una configuración razonable para comenzar puede ser:

```text
Encoding: UTF-8
Character set: Guess optimal character set
Font: Terminus
Font size: 12x6
```

<p align="center">
  <img src="https://github.com/VintaBytes/LuckFox-Lyra-B-Picocalc/blob/main/Linux_Install_LuckFox_Lyra_B/docs/img/1.png" width="300">
  <img src="https://github.com/VintaBytes/LuckFox-Lyra-B-Picocalc/blob/main/Linux_Install_LuckFox_Lyra_B/docs/img/2.png" width="300">
  <img src="https://github.com/VintaBytes/LuckFox-Lyra-B-Picocalc/blob/main/Linux_Install_LuckFox_Lyra_B/docs/img/3.png" width="300">
</p>

En una pantalla pequeña como la de la PicoCalc, una fuente de 12 píxeles de alto por 6 píxeles de ancho puede permitir ver una buena cantidad de líneas y columnas.

Después de finalizar el asistente, el sistema debería guardar la configuración.

---

## Aplicar los cambios

En algunos casos, la fuente cambia inmediatamente después de terminar la configuración.

Si no cambia, se puede reiniciar la consola o directamente reiniciar el sistema:

```bash
sudo reboot
```

Luego de reiniciar, la consola debería arrancar usando la nueva fuente seleccionada.

---

## Probar fuentes manualmente

También se pueden probar fuentes sin cambiar todavía la configuración permanente.

Las fuentes disponibles suelen estar en:

```bash
/usr/share/consolefonts/
```

Para ver algunas fuentes instaladas, podés usar:

```bash
ls /usr/share/consolefonts/
```

Por ejemplo, para buscar fuentes Terminus:

```bash
ls /usr/share/consolefonts/ | grep Terminus
```

Una fuente puede probarse con:

```bash
sudo setfont /usr/share/consolefonts/NOMBRE_DE_LA_FUENTE.psf.gz
```

Por ejemplo:

```bash
sudo setfont /usr/share/consolefonts/Lat2-Terminus12x6.psf.gz
```

Si la fuente existe y es compatible, la consola debería cambiar inmediatamente.

Este método es útil para experimentar, porque permite comparar distintas fuentes antes de dejar una configuración definitiva.

---

## Comprobar el tamaño de la terminal

Después de cambiar la fuente, puede ser útil comprobar cuántas columnas y filas detecta la consola.

Ejecutá:

```bash
stty size
```

El resultado tendrá una forma similar a esta:

```text
26 53
```

El primer número indica la cantidad de filas y el segundo la cantidad de columnas.

En una pantalla pequeña, esto es muy importante. Una fuente más grande mostrará menos texto. Una fuente más pequeña permitirá ver más contenido, pero puede ser más difícil de leer.

---

## Revisar la configuración actual

La configuración de `console-setup` suele guardarse en:

```bash
/etc/default/console-setup
```

Podés verla con:

```bash
cat /etc/default/console-setup
```

Un ejemplo de configuración podría verse así:

```text
ACTIVE_CONSOLES="/dev/tty[1-6]"

CHARMAP="UTF-8"

CODESET="guess"
FONTFACE="Terminus"
FONTSIZE="12x6"
```

También podría aparecer una configuración más específica, dependiendo de la fuente elegida.

---

## Editar la configuración manualmente

Si querés modificar la configuración sin volver a ejecutar el asistente, podés editar el archivo:

```bash
sudo nano /etc/default/console-setup
```

Por ejemplo, para usar Terminus 12x6, podrías dejar algo similar a:

```text
ACTIVE_CONSOLES="/dev/tty[1-6]"
CHARMAP="UTF-8"
CODESET="guess"
FONTFACE="Terminus"
FONTSIZE="12x6"
```

Después de guardar los cambios, podés aplicar la configuración con:

```bash
sudo setupcon
```

O reiniciar el sistema:

```bash
sudo reboot
```

---

## Cargar una fuente específica con setfont

Si no querés depender de `console-setup`, también podés cargar una fuente concreta usando `setfont`.

Por ejemplo:

```bash
sudo setfont /usr/share/consolefonts/Lat2-Terminus12x6.psf.gz
```

Este cambio se aplica en el momento, pero normalmente no queda fijo después de reiniciar.

Es una buena opción para probar fuentes rápidamente, pero no siempre alcanza si queremos una configuración persistente.

---

## Hacer persistente una fuente personalizada

Si se quiere usar siempre una fuente concreta, incluso después de reiniciar, una opción es crear un servicio de `systemd`.

Esto puede ser útil si estamos usando una fuente modificada o una fuente que no queda bien aplicada solamente con `console-setup`.

Primero, copiamos la fuente a una ubicación del sistema. Por ejemplo:

```bash
sudo cp MiFuente.psf.gz /usr/share/consolefonts/
```

Luego creamos un servicio:

```bash
sudo nano /etc/systemd/system/picocalc-fuente.service
```

Dentro del archivo escribimos:

```ini
[Unit]
Description=Cargar fuente personalizada PicoCalc
After=local-fs.target

[Service]
Type=oneshot
ExecStart=/usr/bin/setfont /usr/share/consolefonts/MiFuente.psf.gz
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Guardamos el archivo y activamos el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable picocalc-fuente.service
sudo systemctl start picocalc-fuente.service
```

Para comprobar su estado:

```bash
systemctl status picocalc-fuente.service
```

Si todo salió bien, la fuente debería cargarse automáticamente en cada arranque.

---

## Comparar distintas fuentes

Para elegir una fuente conviene probar varias opciones.

Algunos criterios útiles son:

* Que los caracteres se vean nítidos.
* Que entren suficientes columnas.
* Que entren suficientes líneas.
* Que los símbolos importantes se vean correctamente.
* Que no resulte cansadora para leer durante varios minutos.
* Que los programas de consola se vean bien, especialmente menús, editores y aplicaciones con `ncurses`.

En la PicoCalc, una diferencia pequeña en el tamaño de la fuente puede cambiar mucho la experiencia de uso.

---

## Problemas posibles

### La fuente no cambia

Probá aplicar manualmente la configuración:

```bash
sudo setupcon
```

O reiniciar:

```bash
sudo reboot
```

También podés probar directamente con `setfont` para verificar si la fuente funciona:

```bash
sudo setfont /usr/share/consolefonts/Lat2-Terminus12x6.psf.gz
```

---

### La fuente elegida no existe

Si el comando falla, revisá el nombre real del archivo:

```bash
ls /usr/share/consolefonts/
```

También podés buscar por nombre:

```bash
ls /usr/share/consolefonts/ | grep Terminus
```

---

### Se ven caracteres raros

Revisá que la codificación esté configurada como UTF-8.

Podés volver a ejecutar:

```bash
sudo dpkg-reconfigure console-setup
```

Y elegir:

```text
UTF-8
```

---

### Entran menos columnas o menos líneas

Eso es normal si elegís una fuente más grande.

Podés comprobar el tamaño actual con:

```bash
stty size
```

Si necesitás más espacio, probá una fuente más pequeña o más angosta.

---

## Volver a configurar desde cero

Si algo no queda bien, podés volver a ejecutar el asistente:

```bash
sudo dpkg-reconfigure console-setup
```

Y luego reiniciar:

```bash
sudo reboot
```

Este método suele ser el más simple para volver a una configuración conocida.

---

## Notas finales

Cambiar la fuente de consola parece un ajuste menor, pero en una pantalla pequeña como la de la PicoCalc puede mejorar mucho la experiencia de uso.

Una fuente adecuada permite leer mejor, aprovechar más líneas de terminal y trabajar de manera más cómoda con editores, menús y programas en Python.

En este tipo de dispositivo, la consola no es solamente una herramienta de administración: es el entorno principal de trabajo.
