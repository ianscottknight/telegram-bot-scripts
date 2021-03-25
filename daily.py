import os
import dotenv
import requests
from datetime import datetime
import time
import pytz
import schedule
from icalevents import icalevents


dotenv.load_dotenv()

BOT_API_KEY = os.environ["BOT_API_KEY"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

PERSONAL_CALENDAR_URL = os.environ["PERSONAL_CALENDAR_URL"]
WORK_CALENDAR_URL = os.environ["WORK_CALENDAR_URL"]

DEFAULT_TASKS_TXT = "default_tasks.txt"
with open(DEFAULT_TASKS_TXT, "r") as f:
    DAILY_TASKS = [line.strip() for line in f.readlines()]


def get_tasks_string():
    s = "Tasks:"

    if DAILY_TASKS:
        for task in DAILY_TASKS:
            s += "\n- " + task
    else:
        s += "\n<empty>"

    return s


def get_calendar_events_string(calendar_url, calendar_name):
    s = f"{calendar_name}:"

    tz = pytz.timezone("US/Central")
    today = datetime.today().astimezone(tz)

    events = icalevents.events(calendar_url, fix_apple=True)
    events = sorted(events, key=lambda e: e.start)
    for e in events:
        e.start = e.start.astimezone(tz)
        e.end = e.end.astimezone(tz)
    events = [e for e in events if e.start.date() == today.date()]

    if len(events) > 0:
        for e in events:
            start = e.start.strftime("%H:%M")
            end = e.end.strftime("%H:%M")
            s += (
                f"\n* {start} - {end} {today.tzname()}: {e.summary.replace('+', '%2B')}"
            )
    else:
        s += "\n<empty>"

    return s


def job():
    date_str = datetime.today().strftime("%Y.%m.%d %a").upper()

    message_text = date_str + "\n"

    s = get_tasks_string()
    message_text += "\n" + s + "\n"

    s = get_calendar_events_string(WORK_CALENDAR_URL, "Work Calendar")
    message_text += "\n" + s + "\n"

    s = get_calendar_events_string(PERSONAL_CALENDAR_URL, "Personal Calendar")
    message_text += "\n" + s + "\n"

    url = f"https://api.telegram.org/bot{BOT_API_KEY}/sendMessage?chat_id={CHANNEL_ID}&text={message_text}"
    response = requests.get(url)

    print(response.text)


schedule.every().day.at("05:00").do(job)

while 1:
    schedule.run_pending()
    time.sleep(1)
