import asyncio
import websockets
import json
import random
import urllib.request # Biblioteca nativa para fazer requisições na internet

jogadores_conectados = {} 
jogadores_lista = []      
jogo_em_andamento = False
turno_atual_index = 0
silaba_atual = ""
tempo_restante = 15
bomba_task = None

# Variável para guardar as palavras já ditas na partida
palavras_usadas = set() 

silabas_disponiveis = ["CA", "MA", "PA", "BA", "LA", "DE", "RO", "TE", "VI", "NO", "SA", "TU", "DO", "FA", "GE"]

def consultar_api_dicionario(palavra):
    # A API do dicionário aberto retorna dados se a palavra existir ou vazio se não existir
    url = f"https://api.dicionario-aberto.net/word/{palavra.lower()}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resposta:
            dados = json.loads(resposta.read().decode('utf-8'))
            # Se a lista tiver mais de 0 itens a palavra existe
            return len(dados) > 0
    except Exception as e:
        print(f"Erro na API ou palavra não encontrada: {e}")
        return False

async def avisar_todos_jogadores():
    nomes = list(jogadores_conectados.values())
    mensagem = json.dumps({
        "tipo": "atualizacao_jogadores",
        "jogadores": nomes,
        "jogo_em_andamento": jogo_em_andamento
    })
    for ws in jogadores_conectados:
        try: await ws.send(mensagem)
        except: pass

async def loop_da_bomba():
    global jogo_em_andamento, tempo_restante, turno_atual_index, jogadores_lista
    
    while jogo_em_andamento:
        await asyncio.sleep(1)
        tempo_restante -= 1
        
        mensagem_tick = json.dumps({"tipo": "tick", "tempo": tempo_restante})
        for ws in jogadores_conectados:
            try: await ws.send(mensagem_tick)
            except: pass
        
        if tempo_restante <= 0:
            ws_eliminado = jogadores_lista[turno_atual_index]
            nome_eliminado = jogadores_conectados[ws_eliminado]
            print(f"KABOOM! {nome_eliminado} explodiu.")
            
            msg_explosao = json.dumps({"tipo": "explosao", "eliminado": nome_eliminado})
            for ws in jogadores_conectados:
                try: await ws.send(msg_explosao)
                except: pass
            
            jogadores_lista.pop(turno_atual_index)
            
            if len(jogadores_lista) == 1:
                vencedor_ws = jogadores_lista[0]
                vencedor_nome = jogadores_conectados[vencedor_ws]
                msg_fim = json.dumps({"tipo": "fim_de_jogo", "vencedor": vencedor_nome})
                
                for ws in jogadores_conectados:
                    try: await ws.send(msg_fim)
                    except: pass
                
                jogo_em_andamento = False
                jogadores_lista.clear()
                for w in jogadores_conectados:
                    jogadores_lista.append(w)
                    
                await avisar_todos_jogadores()
                break
                
            else:
                if turno_atual_index >= len(jogadores_lista):
                    turno_atual_index = 0
                await enviar_nova_rodada()

async def enviar_nova_rodada():
    global jogo_em_andamento, turno_atual_index, silaba_atual, tempo_restante
    
    if len(jogadores_lista) == 0:
        jogo_em_andamento = False
        return

    silaba_atual = random.choice(silabas_disponiveis)
    tempo_restante = 15 
    
    ws_da_vez = jogadores_lista[turno_atual_index]
    nome_da_vez = jogadores_conectados[ws_da_vez]

    mensagem = json.dumps({
        "tipo": "nova_rodada",
        "silaba": silaba_atual,
        "jogador_da_vez": nome_da_vez
    })

    for ws in jogadores_conectados:
        try: await ws.send(mensagem)
        except: pass

async def lidar_com_cliente(websocket):
    global jogo_em_andamento, turno_atual_index, bomba_task
    
    try:
        async for mensagem_texto in websocket:
            dados = json.loads(mensagem_texto)
            
            if dados.get("tipo") == "entrar":
                nome = dados.get("nome")
                jogadores_conectados[websocket] = nome
                
                if not jogo_em_andamento:
                    jogadores_lista.append(websocket)
                    
                await avisar_todos_jogadores()
                
            elif dados.get("tipo") == "iniciar_jogo":
                if not jogo_em_andamento and len(jogadores_lista) >= 2:
                    jogo_em_andamento = True
                    turno_atual_index = 0 
                    palavras_usadas.clear() # Limpa as palavras usadas da partida anterior
                    await enviar_nova_rodada()
                    bomba_task = asyncio.create_task(loop_da_bomba())
                elif len(jogadores_lista) < 2:
                    await websocket.send(json.dumps({"tipo": "erro", "mensagem": "É preciso pelo menos 2 jogadores!"}))

            elif dados.get("tipo") == "tentativa_palavra":
                if not jogo_em_andamento: return
                
                if len(jogadores_lista) > 0 and turno_atual_index < len(jogadores_lista):
                    ws_da_vez = jogadores_lista[turno_atual_index]
                    
                    if websocket == ws_da_vez:
                        palavra = dados.get("palavra", "").upper()

                        if silaba_atual not in palavra:
                            await websocket.send(json.dumps({"tipo": "erro_jogada", "mensagem": f"A palavra precisa conter a sílaba {silaba_atual}!"}))
                            continue 
                            
                        if palavra in palavras_usadas:
                            await websocket.send(json.dumps({"tipo": "erro_jogada", "mensagem": "Essa palavra já foi usada nesta partida!"}))
                            continue

                        palavra_existe = await asyncio.to_thread(consultar_api_dicionario, palavra)
                        
                        if palavra_existe:

                            palavras_usadas.add(palavra) # Guarda a palavra no set
                            print(f"Acertou! {jogadores_conectados[websocket]} digitou {palavra} (Palavra válida!)")
                            
                            turno_atual_index = (turno_atual_index + 1) % len(jogadores_lista)
                            await enviar_nova_rodada() 
                        else:
                            await websocket.send(json.dumps({"tipo": "erro_jogada", "mensagem": "Essa palavra não existe no dicionário português!"}))

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if websocket in jogadores_conectados:
            jogadores_conectados.pop(websocket)
            if websocket in jogadores_lista:
                jogadores_lista.remove(websocket)
            
            if jogo_em_andamento:
                if len(jogadores_lista) == 1:
                    jogo_em_andamento = False
                elif len(jogadores_lista) > 1 and turno_atual_index >= len(jogadores_lista):
                    turno_atual_index = 0
                    
            await avisar_todos_jogadores()

async def main():
    print("Servidor da Bomba iniciado! API de Dicionário ATIVADA.")
    async with websockets.serve(lidar_com_cliente, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())