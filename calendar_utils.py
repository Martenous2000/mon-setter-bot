"""Lecture des créneaux libres depuis Google Calendar (OAuth refresh token).

Le bot ne propose jamais un créneau au hasard : il lit le vrai agenda pour éviter
de proposer un horaire déjà pris ou hors des heures de disponibilité.
"""

import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

import config

PARIS_OFFSET_SUMMER = timezone(timedelta(hours=2))
PARIS_OFFSET_WINTER = timezone(timedelta(hours=1))


def _paris_tz(dt: datetime) -> timezone:
    """Approximation DST simple : avril-octobre = été, sinon hiver."""
    return PARIS_OFFSET_SUMMER if 3 < dt.month < 11 else PARIS_OFFSET_WINTER


def _get_access_token() -> str:
    data = urllib.parse.urlencode(
        {
            "client_id": config.GOOGLE_CALENDAR_CLIENT_ID,
            "client_secret": config.GOOGLE_CALENDAR_CLIENT_SECRET,
            "refresh_token": config.GOOGLE_CALENDAR_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))["access_token"]


def _fetch_busy_intervals(access_token: str, time_min: datetime, time_max: datetime) -> list[tuple[datetime, datetime]]:
    body = json.dumps(
        {
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "items": [{"id": config.GOOGLE_CALENDAR_ID}],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://www.googleapis.com/calendar/v3/freeBusy",
        data=body,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    busy_raw = payload["calendars"][config.GOOGLE_CALENDAR_ID]["busy"]
    return [
        (datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"]))
        for b in busy_raw
    ]


def _is_within_working_hours(slot_start: datetime, slot_end: datetime) -> bool:
    day_start = slot_start.replace(
        hour=config.WORKDAY_START_HOUR, minute=config.WORKDAY_START_MINUTE, second=0, microsecond=0
    )
    day_end = slot_start.replace(
        hour=config.WORKDAY_END_HOUR, minute=config.WORKDAY_END_MINUTE, second=0, microsecond=0
    )
    lunch_start = slot_start.replace(
        hour=config.LUNCH_BREAK_START_HOUR, minute=config.LUNCH_BREAK_START_MINUTE, second=0, microsecond=0
    )
    lunch_end = slot_start.replace(
        hour=config.LUNCH_BREAK_END_HOUR, minute=config.LUNCH_BREAK_END_MINUTE, second=0, microsecond=0
    )
    if slot_start < day_start or slot_end > day_end:
        return False
    if slot_start < lunch_end and slot_end > lunch_start:
        return False
    return True


def _overlaps_busy(slot_start: datetime, slot_end: datetime, busy: list[tuple[datetime, datetime]]) -> bool:
    return any(slot_start < b_end and slot_end > b_start for b_start, b_end in busy)


def get_next_available_slots(count: int = 2, slot_minutes: int = 30, days_ahead: int = 10) -> list[datetime]:
    """Retourne les N prochains créneaux libres, en respectant les contraintes de config.py."""
    if not (
        config.GOOGLE_CALENDAR_CLIENT_ID
        and config.GOOGLE_CALENDAR_CLIENT_SECRET
        and config.GOOGLE_CALENDAR_REFRESH_TOKEN
        and config.GOOGLE_CALENDAR_ID
    ):
        return []

    access_token = _get_access_token()
    now = datetime.now(timezone.utc)
    time_min = now
    time_max = now + timedelta(days=days_ahead)
    busy = _fetch_busy_intervals(access_token, time_min, time_max)

    tz = _paris_tz(now.astimezone())
    cursor = now.astimezone(tz)
    # arrondi au prochain quart d'heure
    minute_rounding = (15 - cursor.minute % 15) % 15
    cursor = (cursor + timedelta(minutes=minute_rounding)).replace(second=0, microsecond=0)

    found: list[datetime] = []
    limit = cursor + timedelta(days=days_ahead)
    while cursor < limit and len(found) < count:
        slot_end = cursor + timedelta(minutes=slot_minutes)
        if _is_within_working_hours(cursor, slot_end) and not _overlaps_busy(
            cursor.astimezone(timezone.utc), slot_end.astimezone(timezone.utc), busy
        ):
            found.append(cursor)
            cursor += timedelta(hours=4)  # espace les propositions dans la journée/les jours
        else:
            cursor += timedelta(minutes=15)
    return found
