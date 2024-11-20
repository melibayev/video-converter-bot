import os
import json
import ffmpeg
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Constants for file storage
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
USERS_LOG_FILE = "users.log"
ADMIN_FILE = "admin.json"
user_videos = {}

# --- User Logging Functions ---
def get_admin():
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, "r") as file:
            return json.load(file).get("admin_id")
    return None

def set_admin(user_id):
    if not os.path.exists(ADMIN_FILE):  # Set admin only once
        with open(ADMIN_FILE, "w") as file:
            json.dump({"admin_id": user_id}, file)

def log_user_data(user):
    user_data = {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    try:
        # Read existing data
        if os.path.exists(USERS_LOG_FILE):
            with open(USERS_LOG_FILE, "r") as file:
                users = json.load(file)
        else:
            users = []

        # Update the timestamp if the user already exists
        for existing_user in users:
            if existing_user["user_id"] == user_data["user_id"]:
                existing_user["timestamp"] = user_data["timestamp"]
                break
        else:
            # Add new user if not found
            users.append(user_data)

        # Write updated data back to the file
        with open(USERS_LOG_FILE, "w") as file:
            json.dump(users, file, indent=4)

    except Exception as e:
        print(f"Error logging user data: {e}")

# --- Command Handlers ---
async def start(update: Update, context):
    user = update.effective_user
    log_user_data(user)

    # Set admin if not already set
    if get_admin() is None:
        set_admin(user.id)
        print(f"Admin set: {user.id}")

    await update.message.reply_text(
        "Welcome! Send me a video, and I'll help you convert it to MP3 or Telegram voice format. 🎥➡️🎧"
    )

async def list_users(update: Update, context):
    user = update.effective_user
    admin_id = get_admin()

    if user.id != admin_id:
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    if os.path.exists(USERS_LOG_FILE):
        with open(USERS_LOG_FILE, "r") as file:
            users = json.load(file)

        if not users:
            await update.message.reply_text("No users have used the bot yet.")
            return

        response = "📋 List of users who used the bot:\n\n"
        for u in users:
            response += (
                f"👤 User ID: {u['user_id']}\n"
                f"   Username: @{u['username'] or 'N/A'}\n"
                f"   First Name: {u['first_name']}\n"
                f"   Last Active: {u['timestamp']}\n\n"
            )
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("No user log file found. No users have used the bot yet.")

# --- Video Handling ---
async def handle_video(update: Update, context):
    user = update.effective_user
    log_user_data(user)

    video_file = update.message.video
    if video_file.file_size > MAX_FILE_SIZE:
        await update.message.reply_text("The file is too large. Please send a smaller video (max 50 MB). 📏")
        return

    video_path = f"video_{update.message.message_id}.mp4"
    video_file = await video_file.get_file()
    await video_file.download_to_drive(video_path)
    user_videos[user.id] = video_path

    keyboard = [
        [InlineKeyboardButton("MP3 🎧", callback_data="mp3")],
        [InlineKeyboardButton("Voice 🎙️", callback_data="voice")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose the format you want to convert the video to:", reply_markup=reply_markup)

async def process_conversion(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id
    format_choice = query.data
    video_path = user_videos.get(user_id)

    if not video_path:
        await query.answer("No video found to process. Please send a video first.", show_alert=True)
        return

    await query.answer("Processing your request... ⏳")

    output_path = video_path.replace(".mp4", ".mp3") if format_choice == "mp3" else video_path.replace(".mp4", ".ogg")
    audio_format = {"format": "mp3"} if format_choice == "mp3" else {"format": "opus", "acodec": "libopus", "ar": "16000"}

    try:
        ffmpeg.input(video_path).output(output_path, **audio_format).run(cmd="ffmpeg", overwrite_output=True)
        if format_choice == "mp3":
            await query.message.reply_audio(audio=open(output_path, "rb"), caption="Here's your MP3! 🎧")
        else:
            await query.message.reply_voice(voice=open(output_path, "rb"), caption="Here's your Telegram voice message! 🎙️")
    finally:
        os.remove(video_path)
        os.remove(output_path)
        del user_videos[user_id]

    await query.message.reply_text("Conversion completed! 🎉")

# --- Main Function ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("users", list_users))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(CallbackQueryHandler(process_conversion))

    app.run_polling()

if __name__ == "__main__":
    main()
