# fsociety-message-crypted

A small, local desktop utility for encrypting and decrypting text messages. It provides a dark, full-black interface for preparing an encrypted message packet, sharing that packet through a channel you choose, and opening it again with the shared password.

> **Project status:** This is a prototype. It is not an online chat service, and it has not received an independent security audit.

## Contents

- [Overview](#overview)
- [Features](#features)
- [How message encryption works](#how-message-encryption-works)
- [Security model and limitations](#security-model-and-limitations)
- [Requirements](#requirements)
- [Installation and launch](#installation-and-launch)
- [Using the application](#using-the-application)
- [Keyboard shortcuts](#keyboard-shortcuts)
- [Saved packets and privacy](#saved-packets-and-privacy)
- [Troubleshooting](#troubleshooting)
- [Project structure](#project-structure)
- [License](#license)

## Overview

`fsociety-message-crypted` is a desktop message-encryption prototype built with Python and Tkinter. It encrypts text locally on your computer and produces a text packet that you can copy into another application. The recipient uses the same shared password and this application to decrypt the packet.

The program does **not** connect to a chat server, create accounts, or send messages over the internet. You choose how to deliver the packet, such as through an email or messaging service. Share the password separately from the encrypted packet.

## Features

- Encrypt text locally and create a portable `CC1` packet.
- Decrypt a packet with the shared password.
- Copy the packet or decrypted text to the clipboard.
- Save encrypted packets in a local list for later use.
- Import a packet from a text file.
- Reveal or mask a password field while entering a password.
- Use a black application background and standard text editing shortcuts.
- Run on Windows, macOS, and Linux where Python and Tkinter are available.

## How message encryption works

For every encryption operation, the application generates a fresh random 16-byte salt and 12-byte nonce. It derives a 256-bit key from the password with PBKDF2-HMAC-SHA256 using 600,000 iterations, then encrypts the message with AES-GCM through the Python `cryptography` package. AES-GCM also authenticates the encrypted data, so decryption fails if the password is wrong or the packet has been changed.

The resulting packet has this general form:

```text
CC1.<salt>.<nonce>.<ciphertext-and-authentication-tag>
```

The fields are URL-safe Base64 text without padding. The packet contains the salt, nonce, and encrypted message; it does not contain the password. The `CC1` marker identifies the packet format used by this prototype.

## Security model and limitations

This application is intended as a small demonstration of local, password-based message encryption. Keep these limits in mind:

- **Both people need the same password.** This is symmetric encryption; the application does not provide public/private keys or an automatic key exchange.
- **Verify who gave you the password.** The application cannot authenticate the sender. If someone can replace both the packet and the password, this program cannot tell you who created the message.
- **Use a strong, unique password.** The interface accepts passwords with at least eight characters, but that minimum is not a recommendation. Prefer a long, randomly generated password and share it through a separate trusted channel.
- **The app does not send messages.** Your chosen email or chat provider may retain the packet, its size, delivery metadata, or other information. Sending the password alongside the packet weakens the separation between them.
- **Plain text is visible while you use the app.** The message is handled in the application's memory and shown on screen during encryption or after decryption. Copying text also places it on your operating system's clipboard.
- **Saved packets are encrypted packets, not password vault entries.** The local list stores packet text and labels. It does not store the password. Protect access to your operating-system account and backups.
- **No independent audit has been performed.** Do not treat this prototype as a vetted product for highly sensitive or safety-critical communications.
- **Lost passwords cannot be recovered.** There is no password reset or recovery mechanism.

Encryption is only one part of secure communication. The recipient, password-sharing channel, devices, operating systems, backups, and any messaging service you use are outside this application's control.

## Requirements

- Python 3.10 or newer.
- Tkinter, which is included with most standard Python installations. Some Linux distributions package it separately (often as `python3-tk`).
- The Python package `cryptography` (version 42.0.0 or newer).

## Installation and launch

### Windows

1. Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/). During setup, enable the option to add Python to `PATH`.
2. Download or clone this repository and open the project folder in File Explorer.
3. Double-click `run_windows.bat`. The launcher installs the listed dependency and starts the application.

You can also open Command Prompt or PowerShell in the project folder and run:

```powershell
py -m pip install -r requirements.txt
py fsociety_message_crypted.py
```

### macOS

1. Install Python 3.10 or newer.
2. Open Terminal and change to the project folder.
3. Install the dependency and launch the app:

```bash
python3 -m pip install -r requirements.txt
python3 fsociety_message_crypted.py
```

### Linux

1. Install Python 3.10 or newer and Tkinter using your distribution's package manager if needed.
2. Open a terminal in the project folder and run:

```bash
python3 -m pip install -r requirements.txt
python3 fsociety_message_crypted.py
```

For example, on Debian or Ubuntu, Tkinter may be installed with:

```bash
sudo apt install python3-tk
```

If your system marks its Python installation as externally managed, create and activate a virtual environment in the project folder before installing dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python fsociety_message_crypted.py
```

On Windows, activate it with `.venv\Scripts\activate` instead of the `source` command.

## Using the application

The interface labels are currently in Turkish. The main workflow is:

1. Open **Şifrele** (Encrypt) and enter the message.
2. Enter a strong shared password. The interface requires at least eight characters; choose a much longer password for real use.
3. Select **Mesajı şifrele** (Encrypt message). The resulting `CC1` packet appears in the output area.
4. Copy and send the packet through a service of your choice.
5. Communicate the password separately through a trusted channel.
6. The recipient opens **Şifre çöz** (Decrypt), pastes the packet, enters the password, and selects **Şifreyi çöz** (Decrypt).

The **Kayıtlı paketler** (Saved packets) tab can store, import, load, or delete encrypted packets on the current computer. The **Güvenlik** (Security) tab contains a short in-app explanation of the workflow and its limitations.

## Keyboard shortcuts

- **Ctrl+A** selects all text in the active text box or password/input field. It also selects all entries in the saved-packets list.
- Copy, cut, and paste use the standard keyboard shortcuts supported by your desktop environment (usually **Ctrl+C**, **Ctrl+X**, and **Ctrl+V** on Windows/Linux, or **Command+C**, **Command+X**, and **Command+V** on macOS).

## Saved packets and privacy

Saved packet data is stored in the current user's home directory:

```text
.fsociety-message-crypted/saved_packets.json
```

On macOS and Linux, the leading dot makes this folder hidden in many file browsers. On Windows, it is a folder inside the user's profile directory. The file contains saved encrypted packet strings and their labels; it does not contain the passwords. Decrypted messages and passwords are not added to the saved-packets list.

The storage folder is created the first time the application starts. Back up or remove it using your operating system's file manager if needed. Deleting this file removes the locally saved packet list but does not affect copies of packets shared elsewhere.

For people upgrading from the included `crypted-chat` prototype, the application can also read its previous packet list from `.crypted_chat_desktop/saved_packets.json` when the new file does not exist. Saving or changing packets writes them to the new `fsociety-message-crypted` folder.

## Troubleshooting

### `No module named 'cryptography'`

Install the project dependencies from the project folder:

```bash
python -m pip install -r requirements.txt
```

Use `python3` instead of `python` on systems where Python 3 is installed under that command.

### `No module named '_tkinter'` or the window does not open

Install the Tkinter package supplied by your operating system, then try launching the program again. On some Linux distributions this is packaged separately as `python3-tk`.

### The packet cannot be decrypted

Check that the complete packet was copied, including the `CC1.` prefix, and that the recipient entered the exact same password. A wrong password or any change to the packet causes authenticated decryption to fail.

### Python or `pip` is not recognized

Reinstall Python with its command-line option enabled, or use the Python launcher available on your system (`py` on many Windows installations and `python3` on many macOS/Linux installations).

## Project structure

```text
fsociety-message-crypted/
├── fsociety_message_crypted.py   # Tkinter desktop application
├── requirements.txt              # Python dependency list
├── run_windows.bat               # Windows setup and launch helper
└── README.md                     # Project documentation
```

## License

This repository does not currently include a license file. Add a `LICENSE` file before inviting others to reuse, modify, or distribute the project.
