"""Server-rendered HTML board of all collected job postings.

Single self-contained page (embedded CSS + tiny JS, no external deps) served by
the API at GET /. Posts come straight from the DB so the user can browse
everything that arrived from every exchange in one place.
"""
from datetime import datetime
from html import escape
from typing import Optional

from config.topics import SOURCES, TOPIC_BY_KEY

_CSS = """
:root{
  --bg:#0f1320; --panel:#171c2e; --panel2:#1f2740; --line:#2a3354;
  --text:#e8ecf6; --muted:#9aa6c4; --accent:#6c8cff; --accent2:#36d6a0;
  --chip:#243154;
}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  background:radial-gradient(1200px 800px at 80% -10%,#1b2440 0,transparent 60%),var(--bg);
  color:var(--text);-webkit-font-smoothing:antialiased}
header{padding:28px 24px 18px;border-bottom:1px solid var(--line);
  display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
h1{font-size:22px;margin:0;font-weight:700;letter-spacing:.2px}
h1 .dot{color:var(--accent2)}
.sub{color:var(--muted);font-size:13px;margin-top:4px}
.wrap{max-width:1200px;margin:0 auto;padding:22px 18px 60px}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 18px}
.fbtn{background:var(--panel2);border:1px solid var(--line);color:var(--muted);
  padding:7px 13px;border-radius:999px;cursor:pointer;font-size:13px;transition:.15s}
.fbtn:hover{color:var(--text);border-color:var(--accent)}
.fbtn.active{background:var(--accent);color:#0b1020;border-color:var(--accent);font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:16px}
.card{background:linear-gradient(180deg,var(--panel),var(--panel2));border:1px solid var(--line);
  border-radius:16px;padding:16px 16px 14px;display:flex;flex-direction:column;gap:10px;
  transition:.18s;position:relative;overflow:hidden}
.card:hover{transform:translateY(-3px);border-color:var(--accent);box-shadow:0 10px 30px rgba(0,0,0,.35)}
.card .top{display:flex;align-items:center;justify-content:space-between;gap:10px}
.src{font-size:12px;color:var(--muted);font-weight:600}
.src .em{font-size:15px;margin-right:5px}
.title{font-size:16px;font-weight:650;line-height:1.3;margin:0}
.title a{color:var(--text);text-decoration:none}
.title a:hover{color:var(--accent)}
.meta{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:13px;color:var(--muted)}
.budget{color:var(--accent2);font-weight:700}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{background:var(--chip);border:1px solid var(--line);color:#cdd8f5;font-size:11.5px;
  padding:3px 9px;border-radius:999px;white-space:nowrap}
.desc{color:var(--muted);font-size:13px;line-height:1.45;
  display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
.date{font-size:11.5px;color:#6f7ba0;margin-top:auto}
.badge{position:absolute;top:12px;right:12px;font-size:10.5px;font-weight:700;
  padding:3px 8px;border-radius:999px;text-transform:uppercase;letter-spacing:.5px}
.badge.vac{background:rgba(255,80,80,.16);color:#ff8a8a;border:1px solid rgba(255,80,80,.35)}
.badge.notif{background:rgba(54,214,160,.14);color:var(--accent2);border:1px solid rgba(54,214,160,.35)}
.empty{text-align:center;color:var(--muted);padding:60px 0;font-size:15px}
footer{text-align:center;color:#5b658a;font-size:12px;padding:24px}
"""


def _topics_labels(csv: Optional[str]) -> list[str]:
    if not csv:
        return []
    out = []
    for k in csv.split(","):
        k = k.strip()
        if not k:
            continue
        t = TOPIC_BY_KEY.get(k)
        out.append(f"{t['emoji']} {t['name']}" if t else k)
    return out


def _fmt_date(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    return dt.strftime("%d.%m.%Y %H:%M")


def _clean(text: str, limit: int = 320) -> str:
    if not text:
        return ""
    t = " ".join(text.split())
    return t[:limit].rstrip(" ,.;:") + ("…" if len(t) > limit else "")


def render_jobs_page(rows: list, base_url: str = "") -> str:
    cards = []
    for r in rows:
        src = SOURCES.get(r.source, {})
        s_emoji = src.get("emoji", "•")
        s_name = src.get("name", r.source)
        topics = _topics_labels(r.matched_topics)
        chips = "".join(f'<span class="chip">{escape(c)}</span>' for c in topics)
        badge = ""
        if getattr(r, "is_vacancy", False):
            badge = '<span class="badge vac">вакансия</span>'
        elif getattr(r, "notified", False):
            badge = '<span class="badge notif">прислано</span>'
        desc = _clean(r.description or "")
        url = r.url or "#"
        chips_html = f'<div class="chips">{chips}</div>' if chips else ""
        desc_html = f'<div class="desc">{escape(desc)}</div>' if desc else ""
        cards.append(
            f'\n        <article class="card" data-src="{escape(r.source)}">\n'
            f"          {badge}\n"
            f'          <div class="top">\n'
            f'            <span class="src"><span class="em">{s_emoji}</span>{escape(s_name)}</span>\n'
            f'            <span class="date">{escape(_fmt_date(r.seen_at))}</span>\n'
            f"          </div>\n"
            f'          <h3 class="title"><a href="{escape(url)}" target="_blank" rel="noopener">'
            f'{escape(r.title or "Без названия")}</a></h3>\n'
            f'          <div class="meta">\n'
            f'            <span class="budget">💰 {escape(r.budget or "Не указан")}</span>\n'
            f"          </div>\n"
            f"          {chips_html}\n"
            f"          {desc_html}\n"
            f"        </article>"
        )

    grid = "\n".join(cards) if cards else '<div class="empty">Пока нет сохранённых объявлений.</div>'

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Фриланс-монитор · все объявления</title>
<meta http-equiv="refresh" content="90">
<style>{_CSS}</style>
</head>
<body>
<header>
  <div>
    <h1>Фриланс-монитор <span class="dot">●</span></h1>
    <div class="sub">Все собранные объявления со всех бирж · обновляется автоматически</div>
  </div>
  <div class="sub">{len(rows)} объявлений в базе</div>
</header>
<div class="wrap">
  <div class="filters" id="filters"></div>
  <div class="grid" id="grid">{grid}</div>
</div>
<footer>freelance-monitor-bot · локальная доска объявлений</footer>
<script>
const grid=document.getElementById('grid');
const filters=document.getElementById('filters');
const sources=[...new Set([...grid.querySelectorAll('.card')].map(c=>c.dataset.src))];
function mk(label,src,active){{
  const b=document.createElement('button');b.className='fbtn'+(active?' active':'');
  b.textContent=label;b.onclick=()=>apply(src,b);return b;
}}
function apply(src,btn){{
  [...filters.children].forEach(x=>x.classList.remove('active'));
  btn.classList.add('active');
  [...grid.children].forEach(c=>{{c.style.display=(!src||c.dataset.src===src)?'':'none';}});
}}
filters.appendChild(mk('Все',null,true));
sources.forEach(s=>filters.appendChild(mk(s,s,false)));
</script>
</body>
</html>"""
