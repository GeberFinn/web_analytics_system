# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
#import telebot
#from telebot.types import *
from telegram import Update, Bot
from telegram import ParseMode
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import ReplyKeyboardRemove
from telegram.ext import CallbackContext
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.ext import CallbackQueryHandler
from telegram import KeyboardButton
from telegram import ReplyKeyboardMarkup
import sys

import database
import validators

import datetime

from config import load_config
import pandas as pd

import urllib
import urllib.request

from clickhouse_driver import Client


config = load_config()

client = Client(host='localhost', port=9000,user='default', settings={'use_numpy': True})


AUTH_QUESTION = 1
FIRST_QUESTION = 3

BUTTON1_AUTH = "Авторизация"
BUTTON1_GEO = "Мое местоположение"


def get_base_reply_keyboard():
    """
    Функция для создания reply-клавиатуры для аутентификации

    :return: ReplyKeyboardMarkup
    """
    keyboard = [
        [
            KeyboardButton(BUTTON1_AUTH, request_contact=True),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

def keyboard_generator(cq,orientation = 'horizontal'):

    """
    Функция для создания inline-клавиатуры

    :param cq: Текущий вопрос
    :param orientation: Ориентация растоложения клавиш ('horizontal' и 'vertical')
    :return: answer_list - Набор объектов InlineKeyboardButton
    """

    buttons = database.get_buttons(cq)
    #print(f'Buttons: {buttons}')
    answer_list = []
    empty_list = []
    line_list = []
    #print(f"Клавиатура создается под {cq} вопрос")
    if orientation == 'horizontal':
        for e in buttons:
            if e[1] == cq:
                empty_list.append(InlineKeyboardButton(text=e[2], callback_data=e[0]))
        answer_list.append(empty_list)
        #print(answer_list)
    elif orientation == 'vertical':
        for e in buttons:
            if e[1] == cq:
                answer_list.append([InlineKeyboardButton(text=e[2], callback_data=e[0])])

        #answer_list.append(empty_list)
        #print(answer_list)
    return InlineKeyboardMarkup(answer_list)


#bot = telebot.TeleBot(bot_API)

def get_pict(url,name):

    opener = urllib.request.build_opener()
    opener.addheaders = headers
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(url,f"./images/{name}.png")



def do_start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    context.bot.send_message(
        chat_id=chat_id,
        text=f"""Здравствуйте

Перечнень команд, которые могут пригодиться:

* /new - начать сессию
* /cancel - отменить сессию
* /help - получение справки 
""")

def do_help(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    context.bot.send_message(
        chat_id=chat_id,
        text=f"""
* /new - начать сессию
* /cancel - отменить текущую сессию 
    """)
    pass

def do_cancel(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    context.bot.send_message(
        chat_id=chat_id,
        text=f"""Текущая сессия отменена.
""")
    do_new(update, context)


def do_new(update: Update, context: CallbackContext):
    print('z')
    print(update.message.__dict__)
    print('v')
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chat_id = update.message.chat.id
    #print(chat_id)
    user_data = database.check_user_id(chat_id)
    #print(user_data)
    if user_data:                                       # Если id и номер пользователя есть в БД
        #context.bot.send_message(
        #    chat_id=chat_id,
        #    text=" ",
        #    reply_markup=ReplyKeyboardRemove())

        #print(user_data)
        user_name = user_data[0][2]
        session_id = database.insert_account_chat(chat_id, now, 1)
        context.user_data[2] = session_id
        context.bot.send_message(
            chat_id=chat_id,
            text=f"{user_name}, какой источник данных интересует?",
            reply_markup=keyboard_generator(FIRST_QUESTION))

        context.user_data[1] = FIRST_QUESTION           # Записываем общие данные

    else:                                               # Если id пользователя не был найден
        context.bot.send_message(
            chat_id=chat_id,
            text="Ваш аккаунт не авторизован \U0001F513. Нажмите на клавишу 'Авторизация'... ",
            reply_markup=get_base_reply_keyboard())
        context.user_data[1] = AUTH_QUESTION            # Записываем общие данные
    context.user_data[0] = chat_id

def do_work(update: Update, context: CallbackContext):

    print(context.user_data)
    chat_id = context.user_data[0]
    user_name = database.check_user_id(chat_id)
    #print('work')
    if user_name:
        user_name = user_name[0][2] # TODO

    current_question = context.user_data[1]
    #print(f"Work state #{current_question}")
    #print(current_question)
    question = database.get_question_info(current_question)
    question_text = question[0][1]
    question_type = question[0][2]
    #print(question_text, question_type)

    #print(update.callback_query)
    #print(update.message)

    if question_type == 1:                                          # text
        #print('Now i\'m here 1')
        answer_id, answer_text = validators.text_validator(update)
        #print(context.user_data[2],current_question,answer_id, answer_text)

        print(context.user_data[2],current_question,answer_id,answer_text)

        database.insert_answer(ichatid=context.user_data[2],                # INSERT в БД
                               iquestionid=current_question,ianswerid=answer_id,vcanswer=answer_text)

        # TODO INSERT в БД
        #print('ENTER:',current_question, answer_id)
        question = database.get_next_question(current_question, answer_id)
        #print(question)
        next_question = question[0][2]
        #print(f'Next question: {next_question}')

        if answer_id == 9:     # Визиты
            pict_list = [config.Matomo_urls['Visits'],config.Matomo_urls['Visits'],config.Matomo_urls['Visits'],config.Matomo_urls['Visits']]
            pass
        elif answer_id == 10:  # Уст-ва
            pict_name = f'''{context.user_data[2]}_{current_question}_{answer_id}_{answer_text}'''
            url = config.Matomo_urls['Devices']
            get_pict(url=url,name=pict_name)
            img = open(r'./images/'+pict_name+r'.png', 'rb')
            context.bot.send_photo(chat_id, img) #reply_to_message_id=message.message_id)
            img.close()
            #context.bot.send_photo()
            pass
        elif answer_id == 11:  # Пользователи
            pass
        elif answer_id == 12:  # Карта
            pass
        elif answer_id == 14:  # Статусы
            pass
        elif answer_id == 15:  # Ошибки
            pass
        elif answer_id == 16:  # Предупреждения
            pass
        elif answer_id == 17:  # Запросы
            pass

        if next_question is None:
            #print('Конец')
            context.bot.send_message(
                chat_id=chat_id,
                text=f"Сессия окончена. Запустите новую с помощью команды /new"
                )
        else:
            context.user_data[1] = next_question
            question_info = database.get_question_info(context.user_data[1])
            question_text = question_info[0][1]
            if database.get_buttons(next_question):
                context.bot.send_message(
                    chat_id=chat_id,
                    text=f"{question_text}",
                    reply_markup=keyboard_generator(context.user_data[1], orientation='vertical'))
            else:
                context.bot.send_message(
                    chat_id=chat_id,
                    text=f"{question_text}")




def main():


    #print("start")
    #main_handler = CallbackQueryHandler(callback = do_work,pass_user_data=True, pass_chat_data=True)

    #updater.dispatcher.add_handler(main_handler)

    updater = Updater(
        token=config.TG_TOKEN,
        use_context=True,
    )#base_url=config.TG_API_URL,  #request_kwargs=config.REQUEST_KWARGS

    new_handler = CommandHandler("new", do_new)
    start_handler = CommandHandler("start", do_start)
    cancel_handler = CommandHandler("cancel", do_cancel)
    help_handler = CommandHandler("help", do_help)

    updater.dispatcher.add_handler(start_handler)
    updater.dispatcher.add_handler(new_handler)
    updater.dispatcher.add_handler(cancel_handler)
    updater.dispatcher.add_handler(help_handler)
    buttons_handler = CallbackQueryHandler(callback=do_work,pass_user_data=True, pass_chat_data=True)
    message_handler = MessageHandler(Filters.all, do_work)

    updater.dispatcher.add_handler(message_handler)
    updater.dispatcher.add_handler(buttons_handler)

    # Начать обработку входящих сообщений
    updater.start_polling()
    # Не прерывать скрипт до обработки всех сообщений
    updater.idle()


if __name__ == '__main__':
    main()
    pass





#bot.send_message(477068727, "Hi")

    #get_pict()
    ##img=urllib.request.urlopen(r'''http://localhost:3000/render/d-solo/OorPxN97k/new-dashboard-copy?orgId=1&from=1653736631445&to=1653758231445&panelId=2&width=1000&height=500&tz=Europe%2FMoscow''').read()
    #img = open('test.png', 'rb')
    #bot.send_photo(message.chat.id, img) #reply_to_message_id=message.message_id)
    #img.close()
    #bot.send_message(message.chat.id, f"{message.chat.id}")



#@bot.message_handler(commands=['start'])
# def start(message):
#     markup = get_base_reply_keyboard()
#     #markup = ReplyKeyboardMarkup(resize_keyboard=True)
#     #item1 = KeyboardButton("Логи веб-приложения")
#     #item2 = KeyboardButton("Мониторинг Matomo")
#     #markup.add(item1,item2)
#
#     #message
#     bot.send_message(message.chat.id, f'Добрый день, {message.from_user.first_name} ({message.chat.id})',reply_markup=markup)


# @bot.message_handler(content_types=['text'])
# def bot_message(message):
#     if message.chat.type == 'private':
#         if message.text == 'Логи веб-приложения':
#
#             markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#             item1 = types.KeyboardButton("Выгрузка логов по шаблону")
#             item2 = types.KeyboardButton("Сформировать запрос логов")
#             markup.add(item1, item2)
#             bot.send_message(message.chat.id, "Способ выгрузки", reply_markup=markup)
#
#         elif message.text == 'Сформировать запрос логов':
#             markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#             item1 = types.KeyboardButton("Выгрузка логов по шаблону")
#             item2 = types.KeyboardButton("Сформировать запрос")
#             markup.add(item1, item2)
#             bot.send_message(message.chat.id, "Вид запроса", reply_markup=markup)
#
#             #message.json['list'].append(2)
#             #print(message.json)
#         elif message.text == "Мониторинг Matomo":
#             markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#             location_keyboard = types.KeyboardButton(text="send_location",
#                                                request_location=True)  # creating location button object
#             contact_keyboard = types.KeyboardButton('Share contact', request_contact=True)  # creating contact button object
#               # creating keyboard object
#             markup.add(location_keyboard, contact_keyboard)
#             bot.send_message(message.chat.id,
#                 "Would you mind sharing your location and contact with me?",
#                 reply_markup=markup)
#         elif message.text == "Выгрузка логов по шаблону":
#             markup = types.ReplyKeyboardMarkup(resize_keyboard=True,)
#             item1 = types.KeyboardButton("Статусы")
#             item2 = types.KeyboardButton("Самые длительные запросы")
#             item3 = types.KeyboardButton("Топ ошибок")
#             item4 = types.KeyboardButton("Топ предупреждений")
#
#             markup.add(item1, item2,item3,item4)
#
#             bot.send_message(message.chat.id,
#                              "Выберите шаблон",
#                              reply_markup=markup)
#         elif message.text == "Статусы":
#             get_pict(url=status_url)
#         ##img=urllib.request.urlopen(r'''http://localhost:3000/render/d-solo/OorPxN97k/new-dashboard-copy?orgId=1&from=1653736631445&to=1653758231445&panelId=2&width=1000&height=500&tz=Europe%2FMoscow''').read()
#             img = open('test.png', 'rb')
#             bot.send_photo(message.chat.id, img) #reply_to_message_id=message.message_id)
#             img.close()
#             #bot.send_message(message.chat.id, f"{message.chat.id}")
#         elif message.text == "Самые длительные запросы":
#             get_pict(url=top_duration_url)
#             ##img=urllib.request.urlopen(r'''http://localhost:3000/render/d-solo/OorPxN97k/new-dashboard-copy?orgId=1&from=1653736631445&to=1653758231445&panelId=2&width=1000&height=500&tz=Europe%2FMoscow''').read()
#             img = open('test.png', 'rb')
#             bot.send_photo(message.chat.id, img)  # reply_to_message_id=message.message_id)
#             img.close()
#         elif message.text == "Топ ошибок":
#             get_pict(url=top_emergencies_url)
#             ##img=urllib.request.urlopen(r'''http://localhost:3000/render/d-solo/OorPxN97k/new-dashboard-copy?orgId=1&from=1653736631445&to=1653758231445&panelId=2&width=1000&height=500&tz=Europe%2FMoscow''').read()
#             img = open('test.png', 'rb')
#             bot.send_photo(message.chat.id, img)  # reply_to_message_id=message.message_id)
#             img.close()
#         elif message.text == "Топ предупреждений":
#             get_pict(url=top_warnings_url)
#             ##img=urllib.request.urlopen(r'''http://localhost:3000/render/d-solo/OorPxN97k/new-dashboard-copy?orgId=1&from=1653736631445&to=1653758231445&panelId=2&width=1000&height=500&tz=Europe%2FMoscow''').read()
#             img = open('test.png', 'rb')
#             bot.send_photo(message.chat.id, img)  # reply_to_message_id=message.message_id)
#             img.close()
#         #print(message.__dict__)
#
# @bot.message_handler(content_types=['contact'])
# def contact_handler(message):
#     print(message.contact)


#bot.polling(none_stop=True)



# Press the green button in the gutter to run the script.

    #get_pict()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
