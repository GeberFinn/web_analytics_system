import requests
from telegram import Update
from telegram import File, PassportFile, Bot
import telegram.utils.request
from telegram import *
from telegram.ext import Updater
from database import *
import re
from config import *
import urllib.request
import shutil
import sys
import datetime

config = load_config()
TG_TOKEN = config.TG_TOKEN
#TG_API_URL = config.TG_API_URL


def name_validator(update: Update):
    answer_text = None
    answer_id = None
    if update.callback_query is None:  # Ручной
        answer_text = update.message.text

    else:  # Клавиша
        answer_text = 'Default'
        answer_id = None
        query = update.callback_query

    return answer_id, answer_text


def text_validator(update: Update):
    answer_text = None
    answer_id = None
    if update.callback_query is None:  # Ручной
        return

    else:  # Клавиша

        query = update.callback_query
        data = query['data']
        answer_info = get_answer_info(data)
        answer_text = answer_info[0][2]
        answer_id = answer_info[0][0]

    return answer_id, answer_text


def time_validator(update: Update):
    answer_text = None
    answer_id = None
    if update.callback_query is None:  # Ручной
        answer_text = update.message.text
        answer_text.strip()
        print(answer_text)
        # TODO Валидации
    else:  # Клавиша
        query = update.callback_query
        current_answer = query['data']
        print(current_answer)
        answer_id = current_answer
        answer_info = get_answer_info(current_answer)
        answer_text = answer_info[0][2]
    #
    #        if answer_text == 'Указать текущее время':
    #
    #            answer_text = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # print(f'Time: {answer_text}')
    # print(f'Answer: {answer_id}')
    return answer_id, answer_text


def text_data_validator(update: Update):
    if update.callback_query is None:

        print(update.message.text)
    else:

        query = update.callback_query
        # print(query)


def text_geo_validator(update: Update):
    if update.callback_query is None:

        print(update.message.text)
    else:

        query = update.callback_query
        data = query['data']
        answer_info = get_answer_info(data)
        answer_text = answer_info[0][2]
        answer_id = answer_info[0][0]


def contact_validator(update: Update):
    answer_id = None
    answer_text = None
    acc_id = None

    if update.callback_query is None:  # Ручной

        data = update.message.text
        if data is None:
            phone_number = update.message.contact.phone_number
            # print(f'Телефон по клавише: {phone_number}')
            answer_text = phone_number

        else:  # Ввод телефона вручную, скорее всего не будет
            print(f'Телефон не по клавише: {data}')
            # TODO Валидация номера
            # answer_text = data

        answer_text = re.search(r'(\d)(\d)(\d)(\d)(\d)(\d)(\d)(\d)(\d)(\d)(\d)$', answer_text)
        answer_text = answer_text.group(0)
        # print(answer_text)
        # TODO Проверить наличие номера в БД
        user = check_user_phone(answer_text)
        if user:
            acc_id = user[0][0]
            user_name = user[0][2]
            user_id = user[0][3]
            # print(f'\nUser found:\n* {acc_id}\n* {user_id}\n* {user_name}\n')

        else:
            # print('User not found')
            answer_text = 0

    # elif update.callback_query is not None:  # По клавише скорей всего не потребуется
    #    answer_id = None
    #    query = update.callback_query
    #    #print(query)
    # else:
    #    #print('Что-то еще...')

    return acc_id, answer_id, answer_text,  # Обработчик возвращает id и текст ответа, если ошибка, то 0
