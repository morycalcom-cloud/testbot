import os
import chess
import chess.engine
import requests
from flask import Flask, request

TOKEN = "YOUR_BALE_BOT_TOKEN"
API = f"https://tapi.bale.ai/bot{TOKEN}"

STOCKFISH_PATH = "./stockfish"  # اگر نداری، ربات بدون AI هم کار می‌کنه

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

def render(board):
    return str(board)

def new_game(chat_id):
    board = chess.Board()
    games[chat_id] = board
    return board

def get_ai_move(board):
    """اگر stockfish نبود، حرکت رندوم می‌زند"""
    try:
        engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
        result = engine.play(board, chess.engine.Limit(time=0.3))
        engine.quit()
        return result.move
    except:
        return list(board.legal_moves)[0]  # fallback ساده


@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    if not data or "message" not in data:
        return "ok"

    msg = data["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()

    if text == "/start":
        send(chat_id,
             "♟️ شطرنج آنلاین فعال شد!\n"
             "/new برای شروع بازی")

    elif text == "/new":
        board = new_game(chat_id)
        send(chat_id,
             "🎮 بازی شروع شد!\nتو سفید هستی\n\n" + render(board))

    elif chat_id in games:
        board = games[chat_id]

        try:
            move = chess.Move.from_uci(text)

            if move in board.legal_moves:
                board.push(move)

                if board.is_game_over():
                    send(chat_id, "🏁 بازی تموم شد: " + board.result())
                    del games[chat_id]
                    return "ok"

                ai_move = get_ai_move(board)
                board.push(ai_move)

                send(chat_id,
                     f"🤖 حرکت من: {ai_move}\n\n{render(board)}")

                if board.is_game_over():
                    send(chat_id, "🏁 پایان بازی: " + board.result())
                    del games[chat_id]

            else:
                send(chat_id, "❌ حرکت غیرقانونی (مثلاً e2e4)")

        except:
            send(chat_id, "♟️ فرمت درست: e2e4")

    return "ok"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
