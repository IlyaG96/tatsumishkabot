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


def make_text_from_audio(audio_message, chat_id):
    recognizer = sr.Recognizer()
    try:
        user_audio_file = sr.AudioFile(f'{chat_id}.wav')
        with user_audio_file as source:
            user_audio = recognizer.record(source)
        text = recognizer.recognize_google(user_audio, language='ru-ru')

    finally:
        os.unlink(f'{chat_id}.ogg')
        os.unlink(f'{chat_id}.wav')

    return text


def process_message(update, context):

    chat_id = update.message.chat_id
    try:
        voice = context.bot.get_file(update.message.voice.file_id)
    except AttributeError:
        voice = context.bot.get_file(update.message.audio.file_id)

    voice.download(f'{chat_id}.ogg')

    src_filename = f'{chat_id}.ogg'
    dest_filename = f'{chat_id}.wav'

    process = subprocess.run(['ffmpeg', '-i', src_filename, dest_filename])
    if process.returncode != 0:
        raise Exception('Something went wrong')
    user_audio_file = sr.AudioFile(f'{chat_id}.wav')

    message = make_text_from_audio(user_audio_file, chat_id)
    update.message.reply_text(
        message
    )

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
                MessageHandler(Filters.voice, process_message),
                MessageHandler(Filters.audio, process_message)
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
