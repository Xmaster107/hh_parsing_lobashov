import telebot
from telebot import types
from threading import Thread, Event
from database import create_database, save_vacancies_to_db, filter_vacancies
from api import fetch_vacancies

# Инициализация бота
bot = telebot.TeleBot("7323047403:AAHIqyjWfhFbHAf5eStyqfRRd9ilvNNVm1g")

# Инициализация словаря данных пользователя
user_data = {}
stop_event = Event()

def send_main_menu(chat_id):
    "Отправляет главное меню."
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("Установить регион"),
               types.KeyboardButton("Установить специальность"),
               types.KeyboardButton("Установить тип занятости"),
               types.KeyboardButton("Установить график работы"),
               types.KeyboardButton("Установить валюту зарплаты"),
               types.KeyboardButton("Установить опыт"),
               types.KeyboardButton("Искать вакансии"),
               types.KeyboardButton("Стоп"))
    bot.send_message(chat_id, "Пожалуйста, выберите:", reply_markup=markup)

def send_experience_menu(chat_id):
    "Отправляет меню выбора опыта."
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("Нет опыта"),
               types.KeyboardButton("От 1 года до 3 лет"),
               types.KeyboardButton("От 3 до 6 лет"),
               types.KeyboardButton("Более 6 лет"),
               types.KeyboardButton("Free"))
    bot.send_message(chat_id, "Выберите опыт работы:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    "Обработчик команды /start."
    chat_id = message.chat.id
    user_data[chat_id] = {}
    send_main_menu(chat_id)

@bot.message_handler(func=lambda message: True)
def message_handler(message):
    "Обработчик сообщений."
    chat_id = message.chat.id
    text = message.text.lower()

    if chat_id not in user_data:
        user_data[chat_id] = {}

    if text == 'установить регион':
        user_data[chat_id]['filter'] = 'region'
        bot.send_message(chat_id, "Введите регион (например, 1 для Москвы):")
    elif text == 'установить специальность':
        user_data[chat_id]['filter'] = 'specialty'
        bot.send_message(chat_id, "Введите специальность (например, менеджер по работе с клиентами):")
    elif text == 'установить тип занятости':
        user_data[chat_id]['filter'] = 'employment'
        bot.send_message(chat_id, "Введите тип занятости (или 'Free' для пропуска):")
    elif text == 'установить график работы':
        user_data[chat_id]['filter'] = 'schedule'
        bot.send_message(chat_id, "Введите график работы (или 'Free' для пропуска):")
    elif text == 'установить валюту зарплаты':
        user_data[chat_id]['filter'] = 'currency'
        bot.send_message(chat_id, "Введите валюту зарплаты (или 'Free' для пропуска):")
    elif text == 'установить опыт':
        user_data[chat_id]['filter'] = 'experience'
        send_experience_menu(chat_id)
    elif text == 'искать вакансии':
        stop_event.clear()
        region = user_data[chat_id].get('region', '1')
        specialty = user_data[chat_id].get('specialty', 'менеджер по работе с клиентами')
        employment = user_data[chat_id].get('employment', 'Free')
        schedule = user_data[chat_id].get('schedule', 'Free')
        currency = user_data[chat_id].get('currency', 'Free')
        experience = user_data[chat_id].get('experience', 'Free')

        vacancies = fetch_vacancies(region, specialty)
        save_vacancies_to_db(vacancies)
        filtered_vacancies = filter_vacancies(employment, schedule, currency, experience)

        def send_vacancies():
            if filtered_vacancies:
                for vacancy in filtered_vacancies:
                    if stop_event.is_set():
                        break
                    vacancy_str = (f"ID: {vacancy[0]}\n"
                                   f"Название: {vacancy[1]}\n"
                                   f"Зарплата от: {vacancy[2]}\n"
                                   f"Зарплата до: {vacancy[3]}\n"
                                   f"Валюта зарплаты: {vacancy[4]}\n"
                                   f"Опыт: {vacancy[5]}\n"
                                   f"Тип занятости: {vacancy[6]}\n"
                                   f"График работы: {vacancy[7]}\n"
                                   f"URL: {vacancy[8]}\n"
                                   f"{'-' * 40}\n")
                    bot.send_message(chat_id, vacancy_str)
            else:
                bot.send_message(chat_id, "Нет вакансий с указанными параметрами.")
            send_main_menu(chat_id)

        Thread(target=send_vacancies).start()
    elif text == 'стоп':
        stop_event.set()
        user_data.pop(chat_id, None)
        bot.send_message(chat_id, "Процесс остановлен. Для нового поиска используйте /start.")
        send_main_menu(chat_id)
    else:
        filter_type = user_data[chat_id].get('filter', None)
        if filter_type:
            user_data[chat_id][filter_type] = message.text
            bot.send_message(chat_id, f"{filter_type.capitalize()} установлено: {message.text}")
            send_main_menu(chat_id)

if __name__ == "__main__":
    create_database()
    bot.polling()