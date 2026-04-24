from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
from fastapi import Query
from clickhouse_driver import Client
import os
import math
from datetime import date, timedelta


from schemas import ReportResponse
from keycloak_auth import verify_token, get_user_info

app = FastAPI(title="Reports API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Credentials": "true",
        }
    )

security = HTTPBearer()

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "reports-realm")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "reports-api")

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "9000"))
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DB", "bionic_olap")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "reports")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "reports")


def get_clickhouse_client():
    client = Client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        user=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DB,
    )
    try:
        yield client
    finally:
        client.disconnect()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No credentials provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_info = await verify_token(token)
    if not token_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_info = await get_user_info(token)
    if not user_info:
        user_info = {
            "preferred_username": token_info.get("username"),
            "sub": token_info.get("sub")
        }

    return user_info


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/reports", response_model=ReportResponse)
async def get_user_report(
    current_user: dict = Depends(get_current_user),
    ch: Client = Depends(get_clickhouse_client),
    from_date: Optional[date] = Query(None, description="Начало периода (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="Конец периода (YYYY-MM-DD)"),
):
    email = (
        current_user.get("email")
        or current_user.get("preferred_username")
        or current_user.get("sub")
    )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to identify user (no email/username in token)",
        )

    max_rows = ch.execute("SELECT max(report_date) FROM mart_user_telemetry_daily")
    max_report_date = max_rows[0][0]

    if max_report_date is None:
        return ReportResponse(
            username=email,
            total_usage=0,
            active_sessions=0,
            last_activity=None,
            report_data={},
        )

    if to_date is None:
        to_date = max_report_date

    if from_date is None:
        from_candidate = to_date - timedelta(days=6)
        from_date = from_candidate

    if from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="from_date must be less than or equal to to_date",
        )

    if to_date > max_report_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Data for the requested period is not fully available yet. "
                f"Max available date is {max_report_date.isoformat()}."
            ),
        )

    email_search = email
    if "@" not in email:
        email_search = f"{email}@%"

    query = """
        SELECT
            any(client_id)                   AS client_id,
            any(full_name)                   AS full_name,
            any(country)                     AS country,
            any(city)                        AS city,
            any(prosthesis_id)               AS prosthesis_id,
            sum(total_events)                AS total_events,
            avg(avg_reaction_ms)             AS avg_reaction_ms,
            quantile(0.95)(p95_reaction_ms)  AS p95_reaction_ms,
            avg(avg_battery_level)           AS avg_battery_level,
            sum(errors_count)                AS errors_count,
            max(last_event_ts)               AS last_event_ts
        FROM mart_user_telemetry_daily
        WHERE (email = %(email)s OR email LIKE %(email_search)s)
          AND report_date BETWEEN %(from_date)s AND %(to_date)s
    """

    rows = ch.execute(
        query,
        {
            "email": email,
            "email_search": email_search,
            "from_date": from_date,
            "to_date": to_date,
        },
    )

    if not rows or rows[0][0] is None:
        return ReportResponse(
            username=email,
            total_usage=0,
            active_sessions=0,
            last_activity=None,
            report_data={
                "from_date": from_date.isoformat(),
                "to_date": to_date.isoformat(),
                "message": "No data for this period",
            },
        )

    (
        client_id,
        full_name,
        country,
        city,
        prosthesis_id,
        total_events,
        avg_reaction_ms,
        p95_reaction_ms,
        avg_battery_level,
        errors_count,
        last_event_ts,
    ) = rows[0]

    def safe_float(value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            if math.isnan(value) or math.isinf(value):
                return None
            return float(value)
        return value

    return ReportResponse(
        username=email,
        total_usage=int(total_events or 0),
        active_sessions=int(errors_count or 0),
        last_activity=last_event_ts.isoformat() if last_event_ts else None,
        report_data={
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "client_id": client_id,
            "full_name": full_name,
            "email": email,
            "country": country,
            "city": city,
            "prosthesis_id": prosthesis_id,
            "total_events": total_events,
            "avg_reaction_ms": safe_float(avg_reaction_ms),
            "p95_reaction_ms": safe_float(p95_reaction_ms),
            "avg_battery_level": safe_float(avg_battery_level),
            "errors_count": errors_count,
            "last_event_ts": last_event_ts.isoformat() if last_event_ts else None,
        },
    )


@app.get("/")
async def root():
    return {
        "message": "Reports API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "reports": "/reports"
        }
    }