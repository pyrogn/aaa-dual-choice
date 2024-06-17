# Dual Choice (WIP)

Данный проект является частью решения в рамках проекта [Автоулучшение фото](https://github.com/pyrogn/aaa-image-enhancement).

## Цель

- Узнать и посчитать у пользователей предпочитаемый вариант улучшения фото
- Потренироваться в тестах

## Видеодемонстрация

https://github.com/pyrogn/aaa-dual-choice/assets/60060559/d64a314c-48ae-4465-ad53-6c6c9f7625b3

## Установка

- Установить Rye, just
- Иметь запущенный docker engine
- `rye sync`

## Запуск

- `just up-dev` и смотреть на http://localhost:8001
- `just up-prod` и смотреть на http://localhost
- `just down` для выключения
- `just analysis` получить результаты исследования

## Тесты

Данный проект обложен тестами (для обучения):
- `just test` запускает юнит тесты (с моками для redis, postgres)
- `just test-db-redis` запускает тесты над настоящими redis, postgres
- `just test-browser` запускает тесты над фронтендом через seleniumbase
- `just test-full` запускает все тесты

## Данные

Написать:
- Как положить фото
- Как получить результаты

## TODO

- [x] Better app
- [x] How to change passwords
- [x] Better script to calculate statistics (how to run)
- [x] Better justfile with up and down, test, clean db
- [x] Make basic and full test suite
