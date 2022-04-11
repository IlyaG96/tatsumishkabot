import subprocess
from enum import Enum, auto
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from environs import Env
import speech_recognition as sr
import os


class BotStates(Enum):
    START = auto()
    HANDLE_MESSAGE = auto()


def start(update, context):
    update.message.reply_text(
        'Привет! Отправь мне голосовое сообщение, а я переведу его в текст!'
    )

    return BotStates.HANDLE_MESSAGE


def send_message(update, context):
    voice = context.bot.get_file(update.message.voice.file_id)
    voice.download(f'{update.message.chat_id}.ogg')
    recognizer = sr.Recognizer()
    src_filename = f'{update.message.chat_id}.ogg'
    dest_filename = f'{update.message.chat_id}.wav'

    process = subprocess.run(['ffmpeg', '-i', src_filename, dest_filename])
    if process.returncode != 0:
        raise Exception('Something went wrong')
    try:
        user_audio_file = sr.AudioFile(f'{update.message.chat_id}.wav')
        with user_audio_file as source:
            user_audio = recognizer.record(source)
        text = recognizer.recognize_google(user_audio, language='ru-ru')

        update.message.reply_text(
            text
        )
    except Exception as e:
        print(e)
    finally:
        os.unlink(f'{update.message.chat_id}.ogg')
        os.unlink(f'{update.message.chat_id}.wav')

    return BotStates.HANDLE_MESSAGE


def main():
    env = Env()
    env.read_env()
    telegram_token = env.str('TG_TOKEN')

    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    voice_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
        ],
        states={
            BotStates.HANDLE_MESSAGE: [
                MessageHandler(Filters.voice, send_message),
            ],
        },

        per_user=True,
        per_chat=True,
        fallbacks=[],
    )

    dispatcher.add_handler(voice_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
