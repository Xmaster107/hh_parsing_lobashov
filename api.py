import requests

def fetch_vacancies(region, specialty):
    "Получает вакансии из API hh.ru."
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