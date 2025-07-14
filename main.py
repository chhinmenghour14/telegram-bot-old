import os
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load your bot token
TOKEN = os.getenv("TELEGRAM_TOKEN")

# 🟢 Dummy server for Render port binding and UptimeRobot monitoring
def run_dummy_server():
    class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write("✅ Bot is alive!".encode('utf-8'))
    
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()

    port = int(os.environ.get("PORT", 10000))  # Render sets this automatically
    server = HTTPServer(("", port), Handler)
    print(f"✅ Dummy HTTP server running on port {port}")
    server.serve_forever()

# 🔵 /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! Send me ABA PayWay-style messages like `$1.92`, and I’ll sum them up for you.")

# 🟠 Handle messages with dollar amounts
async def sum_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Match prices like $1.92, $20
    prices = re.findall(r"\$\d+(?:\.\d{1,2})?", text)

    if not prices:
        await update.message.reply_text("⚠️ មិនមានតម្លៃដែលមានសញ្ញា `$` ឃើញទេ។")
        return

    try:
        total = sum(float(p[1:]) for p in prices)  # Remove `$` and convert
        await update.message.reply_text(f"💰 លុយសរុប = ${total:.2f}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error calculating total: {e}")

# 🔧 Main bot startup
if __name__ == "__main__":
    # Start dummy HTTP server for Render
    threading.Thread(target=run_dummy_server, daemon=True).start()

    # Start Telegram bot
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, sum_prices))

    print("🤖 Bot is running...")
    app.run_polling()
