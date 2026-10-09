"""Выгрузка разделов «Пословиц русского народа» Даля с Викитеки.

Сохраняет отрисованный текст каждого раздела в raw/<раздел>.txt.
Уже скачанные разделы пропускает, поэтому прерванную выгрузку можно продолжить.
"""
import json
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://ru.wikisource.org/w/api.php"
BASE = "Пословицы русского народа (Даль)"
ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
UA = {"User-Agent": "DalnomerSkill/1.0 (https://github.com/OWNER/dalnomer)"}


def api(**params):
    params.update(format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(8):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            wait = int(e.headers.get("Retry-After") or 0) or 10 * (attempt + 1)
            print(f"  429, жду {wait} с")
            time.sleep(wait)
    raise RuntimeError("Викитека не отвечает: " + url)


def section_titles():
    data = api(action="parse", page=BASE, prop="links")
    titles = [l["title"] for l in data["parse"]["links"]
              if l["title"].startswith(BASE + "/") and l.get("exists")]
    return [t for t in dict.fromkeys(titles) if not t.endswith("/Напутное")]


def html_to_lines(html):
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.S)
    # номера страниц скана и сноски
    html = re.sub(r'<span[^>]*class="[^"]*pagenum[^"]*"[^>]*>.*?</span>', "", html, flags=re.S)
    html = re.sub(r'<sup[^>]*class="reference"[^>]*>.*?</sup>', "", html, flags=re.S)
    html = re.sub(r"<(br|/p|/dd|/li|/div|/h\d|/tr)[^>]*>", "\n", html)
    html = re.sub(r"<h(\d)[^>]*>", "\n## ", html)
    text = re.sub(r"<[^>]+>", "", html)
    import html as h
    text = h.unescape(text)
    return [re.sub(r"\s+", " ", l).strip() for l in text.split("\n")]


def main():
    RAW.mkdir(exist_ok=True)
    titles = section_titles()
    print(len(titles), "разделов")
    for t in titles:
        name = t.split("/", 1)[1]
        out = RAW / (re.sub(r'[\\/:*?"<>|]', "_", name) + ".txt")
        if out.exists():
            continue
        data = api(action="parse", page=t, prop="text", disablelimitreport="1")
        lines = [l for l in html_to_lines(data["parse"]["text"]) if l]
        out.write_text(name + "\n" + "\n".join(lines), encoding="utf-8")
        print(f"{name}: {len(lines)} строк")
        time.sleep(3)


if __name__ == "__main__":
    main()
