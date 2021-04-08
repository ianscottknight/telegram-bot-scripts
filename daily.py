import os
import dotenv
import argparse
import requests
from datetime import datetime
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

DEFAULT_TASKS_TXT = "default_tasks.txt"

WORK_CALENDAR_URL = os.environ["WORK_CALENDAR_URL"]
PERSONAL_CALENDAR_URL = os.environ["PERSONAL_CALENDAR_URL"]

NOTES_SHELL_SCRIPT = "run_notes_script.sh"
NOTES_TODO_TXT = "notes_todo.txt"


parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", action="store_true")

args = parser.parse_args()


def get_tasks_string():
    with open(DEFAULT_TASKS_TXT, "r") as f:
        daily_tasks = [line.strip() for line in f.readlines()]

    s = "Tasks:"

    if daily_tasks:
        for task in daily_tasks:
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

    s = get_tasks_string()
    message_text += "\n" + s + "\n"

    s = get_calendar_events_string(WORK_CALENDAR_URL, "Work Calendar")
    message_text += "\n" + s + "\n"

    s = get_calendar_events_string(PERSONAL_CALENDAR_URL, "Personal Calendar")
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
