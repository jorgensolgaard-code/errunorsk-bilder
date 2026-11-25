"""Render a «Gjett ordet» Reel (1080x1920 MP4, ~9.5 s) from a JSON word entry.

Usage: python3 render_reel.py words.json out_dir
words.json: list of {"id","ord","landsdel","valg":[A,B,C],"riktig":0-2,"eksempel"}

Timeline: word + options appear (0-1.5 s), countdown 3-2-1 (3-6 s),
correct answer revealed with example sentence (6-9.5 s).
Frames are rendered with Playwright and encoded with ffmpeg (H.264 + silent AAC).
"""
import json, sys, html, pathlib, subprocess, tempfile
from playwright.sync_api import sync_playwright

FPS = 30
DURATION = 9.5

TEMPLATE = """<!doctype html><html lang="no"><head><meta charset="utf-8"><style>
body{margin:0}
.root{width:1080px;height:1920px;box-sizing:border-box;padding:250px 110px 400px;background:#F5C842;color:#141414;
font-family:'Inter Display',Inter,sans-serif;display:flex;flex-direction:column;position:relative;overflow:hidden}
.top{display:flex;justify-content:space-between;align-items:center}
.tag{padding:16px 30px;background:#141414;color:#F5C842;border-radius:16px;font-size:36px;font-weight:800}
.reg{font-size:36px;font-weight:500}
.mid{flex-grow:1;display:flex;flex-direction:column;justify-content:center;gap:44px}
.q{margin:0;font-size:60px;font-weight:500}
h1{margin:0;font-size:220px;font-weight:800;line-height:.9;letter-spacing:-.03em;transform-origin:left center;width:max-content}
.opts{display:flex;flex-direction:column;gap:22px}
.opt{padding:30px 36px;border:5px solid #141414;border-radius:24px;background:#FFFFFF;font-size:48px;font-weight:500;
display:flex;justify-content:space-between;align-items:center}
.opt.right{background:#141414;color:#F5C842;font-weight:800}
.check{font-size:52px;opacity:0}
.below{height:200px;position:relative}
.count{position:absolute;left:0;right:0;top:0;display:flex;align-items:center;gap:28px}
.num{width:150px;height:150px;border-radius:50%;background:#141414;color:#F5C842;display:flex;align-items:center;justify-content:center;
font-size:96px;font-weight:800}
.hint{font-size:44px;font-weight:500}
.ex{position:absolute;left:0;right:0;top:0;font-size:50px;font-weight:500;line-height:1.25;opacity:0}
.foot{position:absolute;left:110px;right:110px;bottom:300px;display:flex;justify-content:space-between;font-size:34px;font-weight:800}
.foot span+span{font-weight:500}
</style></head><body><div class="root">
<div class="top"><span class="tag">Gjett ordet</span><span class="reg">__LANDSDEL__</span></div>
<div class="mid"><p class="q">Hva betyr</p><h1>__ORD__?</h1>
<div class="opts">__OPTS__</div>
<div class="below">
 <div class="count"><div class="num">3</div><div class="hint">Gjett før svaret kommer!</div></div>
 <div class="ex">__EKS__</div>
</div></div>
<div class="foot"><span>@errunorsk</span><span>Svar i kommentarfeltet</span></div>
</div>
<script>
const clamp=(x)=>Math.max(0,Math.min(1,x));
const ease=(x)=>1-Math.pow(1-clamp(x),3);
const back=(x)=>{x=clamp(x);const c=1.7;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2);};
// Fit the headline into the 860px column once.
(()=>{const h=document.querySelector('h1');let s=220;
 while(h.getBoundingClientRect().width>860&&s>90){s-=4;h.style.fontSize=s+'px';}})();
window.setT=(t)=>{
 const h=document.querySelector('h1'), q=document.querySelector('.q');
 q.style.opacity=ease(t/0.3);
 const k=back((t-0.1)/0.5); h.style.transform=`scale(${0.6+0.4*k})`; h.style.opacity=ease((t-0.1)/0.3);
 const opts=[...document.querySelectorAll('.opt')], R=__RIKTIG__;
 opts.forEach((o,i)=>{const p=ease((t-0.6-i*0.25)/0.4);
   let op=p, tx=(1-p)*80;
   if(t>=6.0){const r=ease((t-6.0)/0.3); if(i!==R) op=1-0.65*r;}
   o.style.opacity=op; o.style.transform=`translateX(${tx}px)`;
   const right=(i===R&&t>=6.0); o.classList.toggle('right',right);
   if(i===R){const c=o.querySelector('.check'); c.style.opacity=right?1:0;
     const pop=right?back((t-6.0)/0.35):1; o.style.transform=`translateX(${tx}px) scale(${0.94+0.06*pop})`;}
 });
 const cnt=document.querySelector('.count'), num=document.querySelector('.num');
 if(t<6.0){cnt.style.opacity=ease((t-1.6)/0.4);
   const n=t<4?3:(t<5?2:1); num.textContent=n;
   const local=t<3?0:(t-Math.floor(t)); num.style.transform=`scale(${t<3?1:1+0.25*(1-ease(local/0.3))})`;}
 else cnt.style.opacity=1-ease((t-6.0)/0.2);
 document.querySelector('.ex').style.opacity=ease((t-6.4)/0.4);
};
</script></body></html>"""


def build_html(w):
    opts = "".join(
        f'<div class="opt"><span>{l} · {html.escape(t)}</span><span class="check">✓</span></div>'
        for l, t in zip("ABC", w["valg"]))
    return (TEMPLATE.replace("__LANDSDEL__", html.escape(w["landsdel"]))
            .replace("__ORD__", html.escape(w["ord"]))
            .replace("__OPTS__", opts)
            .replace("__EKS__", html.escape(w.get("eksempel", "")))
            .replace("__RIKTIG__", str(int(w["riktig"]))))


def main(src, out):
    words = json.loads(pathlib.Path(src).read_text())
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        for w in words:
            pg.set_content(build_html(w))
            pg.evaluate("document.fonts.ready")
            with tempfile.TemporaryDirectory() as tmp:
                n = int(DURATION * FPS)
                for i in range(n):
                    pg.evaluate(f"setT({i / FPS})")
                    pg.screenshot(path=f"{tmp}/f{i:04d}.png")
                # Cover frame (shown in grid): question with options, before the reveal.
                pg.evaluate("setT(2.5)")
                pg.screenshot(path=str(out / f'{w["id"]}-cover.png'))
                subprocess.run([
                    "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{tmp}/f%04d.png",
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                    "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high",
                    "-crf", "20", "-r", str(FPS), "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                    str(out / f'{w["id"]}.mp4')], check=True)
            print("rendered", w["id"])
        b.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
