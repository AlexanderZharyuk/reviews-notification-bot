import os

import requests
import telegram

from dotenv import load_dotenv


def get_user_reviews(devman_token: str) -> dict:
	url = 'https://dvmn.org/api/user_reviews/'
	headers = {
		'Authorization': f'Token {devman_token}',
	}

	response = requests.get(url=url, headers=headers)
	response.raise_for_status()

	return response.json()


def create_long_polling(devman_token:str, timestamp: (str, float)) -> dict:
	url = f'https://dvmn.org/api/long_polling/'
	headers = {
		'Authorization': f'Token {devman_token}',
	}

	params = {
		'timestamp': timestamp
	}

	response = requests.get(url=url, headers=headers, params=params)
	response.raise_for_status()

	return response.json()


def get_info_for_message(response: dict) -> str:
	message = ''
	for lesson in response['new_attempts']:
		lesson_title = lesson['lesson_title']
		lesson_url =  lesson['lesson_url']
		
		if lesson['is_negative']:
			approve_lesson = 'Преподаватель попросил внести правки в проект.'
		else:
			approve_lesson = 'Преподаватель принял работу!'

		message += f'<b>Название урока</b>: {lesson_title}\n\n' \
				   f'{approve_lesson}\n' \
				   f'<b>Ссылка на урок</b>: {lesson_url}\n\n'
				   
	return message


def send_message(bot: telegram.Bot, chat_id: str, service_response: dict) -> None:
	if len(service_response['new_attempts']) > 1:
		message = 'У вас появились ревью по следующим урокам:\n\n'
	else:
		message = '🚀 Новое ревью!\n\n'
		
	message += get_info_for_message(service_response)
	bot.send_message(text=message, chat_id=chat_id, parse_mode=telegram.ParseMode.HTML)



if __name__=='__main__':
	load_dotenv()
	devman_token = os.getenv('DEVMAN_TOKEN')
	telegram_token = os.getenv('TELEGRAM_TOKEN')
	telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
	bot = telegram.Bot(telegram_token)
	timestamp = ''

	while True:
		try:
			service_response = create_long_polling(devman_token, timestamp)
		except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
			continue

		if service_response['status'] == 'timeout':
			timestamp = service_response['timestamp_to_request']
		else:
			timestamp = service_response['last_attempt_timestamp']
			send_message(bot, telegram_chat_id, service_response)
