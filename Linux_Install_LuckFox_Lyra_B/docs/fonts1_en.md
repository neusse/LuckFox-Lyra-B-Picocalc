# Changing the console font on PicoCalc with Luckfox Lyra B and Linux

<span><img src="https://img.shields.io/badge/PicoCalc-LuckFox%20%2B%20Linux-5E81AC?style=for-the-badge&logo=linux&logoColor=white"/></span> <span><img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black"/></span> <span><img src="https://img.shields.io/badge/Ubuntu-24.04.2-E95420?style=for-the-badge&logo=ubuntu&logoColor=white"/></span>

This document explains how to change the font used by the Linux console on a **PicoCalc** modified with a **[Luckfox Lyra B](https://github.com/VintaBytes/LuckFox-Lyra-B-Picocalc/blob/main/Linux_Install_LuckFox_Lyra_B/readme_en.md)**.

This procedure is intended for a Linux installation running in console mode, without a graphical environment, where the PicoCalc is mainly used as a small portable computer for the terminal, text editing, programming, and running scripts.

The console font is important on this device because the screen is small. A font that is too large, too wide, or not very readable can reduce the number of visible columns and lines, making real terminal use more difficult.

---

## Goal

The goal of this procedure is to change the text font used by the Linux console in order to improve readability and make better use of the available screen space.

In particular, the idea is to choose a more comfortable font for the PicoCalc, for example a variant of **Terminus**, which usually works well on small screens because it is clear, compact, and readable.

---

## Context

In a normal desktop Linux installation, the font is usually configured from the graphical environment.

But in this case we are working with the PicoCalc using Linux directly in the console. For that reason, the font we are interested in is not a desktop font like the ones used in LibreOffice, Firefox, or VS Code, but a **console font**.

These fonts are usually located in:

```bash
/usr/share/consolefonts/
```

And they can be configured using tools such as:

```bash
sudo apt install console-setup
sudo dpkg-reconfigure console-setup
```

It is also possible to test fonts manually with the command:

```bash
setfont
```

---

## Prerequisites

Before starting, this guide assumes that you already have:

* [A PicoCalc working with a Luckfox Lyra B](https://github.com/VintaBytes/LuckFox-Lyra-B-Picocalc/blob/main/Linux_Install_LuckFox_Lyra_B/readme_en.md).
* Linux installed and booting correctly.
* Access to a terminal.
* An internet connection on the device, or access through ADB from a computer.
* A user with `sudo` permissions.

If you have not configured networking yet, some commands such as `apt install` may not work until the connection is solved first.

---

## Installing the necessary tools

To configure the console font, first install the `console-setup` package.

Run:

```bash
sudo apt update
sudo apt install console-setup
```

This package installs the tools needed to configure the keyboard, the character map, and the font used by the console.

---

## Configuring the font with dpkg-reconfigure

Once the package is installed, you can launch the configuration assistant:

```bash
sudo dpkg-reconfigure console-setup
```

This command opens a text-mode assistant. The exact options may vary slightly depending on the installed Linux image, but in general it allows you to choose:

* Character encoding.
* Character set.
* Font family.
* Font size.

A reasonable starting configuration could be:

```text
Encoding: UTF-8
Character set: Guess optimal character set
Font: Terminus
Font size: 12x6
```

On a small screen like the PicoCalc display, a font that is 12 pixels high by 6 pixels wide can allow a good number of lines and columns to be visible.

After finishing the assistant, the system should save the configuration.

---

## Applying the changes

In some cases, the font changes immediately after finishing the configuration.

If it does not change, you can restart the console or directly reboot the system:

```bash
sudo reboot
```

After rebooting, the console should start using the newly selected font.

---

## Testing fonts manually

You can also test fonts without changing the permanent configuration yet.

The available fonts are usually located in:

```bash
/usr/share/consolefonts/
```

To see some of the installed fonts, you can use:

```bash
ls /usr/share/consolefonts/
```

For example, to search for Terminus fonts:

```bash
ls /usr/share/consolefonts/ | grep Terminus
```

A font can be tested with:

```bash
sudo setfont /usr/share/consolefonts/FONT_NAME.psf.gz
```

For example:

```bash
sudo setfont /usr/share/consolefonts/Lat2-Terminus12x6.psf.gz
```

If the font exists and is compatible, the console should change immediately.

This method is useful for experimenting, because it allows you to compare different fonts before leaving one as the final configuration.

---

## Checking the terminal size

After changing the font, it can be useful to check how many columns and rows the console detects.

Run:

```bash
stty size
```

The result will look similar to this:

```text
26 53
```

The first number indicates the number of rows, and the second one indicates the number of columns.

On a small screen, this is very important. A larger font will show less text. A smaller font will allow more content to be displayed, but it may be harder to read.

---

## Checking the current configuration

The `console-setup` configuration is usually saved in:

```bash
/etc/default/console-setup
```

You can view it with:

```bash
cat /etc/default/console-setup
```

An example configuration could look like this:

```text
ACTIVE_CONSOLES="/dev/tty[1-6]"

CHARMAP="UTF-8"

CODESET="guess"
FONTFACE="Terminus"
FONTSIZE="12x6"
```

A more specific configuration may also appear, depending on the selected font.

---

## Editing the configuration manually

If you want to modify the configuration without running the assistant again, you can edit the file:

```bash
sudo nano /etc/default/console-setup
```

For example, to use Terminus 12x6, you could leave something similar to:

```text
ACTIVE_CONSOLES="/dev/tty[1-6]"
CHARMAP="UTF-8"
CODESET="guess"
FONTFACE="Terminus"
FONTSIZE="12x6"
```

After saving the changes, you can apply the configuration with:

```bash
sudo setupcon
```

Or reboot the system:

```bash
sudo reboot
```

---

## Loading a specific font with setfont

If you do not want to depend on `console-setup`, you can also load a specific font using `setfont`.

For example:

```bash
sudo setfont /usr/share/consolefonts/Lat2-Terminus12x6.psf.gz
```

This change is applied immediately, but it usually does not remain fixed after rebooting.

It is a good option for quickly testing fonts, but it is not always enough if you want a persistent configuration.

---

## Making a custom font persistent

If you want to always use a specific font, even after rebooting, one option is to create a `systemd` service.

This can be useful if you are using a modified font or a font that is not applied correctly using only `console-setup`.

First, copy the font to a system location. For example:

```bash
sudo cp MyFont.psf.gz /usr/share/consolefonts/
```

Then create a service:

```bash
sudo nano /etc/systemd/system/picocalc-font.service
```

Inside the file, write:

```ini
[Unit]
Description=Load custom PicoCalc font
After=local-fs.target

[Service]
Type=oneshot
ExecStart=/usr/bin/setfont /usr/share/consolefonts/MyFont.psf.gz
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Save the file and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable picocalc-font.service
sudo systemctl start picocalc-font.service
```

To check its status:

```bash
systemctl status picocalc-font.service
```

If everything went well, the font should load automatically on every boot.

---

## Comparing different fonts

To choose a font, it is a good idea to test several options.

Some useful criteria are:

* Characters should look sharp.
* Enough columns should fit on the screen.
* Enough lines should fit on the screen.
* Important symbols should display correctly.
* The font should not be tiring to read for several minutes.
* Console programs should look good, especially menus, editors, and applications using `ncurses`.

On the PicoCalc, a small difference in font size can greatly change the user experience.

---

## Possible problems

### The font does not change

Try applying the configuration manually:

```bash
sudo setupcon
```

Or reboot:

```bash
sudo reboot
```

You can also test directly with `setfont` to verify whether the font works:

```bash
sudo setfont /usr/share/consolefonts/Lat2-Terminus12x6.psf.gz
```

---

### The selected font does not exist

If the command fails, check the real filename:

```bash
ls /usr/share/consolefonts/
```

You can also search by name:

```bash
ls /usr/share/consolefonts/ | grep Terminus
```

---

### Strange characters are displayed

Check that the encoding is configured as UTF-8.

You can run again:

```bash
sudo dpkg-reconfigure console-setup
```

And choose:

```text
UTF-8
```

---

### Fewer columns or fewer lines fit on the screen

This is normal if you choose a larger font.

You can check the current size with:

```bash
stty size
```

If you need more space, try a smaller or narrower font.

---

## Configuring everything again from scratch

If something does not look right, you can run the assistant again:

```bash
sudo dpkg-reconfigure console-setup
```

And then reboot:

```bash
sudo reboot
```

This method is usually the simplest way to return to a known configuration.

---

## Final notes

Changing the console font may seem like a minor adjustment, but on a small screen like the PicoCalc display it can greatly improve the user experience.

A suitable font makes it easier to read, allows more terminal lines to be used, and makes working with editors, menus, and Python programs more comfortable.

On this type of device, the console is not just an administration tool: it is the main working environment.
