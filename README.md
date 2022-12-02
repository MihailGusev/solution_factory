# Solution factory

## Запуск
Проект основан на Django и Celery. В качестве брокера сообщений использовался RabbitMQ
- Установить RabbitMQ
- Установить зависимости из файла *requirements.txt*
- Выполнить миграции с помощью команд
    - `py.exe manage.py makemigrations`
    - `py.exe manage.py migrate`
- Запустить celery worker командой `celery -A solution_factory.celery worker --loglevel=info -P eventlet`
- Запустить celery beat командой `celery -A solution_factory.celery beat --loglevel=info`
- Запустить проект командой `py.exe manage.py runserver`

## Использование
Проект предоставляет 4 эндпоинта для работы:
- api/v1/clients/ позволяет добавлять клиентов (POST)
- api/v1/clients/id позволяет редактировать (PUT) и удалять(DELETE) клиентов
- api/v1/mailings/ позволяет добавлять новые рассылки (POST) и просматривать статистику по всем рассылкам (GET)
- api/v1/mailings/id позволяет редактировать (PUT), удалять (DELETE) и просматривать (GET) статистику по рассылке

## Формат данных
### Клиент
Клиент имеет следующие поля: phone (в формате 7ХХХХХХХХХХ), operator_code, tag, timezone.
Поле tag является не обязательным. 
Пример POST запроса на **api/v1/clients/**:
{
    "phone":"78218173218",
    "operator_code":"123",
    "timezone":"timezone"
}
В ответ должны прийти те же данные с добавлением *id* и *tag*, если он не был указан:
{
    "id": 4,
    "phone": "78218173218",
    "operator_code": "123",
    "tag": null,
    "timezone": "timezone"
}

Редактирование и удаление осуществляется также, но по *id*, полученному из POST-запроса

### Рассылка
Рассылка имеет следующие поля: start_time (дата и время начала рассылки), text (текст рассылки), 
client_operator_code_filter (фильтр клиентов по коду оператора), client_tag_filter (фильтр клиентов по тегу), 
end_time (время, после которого сообщения рассылки должны перестать рассылаться даже если некоторые из них ещё не были доставлены).

Поля фильтров являются не обязательными.
Пример POST запроса на **api/v1/mailings/**:
{
    "start_time":"2022-12-02T16:50:00Z",
    "text":"hello",
    "client_tag_filter":"VIP"
    "end_time":"2028-11-20"
}

В ответ должны прийти те же данные с добавлением *id* и фильтров, если они не были указаны:
{
    "id": 35,
    "start_time": "2022-12-02T16:50:00Z",
    "text": "hello",
    "client_operator_code_filter": null,
    "client_tag_filter":"VIP"
    "end_time": "2028-11-20T00:00:00Z"
}

Редактирование и удаление осуществляется также, но по *id*, полученному из POST-запроса 
(редактирование рассылки невозможно, если она уже была начата).

Статистика, предоставляемая по адресу api/v1/mailings/ с помощью метода GET 
включает в себя общее количество рассылок, а также информацию о количестве сообщений и их статусах:
{
    "message_data": [
        {
            "status": "FAILED",
            "count": 1
        },
        {
            "status": "Pending",
            "count": 2
        }
    ],
    "total_mailings": 34
}
По одной рассылке данные приходят в том же формате, но уже без информации о количестве рассылок