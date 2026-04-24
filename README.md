# WORDBOMB - Bomba de Palavras

Jogo multiplayer de palavras em tempo real com tema arcade, feito com:

- Front-end em HTML/CSS/JavaScript (`index.html`)
- Servidor Python com WebSocket (`servidor.py`)
- Validação de palavras via API de dicionario

## Requisitos

- Python 3.10+ (recomendado)
- `pip` funcionando
- Internet (para validar palavras na API e carregar fontes/QR por CDN)

## Instalacao

No terminal, dentro da pasta do projeto:

```bash
pip install websockets
```

## Como executar

1. Abra a pasta do projeto no terminal.
2. Inicie o servidor:

```bash
python servidor.py
```

Ao iniciar, o projeto sobe:

- HTTP em `http://0.0.0.0:8000` (serve o `index.html`)
- WebSocket em `ws://0.0.0.0:8765`

3. No computador, abra:

`http://localhost:8000/index.html`

## Jogar pelo celular (QR Code)

Na tela inicial existe um bloco "Entrar pelo celular" com QR Code automatico.

- O QR aponta para `http://<ipv4-da-rede>:8000/index.html`
- Escaneie com o celular para abrir o jogo
- O celular deve estar na mesma rede Wi-Fi do computador

Se o IP nao for detectado automaticamente, use o campo manual para informar o IPv4.

## Como jogar

1. Digite seu nome e entre na arena.
2. Aguarde pelo menos 2 jogadores.
3. Clique em "Iniciar Jogo".
4. Na sua vez, envie uma palavra contendo a silaba exibida.
5. Nao pode repetir palavras na mesma partida.
6. Quem deixar o tempo zerar, explode.

## Estrutura do projeto

- `index.html`: interface do jogo, lobby, partida e QR Code
- `servidor.py`: logica de partida, conexoes WebSocket e servidor HTTP local

## Solucao de problemas

### QR Code nao aparece

- Recarregue com `Ctrl + F5`
- Verifique se abriu por `http://localhost:8000/index.html`
- Confira se o `python servidor.py` esta rodando

### Celular nao conecta

- Confirme que PC e celular estao na mesma rede
- Libere portas `8000` e `8765` no firewall do Windows
- Teste abrir no celular a URL mostrada abaixo do QR

### Erro ao conectar WebSocket

- Garanta que o servidor Python esta ativo
- Nao abra o arquivo com `file://`, sempre use `http://localhost:8000/index.html`

## Observacoes tecnicas

- O jogo usa `location.hostname` para montar o WebSocket, permitindo acesso por IP local.
- O servidor possui endpoint `GET /local-ip` para descobrir o IPv4 da maquina.
- Ha fallback de geracao de QR para manter exibicao mesmo se a biblioteca principal falhar.

