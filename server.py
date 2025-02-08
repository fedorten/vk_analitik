from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import aiohttp
import asyncio
import datetime

ACCESS_TOKEN = 'vk1.a.VqYGmQ8bRMMeyjafQqxj6t9Wo07zPRmaPqhv9WrzorFSISODa4cfjIslfJ51IXm_Qeby-bqbW69uE5yr_cjaNIAQSNmWkM0GrBStNwH5_ED4eB4_L6HmCyYdDucINrpNAIww89BSNNmzZ70wCySvOOWa7RLF1yjek3j6X6QjXG9ZqLeYD8C7tdDJ-i0qdRNca_eOe854bsV595aNqXp9Dw'
API_VERSION = '5.131'

app = FastAPI()

# Разрешаем фронту делать запросы к серверу
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def make_api_request(method, params):
    """Асинхронный запрос к API VK."""
    url = f'https://api.vk.com/method/{method}'
    params.update({'access_token': ACCESS_TOKEN, 'v': API_VERSION})
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            return await response.json()

async def search_groups(query, count=5, offset=0):
    """Поиск групп по ключевым словам."""
    await asyncio.sleep(0.34)  # Задержка для соблюдения лимита запросов
    response = await make_api_request('groups.search', {'q': query, 'count': count, 'offset': offset})
    return response.get('response', {}).get('items', [])

async def get_group_info(group_id):
    """Получение информации о группе."""
    await asyncio.sleep(0.34)  # Задержка для соблюдения лимита запросов (3 запроса в секунду)
    response = await make_api_request('groups.getById', {'group_id': group_id, 'fields': 'description,members_count'})
    return response.get('response', [{}])[0]

async def get_group_members(group_id, count=100):
    """Получение списка участников группы."""
    await asyncio.sleep(0.34)  # Задержка для соблюдения лимита запросов (3 запроса в секунду)
    response = await make_api_request('groups.getMembers', {'group_id': group_id, 'fields': 'bdate,sex', 'count': count})
    return response.get('response', {}).get('items', [])

def calculate_age(bdate):
    """Расчет возраста по дате рождения."""
    if not bdate or len(bdate.split('.')) < 3:
        return None
    day, month, year = map(int, bdate.split('.'))
    today = datetime.date.today()
    return today.year - year - ((today.month, today.day) < (month, day))

def analyze_members(members):
    """Анализ подписчиков: пол и возраст."""
    sex_count = {'female': 0, 'male': 0}
    ages = []

    for member in members:
        if 'sex' in member:
            if member['sex'] == 1:
                sex_count['female'] += 1
            elif member['sex'] == 2:
                sex_count['male'] += 1

        if 'bdate' in member:
            age = calculate_age(member['bdate'])
            if age is not None:
                ages.append(age)

    total = sex_count['female'] + sex_count['male']
    female_percent = (sex_count['female'] / total * 100) if total > 0 else 0
    male_percent = (sex_count['male'] / total * 100) if total > 0 else 0
    avg_age = sum(ages) / len(ages) if ages else None

    return female_percent, male_percent, avg_age

@app.get("/")
def read_root():
    return FileResponse("index.html")

@app.get("/search")
async def search_vk_groups(
    q: str = Query(..., description="Поиск групп по ключевому слову"),
    offset: int = Query(0, description="Смещение для пагинации")
):
    """Запрос от фронта -> Поиск групп -> Анализ -> Отправка данных обратно"""
    groups = await search_groups(q, count=5, offset=offset)  # Передаем offset в search_groups
    results = []

    for group in groups:
        group_id = group['id']
        group_info = await get_group_info(group_id)
        members = await get_group_members(group_id, count=100)

        if not members:
            continue

        female_percent, male_percent, avg_age = analyze_members(members)

        results.append({
            "group_id": group_id,
            "name": group['name'],
            "members_count": group_info.get('members_count', 'Неизвестно'),
            "female_percent": female_percent,
            "male_percent": male_percent,
            "avg_age": avg_age
        })
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
