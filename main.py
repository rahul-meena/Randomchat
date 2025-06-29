from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Stores unpaired users and active chat pairs
waiting_users = []
active_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id in active_chats:
        await update.message.reply_text("🔄 You're already in a chat. Use /stop to end it first.")
        return
    if user_id in waiting_users:
        await update.message.reply_text("⏳ Still waiting for a partner...")
        return
    if waiting_users:
        partner_id = waiting_users.pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id
        await context.bot.send_message(chat_id=partner_id, text="🎉 Connected! Say hi to your stranger!")
        await update.message.reply_text("🎉 Connected! Say hi to your stranger!")
    else:
        waiting_users.append(user_id)
        await update.message.reply_text("🔍 Waiting for a partner...")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id in waiting_users:
        waiting_users.remove(user_id)
        await update.message.reply_text("❌ Left the queue.")
    elif user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)
        await context.bot.send_message(chat_id=partner_id, text="❌ Stranger left the chat.")
        await update.message.reply_text("❌ You left the chat.")
    else:
        await update.message.reply_text("ℹ️ You're not in a chat.")

async def next_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await stop(update, context)
    await start(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        try:
            await context.bot.send_message(chat_id=partner_id, text=update.message.text)
        except:
            await update.message.reply_text("❗ Could not send message.")
    else:
        await update.message.reply_text("❌ You're not in a chat. Use /start to find a partner.")

async def block_non_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Only text messages are allowed in anonymous chat.")

def main():
    import os
    TOKEN = os.environ.get("BOT_TOKEN")  # Set this in Railway or .env

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("next", next_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(~filters.TEXT & ~filters.COMMAND, block_non_text))

    print("Bot running...")
    app.run_polling()

if __name__ == '__main__':
    main()
