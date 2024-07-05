import sqlite3
import requests
import telebot
from telebot import types
from threading import Thread, Event


# Функция для создания базы данных
def create_database():
    conn = sqlite3.connect('vacancies.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vacancies (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            salary_from INTEGER,
            salary_to INTEGER,
            salary_currency TEXT,
            experience TEXT,
            employment TEXT,
            schedule TEXT,
            url TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()


# Функция для очистки базы данных
def clear_database():
    conn = sqlite3.connect('vacancies.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM vacancies')
    conn.commit()
    conn.close()


# Функция для сохранения вакансий в базу данных
def save_vacancies_to_db(vacancies):
    clear_database()  # Очистка базы данных перед сохранением новых данных
    conn = sqlite3.connect('vacancies.db')
    cursor = conn.cursor()
    for vacancy in vacancies:
        try:
            cursor.execute('''
                INSERT INTO vacancies (id, name, salary_from, salary_to, salary_currency, experience, employment, schedule, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vacancy['id'],
                vacancy['name'],
                vacancy.get('salary', {}).get('from'),
                vacancy.get('salary', {}).get('to'),
                vacancy.get('salary', {}).get('currency'),
                vacancy.get('experience', {}).get('name'),
                vacancy.get('employment', {}).get('name'),
                vacancy.get('schedule', {}).get('name'),
                vacancy['alternate_url']
            ))
        except sqlite3.IntegrityError:
            continue
    conn.commit()
    conn.close()


# Функция для фильтрации вакансий и возвращения их в виде строки
def filter_vacancies(employment, schedule, currency, experience):
    conn = sqlite3.connect('vacancies.db')
    cursor = conn.cursor()
    query = 'SELECT * FROM vacancies WHERE 1=1'
    params = []

    if employment.lower() != 'free':
        query += ' AND employment = ?'
        params.append(employment)

    if schedule.lower() != 'free':
        query += ' AND schedule = ?'
        params.append(schedule)

    if currency.lower() != 'free':
        query += ' AND salary_currency = ?'
        params.append(currency)

    if experience.lower() != 'free':
        query += ' AND experience = ?'
        params.append(experience)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return rows


# Функция для получения вакансий из API
def fetch_vacancies(region, specialty):
    url = 'https://api.hh.ru/vacancies'
    params = {
        'text': specialty,
        'area': region,
        'search_field': 'name',
        'only_with_salary': True,
        'per_page': 100
    }

    vacancies = []
    page = 0
    while True:
        params['page'] = page
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        vacancies.extend(data['items'])
        if page >= data['pages'] - 1:
            break
        page += 1

    return vacancies


# Инициализация бота
bot = telebot.TeleBot("7323047403:AAHIqyjWfhFbHAf5eStyqfRRd9ilvNNVm1g")

# Инициализация словаря данных пользователя
user_data = {}

stop_event = Event()


def send_main_menu(chat_id):
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
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("Нет опыта"),
               types.KeyboardButton("От 1 года до 3 лет"),
               types.KeyboardButton("От 3 до 6 лет"),
               types.KeyboardButton("Более 6 лет"),
               types.KeyboardButton("Free"))
    bot.send_message(chat_id, "Выберите опыт работы:", reply_markup=markup)


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    send_main_menu(chat_id)


@bot.message_handler(func=lambda message: True)
def message_handler(message):
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
