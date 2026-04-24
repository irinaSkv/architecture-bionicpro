#!/usr/bin/env python3

import csv
import random
from datetime import datetime, timedelta

ERROR_CODES = [
    'ERR_TIMEOUT',
    'ERR_SIGNAL',
    'ERR_BATTERY',
    'ERR_CONNECTION',
    'ERR_SENSOR',
    None,
]

def get_max_client_id(csv_path):
    max_id = 0
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                client_id = int(row['client_id'])
                if client_id > max_id:
                    max_id = client_id
    except FileNotFoundError:
        pass
    return max_id

def add_client_to_crm(csv_path, client_id, full_name, email, country, city, prosthesis_id, activation_date):
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            client_id,
            full_name,
            email,
            country,
            city,
            prosthesis_id,
            activation_date
        ])

def generate_telemetry_for_client(num_records, client_id, prosthesis_id, csv_path):
    """Генерирует записи телеметрии для конкретного клиента"""
    records = []
    today = datetime.now().date()

    for i in range(num_records):
        days_ago = random.randint(1, 90)
        event_date = today - timedelta(days=days_ago)

        if event_date >= today:
            event_date = today - timedelta(days=random.randint(1, 90))

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

    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'event_ts', 'client_id', 'prosthesis_id', 'reaction_time_ms',
            'battery_level', 'error_code'
        ])
        writer.writerows(records)

def main():
    crm_path = 'airflow/data/crm_clients.csv'
    telemetry_path = 'airflow/data/telemetry.csv'

    max_client_id = get_max_client_id(crm_path)
    new_client_id = max_client_id + 1

    print(f"Max client_id: {max_client_id}")
    print(f"New client_id: {new_client_id}")

    full_name = "Name Lastname"
    email = "test@example.com"
    country = "US"
    city = "New York"
    prosthesis_id = random.randint(100, 999)

    today = datetime.now().date()
    days_ago = random.randint(1, 365)
    activation_date = today - timedelta(days=days_ago)
    if activation_date >= today:
        activation_date = today - timedelta(days=random.randint(1, 365))

    print(f"\nAdd client to {crm_path}...")
    add_client_to_crm(crm_path, new_client_id, full_name, email, country, city, prosthesis_id,
        activation_date.strftime('%Y-%m-%d')
    )
    print(f"✓ Successfully added: client_id={new_client_id}, email={email}")

    print(f"\nGenerate 500 records of telemetry for client_id={new_client_id}...")
    generate_telemetry_for_client(500, new_client_id, prosthesis_id, telemetry_path)
    print(f"✓ Successfully added 500 records of telemetry")

    print("\nReady!")

if __name__ == '__main__':
    main()