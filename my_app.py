import markovify as markovify
import telebot
from telebot import types
import conf
from random import choice
import pandas as pd
import flask

WEBHOOK_URL_BASE = "https://{}:{}".format(conf.WEBHOOK_HOST, conf.WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(conf.TOKEN)

bot = telebot.TeleBot(conf.TOKEN, threaded=False)

bot.remove_webhook()

bot.set_webhook(url=WEBHOOK_URL_BASE+WEBHOOK_URL_PATH)

app = flask.Flask(__name__)


@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.send_message(message.chat.id,
                     'Этот бот предлагает вам сыграть в игру и угадать, кем написана присланная строчка - Чеховым или '
                     'компьютером с помощью цепи Маркова. Вам нужно будет выбрать, нажав на одну из двух кнопок. Для '
                     'начала нажмите /start. При возникновении затруднений нажмите /help. Для того, чтобы посмотреть '
                     'статистику своей игры нажмите /stats.')


@bot.message_handler(commands=['start'])
def repeat_all_messages(message):
    # создаем клавиатуру
    keyboard = types.InlineKeyboardMarkup()

    button1 = types.InlineKeyboardButton(text="Чехов", callback_data="button1")
    button2 = types.InlineKeyboardButton(text="Компьютер", callback_data="button2")
    keyboard.add(button1)
    keyboard.add(button2)

    # отправляем сообщение пользователю
    with open('C:\\Users\\npelt\\chekhov.txt', encoding='utf-8') as f:
        text = f.read().split('. ')
        global check
        global mark
        global output  # помечаем переменные global чтобы можно было отсылать к ним из других функций
        check = choice(text)  # выбираем случайное предложение из текста
        for i in range(1):
            m = markovify.Text(text)  # создаём марковскую цепь
            mark = m.make_sentence()
        output = choice([mark, check])  # случайно выбираем оригинальное предложение или марковскую цепь для вывода

    bot.send_message(message.chat.id, output)
    bot.send_message(message.chat.id, "Чехов или компьютер?", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    cid = str(call.message.chat.id)
    if call.message:  # в зависимости от ответа пользователя выводим результат и заносим его в таблицу
        if call.data == "button1" and output == check:
            with open('answers.csv', 'a', encoding='utf-8') as answers:
                answers.write(cid + '\t' + '+' + '\n')
            bot.send_message(call.message.chat.id, "Вы угадали! \nЕсли хотите сыграть ещё раз, нажмите /start \nЕсли "
                                                   "хотите посмотреть результаты, нажмите /stats")
            bot.send_sticker(call.message.chat.id, 'CAACAgIAAxkBAAEBdvxgz0O9Il'
                                                   '-ne3lD1WOyAXJNqj4cywACGQEAAlERmR_3E0cFdeNFWx8E')
        if call.data == "button2" and output == check:
            with open('answers.csv', 'a', encoding='utf-8') as answers:
                answers.write(cid + '\t' + '-' + '\n')
            bot.send_message(call.message.chat.id, "Вы не угадали:( \nЕсли хотите сыграть ещё раз, нажмите /start "
                                                   "\nЕсли хотите посмотреть результаты, нажмите /stats")
            bot.send_sticker(call.message.chat.id, 'CAACAgIAAxkBAAEBdw5gz0SZ6GH'
                                                   'o0dhBAxWl8t2fNGJBxQACdAEAAsogeQQWfiBIoU72Ox8E')

        if call.data == "button1" and output == mark:
            with open('answers.csv', 'a', encoding='utf-8') as answers:
                answers.write(cid + '\t' + '-' + '\n')
            bot.send_message(call.message.chat.id, "Вы не угадали:(( \nЕсли хотите сыграть ещё раз, нажмите /start "
                                                   "\nЕсли хотите посмотреть результаты, нажмите /stats")
            bot.send_sticker(call.message.chat.id, 'CAACAgIAAxkBAAEBdxpgz0TVV'
                                                   '-HksCZR5UNdxpAR4CM9vwACcwADaQHUBTJdccdSVnzOHwQ')
        if call.data == "button2" and output == mark:
            with open('answers.csv', 'a', encoding='utf-8') as answers:
                answers.write(cid + '\t' + '+' + '\n')
            bot.send_message(call.message.chat.id, "Вы угадали!! \nЕсли хотите сыграть ещё раз, нажмите /start \nЕсли "
                                                   "хотите посмотреть результаты, нажмите /stats")
            bot.send_sticker(call.message.chat.id, 'CAACAgIAAxkBAAEBdwtgz0RqkQTr0Y4CcilpzKY3Fby8rQACjgAD6fI9GsmVMl4'
                                                   '-eU1DHwQ')


@bot.message_handler(commands=['stats'])
def statistics(message):
    mid = message.chat.id
    df = pd.read_csv("answers.csv", sep="\t")  # читаем таблицу с результатами
    df_g = df.loc[(df['id'] == mid) & (df['result'] == '+')]  # смотрим правильные ответы конкретного пользователя
    col_g = df_g['result']
    res_g = str(col_g.count())  # считаем количество правильных ответов
    df_b = df.loc[(df['id'] == mid) & (df['result'] == '-')]  # то же для неправильных ответов
    col_b = df_b['result']
    res_b = str(col_b.count())

    reply = 'правильных ответов: ' + res_g + '\n' + 'неправильных ответов: ' + res_b  # выводим статистику пользователю
    bot.send_message(message.chat.id, reply)


@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)
