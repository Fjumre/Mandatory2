#!/usr/bin/env python3

# --------------------------------------------------
# IMPORTER NECESSÆRE MODULER
# --------------------------------------------------
from datetime import datetime  # Bruges til tidsstempler i logfiler
import socket                 # Bruges til TCP/IP-forbindelser (vores webserver)

# --------------------------------------------------
# OPSÆTNING AF SERVEREN
# --------------------------------------------------

server_port = 8080  # Port som serveren lytter på

# Opret en TCP/IP-socket (IPv4 + TCP)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Gør socket genanvendelig, så man kan genstarte hurtigt uden "Address already in use"
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind socket til alle netværksinterfaces
# "" betyder, at serveren accepterer forbindelser fra alle IP-adresser
server_socket.bind(("", server_port))

# Start med at lytte efter forbindelser (kun én klient i kø)
server_socket.listen(1)

# --------------------------------------------------
# FIND DEN LOKALE IP-ADRESSE
# --------------------------------------------------
# Dette gør det muligt for andre på samme netværk at tilgå serveren
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Midlertidig UDP-socket
try:
    s.connect(("8.8.8.8", 80))  # Google DNS bruges kun til at bestemme lokal IP
    server_ip = s.getsockname()[0]  # Lokal IP findes via getsockname()
finally:
    s.close()  # Luk midlertidig socket

# Print besked så vi kan se, hvor serveren kører
print(f"Serveren kører på: http://{server_ip}:{server_port}/")
print("Tryk Ctrl+C for at stoppe serveren.\n")

# --------------------------------------------------
# START SERVER-LØKKE
# --------------------------------------------------
# Serveren kører i en evig løkke og håndterer én klient ad gangen
while True:
    # Acceptér indkommende forbindelse
    connection_socket, addr = server_socket.accept()
    print(f"Forbindelse fra {addr} etableret.")

    # --------------------------------------------------
    # MODTAG HTTP-REQUEST FRA KLIENT
    # --------------------------------------------------
    # recv(4096) læser op til 4096 bytes (nok til headers og små sider)
    msg = connection_socket.recv(4096)
    request_text = msg.decode(errors="ignore")  # Decode bytes til tekst

    # --------------------------------------------------
    # IGNORÉR TOMME REQUESTS
    # --------------------------------------------------
    if not request_text.strip():
        connection_socket.close()
        continue

    # --------------------------------------------------
    # SPLIT REQUESTEN I LINJER
    # --------------------------------------------------
    request_lines = request_text.splitlines()
    try:
        request_line = request_lines[0]  # Fx: GET /index.html HTTP/1.1
    except IndexError:
        request_line = "-"

    # --------------------------------------------------
    # IGNORÉR BROWSER-FAVICON REQUESTS
    # --------------------------------------------------
    if request_line.startswith("GET /favicon.ico"):
        connection_socket.close()
        continue

    # Print hele requesten til konsollen (inkl. headers)
    print("---------- FULL HTTP REQUEST ----------")
    print(request_text)
    print("--------------------------------------")

    # --------------------------------------------------
    # HÅNDTER FILANMODNING
    # --------------------------------------------------
    try:
        parts = request_line.split()
        if len(parts) != 3 or parts[0] != "GET":
            raise ValueError("Bad Request")
        method, path, version = parts

        # Standardfil hvis root "/"
        if path == "/":
            filename = "index.html"
        else:
            filename = path.lstrip("/")

        # Åbn filen
        with open(filename, "r", encoding="utf-8") as f:
            response_body = f.read()

        http_response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{response_body}"
        status_code = 200

    # --------------------------------------------------
    # 404 hvis fil ikke findes
    # --------------------------------------------------
    except FileNotFoundError:
        try:
            with open("404.html", "r", encoding="utf-8") as f:
                response_body = f.read()
        except FileNotFoundError:
            response_body = "<h1>404 Not Found</h1>"

        http_response = f"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n{response_body}"
        status_code = 404

    # --------------------------------------------------
    # 400 hvis request er forkert formateret
    # --------------------------------------------------
    except Exception:
        try:
            with open("400.html", "r", encoding="utf-8") as f:
                response_body = f.read()
        except FileNotFoundError:
            response_body = "<h1>400 Bad Request</h1>"

        http_response = f"HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n{response_body}"
        status_code = 400

    # --------------------------------------------------
    # SEND SVAR TIL KLIENT
    # --------------------------------------------------
    connection_socket.send(http_response.encode())

    # --------------------------------------------------
    # LOG REQUEST I APACHE-LIGNENDE FORMAT
    # --------------------------------------------------
    now = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0000")
    response_size = len(response_body.encode())

    # Gem alle headers som én streng (for log)
    headers_text = "\n".join(request_lines[1:]) if len(request_lines) > 1 else "-"

    log_entry = f"{addr[0]} - - [{now}] \"{request_line}\" {status_code} {response_size}\n"
    print(f"Request: {request_line} --> Status: {status_code}")
    print(f"Headers:\n{headers_text}\n")

    # Skriv log til fil
    with open("server.log", "a") as log_file:
        log_file.write(log_entry)

    # --------------------------------------------------
    # LUK FORBINDELSEN TIL KLIENTEN
    # --------------------------------------------------
    connection_socket.close()
