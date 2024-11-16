import os
import json
import ffmpeg
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv

load_dotenv()  # Loads variables from the .env file
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Maximum allowed file size (in bytes, for example, 50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Load existing users from a file
def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# Save users to a file
def save_users():
    with open('users.json', 'w') as f:
        json.dump(user_list, f, indent=4)


# Initialize user dictionary and load existing data
user_list = load_users()

ADMIN_USER_ID = None
PENDING_CONVERSIONS = {}  # Dictionary to track pending video-to-format mappings


async def start(update: Update, context):
    global ADMIN_USER_ID
    user_id = update.message.from_user.id
    first_name = update.message.from_user.first_name
    username = update.message.from_user.username

    if ADMIN_USER_ID is None:
        ADMIN_USER_ID = user_id
        print(f"Admin User ID set to: {ADMIN_USER_ID}")

    user_list[user_id] = {
        "first_name": first_name,
        "username": username or "N/A"  # Handle cases where username is None
    }
    save_users()

    # Sending welcome message
    await update.message.reply_text(
        "Welcome! This bot helps you convert videos to MP3 or Telegram audio format. 🎶"
    )
    await update.message.reply_text("Send me your video to get started! 🎥➡️🎧")


# Command handler for listing users (for admin only)
async def list_users(update: Update, context):
    user_id = update.message.from_user.id

    # Check if the command is from the admin
    if user_id == ADMIN_USER_ID:
        # Construct a message with user details
        user_info = "\n".join(
            [f"{uid}: {info['first_name']} (@{info['username']})" for uid, info in user_list.items()]
        )
        if user_info:
            await update.message.reply_text(f"Users who interacted with the bot:\n{user_info}")
        else:
            await update.message.reply_text("No users have interacted with the bot yet.")
    else:
        await update.message.reply_text("You don't have permission to use this command.")


# Handler for receiving video files
async def handle_video(update: Update, context):
    user_id = update.message.from_user.id
    video_file = update.message.video

    # Checking if the video is too large
    if video_file.file_size > MAX_FILE_SIZE:
        await update.message.reply_text("The file is too large. Please send a smaller video (max 50 MB). 📏")
        return

    # Save the video details for later processing
    PENDING_CONVERSIONS[user_id] = video_file

    # Ask the user to select the desired format
    keyboard = [
        [InlineKeyboardButton("MP3", callback_data="mp3"), InlineKeyboardButton("Audio", callback_data="audio")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose the format for conversion:", reply_markup=reply_markup)


# Handler for processing format selection
async def handle_format_selection(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    if user_id not in PENDING_CONVERSIONS:
        await query.edit_message_text("No pending video found. Please send a video first.")
        return

    format_choice = query.data
    video_file = PENDING_CONVERSIONS.pop(user_id)  # Get the pending video file

    video_path = f"audio{query.message.message_id}.mp4"
    output_path = video_path.replace(".mp4", f".{format_choice}")

    # Downloading the video
    video_file = await video_file.get_file()
    await video_file.download_to_drive(video_path)

    try:
        # Convert video to the chosen format
        if format_choice == "mp3":
            ffmpeg.input(video_path).output(output_path).run(cmd='ffmpeg', overwrite_output=True)
            send_function = update.callback_query.message.reply_audio
        elif format_choice == "audio":
            ffmpeg.input(video_path).output(output_path, acodec="libopus").run(cmd='ffmpeg', overwrite_output=True)
            send_function = update.callback_query.message.reply_voice
        else:
            await query.edit_message_text("Invalid choice.")
            return

        # Send the converted file
        await send_function(
            audio=open(output_path, 'rb'),
            caption="Converted by @video_to_mp3_maker_bot"
        )
        await query.edit_message_text("Conversion completed! 🎉")
    finally:
        # Clean up temporary files
        os.remove(video_path)
        if os.path.exists(output_path):
            os.remove(output_path)


# Main function to run the bot
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Add command and message handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("users", list_users))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(CallbackQueryHandler(handle_format_selection))

    # Start the bot
    app.run_polling()


if __name__ == '__main__':
    main()
