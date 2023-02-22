# Foodgram - Продуктовый помощник
## Стек технологий

[![Python](https://img.shields.io/badge/-Python-464646?style=flat-square&logo=Python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat-square&logo=Django)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat-square&logo=Django%20REST%20Framework)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat-square&logo=PostgreSQL)](https://www.postgresql.org/)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat-square&logo=NGINX)](https://nginx.org/ru/)
[![gunicorn](https://img.shields.io/badge/-gunicorn-464646?style=flat-square&logo=gunicorn)](https://gunicorn.org/)
[![docker](https://img.shields.io/badge/-Docker-464646?style=flat-square&logo=docker)](https://www.docker.com/)
[![Yandex.Cloud](https://img.shields.io/badge/-Yandex.Cloud-464646?style=flat-square&logo=Yandex.Cloud)](https://cloud.yandex.ru/)
## Описание проекта
Это дипломная работа по курсу Я.Практикум.
Сайт для публикации рецептов с возможностью подписки на автора, добавление рецепта в избранное, добавление рецепта в корзину и скачивания списка покупок в формате txt

## Установка проекта локально

1. Клонирование проекта с git
```bash
git@github.com:teacea/foodgram-project-react.git
```
2. Перейти в папку , создать и активировать виртуальное окружение
```bash
cd foodgram-project-react
python -m venv venv
source venv/bin/activate
```
3. Создать в папке infra файл .env по примеру 

4. Перейти в корневую директорию проекта и установить зависимости, выполинть миграции

```bash
cd backend/
pip install -r requirements.txt
python manage.py migrate
```
5. Запустить сервер 

```bash
python manage.py runserver
```
