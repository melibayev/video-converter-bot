import os
import json
import ffmpeg
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
import os

load_dotenv()  # Loads variables from the .env file
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

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
        "Welcome! This bot helps you convert videos to MP3 format. 🎶"
    )
    await update.message.reply_text("Now, send me your video to convert to MP3! 🎥➡️🎧")


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


# Handler for receiving video files with progress updates
async def handle_video(update: Update, context):
    # Get file size directly from the video
    video_file = update.message.video

    # Checking if the video is too large
    if video_file.file_size > MAX_FILE_SIZE:
        await update.message.reply_text("The file is too large. Please send a smaller video (max 50 MB). 📏")
        return

    # Sending "Converting..." message
    converting_message = await update.message.reply_text("Converting your video... ⏳")
    await asyncio.sleep(2)  # Simulate processing time

    # Updating with "Almost done..." message
    await converting_message.edit_text("Almost done... 🔄")
    video_path = f"audio{update.message.message_id}.mp4"
    output_path = video_path.replace(".mp4", ".mp3")

    # Downloading the video and convert to MP3
    video_file = await video_file.get_file()  # Download file from Telegram
    await video_file.download_to_drive(video_path)

    try:
        # Convert video to MP3
        ffmpeg.input(video_path).output(output_path).run(cmd='C:\\ffmpeg\\bin\\ffmpeg.exe', overwrite_output=True)

        # Sending MP3 file to user with bot link in the caption
        await converting_message.delete()
        await update.message.reply_audio(
            audio=open(output_path, 'rb'),
            caption="Converted by @video_to_mp3_maker_bot"
        )
        await update.message.reply_text("Conversion completed! 🎉")
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

    # Start the bot
    app.run_polling()


if __name__ == '__main__':
    main()

