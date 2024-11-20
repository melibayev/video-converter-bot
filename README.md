# Telegram Video Converter Bot 🎥➡️🎧

A Telegram bot that converts video files into MP3 audio or Telegram voice message formats. Users can send a video file to the bot and choose the desired conversion format.

## Features 🚀
- Converts videos to MP3 audio files.
- Converts videos to Telegram-compatible voice messages.
- Handles large user bases with logging for admin monitoring.
- Includes admin-only commands to list all users who have used the bot.
- User-friendly progress updates during conversion.

## Prerequisites 🛠️
1. **Python 3.8+** installed on your system.
2. **FFmpeg** installed and added to the system path.
3. A Telegram bot token from [BotFather](https://core.telegram.org/bots#botfather).

## Installation 📦
1. Clone this repository:
    ```bash
    git clone https://github.com/melibayev/video-converter-bot.git
    cd video-converter-bot
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Set up your `.env` file with the following content:
    ```
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    ```

4. Run the bot:
    ```bash
    python main.py
    ```

## Usage 📝
- Start the bot using `/start`.
- Send a video file to the bot.
- Choose the format for conversion:
  - **MP3**: Receive the video’s audio as an MP3 file.
  - **Voice**: Receive the video’s audio as a Telegram voice message.
- The converted file will be sent back to you with a friendly caption.

## Admin Commands 🔐
- **`/users`**: List all users who have interacted with the bot. *(Admin only)*


## Files and Logs 📁
- **`users.log`**: Logs all users interacting with the bot (user ID, username, first name, and timestamp).
- **`admin.json`**: Stores the admin ID after the first bot run.

## License 📜
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contributing 🤝
Contributions are welcome! If you have any suggestions or improvements, feel free to open an issue or submit a pull request.

## Author 👨‍💻
Developed by [Elbek Meliboev](https://github.com/melibayev).

---

## Acknowledgements 🙏
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [FFmpeg](https://ffmpeg.org/)
