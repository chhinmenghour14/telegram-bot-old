import os
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")

user_batches = {}


def run_dummy_server():
    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write("🤖 បូតរស់រានមានជីវិត!".encode('utf-8'))

        def do_HEAD(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()

    # Get port from environment variable, default to 10000
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("", port), HealthCheckHandler)
    print(f"✅ ម៉ាស៊ីនបម្រើ HTTP ដំណើរការនៅ port {port}")
    server.serve_forever()

# 🔵 /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 សួស្តី! នេះជារបៀបដែលខ្ញុំដំណើរការ:\n\n"
        "• សារធម្មតា: ខ្ញុំនឹងបូកទឹកប្រាក់ដុល្លារដូចជា `$1.92 + $5` ឬ `2.50 ដុល្លារ`\n"
        "• សារបញ្ជូនបន្ត: ខ្ញុំនឹងចាប់ផ្តើមបូកបាច់ថ្មីដោយស្វ័យប្រវត្តិរាល់ពេលអ្នកបញ្ជូនបន្តសារ ហើយនឹងផ្តល់ផលបូកសរុបបន្ទាប់ពីផ្អាកបន្តិច។\n"
        "• ប្រើ /show ដើម្បីមើលផលបូកបាច់បច្ចុប្បន្នរបស់អ្នក\n"
        "• ប្រើ /sum ដើម្បីបូក"
    )

# 🔵 /show command handler
async def sum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_batches:
        batch = user_batches[user_id]
        elapsed = time.time() - batch["last_forward_time"]
        elapsed_min = int(elapsed // 60)
        elapsed_sec = int(elapsed % 60)

        await update.message.reply_text(
            f"📦 ផលបូកបាច់បច្ចុប្បន្ន: ${batch['total']:.2f}\n"
            f"⏱ បញ្ជូនចុងក្រោយ: {elapsed_min} នាទី {elapsed_sec} វិនាទីមុន\n"
            f"📄 សារដែលបានបញ្ជូន: {batch['count']} ក្នុងបាច់នេះ"
        )
    else:
        await update.message.reply_text("ℹ️ អ្នកមិនទាន់មានបាច់សកម្មទេ។ សូមបញ្ជូនសារដើម្បីចាប់ផ្តើម។")

async def show_batch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_batches:
        batch = user_batches[user_id]
        elapsed = time.time() - batch["last_forward_time"]
        elapsed_min = int(elapsed // 60)
        elapsed_sec = int(elapsed % 60)

        await update.message.reply_text(
            f"📦 ផលបូកបាច់បច្ចុប្បន្ន: ${batch['total']:.2f}\n"
            f"⏱ បញ្ជូនចុងក្រោយ: {elapsed_min} នាទី {elapsed_sec} វិនាទីមុន\n"
            f"📄 សារដែលបានបញ្ជូន: {batch['count']} ក្នុងបាច់នេះ"
        )
        del user_batches[user_id]
        await update.message.reply_text("🧹 បាច់ត្រូវបានជម្រះបន្ទាប់ពីបង្ហាញ។")
        
    else:
        await update.message.reply_text("ℹ️ អ្នកមិនទាន់មានបាច់សកម្មទេ។ សូមបញ្ជូនសារដើម្បីចាប់ផ្តើម។")
# 🔵 /clear command handler
async def clear_batch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_batches:
        del user_batches[user_id]
        await update.message.reply_text("🧹 បាច់ត្រូវបានជម្រះ! ការបញ្ជូនបន្ទាប់នឹងចាប់ផ្តើមបាច់ថ្មី។")
    else:
        await update.message.reply_text("ℹ️ គ្មានបាច់សកម្មដើម្បីជម្រះទេ។")

# 🟠 Handle messages with dollar amounts
async def sum_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    # Match prices with $ sign or "dollar" in Khmer
    price_patterns = re.findall(r"\$\d+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?\s*(?:ដុល្លារ|ដុល)", text, re.IGNORECASE)

    if not price_patterns:
        if not update.message.forward_date:
            await update.message.reply_text("⚠️ មិនមានតម្លៃដែលមានសញ្ញា `$` ឬ `ដុល្លារ` ឃើញទេ។")
        return

    current_sum = 0.0
    try:
        for p_str in price_patterns:
            if p_str.startswith('$'):
                current_sum += float(p_str[1:])
            elif re.search(r'\s*(?:ដុល្លារ|ដុល)', p_str, re.IGNORECASE):
                numeric_part = re.sub(r'\s*(?:ដុល្លារ|ដុល)', '', p_str, flags=re.IGNORECASE).strip()
                current_sum += float(numeric_part)
            else:
                print(f"ការព្រមាន: ទម្រង់តម្លៃមិនស្គាល់ '{p_str}'")

    except ValueError as e:
        await update.message.reply_text(f"❌ កំហុសក្នុងការបកស្រាយតម្លៃ: {e}។ សូមធានាថាលេខមានសុពលភាព។")
        return
    except Exception as e:
        await update.message.reply_text(f"❌ កំហុសមិនបានរំពឹងទុក: {e}")
        return

    if update.message.forward_date:  # Forwarded message
        # Initialize new batch if needed
        if user_id not in user_batches:
            user_batches[user_id] = {"total": 0.0, "count": 0, "last_forward_time": time.time()}

        batch = user_batches[user_id]

        # Update batch
        batch["total"] += current_sum
        batch["count"] += 1
        batch["last_forward_time"] = time.time()
    else:  # Regular message
        await update.message.reply_text(f"💰 លុយសរុប = ${current_sum:.2f}")

# 🔧 Main bot startup
if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()

    app = Application.builder().token(TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("show", show_batch))
    app.add_handler(CommandHandler("sum", sum))

    # Add message handler for text messages that are not commands
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, sum_prices))

    print("🤖 បូតកំពុងដំណើរការ...")
    app.run_polling()