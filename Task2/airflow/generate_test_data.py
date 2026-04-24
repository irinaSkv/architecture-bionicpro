#!/usr/bin/env python3

import csv
import random
from datetime import datetime, timedelta
import os

COUNTRIES_CITIES = {
    'RU': ['Moscow', 'SPB', 'Novosibirsk', 'Ekaterinburg', 'Kazan'],
    'US': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'],
    'GB': ['London', 'Manchester', 'Birmingham', 'Glasgow', 'Liverpool'],
    'FR': ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice'],
    'IT': ['Rome', 'Milan', 'Naples', 'Turin', 'Palermo'],
    'DE': ['Berlin', 'Munich', 'Hamburg', 'Frankfurt', 'Cologne'],
    'ES': ['Madrid', 'Barcelona', 'Valencia', 'Seville', 'Zaragoza'],
}

ERROR_CODES = [
    'ERR_TIMEOUT',
    'ERR_SIGNAL',
    'ERR_BATTERY',
    'ERR_CONNECTION',
    'ERR_SENSOR',
    None,
]

FIRST_NAMES = [
    'Иван', 'Петр', 'Сергей', 'Никита', 'Михаил', 'Федор',  'Александр', 'Андрей' 'Дмитрий',
    'Анна', 'Татьяна', 'Наталья', 'Надежда', 'Мария', 'Елена', 'Виктория', 'Ольга', 'Ирина',
    'David', 'John', 'James', 'Michael', 'Robert', 'Tom', 'William', 'Richard', 'Victor',
    'Lisa', 'Sarah', 'Michelle', 'Emily', 'Jessica', 'Marta', 'Jennifer', 'Amy', 'Michelle', 'Tiffany',
    'Andreas', 'Hans', 'Wolfgang', 'Klaus', 'Michael', 'Wolfgang', 'Thomas', 'Stefan', 'Bob',
    'Nicole', 'Anna', 'Andrea', 'Maria', 'Sabine', 'Susanne',
]

LAST_NAMES = [
    'Иванов', 'Петров', 'Сидоров', 'Чижиков', 'Кузнецов', 'Попов', 'Лобов',
    'Лебедев', 'Баринов', 'Новиков', 'Павлов', 'Волков', 'Бранкин',
    'Garcia', 'Smith', 'Williams', 'Jones', 'Brown', 'Johnson', 'Miller',
    'Wilson', 'Davis', 'Martinez', 'Hernandez', 'Rodriguez', 'Lopez',
    'Müller', 'Weber', 'Meyer', 'Schmidt', 'Fischer', 'Schneider', 'Wagner',
    'Richter', 'Becker', 'Schulz', 'Koch', 'Hoffmann', 'Schafer', 'Bauer',
]


def generate_email(first_name, last_name, country):
    domains = {
        'RU': ['mail.ru', 'yandex.ru', 'gmail.com'],
        'DE': ['gmail.com', 'web.de', 'gmx.de'],
        'US': ['gmail.com', 'yahoo.com', 'outlook.com'],
        'FR': ['gmail.com', 'orange.fr', 'free.fr'],
        'IT': ['gmail.com', 'libero.it', 'yahoo.it'],
        'ES': ['gmail.com', 'yahoo.es', 'hotmail.es'],
        'GB': ['gmail.com', 'yahoo.co.uk', 'outlook.com'],
    }

    domain = random.choice(domains.get(country, ['gmail.com']))
    name_part = f"{first_name.lower()}.{last_name.lower()}"
    number = random.randint(1, 999)
    return f"{name_part}{number}@{domain}"


def generate_crm_clients(num_records):
    records = []
    client_ids = set()

    while len(client_ids) < num_records:
        client_ids.add(random.randint(1, 100000))

    client_ids = sorted(list(client_ids))

    today = datetime.now().date()

    for i, client_id in enumerate(client_ids):
        country = random.choice(list(COUNTRIES_CITIES.keys()))
        city = random.choice(COUNTRIES_CITIES[country])

        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"

        email = generate_email(first_name, last_name, country)

        prosthesis_id = random.randint(100, 999)

        days_ago = random.randint(1, 365)
        activation_date = today - timedelta(days=days_ago)
        if activation_date >= today:
            activation_date = today - timedelta(days=random.randint(1, 365))

        records.append({
            'client_id': client_id,
            'full_name': full_name,
            'email': email,
            'country': country,
            'city': city,
            'prosthesis_id': prosthesis_id,
            'activation_date': activation_date.strftime('%Y-%m-%d'),
        })

    return records


def generate_telemetry(num_records, client_ids):
    records = []

    today = datetime.now().date()

    for i in range(num_records):
        client_id = random.choice(client_ids)

        prosthesis_id = random.randint(100, 999)

        days_ago = random.randint(1, 30)
        event_date = today - timedelta(days=days_ago)
        if event_date >= today:
            event_date = today - timedelta(days=random.randint(1, 30))

        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        event_ts = datetime.combine(event_date, datetime.min.time().replace(
            hour=hour, minute=minute, second=second
        ))

        reaction_time_ms = random.randint(50, 200)

        battery_level = random.randint(20, 100)

        error_code = random.choice(ERROR_CODES) if random.random() < 0.2 else None

        records.append({
            'event_ts': event_ts.strftime('%Y-%m-%dT%H:%M:%S'),
            'client_id': client_id,
            'prosthesis_id': prosthesis_id,
            'reaction_time_ms': reaction_time_ms,
            'battery_level': battery_level,
            'error_code': error_code if error_code else '',
        })

    return records


def main():
    num_crm = random.randint(200, 1000)
    num_telemetry = random.randint(500, 1000)

    crm_records = generate_crm_clients(num_crm)

    client_ids = [r['client_id'] for r in crm_records]

    telemetry_records = generate_telemetry(num_telemetry, client_ids)

    data_dir = 'airflow/data'
    os.makedirs(data_dir, exist_ok=True)

    crm_path = os.path.join(data_dir, 'crm_clients.csv')
    with open(crm_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'client_id', 'full_name', 'email', 'country', 'city',
            'prosthesis_id', 'activation_date'
        ])
        writer.writeheader()
        writer.writerows(crm_records)

    telemetry_path = os.path.join(data_dir, 'telemetry.csv')
    with open(telemetry_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'event_ts', 'client_id', 'prosthesis_id', 'reaction_time_ms',
            'battery_level', 'error_code'
        ])
        writer.writeheader()
        writer.writerows(telemetry_records)


if __name__ == '__main__':
    main()