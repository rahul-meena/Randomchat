from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# Store user states
waiting_users = []
active_chats = {}

# ⏹ Stop chat logic
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id in waiting_users:
        waiting_users.remove(user_id)
        await update.effective_chat.send_message("❌ Left the queue.")
    elif user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)
        await context.bot.send_message(chat_id=partner_id, text="❌ Stranger left the chat.")
        await update.effective_chat.send_message("❌ You left the chat.")
    else:
        await update.effective_chat.send_message("ℹ️ You're not in a chat.")

# 🔁 Start or match with stranger
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    if user_id in active_chats:
        await update.effective_chat.send_message("🔄 You're already in a chat. Use ❌ Stop to leave.")
        return
    if user_id in waiting_users:
        await update.effective_chat.send_message("⏳ Still waiting for a partner...")
        return

    if waiting_users:
        partner_id = waiting_users.pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Next", callback_data="next"),
             InlineKeyboardButton("❌ Stop", callback_data="stop"),
             InlineKeyboardButton("🚩 Report", callback_data="report")]
        ])

        await context.bot.send_message(chat_id=partner_id, text="🎉 Connected! Say hi to your stranger!", reply_markup=keyboard)
        await update.effective_chat.send_message("🎉 Connected! Say hi to your stranger!", reply_markup=keyboard)

    else:
        waiting_users.append(user_id)
        await update.effective_chat.send_message("🔍 Waiting for a partner...")

# ⏭ Next command
async def next_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await stop(update, context)
    await start(update, context)

# 💬 Message relay between paired users
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        try:
            await context.bot.send_message(chat_id=partner_id, text=update.message.text)
        except:
            await update.effective_chat.send_message("❗ Message failed to send.")
    else:
        await update.effective_chat.send_message("❌ You're not in a chat. Use /start to find a partner.")

# 🚫 Block non-text
async def block_non_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_chat.send_message("❌ Only text messages are allowed in anonymous chat.")

# 🧠 Handle button presses
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "next":
        await stop(update, context)
        await start(update, context)

    elif query.data == "stop":
        await stop(update, context)

    elif query.data == "report":
        await query.edit_message_text("🚨 Report received. Admin will review it.")
        # Optionally log or notify admin

# 🚀 Main bot setup
def main():
    import os
    TOKEN = os.environ.get("BOT_TOKEN")  # Set this on Railway or in .env

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("next", next_cmd))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(~filters.TEXT & ~filters.COMMAND, block_non_text))
    app.add_handler(CallbackQueryHandler(handle_buttons))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
