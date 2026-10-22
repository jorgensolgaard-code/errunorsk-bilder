"""Render a «Gjett ordet» post (1080x1350 PNG) from a JSON word entry.

Usage: python3 render.py words.json out_dir
words.json: list of {"id","ord","landsdel","valg":[A,B,C]}
"""
import json, sys, html, pathlib
from playwright.sync_api import sync_playwright

TEMPLATE = """<!doctype html><html lang="no"><head><meta charset="utf-8"><style>
body{{margin:0}}
.root{{width:1080px;height:1350px;box-sizing:border-box;padding:88px;background:#F5C842;color:#141414;
font-family:'Inter Display',Inter,sans-serif;display:flex;flex-direction:column}}
.top{{display:flex;justify-content:space-between;align-items:center}}
.tag{{padding:14px 28px;background:#141414;color:#F5C842;border-radius:14px;font-size:32px;font-weight:800}}
.reg{{font-size:30px;font-weight:500}}
.mid{{flex-grow:1;display:flex;flex-direction:column;justify-content:center;gap:48px}}
.q{{margin:0;font-size:52px;font-weight:500}}
h1{{margin:0;font-size:{size}px;font-weight:800;line-height:.9;letter-spacing:-.03em}}
.opts{{display:flex;flex-direction:column;gap:18px}}
.opt{{padding:26px 32px;border:4px solid #141414;border-radius:20px;background:#FFFFFF;font-size:40px;font-weight:500}}
.foot{{display:flex;justify-content:space-between;align-items:center;font-size:30px;font-weight:800}}
.foot span+span{{font-weight:500}}
</style></head><body><div class="root">
<div class="top"><span class="tag">Gjett ordet</span><span class="reg">{landsdel}</span></div>
<div class="mid"><p class="q">Hva betyr</p><h1>{ord}?</h1>
<div class="opts">{opts}</div></div>
<div class="foot"><span>@errunorsk</span><span>Svar i kommentarfeltet</span></div>
</div></body></html>"""


def size_for(word: str) -> int:
    # Shrink long words so they fit the 904px text width.
    n = len(word) + 1
    return max(120, min(240, int(904 / (n * 0.56))))


def main(src, out):
    words = json.loads(pathlib.Path(src).read_text())
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        for w in words:
            opts = "".join(
                f'<div class="opt">{l} · {html.escape(t)}</div>'
                for l, t in zip("ABC", w["valg"]))
            pg.set_content(TEMPLATE.format(
                size=size_for(w["ord"]), landsdel=html.escape(w["landsdel"]),
                ord=html.escape(w["ord"]), opts=opts))
            # Shrink the headline until it fits inside the 904px text column.
            pg.evaluate("""() => { const h = document.querySelector('h1');
                h.style.width = 'max-content'; h.style.alignSelf = 'flex-start';
                let s = parseFloat(getComputedStyle(h).fontSize);
                while (h.getBoundingClientRect().width > 900 && s > 80) { s -= 4; h.style.fontSize = s + 'px'; } }""")
            pg.screenshot(path=str(out / f'{w["id"]}.png'))
            print("rendered", w["id"])
        b.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
