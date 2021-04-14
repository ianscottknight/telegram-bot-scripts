import os
import dotenv
import argparse
import requests
from datetime import datetime, timedelta
import time
import pytz
import schedule
from icalevents import icalevents
import subprocess
import urllib3
import random


dotenv.load_dotenv()

BOT_API_KEY = os.environ["BOT_API_KEY"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

DAILY_SCRIPT_TIME = "05:00"

PERSONAL_CALENDAR_URL = os.environ["PERSONAL_CALENDAR_URL"]
WORK_CALENDAR_URL = os.environ["WORK_CALENDAR_URL"]

CALENDAR_URLS = [WORK_CALENDAR_URL, PERSONAL_CALENDAR_URL]

NOTES_SHELL_SCRIPT = "run_notes_script.sh"
NOTES_TODO_TXT = "notes_todo.txt"


parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", action="store_true")

args = parser.parse_args()


def get_tasks_and_calendar_events_string():
    tasks_string = "Tasks:"
    calendar_string = f"Calendar Events:"

    tz = pytz.timezone("US/Central")
    today = datetime.today().astimezone(tz)

    tasks = []
    events = []

    for calendar_url in CALENDAR_URLS:
        events += list(icalevents.events(calendar_url, fix_apple=True))

    for e in events:
        e.start = e.start.astimezone(tz)
        e.end = e.end.astimezone(tz)

    events = sorted(events, key=lambda e: e.start)

    events = [e for e in events if e.start.date() == today.date()]

    filtered_events = []
    for e in events:
        if (
            (e.start.day == today.day)
            and (e.end.day == (today + timedelta(days=1)).day)
            and (e.start.hour == 0)
            and (e.end.hour == 0)
            and (e.start.minute == 0)
            and (e.end.minute == 0)
        ):
            tasks.append(e.summary)
        else:
            filtered_events.append(e)
    events = filtered_events

    if len(events) > 0:
        for e in events:
            start = e.start.strftime("%H:%M")
            end = e.end.strftime("%H:%M")
            calendar_string += (
                f"\n* {start} - {end} {today.tzname()}: {e.summary.replace('+', '%2B')}"
            )
    else:
        calendar_string += "\n<empty>"

    if tasks:
        for task in tasks:
            tasks_string += "\n- " + task
    else:
        tasks_string += "\n<empty>"

    s = tasks_string + "\n\n" + calendar_string

    return s


def get_notes_todo_string():
    subprocess.run(["sh", NOTES_SHELL_SCRIPT])

    with open(NOTES_TODO_TXT, "r") as f:
        notes_todo = [line.strip() for line in f.readlines()]

    # take a random subset of notes
    max_num_notes = 3
    if len(notes_todo) > max_num_notes:
        notes_todo = random.sample(notes_todo, max_num_notes)

    s = "Notes TODO:"

    if notes_todo:
        for note in notes_todo:
            s += "\n* " + note
    else:
        s += "\n<empty>"

    return s


def job():
    date_str = datetime.today().strftime("%Y.%m.%d %a").upper()

    message_text = date_str + "\n"

    s = get_tasks_and_calendar_events_string()
    message_text += "\n" + s + "\n"

    s = get_notes_todo_string()
    message_text += "\n" + s + "\n"

    url = f"https://api.telegram.org/bot{BOT_API_KEY}/sendMessage?chat_id={CHANNEL_ID}&text={message_text}"
    while 1:
        try:
            response = requests.get(url)
            break
        except urllib3.exceptions.MaxRetryError:
            pass

    print(response.text)


schedule.every().day.at(DAILY_SCRIPT_TIME).do(job)

if args.debug:
    job()

while 1:
    schedule.run_pending()
    time.sleep(1)
