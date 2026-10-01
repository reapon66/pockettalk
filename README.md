# PocketTalk

Chat TCP em Python que aceita vários participantes simultaneamente.

## Como executar

1. No computador servidor, execute `python server.py`. Ao iniciar, ele mostrará
   o IP e a porta que devem ser usados pelos clientes.
2. Em `client.py`, ajuste `SERVER_HOST` para o IP mostrado pelo servidor.
3. Em cada computador participante, execute `python client.py`.

Cada mensagem é enviada aos demais participantes conectados. Digite `sair`
para deixar o chat.
