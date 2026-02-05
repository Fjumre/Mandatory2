#!/usr/bin/env python3

# Importér alt fra socket-modulet
# Socket-modulet bruges til at lave netværksforbindelser (fx en webserver)
from socket import *
from datetime import datetime

# --------------------------------------------------
# Opsætning af serveren
# --------------------------------------------------

# Vælg en port til serveren
# 8080 er en almindelig testport til HTTP-servere
server_port = 8080  

# Opret en TCP-socket
# AF_INET = IPv4, SOCK_STREAM = TCP (ikke UDP)
server_socket = socket(AF_INET, SOCK_STREAM)  

# Bind socket til alle netværksinterfaces på den valgte port
# "" betyder alle IP-adresser på maskinen
server_socket.bind(("", server_port))  

# Start med at lytte efter forbindelser
# 1 betyder, at kun én klient kan stå i kø ad gangen
server_socket.listen(1)  

print(f"The server is ready to receive on port {server_port}.")

# --------------------------------------------------
# Start server-løkke
# --------------------------------------------------

# Evig løkke, så serveren kører hele tiden
while True:
    # Acceptér en forbindelse fra en klient
    # connection_socket bruges til at kommunikere med klienten
    # addr indeholder klientens IP-adresse og portnummer
    connection_socket, addr = server_socket.accept()
    print(f"Connection from {addr} established.")

    # Modtag data fra klienten (HTTP-request)
    # recv(2048) læser op til 2048 bytes fra klienten
    msg = connection_socket.recv(2048)

    # Decode bytes til tekst (HTTP-requesten er tekst)
    request_text = msg.decode()
    print("Received request:")

    # Vis kun første linje af HTTP-requesten (fx "GET / HTTP/1.1")
    # Dette er vigtigt, fordi GET-requesten fortæller os hvilken fil klienten vil have
    try:
        print(request_text.splitlines()[0])
    except IndexError:
        print("-")

    # --------------------------------------------------
    # Håndtering af den anmodede fil
    # --------------------------------------------------
    try:
        # Tag første linje af HTTP-requesten
        # Eksempel: "GET /about.html HTTP/1.1"
        request_line = request_text.splitlines()[0]

        # Split linjen i ord: metode, sti, HTTP-version
        # request_line.split()[0] = "GET"
        # request_line.split()[1] = "/about.html" (stien til filen)
        parts = request_line.split()

        # Tjek om requesten er korrekt formateret
        if len(parts) != 3 or parts[0] != "GET":
            raise ValueError("Bad Request")

        method, path, version = parts

        # Hvis brugeren ikke beder om en specifik fil (fx bare "/")
        # skal vi sende standardfilen "index.html"
        if path == "/":
            filename = "index.html"
        else:
            # Hvis brugeren beder om "/about.html" eller "/folder/page.html"
            # Fjern den foranstillede skråstreg, så open() kan finde filen
            # "/about.html" → "about.html"
            # "/folder/page.html" → "folder/page.html"
            # Hvis vi ikke fjerner "/" ville Python prøve at finde filen på root (/)
            filename = path.lstrip("/")

        # Åbn filen i læse-mode
        # Hvis filen ikke findes, ryger vi til except FileNotFoundError
        with open(filename, "r") as f:
            # Læs hele filen ind i response_body
            response_body = f.read()

        # Lav HTTP-response
        # HTTP/1.1 200 OK = standard header for succesfuld forespørgsel
        # "\n\n" = adskiller header fra body
        http_response = f"HTTP/1.1 200 OK\nContent-Type: text/html\n\n{response_body}"
        status_code = 200

    # Hvis filen ikke findes på serveren
    except FileNotFoundError:
        # Send en 404-fejl tilbage til klienten med 404.html
        with open("404.html", "r") as f:
            response_body = f.read()
        http_response = f"HTTP/1.1 404 Not Found\nContent-Type: text/html\n\n{response_body}"
        status_code = 404

    # Hvis requesten er forkert formateret
    except Exception:
        # Send en 400-fejl tilbage med 400.html
        with open("400.html", "r") as f:
            response_body = f.read()
        http_response = f"HTTP/1.1 400 Bad Request\nContent-Type: text/html\n\n{response_body}"
        status_code = 400

    # --------------------------------------------------
    # Send svar til klienten
    # --------------------------------------------------

    # Encode response til bytes og send den gennem socket
    connection_socket.send(http_response.encode())

    # --------------------------------------------------
    # Log request til fil i Apache-format
    # --------------------------------------------------
    now = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0000")
    try:
        request_line_log = request_text.splitlines()[0]
    except IndexError:
        request_line_log = "-"
    log_entry = f"{addr[0]} - - [{now}] \"{request_line_log}\" {status_code}\n"
    with open("server.log", "a") as log_file:
        log_file.write(log_entry)

    # Luk forbindelsen til klienten
    connection_socket.close()

