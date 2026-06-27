import os
import chess
import chess.engine
import requests
from flask import Flask, request

TOKEN = "YOUR_BALE_BOT_TOKEN"
API = f"https://tapi.bale.ai/bot{TOKEN}"

STOCKFISH_PATH = "./stockfish"  # اگر نداری، fallback فعال میشه

app = Flask(__name__)

games = {}  # chat_id -> board


# ---------- ارسال پیام ----------
def send(chat_id, text):
    try:
        requests.post(f"{API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text
        })
    except:
        pass


# ---------- نمایش صفحه ----------
def board_view(board):
    return str(board)


# ---------- AI ----------
def ai_move(board):
    try:
        engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
        result = engine.play(board, chess.engine.Limit(time=0.5))
        engine.quit()
        return result.move
    except:
        # fallback اگر stockfish نبود
        return list(board.legal_moves)[0]


# ---------- شروع بازی ----------
def new_game(chat_id):
    board = chess.Board()
    games[chat_id] = board
    return board


# ---------- webhook ----------
@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    if not data or "message" not in data:
        return "ok"

    msg = data["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip().lower()

    # ---------- start ----------
    if text == "/start":
        send(chat_id,
             "♟️ شطرنج حرفه‌ای فعال شد!\n\n"
             "دستورات:\n"
             "/new شروع بازی\n"
             "حرکت: e2e4")

    # ---------- new game ----------
    elif text == "/new":
        board = new_game(chat_id)
        send(chat_id,
             "🎮 بازی جدید شروع شد!\n"
             "تو سفید هستی ♙\n\n" +
             board_view(board))

    # ---------- game logic ----------
    elif chat_id in games:
        board = games[chat_id]

        try:
            move = chess.Move.from_uci(text)

            # حرکت کاربر
            if move in board.legal_moves:
                board.push(move)

                # check end
                if board.is_game_over():
                    send(chat_id, "🏁 پایان بازی!\n" + board.result())
                    del games[chat_id]
                    return "ok"

                # AI move
                ai = ai_move(board)
                board.push(ai)

                msg_out = f"🤖 حرکت من: {ai}\n\n{board_view(board)}"
                send(chat_id, msg_out)

                # check again
                if board.is_game_over():
                    send(chat_id, "🏁 پایان بازی!\n" + board.result())
                    del games[chat_id]

            else:
                send(chat_id, "❌ حرکت غیرقانونی!\nمثال: e2e4")

        except:
            send(chat_id, "♟️ فرمت اشتباهه\nمثال درست: e2e4")

    return "ok"


# ---------- run ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
