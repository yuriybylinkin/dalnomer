"""Сборка данных скилла из raw/ (результат fetch.py).

Пишет в skills/dalnomer/data/:
  moments/<момент>.txt  - поговорки по моментам работы, строка: «текст<TAB>раздел»
  mesyatseslov.json     - Месяцеслов по дням старого стиля: {"MM-DD": [...], "MM": [...]}
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
DATA = ROOT / "skills" / "dalnomer" / "data"

MOMENTS = {
    "start": ["Начало — Конец", "Работа — Праздность", "Путь — Дорога"],
    "plan": ["Раздумье — Решимость", "Забота — Опыт", "Запас", "Ум — Глупость"],
    "risk": ["Осторожность", "Оплошность — Расторопность", "Нечаянность — Расплох"],
    "bug": ["Причина — Следствие", "Повод — Причина", "Сознание — Улика", "Вина — Заслуга"],
    "long": ["Терпение — Надежда", "Судьба — Терпение — Надежда", "Упорство"],
    "stuck": ["Поиск — Находка", "Толк — Бестолочь", "Тайна — Любопытство", "Чудо — Диво — Мудреное"],
    "review": ["Правда — Кривда", "Сущность — Наружность", "Верное — Надежное", "Прямота — Лукавство"],
    "hurry": ["Пора — Мера — Успех", "Покой — Движение"],
    "done": ["Начало — Конец", "Хорошо — Худо", "Похвала — Похвальба"],
    "craft": ["Ремесло — Снаряд", "Ремесло — Мастеровой", "Ученье — Наука"],
    "ask": ["Просьба — Согласие — Отказ", "Язык — Речь", "Помощь — Кстати"],
    "legacy": ["Свое — Чужое", "Наследство — Подарок"],
    "failure": ["Горе — Утешение", "Счастье — Удача"],
}

# «Начало — Конец» делится между start и done по словам про окончание
END_WORDS = re.compile(r"конец|конц|конча|кончи|венец|доделал|сделал|отделал|отработал", re.I)

# Автоматический фильтр вместо ручного отбора
BAD = re.compile(
    r"\b(жид|цыган|татар|немец|немц|хохол|хохл|мордв|чухн|поляк|лях|жен[аеуоы]|жён|баб[аеуыо]?\b|бабь|девк)",
    re.I,
)
MAX_LEN = 160


def section_lines(name):
    lines = (RAW / f"{name}.txt").read_text(encoding="utf-8").splitlines()
    body, started = [], False
    for line in lines[1:]:
        if line.startswith("## "):
            started = True
            continue
        if not started or line in ("[править]",) or line.startswith("←"):
            continue
        body.append(line.replace("[править]", "").strip())
    return [l for l in body if l]


def clean(line):
    return re.sub(r"\s+", " ", line).strip()


def build_moments():
    out = DATA / "moments"
    out.mkdir(parents=True, exist_ok=True)
    stats = {}
    for moment, sections in MOMENTS.items():
        rows, dropped = [], 0
        for sec in sections:
            for line in section_lines(sec):
                line = clean(line)
                if sec == "Начало — Конец":
                    is_end = bool(END_WORDS.search(line))
                    if (moment == "done") != is_end:
                        continue
                if len(line) > MAX_LEN or BAD.search(line):
                    dropped += 1
                    continue
                rows.append(f"{line}\t{sec}")
        rows = list(dict.fromkeys(rows))
        (out / f"{moment}.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")
        stats[moment] = (len(rows), dropped)
    return stats


MONTHS = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль",
          "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]


def build_calendar():
    cal, month, day = {}, None, None
    for line in _calendar_lines():
        if line.startswith("## "):
            name = line[3:].strip()
            month = MONTHS.index(name) + 1 if name in MONTHS else None
            day = None
            continue
        if month is None:
            continue
        m = re.match(r"^(\d{1,2})\.\s+(.*)", line)
        if m and 1 <= int(m.group(1)) <= 31:
            day = int(m.group(1))
            line = m.group(2)
        key = f"{month:02d}-{day:02d}" if day else f"{month:02d}"
        cal.setdefault(key, []).append(clean(line))
    (DATA / "mesyatseslov.json").write_text(
        json.dumps(cal, ensure_ascii=False, indent=1), encoding="utf-8")
    return len([k for k in cal if "-" in k])


def _calendar_lines():
    # В Месяцеслове заголовки месяцев нужны, поэтому читаем без section_lines
    lines = (RAW / "Месяцеслов.txt").read_text(encoding="utf-8").splitlines()
    started = False
    for line in lines[1:]:
        if line.startswith("## "):
            started = True
        if started and line.strip() and "[править]" not in line and not line.startswith("←"):
            yield line.strip()


def main():
    stats = build_moments()
    for k, (n, d) in stats.items():
        print(f"{k:8} {n:4} поговорок, отброшено фильтром {d}")
    print("Месяцеслов: дней с записями", build_calendar())


if __name__ == "__main__":
    main()
