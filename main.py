import os
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")

# Dummy server for Render port binding requirement
def run_dummy_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running!")

    port = int(os.environ.get("PORT", 10000))  # Render sets PORT env variable
    server = HTTPServer(("", port), Handler)
    server.serve_forever()

# Telegram command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me ABA PayWay messages and I'll sum up the amounts!")

# Handle ABA-style dollar amounts
async def sum_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Match prices like $1.92, $20, etc.
    prices = re.findall(r"\$\d+(?:\.\d{1,2})?", text)

    if not prices:
        await update.message.reply_text("ត្រូវប្រាកដថាមានអក្សរ រឺលេខបែបនេះ '$1.92'.")
        return

    try:
        total = sum(float(p[1:]) for p in prices)  # remove '$' and convert
        await update.message.reply_text(f"លុយសរុប = ${total:.2f}")
    except Exception as e:
        await update.message.reply_text(f"Error calculating total: {e}")

if __name__ == "__main__":
    # Start dummy HTTP server in a background thread
    threading.Thread(target=run_dummy_server, daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, sum_prices))

    print("Bot is running...")
    app.run_polling()
