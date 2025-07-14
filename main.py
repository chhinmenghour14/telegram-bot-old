import os
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me ABA PayWay messages and I'll sum up the amounts!")

async def sum_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Match prices that start with a dollar sign, e.g., $1.92
    prices = re.findall(r"\$\d+(?:\.\d{1,2})?", text)

    if not prices:
        await update.message.reply_text("ត្រូវប្រាកតថាមានអក្សរ រឺលេខបែបនេះ '$1.92'.")
        return

    try:
        # Convert matched prices to float by stripping the '$'
        total = sum(float(p[1:]) for p in prices)
        await update.message.reply_text(f"លុយសរុប = ${total:.2f}")
    except Exception as e:
        await update.message.reply_text(f"Error calculating total: {e}")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, sum_prices))
    app.run_polling()
