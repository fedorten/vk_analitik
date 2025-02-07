import grequests
from datetime import datetime
import time

ACCESS_TOKEN = 'vk1.a.xF9HpB-2TxcGAuKweYFV7YZTNQCO6_GoiHmaAxiOMtyNM0X9lO1cMcst0NXjgqTauhB6xde8VeLgHHMQzNK_pZS5GIQ-asbMIbKGn2qmoSo2ULDNTB-aQxZ4qLaTVtshsE1I407ngQ0AYRada5NR-qbF1Op4Z3pUi8sjXoR68aJFWt8L9OLwXQ_L8fcV_bkhMwswmkobxxai2od-C_lI_w'
API_VERSION = '5.131'

def make_api_request(method, params):
    """Универсальная функция для асинхронных запросов к API."""
    url = f'https://api.vk.com/method/{method}'
    params.update({'access_token': ACCESS_TOKEN, 'v': API_VERSION})
    return grequests.get(url, params=params)

def search_groups(query, count=10):
    """Поиск групп по ключевым словам."""
    response = grequests.map([make_api_request('groups.search', {'q': query, 'count': count})])[0]
    return response.json().get('response', {}).get('items', [])

def get_group_info(group_id):
    """Получение информации о группе."""
    response = grequests.map([make_api_request('groups.getById', {'group_id': group_id, 'fields': 'description,members_count'})])[0]
    return response.json().get('response', [{}])[0]

def get_group_members(group_id, count=1000):
    """Получение участников группы."""
    response = grequests.map([make_api_request('groups.getMembers', {'group_id': group_id, 'fields': 'bdate,sex', 'count': count})])[0]
    return response.json().get('response', {}).get('items', [])

def calculate_age(bdate):
    """Расчет возраста по дате рождения."""
    if not bdate or len(bdate.split('.')) < 3:
        return None
    day, month, year = map(int, bdate.split('.'))
    today = datetime.today()
    return today.year - year - ((today.month, today.day) < (month, day))

def analyze_members(members):
    """Анализ участников группы: пол и возраст."""
    sex_count = {'female': 0, 'male': 0}
    ages = []

    for member in members:
        if 'sex' in member:
            if member['sex'] == 1:  # Женщины
                sex_count['female'] += 1
            elif member['sex'] == 2:  # Мужчины
                sex_count['male'] += 1

        if 'bdate' in member:
            age = calculate_age(member['bdate'])
            if age is not None:
                ages.append(age)

    # Расчет процентов
    total = sex_count['female'] + sex_count['male']
    female_percent = (sex_count['female'] / total * 100) if total > 0 else 0
    male_percent = (sex_count['male'] / total * 100) if total > 0 else 0

    # Расчет среднего возраста
    avg_age = sum(ages) / len(ages) if ages else None

    return female_percent, male_percent, avg_age

def main():
    query = input("Введите ключевые слова для поиска групп: ")
    groups = search_groups(query, count=5)

    for group in groups:
        group_id = group['id']
        group_name = group['name']
        print(f"\nГруппа: {group_name} (ID: {group_id})")

        # Получаем информацию о группе
        group_info = get_group_info(group_id)
        description = group_info.get('description', 'Описание отсутствует')
        members_count = group_info.get('members_count', 'Неизвестно')
        # print(f"Описание: {description}")
        print(f"Участников: {members_count}")

        # Получаем участников группы
        members = get_group_members(group_id, count=100)
        if not members:
            print("Группа скрывает список участников. Невозможно получить данные.")
            continue

        # Анализ участников
        female_percent, male_percent, avg_age = analyze_members(members)

        # Вывод результатов
        print(f"Распределение пола подписчиков:")
        print(f"  Женщины: {female_percent:.1f}%")
        print(f"  Мужчины: {male_percent:.1f}%")

        if avg_age is not None:
            print(f"Средний возраст участников: {avg_age:.1f} лет")
        else:
            print("Недостаточно данных для расчета среднего возраста.")

        # Задержка между запросами
        time.sleep(0.5)

if __name__ == '__main__':
    main()
