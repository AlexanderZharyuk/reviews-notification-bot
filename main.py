import os
import time
import textwrap
import logging

import requests
import telegram


def prepare_message(response: dict) -> str:
    message = ''

    for lesson in response['new_attempts']:
        lesson_title = lesson['lesson_title']
        lesson_url = lesson['lesson_url']

        if lesson['is_negative']:
            approve_lesson = 'Преподаватель попросил внести правки в проект.'
        else:
            approve_lesson = 'Преподаватель принял работу!'

        message += f"""
                    <b>Название урока</b>: {lesson_title}
                    {approve_lesson}
                    <b>Ссылка на урок</b>: {lesson_url}
                    """

    return textwrap.dedent(message)


def send_message(bot: telegram.Bot, chat_id: str, reviews_info: dict) -> None:
    if len(reviews_info['new_attempts']) > 1:
        message = 'У вас появились ревью по следующим урокам:'
    else:
        message = '🚀 Новое ревью!'

    message += prepare_message(reviews_info)
    bot.send_message(text=message, chat_id=chat_id,
                     parse_mode=telegram.ParseMode.HTML)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info('Бот запущен.')

    devman_token = os.environ['DEVMAN_TOKEN']
    telegram_token = os.environ['TELEGRAM_TOKEN']
    telegram_chat_id = os.environ['TELEGRAM_CHAT_ID']
    bot = telegram.Bot(telegram_token)

    timestamp = ''
    url = f'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {devman_token}',
    }
    response_tries = 0

    while True:
        params = {
            'timestamp': timestamp
        }

        try:
            response = requests.get(url=url, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            response_tries += 1
            if response_tries >= 5:
                time.sleep(60)
                response_tries = 0
            continue

        reviews_info = response.json()
        if reviews_info['status'] == 'timeout':
            timestamp = reviews_info['timestamp_to_request']
        else:
            timestamp = reviews_info['last_attempt_timestamp']
            send_message(bot, telegram_chat_id, reviews_info)
