"""Servidor TCP para um chat com vários clientes simultâneos."""

import socket
import threading


HOST = "0.0.0.0"
PORT = 12000
ENCODING = "utf-8"

# Aqui guardamos quem está no chat. O lock evita conflitos quando duas pessoas
# entram, saem ou enviam mensagens ao mesmo tempo.
clients = {}
clients_lock = threading.Lock()


def get_local_ip():
    """Descobre o IP desta máquina que os outros clientes podem usar."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as test_socket:
            test_socket.connect(("8.8.8.8", 80))
            return test_socket.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def send_message(connection, message, send_lock=None):
    """Envia uma mensagem completa usando uma quebra de linha como delimitador."""
    data = f"{message}\n".encode(ENCODING)
    if send_lock is None:
        connection.sendall(data)
        return

    with send_lock:
        connection.sendall(data)


def broadcast(message, sender=None):
    """Envia uma mensagem para todos, exceto para o remetente opcional."""
    with clients_lock:
        connections = list(clients.items())

    disconnected = []
    for connection, (_, send_lock) in connections:
        if connection is sender:
            continue
        try:
            send_message(connection, message, send_lock)
        except OSError:
            disconnected.append(connection)

    if disconnected:
        with clients_lock:
            for connection in disconnected:
                clients.pop(connection, None)
        for connection in disconnected:
            connection.close()


def handle_client(connection, address):
    """Recebe e distribui as mensagens de um único cliente."""
    name = None
    send_lock = threading.Lock()
    reader = connection.makefile("r", encoding=ENCODING, newline="\n")

    try:
        name = reader.readline().strip()
        if not name:
            send_message(connection, "Nome inválido. Conexão encerrada.")
            return

        # Primeiro damos as boas-vindas; depois avisamos o restante da turma.
        # Assim, a primeira mensagem recebida por quem entrou é sempre a saudação.
        with send_lock:
            with clients_lock:
                clients[connection] = (name, send_lock)
                total = len(clients)
            send_message(
                connection,
                f"Olá, {name}! Há {total} participante(s) no chat. "
                "Digite 'sair' para encerrar.",
            )
        broadcast(f"*** {name} entrou no chat. ***", sender=connection)
        print(f"{name} conectado: {address}")

        for line in reader:
            message = line.strip()
            if not message:
                continue

            if message.lower() == "sair":
                send_message(
                    connection,
                    "Até logo! Conversa encerrada.",
                    send_lock,
                )
                break

            broadcast(f"{name}: {message}", sender=connection)
    except (ConnectionError, OSError):
        pass
    finally:
        reader.close()
        with clients_lock:
            was_connected = clients.pop(connection, None) is not None
        connection.close()

        if name and was_connected:
            broadcast(f"*** {name} saiu do chat. ***")
        print(f"Conexão encerrada, cliente: {address}")


def run_server():
    """Aceita conexões continuamente e inicia um atendimento para cada uma."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        local_ip = get_local_ip()
        print("Servidor iniciado com sucesso!")
        print(f"IP: {local_ip}")
        print(f"Porta: {PORT}")
        print(f"Endereço para os clientes: {local_ip}:{PORT}")

        while True:
            connection, address = server_socket.accept()
            thread = threading.Thread(
                target=handle_client,
                args=(connection, address),
                daemon=True,
            )
            thread.start()


if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
