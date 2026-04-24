from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, date
from clickhouse_driver import Client
import csv

default_args = {
    "owner": "airflow",
    "start_date": datetime(2024, 12, 1),
}

CLICKHOUSE_HOST = "clickhouse"
CLICKHOUSE_DB = "bionic_olap"
CLICKHOUSE_USER = "reports"
CLICKHOUSE_PASSWORD = "reports"

CRM_CSV_PATH = "/opt/airflow/sample_files/crm_clients.csv"
TELEMETRY_CSV_PATH = "/opt/airflow/sample_files/telemetry.csv"

def get_ch_client() -> Client:
    return Client(
        host=CLICKHOUSE_HOST,
        user=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DB,
    )


def init_clickhouse_schema():
    client = get_ch_client()

    client.execute(
        """
        CREATE TABLE IF NOT EXISTS stg_crm_clients (
            client_id       UInt64,
            full_name       String,
            email           String,
            country         String,
            city            String,
            prosthesis_id   UInt64,
            activation_date Date
        )
        ENGINE = MergeTree
        ORDER BY client_id
        """
    )

    client.execute(
        """
        CREATE TABLE IF NOT EXISTS stg_telemetry (
            event_ts        DateTime,
            client_id       UInt64,
            prosthesis_id   UInt64,
            reaction_time_ms Int32,
            battery_level    Int32,
            error_code       Nullable(String)
        )
        ENGINE = MergeTree
        ORDER BY (client_id, event_ts)
        """
    )

    client.execute(
        """
        CREATE TABLE IF NOT EXISTS mart_user_telemetry_daily (
            client_id         UInt64,
            report_date       Date,
            full_name         String,
            email             String,
            country           String,
            city              String,
            prosthesis_id     UInt64,
            activation_date   Date,
            total_events      UInt32,
            avg_reaction_ms   Float64,
            p95_reaction_ms   Float64,
            avg_battery_level Float64,
            errors_count      UInt32,
            last_event_ts     DateTime
        )
        ENGINE = MergeTree
        PARTITION BY toYYYYMM(report_date)
        ORDER BY (client_id, report_date)
        """
    )

def load_crm_staging():
    client = get_ch_client()

    client.execute("TRUNCATE TABLE IF EXISTS stg_crm_clients")

    rows = []
    with open(CRM_CSV_PATH, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            activation_date_raw = row["activation_date"]

            activation_date_obj = date.fromisoformat(activation_date_raw)

            rows.append(
                (
                    int(row["client_id"]),
                    row["full_name"],
                    row["email"],
                    row["country"],
                    row["city"],
                    int(row["prosthesis_id"]),
                    activation_date_obj,
                )
            )

    if rows:
        client.execute(
            """
            INSERT INTO stg_crm_clients (
                client_id, full_name, email, country, city, prosthesis_id, activation_date
            ) VALUES
            """,
            rows,
        )

def load_telemetry_staging():
    client = get_ch_client()

    client.execute("TRUNCATE TABLE IF EXISTS stg_telemetry")

    rows = []
    with open(TELEMETRY_CSV_PATH, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            event_ts_raw = row["event_ts"]

            event_ts_str = event_ts_raw.replace("T", " ")
            event_ts = datetime.fromisoformat(event_ts_str)

            client_id = int(row["client_id"])
            prosthesis_id = int(row["prosthesis_id"])
            reaction_time_ms = int(row["reaction_time_ms"])
            battery_level = int(row["battery_level"])
            error_code = row["error_code"] or None

            rows.append(
                (
                    event_ts,
                    client_id,
                    prosthesis_id,
                    reaction_time_ms,
                    battery_level,
                    error_code,
                )
            )

    if rows:
        client.execute(
            """
            INSERT INTO stg_telemetry (
                event_ts, client_id, prosthesis_id, reaction_time_ms, battery_level, error_code
            ) VALUES
            """,
            rows,
        )

def build_mart_ch():
    client = get_ch_client()

    client.execute("TRUNCATE TABLE IF EXISTS mart_user_telemetry_daily")

    client.execute(
        """
        INSERT INTO mart_user_telemetry_daily (
            client_id,
            report_date,
            full_name,
            email,
            country,
            city,
            prosthesis_id,
            activation_date,
            total_events,
            avg_reaction_ms,
            p95_reaction_ms,
            avg_battery_level,
            errors_count,
            last_event_ts
        )
        SELECT
            t.client_id                                       AS client_id,
            toDate(t.event_ts)                                AS report_date,
            c.full_name                                       AS full_name,
            c.email                                           AS email,
            c.country                                         AS country,
            c.city                                            AS city,
            c.prosthesis_id                                   AS prosthesis_id,
            c.activation_date                                 AS activation_date,
            count()                                           AS total_events,
            avg(t.reaction_time_ms)                           AS avg_reaction_ms,
            quantile(0.95)(t.reaction_time_ms)                AS p95_reaction_ms,
            avg(t.battery_level)                              AS avg_battery_level,
            countIf(t.error_code IS NOT NULL)                 AS errors_count,
            max(t.event_ts)                                   AS last_event_ts
        FROM stg_telemetry t
        INNER JOIN stg_crm_clients c
            ON c.client_id = t.client_id
        GROUP BY
            t.client_id,
            toDate(t.event_ts),
            c.full_name,
            c.email,
            c.country,
            c.city,
            c.prosthesis_id,
            c.activation_date
        """
    )

with DAG(
    dag_id="bionic_user_reports",
    default_args=default_args,
    schedule_interval="0 * * * *",  # раз в час
    catchup=False,
    tags=["bionicpro", "reports"],
) as dag:

    init_clickhouse_schema_task = PythonOperator(
        task_id="init_clickhouse_schema",
        python_callable=init_clickhouse_schema,
    )

    load_crm_staging_task = PythonOperator(
        task_id="load_crm_staging",
        python_callable=load_crm_staging,
    )

    load_telemetry_staging_task = PythonOperator(
        task_id="load_telemetry_staging",
        python_callable=load_telemetry_staging,
    )

    build_mart_ch_task = PythonOperator(
        task_id="build_mart_clickhouse",
        python_callable=build_mart_ch,
    )

    init_clickhouse_schema_task >> [load_crm_staging_task, load_telemetry_staging_task]
    [load_crm_staging_task, load_telemetry_staging_task] >> build_mart_ch_task