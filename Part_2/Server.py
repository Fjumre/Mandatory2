#!/usr/bin/env python3

from datetime import datetime
import socket

server_port = 8080
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("", server_port))
server_socket.listen(1)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(("8.8.8.8", 80))
    server_ip = s.getsockname()[0]
finally:
    s.close()

print(f"Serveren kører på: http://{server_ip}:{server_port}/")
print("Tryk Ctrl+C for at stoppe serveren.\n")

while True:
    connection_socket, addr = server_socket.accept()
    print(f"Forbindelse fra {addr} etableret.")

    msg = connection_socket.recv(4096)
    request_text = msg.decode(errors="ignore")

    if not request_text.strip():
        connection_socket.close()
        continue

    request_lines = request_text.splitlines()
    try:
        request_line = request_lines[0]
    except IndexError:
        request_line = "-"

    if request_line.startswith("GET /favicon.ico"):
        connection_socket.close()
        continue

    print("---------- FULL HTTP REQUEST ----------")
    print(request_text)
    print("--------------------------------------")

    try:
        parts = request_line.split()
        if len(parts) != 3 or parts[0] != "GET":
            raise ValueError("Bad Request")
        method, path, version = parts

        if path == "/":
            filename = "index.html"
        else:
            filename = path.lstrip("/")

        with open(filename, "r", encoding="utf-8") as f:
            response_body = f.read()

        http_response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{response_body}"
        status_code = 200

    except FileNotFoundError:
        try:
            with open("404.html", "r", encoding="utf-8") as f:
                response_body = f.read()
        except FileNotFoundError:
            response_body = "<h1>404 Not Found</h1>"

        http_response = f"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n{response_body}"
        status_code = 404

    except Exception:
        try:
            with open("400.html", "r", encoding="utf-8") as f:
                response_body = f.read()
        except FileNotFoundError:
            response_body = "<h1>400 Bad Request</h1>"

        http_response = f"HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n{response_body}"
        status_code = 400

    connection_socket.send(http_response.encode())

    now = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0000")
    response_size = len(response_body.encode())
    headers_text = "\n".join(request_lines[1:]) if len(request_lines) > 1 else "-"

    log_entry = f"{addr[0]} - - [{now}] \"{request_line}\" {status_code} {response_size}\n"
    print(f"Request: {request_line} --> Status: {status_code}")
    print(f"Headers:\n{headers_text}\n")

    with open("server.log", "a") as log_file:
        log_file.write(log_entry)

    connection_socket.close()
