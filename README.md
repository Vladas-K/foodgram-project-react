# Foodgram -продуктовый помощник.


## **Описание проекта**

Этот сервис предлагает удобный способ обмена рецептами и планирования покупок продуктов. Авторизированные пользователи могут публиковать свои рецепты, подписываться на других пользователей и добавлять понравившиеся рецепты в список «Избранное». Перед походом в магазин можно скачать список продуктов, необходимых для приготовления выбранных блюд. Для неавторизированных пользователей доступен только просмотр рецептов и страниц авторов.

### Проект находится по адресу: 
https://vkitty.hopto.org/

### Email:
v25057777@gmail.com
### Password:
diana2305


## **Стэк технологий**

* Python 3.9
* Django 3.2.3
* djangorestframework 3.12.4
* djoser 2.1.0
* webcolors 1.11.1
* gunicorn 20.1.0
* psycopg2-binary 2.9.6
* pytest-django 4.4.0
* pytest-pythonpath 0.7.3
* pytest 6.2.4
* PyYAML 6.0
* python-dotenv 1.0.0

## Локальный запуск проекта

Клонировать репозиторий и перейти в него в командной строке:

```bash
git clone ...
cd foodgram-project-react
```

Cоздать и активировать виртуальное окружение, установить зависимости:

```bash
python3 -m venv venv
source venv/scripts/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

Установить [docker compose](https://www.docker.com/) на свой компьютер.

Запустить проект через docker-compose:

```bash
docker compose -f docker-compose.yml up --build -d
```

Выполнить миграции:

```bash
docker compose -f docker-compose.yml exec backend python manage.py migrate
```

Собрать статику:

```bash
docker compose -f docker-compose.yml exec backend python manage.py collectstatic
```


## Настройка CI/CD

* Файл workflow
```
foodgram/.github/workflows/main.yml
```

* Добавить секреты
```
DOCKER_PASSWORD - пароль от аккаунта DockerHub
DOCKER_USERNAME - логин DockerHub
HOST - IP адресс сервера
USER - логин на сервере
SSH_KEY - SSH ключ
SSH_PASSPHRASE - пароль от сервера

```

## Автор
Владас Куодис

### Login:
admin
### Password:
diana2305
