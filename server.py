from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from uuid import uuid4
import asyncio
import openai
import os

app = FastAPI()

# Configure a API Key da OpenAI
openai.api_key = os.getenv("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")

# Dicionário para armazenar sessões de jogo
sessions = {}

class Session:
    def __init__(self, session_id):
        self.session_id = session_id
        self.players = []
        self.history = []
        self.lock = asyncio.Lock()

    async def send_to_all(self, message):
        """ Envia uma mensagem para todos os jogadores conectados. """
        async with self.lock:
            for player in self.players:
                await player.send_text(message)

async def send_to_chatgpt(message, model="gpt-4-turbo"):
    """ Envia uma mensagem para o ChatGPT e retorna a resposta. """
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": message}]
    )
    return response["choices"][0]["message"]["content"]

@app.post("/create_session")
def create_session():
    """ Cria uma nova sessão de jogo e retorna o código da sessão. """
    session_id = str(uuid4())[:8]  # Código curto da sessão
    sessions[session_id] = Session(session_id)
    return {"session_id": session_id}

@app.websocket("/join/{session_id}")
async def join_session(websocket: WebSocket, session_id: str):
    """ Permite que os jogadores se conectem a uma sessão. """
    await websocket.accept()

    if session_id not in sessions:
        await websocket.send_text("Erro: Sessão não encontrada.")
        await websocket.close()
        return

    session = sessions[session_id]
    session.players.append(websocket)

    try:
        while True:
            message = await websocket.receive_text()
            print(f"Jogador: {message}")

            # Enviar a mensagem para o ChatGPT (simulando a resposta do Mestre)
            resposta_mestre = await send_to_chatgpt(f"Você é um Mestre de D&D. O jogador disse: {message}")
            
            # Salvar histórico e enviar resposta para todos
            session.history.append(f"Jogador: {message}")
            session.history.append(f"Mestre: {resposta_mestre}")
            await session.send_to_all(f"Mestre: {resposta_mestre}")

    except WebSocketDisconnect:
        session.players.remove(websocket)
