import telebot
from telebot import types
import sqlite3
import datetime

bot = telebot.TeleBot('YOUR_API_TOKEN')

# List of admin chat IDs
admin_chat_ids = [] 

user_ids = {}
bot_start_time = datetime.datetime.now()

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Добро пожаловать в бот! Пожалуйста, подпишитесь, чтобы продолжить.")

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    user_id = message.from_user.id

    user_ids[message.chat.id] = message.from_user.id

    c.execute("SELECT * FROM users WHERE telegram_user_id = ?", (user_id,))
    result = c.fetchone()

    if result is None:
        c.execute("INSERT INTO users VALUES (?)", (user_id,))
        conn.commit()
    keyboard = types.ReplyKeyboardMarkup(row_width=1)
    order_button = types.KeyboardButton('Заказать💰')
    assortment_button = types.KeyboardButton('Ассортимент📕')
    free_button = types.KeyboardButton('Реклама▶️')
    keyboard.add(order_button, assortment_button, free_button)

    bot.send_message(message.chat.id, "🍀 Пожалуйста, выберите вариант:", reply_markup=keyboard)
    

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id in admin_chat_ids:
        keyboard = types.ReplyKeyboardMarkup(row_width=1)
        statistics_button = types.KeyboardButton('Посмотреть статистику 📊')
        send_message_button = types.KeyboardButton('Рассылка✍️')
        menu_button = types.KeyboardButton('Меню📑')
        keyboard.add(statistics_button, send_message_button, menu_button)

        bot.send_message(message.chat.id, "Вы вошли в админ-режим🕵️‍♂️", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")

@bot.message_handler(func=lambda m: m.text == 'Меню📑')
def view_menu(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1)
    order_button = types.KeyboardButton('Заказать💰')
    assortment_button = types.KeyboardButton('Ассортимент📕')
    free_button = types.KeyboardButton('Реклама▶️')
    keyboard.add(order_button, assortment_button, free_button)

    bot.send_message(message.chat.id, "🍀 Пожалуйста, выберите вариант:", reply_markup=keyboard)

def send(message):
    admin_msg = message.text

    conn = sqlite3.connect('users.db')  
    c = conn.cursor()
    
    c.execute("SELECT telegram_user_id FROM users")
    user_ids = c.fetchall()

    for user_id in user_ids:
        try:
            bot.send_message(user_id[0], admin_msg)
            print(f"Message sent to user {user_id[0]}")
        except Exception as e:
            print(f"Failed to send message to user {user_id[0]}. Error: {str(e)}")
            c.execute("DELETE FROM users WHERE telegram_user_id=?", (user_id[0],))
            conn.commit()
            print(f"User {user_id[0]} deleted from the database")

    bot.reply_to(message, "Сообщение отправлено!")

@bot.message_handler(func=lambda m: m.text == 'Рассылка✍️')
def send_message(message):

  bot.send_message(message.chat.id, "Введите сообщение:")
  bot.register_next_step_handler(message, send)

@bot.message_handler(func=lambda message: message.text == 'Посмотреть статистику 📊')
def view_statistics(message):
    total_users = len(admin_chat_ids)

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    total_users_bd = c.fetchone()[0]

    conn.close()
    current_time = datetime.datetime.now()
    uptime = current_time - bot_start_time
    uptime_str = str(uptime).split(".")[0]

    bot.send_message(message.chat.id, f"🕔 Время работы за сессию: {uptime_str}\n\n🔸 Общее количество за сессию: {total_users}\n🔸 Общее количество пользователей: {total_users_bd}")


def process_message(message):
    message_to_send = message.text

    for admin_chat_id in admin_chat_ids:
        bot.send_message(admin_chat_id, message_to_send)

    bot.send_message(message.chat.id, "The message has been sent to all users.")


@bot.message_handler(func=lambda message: message.text == 'Заказать💰')
def order(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=3)
    countries = ['🇧🇻 NO', '🇨🇵 FR', '🇩🇪 DE', '🇨🇿 CZ', '🇫🇮 FI', '🇮🇸 IS', '🇸🇪 SE', '🇱🇻 AT', '🇨🇭 CH']
    for country in countries:
        keyboard.add(types.KeyboardButton(country))

    bot.send_message(message.chat.id, "Пожалуйста, выберите страну:", reply_markup=keyboard)

    bot.register_next_step_handler(message, process_country_selection)


def process_country_selection(message):
    selected_country = message.text

    bot.send_message(message.chat.id, 'Вы выбрали страну: ' + selected_country, reply_markup=types.ReplyKeyboardRemove())

    bot.send_message(message.chat.id, "Пожалуйста, ответьте на первый бесплатный вопрос:")

    bot.register_next_step_handler(message, process_first_free_question, selected_country)


def process_first_free_question(message, selected_country):
    answer1 = message.text

    bot.send_message(message.chat.id, "Пожалуйста, ответьте на второй свободный вопрос:")
    bot.register_next_step_handler(message, process_second_free_question, selected_country, answer1)

order_submissions = {}

def process_second_free_question(message, selected_country, answer1):
    user_id = message.from_user.id
    order_submissions[user_id] = user_id
    
    answer2 = message.text

    notification = f"Новый заказ:\nUsername: @{message.from_user.username}\nСтрана: {selected_country}\nОтвет 1: {answer1}\nОтвет 2: {answer2}"
    for admin_chat_id in admin_chat_ids:
        bot.send_message(admin_chat_id, notification)

    bot.send_message(message.chat.id, "Ваш запрос отправлен. Пожалуйста, дождитесь одобрения.")

    keyboard = types.ReplyKeyboardMarkup(row_width=1)
    order_button = types.KeyboardButton('Заказать💰')
    assortment_button = types.KeyboardButton('Ассортимент📕')
    free_button = types.KeyboardButton('Реклама▶️')
    keyboard.add(order_button, assortment_button, free_button)
    bot.send_message(message.chat.id, "🍀 Пожалуйста, выберите вариант:", reply_markup=keyboard)

    keyboard = types.InlineKeyboardMarkup()
    approve_button = types.InlineKeyboardButton('Утвердить', callback_data='approve' + str(message.chat.id))
    reject_button = types.InlineKeyboardButton('Отклонить', callback_data='reject' + str(message.chat.id))
    keyboard.add(approve_button, reject_button)

    for admin_chat_id in admin_chat_ids:
        bot.send_message(admin_chat_id, "Пожалуйста, выберите действие:", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == 'Ассортимент📕')
def assortment(message):
    services = "Service 1\nService 2\nService 3"
    countries = "🇧🇻 NO, 🇨🇵 FR, 🇩🇪 DE, 🇨🇿 CZ, 🇫🇮 FI, 🇮🇸 IS, 🇸🇪 SE, 🇱🇻 AT, 🇨🇭 CH"
    bot.send_message(message.chat.id, f"Текущие услуги:\n{services}\n\nДоступные страны:\n{countries}")

@bot.message_handler(func=lambda message: message.text == 'Реклама▶️')
def open_url(message):
    url = 'https://t.me/JennaRecruit'
    caption = 'Откройте ссылку и получите рекламу!'
    photo_path = 'reklama.jpg'  # Укажите путь к вашей картинке

    bot.send_chat_action(message.chat.id, 'typing')  # Добавляем "набирает сообщение" для отображения загрузки

    with open(photo_path, 'rb') as photo:
        bot.send_photo(message.chat.id, photo, caption=caption, disable_notification=True)

    bot.send_message(message.chat.id, url, disable_web_page_preview=True)

admin_messages = {}

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = user_ids.get(call.message.chat.id)

    if call.data.startswith('approve'):
        chat_id = call.data[7:]
        print(chat_id)
        bot.send_message(chat_id, "Заказ одобрен.")

        for adm_id in admin_chat_ids:
            user_username = bot.get_chat(chat_id).username
            bot.send_message(adm_id, f"👍 Заказ одобрен.\nusername: @{user_username}")

        admin_message = "Введите комментарий:"
        # Send a message to the administrator asking for their comment
        bot.send_message(call.message.chat.id, admin_message)
        # Store the administrator's chat_id and the associated comment
        admin_messages[call.message.chat.id] = chat_id
    elif call.data.startswith('reject'):
        chat_id = call.data[6:]
        # Extract the chat_id from callback_data
        bot.send_message(chat_id, "Заказ отклонен.")
        for adm_id in admin_chat_ids:
            # Get the username of the admin
            user_username = bot.get_chat(chat_id).username
            # Send the message to the admin
            bot.send_message(adm_id, f"⛔️ Заказ отклонен.\nusername: @{user_username}")
        print(chat_id)
        admin_message = "Введите комментарий:"
        # Send a message to the administrator asking for their comment
        bot.send_message(call.message.chat.id, admin_message)
        # Store the administrator's chat_id and the associated comment
        admin_messages[call.message.chat.id] = chat_id

# Handler for messages from the administrator
@bot.message_handler(func=lambda message: message.chat.id in admin_messages)
def handle_admin_message(message):
    # Retrieve the associated chat_id from the admin_messages dictionary
    chat_id = admin_messages[message.chat.id]
    # Send the administrator's message to the user
    bot.send_message(chat_id, message.text)

# Start the bot
bot.polling()
