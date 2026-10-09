"""Выбор поговорки из сборника Даля.

  python pick.py <момент> [-n N]   N случайных поговорок для момента работы (по умолчанию 3)
  python pick.py day [ГГГГ-ММ-ДД]  записи Месяцеслова на дату (по умолчанию сегодня)
  python pick.py list              список моментов

Недавно выданные поговорки и записи Месяцеслова запоминаются во временном файле
и не повторяются. Если на день записи нет, выдаются поговорки к началу работы.
"""
import datetime
import json
import pathlib
import random
import sys
import tempfile

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
RECENT = pathlib.Path(tempfile.gettempdir()) / "dalnomer-recent.json"
RECENT_MAX = 300


def load_recent():
    try:
        return json.loads(RECENT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def save_recent(items):
    try:
        RECENT.write_text(json.dumps(items[-RECENT_MAX:], ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def moments():
    return sorted(p.stem for p in (DATA / "moments").glob("*.txt"))


def pick_moment(moment, n):
    path = DATA / "moments" / f"{moment}.txt"
    if not path.exists():
        print(f"Нет момента «{moment}». Есть: {', '.join(moments())}")
        sys.exit(1)
    rows = [r for r in path.read_text(encoding="utf-8").splitlines() if r]
    recent = load_recent()
    fresh = [r for r in rows if r not in recent] or rows
    chosen = random.sample(fresh, min(n, len(fresh)))
    for row in chosen:
        text, section = row.split("\t")
        print(f"{text}  [{section}]")
    save_recent(recent + chosen)


def pick_day(date_str):
    date = datetime.date.fromisoformat(date_str) if date_str else datetime.date.today()
    # Даль ведёт Месяцеслов по старому стилю; для 1900-2099 разница 13 дней
    old = date - datetime.timedelta(days=13)
    cal = json.loads((DATA / "mesyatseslov.json").read_text(encoding="utf-8"))
    recent = load_recent()
    print(f"Сегодня {date:%d.%m.%Y}, по старому стилю {old:%d.%m}.")

    day = [l for l in cal.get(f"{old.month:02d}-{old.day:02d}", []) if l not in recent]
    month = [l for l in cal.get(f"{old.month:02d}", []) if l not in recent]
    if day:
        print("Записи Месяцеслова на этот день:")
        for line in day:
            print(" -", line)
    else:
        print("На этот день свежих записей нет. Поговорки к началу работы:")
        pick_moment("start", 3)
        recent = load_recent()
    if month:
        print("Поговорки месяца:")
        for line in month:
            print(" -", line)
    save_recent(recent + day + month)


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
    elif argv[0] == "list":
        print("\n".join(moments()))
    elif argv[0] == "day":
        pick_day(argv[1] if len(argv) > 1 else None)
    else:
        n = int(argv[argv.index("-n") + 1]) if "-n" in argv else 3
        pick_moment(argv[0], n)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
