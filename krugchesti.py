import os
import pandas as pd
import telebot
import sqlite3
import datetime
from telebot import types
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(os.getenv('BOT_KEY'))

user = None


@bot.message_handler(commands=['start'])
def start_message(message):
    global user
    user = message.from_user.id
    keyboard = types.InlineKeyboardMarkup()
    kb1 = types.InlineKeyboardButton(text="Готов. Буду участвовать", callback_data="text1")
    kb2 = types.InlineKeyboardButton(text="Не готов", callback_data="text2")
    kb3 = types.InlineKeyboardButton(text="Скачать БД", callback_data="load_bd")
    if user == 737181059:
        keyboard.add(kb1, kb2, kb3)
    else:
        keyboard.add(kb1, kb2)
    bot.send_message(message.chat.id, '*Привет!*\nКруг Чести - добровольное объединение людей, готовых внести свой '
                                      'личный вклад в позитивные преобразования окружающей действительности, '
                                      'придерживающиеся принципов братства, взаимной поддержки и стремящиеся во всем '
                                      'быть положительным примером подрастающему поколению. \n\nМы предлагаем Вам '
                                      'принять участие в розыгрыше. Вы готовы?\n\nПо вопросам можно обратиться: '
                                      '[{}](tg://user?id={})'.format('Илья Кудрин', '737181059',),
                     parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: True)
def ans(c):
    conn = sqlite3.connect('krug_chesti.db', check_same_thread=False)
    u = conn.cursor()
    if c.data == "text1":
        bot.edit_message_reply_markup(chat_id=c.message.chat.id, message_id=c.message.message_id, reply_markup=None)
        user_id = u.execute("select user_id from Users where user_id = ? limit 1", (str(user),)).fetchone()
        user_id = [user_id]
        user_id = str(user_id).strip('[(\')],')
        if user_id != 'None':
            bot.send_message(c.message.chat.id, 'Вы уже приняли участие!')
        else:
            sent = bot.send_message(c.message.chat.id,
                                    '*Замечательно!*\n\n Укажите свой номер телефона!', parse_mode=ParseMode.MARKDOWN)
            bot.register_next_step_handler(sent, do_end)

    elif c.data == 'text2':
        bot.edit_message_reply_markup(chat_id=c.message.chat.id, message_id=c.message.message_id, reply_markup=None)
        bot.send_message(c.message.chat.id, 'Мы ждем Вас в следующий раз!')
    elif c.data == 'text3':
        bot.edit_message_reply_markup(chat_id=c.message.chat.id, message_id=c.message.message_id, reply_markup=None)
        sent = bot.send_message(c.message.chat.id,
                                '*Хорошо!*\n\n Укажите дополнительный номер телефона!', parse_mode=ParseMode.MARKDOWN)
        bot.register_next_step_handler(sent, do_two_end)
    elif c.data == 'text4':
        bot.send_message(c.message.chat.id, '*Спасибо за участие!*', parse_mode=ParseMode.MARKDOWN)
    elif c.data == 'load_bd':
        df = pd.read_sql('select * from Users', conn)
        df.to_csv('out.csv')
        bot.send_document(c.message.chat.id, open("out.csv", "rb"))
    else:
        bot.edit_message_reply_markup(chat_id=c.message.chat.id, message_id=c.message.message_id, reply_markup=None)
        bot.send_message(c.message.chat.id, 'Нажмите сюда => /start')


def do_end(message):
    conn = sqlite3.connect('krug_chesti.db', check_same_thread=False)
    u = conn.cursor()
    keyboard1 = types.InlineKeyboardMarkup()
    kb1 = types.InlineKeyboardButton(text="Давайте введу", callback_data="text3")
    kb2 = types.InlineKeyboardButton(text="Не буду", callback_data="text4")
    keyboard1.add(kb1, kb2)
    user_id = message.from_user.id
    phone_number = message.text
    data = datetime.date.today()
    bot.send_message(message.chat.id, '*Будете указывать дополнительный свой номер телефона?*',
                     parse_mode=ParseMode.MARKDOWN,  reply_markup=keyboard1)
    u.execute("insert into Users(user_id, phone_number, timestamp) values (?,?,?)", (user_id, phone_number, data))
    conn.commit()


def do_two_end(message):
    conn = sqlite3.connect('krug_chesti.db', check_same_thread=False)
    u = conn.cursor()
    user_id = message.from_user.id
    phone_number_2 = message.text
    bot.send_message(message.chat.id, '*Спасибо за участие!*', parse_mode=ParseMode.MARKDOWN)
    u.execute("update Users set phone_number_2 = ? where user_id = ?", (phone_number_2, user_id))
    conn.commit()


if __name__ == '__main__':
    bot.polling(none_stop=True)
