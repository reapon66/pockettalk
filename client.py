"""Cliente TCP para conversar com vários participantes em um chat."""

import socket
import threading


SERVER_HOST = "192.168.5.133"  # Coloque aqui o IP mostrado ao iniciar o servidor.
SERVER_PORT = 12000
ENCODING = "utf-8"


def send_message(client_socket, message):
    """Envia uma mensagem completa usando uma quebra de linha como delimitador."""
    client_socket.sendall(f"{message}\n".encode(ENCODING))


def receive_messages(client_socket, finished):
    """Exibe mensagens do servidor sem bloquear o envio pelo usuário."""
    reader = client_socket.makefile("r", encoding=ENCODING, newline="\n")
    try:
        for line in reader:
            print(f"\n{line.rstrip()}")
    except (ConnectionError, OSError):
        if not finished.is_set():
            print("\nA conexão com o servidor foi interrompida.")
    finally:
        reader.close()
        finished.set()


def run_client():
    name = input("Digite seu nome: ").strip()
    if not name:
        print("O nome não pode ficar vazio.")
        return

    finished = threading.Event()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            client_socket.connect((SERVER_HOST, SERVER_PORT))
        except OSError as error:
            print(f"Não foi possível conectar ao servidor: {error}")
            return

        send_message(client_socket, name)
        receiver = threading.Thread(
            target=receive_messages,
            args=(client_socket, finished),
            daemon=True,
        )
        receiver.start()

        try:
            while not finished.is_set():
                message = input(f"{name}: ").strip()
                if not message:
                    continue

                send_message(client_socket, message)
                if message.lower() == "sair":
                    receiver.join(timeout=2)
                    break
        except (EOFError, KeyboardInterrupt):
            try:
                send_message(client_socket, "sair")
            except OSError:
                pass
        except (ConnectionError, OSError):
            print("\nNão foi possível enviar a mensagem.")
        finally:
            finished.set()


if __name__ == "__main__":
    run_client()
