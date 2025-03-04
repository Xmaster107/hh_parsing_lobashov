import sqlite3

def create_connection(db_file='vacancies.db'):
    "Создает соединение с базой данных."
    return sqlite3.connect(db_file)

def create_database():
    "Создает таблицу vacancies, если она не существует."
    with create_connection() as conn:
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

def clear_database():
    "Очищает таблицу vacancies."
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM vacancies')
        conn.commit()

def save_vacancies_to_db(vacancies):
    "Сохраняет вакансии в базу данных."
    clear_database()
    with create_connection() as conn:
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

def filter_vacancies(employment, schedule, currency, experience):
    "Фильтрует вакансии по заданным параметрам."
    with create_connection() as conn:
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
        return cursor.fetchall()