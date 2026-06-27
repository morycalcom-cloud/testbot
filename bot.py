import os
import chess
import chess.engine
import requests
from flask import Flask, request

TOKEN = "YOUR_BALE_BOT_TOKEN"
API = f"https://tapi.bale.ai/bot{TOKEN}"

app = Flask(__name__)

games = {}

def send(chat_id, text):
    try:
        requests.post(f"{API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text
        })
    except:
        pass


def new_game(chat_id):
    board = chess.Board()
    games[chat_id] = board
    return board


def ai(board):
    try:
        engine = chess.engine.SimpleEngine.popen_uci("./stockfish")
        move = engine.play(board, chess.engine.Limit(time=0.3)).move
        engine.quit()
        return move
    except:
        return list(board.legal_moves)[0]


@app.route("/", methods=["GET"])
def home():
    return "BOT RUNNING"


# 🔥 اینجا "auto webhook handler" داریم
@app.route("/update", methods=["POST"])
def update():
    data = request.json

    if "message" not in data:
        return "ok"

    msg = data["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip().lower()

    if text == "/start":
        send(chat_id, "♟️ ربات فعال شد /new")

    elif text == "/new":
        board = new_game(chat_id)
        send(chat_id, str(board))

    elif chat_id in games:
        board = games[chat_id]

        try:
            move = chess.Move.from_uci(text)

            if move in board.legal_moves:
                board.push(move)

                if board.is_game_over():
                    send(chat_id, "🏁 پایان: " + board.result())
                    del games[chat_id]
                    return "ok"

                ai_move = ai(board)
                board.push(ai_move)

                send(chat_id, f"🤖 {ai_move}\n\n{board}")

        except:
            send(chat_id, "حرکت اشتباه")

    return "ok"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
