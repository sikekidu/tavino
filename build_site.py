#!/usr/bin/env python3
"""Build the Tavino static site (GitHub Pages) from the定版 article sources."""
import base64, hashlib, html, os, re, shutil, sys

sys.path.insert(0, '/tmp/sitevenv/lib/python3.12/site-packages')
import glob
for p in glob.glob('/tmp/sitevenv/lib/python*/site-packages'):
    sys.path.insert(0, p)
import markdown

ROOT = os.path.expanduser('~/workspace/tavino-site')
VA = os.path.expanduser('~/workspace/tavino-verify-agent')
CE = os.path.expanduser('~/workspace/tavino-car-export')
BRAND = os.path.expanduser('~/workspace/tavino-brand')
BASE = 'https://tavinosourcing.com'
BEEHIIV_FORM = '555f4204-f902-49b1-97fd-2a1af6e33046'
CLARITY_ID = 'zjh5mut81j'
CLARITY = f'''<script type="text/javascript">
    (function(c,l,a,r,i,t,y){{
        c[a]=c[a]||function(){{(c[a].q=c[a].q||[]).push(arguments)}};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    }})(window, document, "clarity", "script", "{CLARITY_ID}");
</script>'''

os.makedirs(ROOT, exist_ok=True)
for d in ['assets/img/a1', 'assets/img/a2', 'assets/img/a3', 'assets/brand', 'assets/img/reports',
          'assets/downloads',
          'verify-1688-supplier', 'us-import-data-buyers', 'chinese-suv-landed-cost',
          'who-supplies-americas-plastics', 'who-supplies-americas-furniture',
          'who-supplies-americas-auto-parts', 'who-supplies-americas-lighting', 'thanks']:
    os.makedirs(os.path.join(ROOT, d), exist_ok=True)

# ---------- brand assets ----------
for f in ['avatar.png', 'favicon.ico', 'favicon-32.png']:
    shutil.copy(os.path.join(BRAND, f), os.path.join(ROOT, 'assets/brand', f))

# ---------- shared template pieces ----------
def head(title, desc, path, og_img, article=None):
    url = f'{BASE}{path}'
    ld = ''
    if article:
        import json
        ld_obj = {"@context": "https://schema.org", "@type": "Article",
                  "headline": article['headline'], "description": desc,
                  "image": f"{BASE}/{og_img}", "datePublished": article['date'],
                  "author": {"@type": "Organization", "name": "Tavino LLC", "url": f"{BASE}/"}}
        ld = f'<script type="application/ld+json">{json.dumps(ld_obj)}</script>'
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{'article' if article else 'website'}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/{og_img}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{BASE}/assets/brand/favicon.ico">
<link rel="stylesheet" href="{BASE}/style.css">
{ld}
{CLARITY}
</head>'''

HEADER = f'''<header class="site-header">
<a class="brand" href="{BASE}/"><img src="{BASE}/assets/brand/avatar.png" alt="Tavino logo" width="36" height="36"><span>Tavino</span></a>
<nav><a href="{BASE}/#research">Research</a></nav>
</header>'''

SUBSCRIBE = f'''<section class="subscribe-quiet">
<p>If this was useful — one free China sourcing brief a week, with the new research:</p>
<script async src="https://subscribe-forms.beehiiv.com/v3/loader.js" data-beehiiv-form="{BEEHIIV_FORM}"></script>
</section>'''

def datapack_block(pack_file, pack_desc):
    return f'''<section class="subscribe-quiet">
<h2 style="color:var(--navy);font-size:20px;margin:0 0 8px">Get the data pack</h2>
<p>{pack_desc}</p>
<p class="small">Subscribe to the free weekly brief and the pack is sent to your inbox automatically. Already subscribed? It is in your welcome email.</p>
<script async src="https://subscribe-forms.beehiiv.com/v3/loader.js" data-beehiiv-form="{BEEHIIV_FORM}"></script>
</section>'''

def clarity_track_script(ep):
    """Clarity custom event for the data-pack claim block on report pages.
    Fires datapack_click_epN on: a click anywhere inside the claim block, a
    click on any direct ZIP download link, and focus entering the embedded
    Beehiiv form (cross-origin iframe — its submit cannot be hooked directly,
    so iframe focus is the closest reliable intent signal)."""
    return f'''<script>
(function(){{
  function fire(){{ if (window.clarity) clarity("event", "datapack_click_{ep}"); }}
  document.addEventListener("click", function(e){{
    if (!e.target.closest) return;
    if (e.target.closest('a[href*="/assets/downloads/"]')) {{ fire(); return; }}
    if (e.target.closest("section.subscribe-quiet")) fire();
  }});
  window.addEventListener("blur", function(){{
    setTimeout(function(){{
      var el = document.activeElement;
      if (el && el.tagName === "IFRAME") fire();
    }}, 0);
  }});
}})();
</script>'''

FOOTER = f'''<footer class="site-footer">
<p>© 2026 Tavino LLC · China sourcing, verified.</p>
<p><a href="https://payhip.com/b/dk5Lb">Free guide: Buying from 1688 without getting burned</a> · <a href="https://medium.com/@TavinoLLC">Medium</a> · <a href="https://x.com/Nathonni">X</a> · <a href="mailto:tavino@muse.ai">tavino@muse.ai</a></p>
</footer>
<script type="text/javascript" async src="https://subscribe-forms.beehiiv.com/attribution.js"></script>
</body>
</html>'''

CSS = '''
:root{--navy:#0A2E5F;--amber:#F5A623;--ink:#1c2733;--paper:#FAF8F5;--mut:#5b6a78;--line:#e5e0d8}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:var(--paper);line-height:1.65}
.site-header{display:flex;justify-content:space-between;align-items:center;max-width:1060px;margin:0 auto;padding:18px 20px}
.brand{display:flex;gap:10px;align-items:center;font-weight:700;font-size:20px;color:var(--navy);text-decoration:none}
.brand img{border-radius:8px}
nav a{margin-left:18px;color:var(--navy);text-decoration:none;font-size:15px}
main{max-width:1060px;margin:0 auto;padding:0 20px 40px}
.hero{text-align:center;padding:38px 10px 8px}
.hero h1{font-size:42px;color:var(--navy);margin:0 0 10px;line-height:1.15}
.hero p.lede{font-size:19px;color:var(--mut);max-width:640px;margin:0 auto 8px}
.subscribe-quiet{max-width:520px;margin:36px auto 0;border-top:1px solid var(--line);padding-top:16px;font-family:system-ui,sans-serif}
.subscribe-quiet p{color:var(--mut);font-size:14px;margin:0 0 6px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin:34px 0}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;overflow:hidden;text-decoration:none;color:var(--ink);display:block}
.card img{width:100%;height:170px;object-fit:cover;display:block}
.card div{padding:16px 18px}
.card h3{margin:0 0 6px;color:var(--navy);font-size:18px;line-height:1.35}
.card p{margin:0;color:var(--mut);font-size:14.5px}
.about{max-width:720px;margin:10px auto 0;color:var(--mut);font-size:15.5px}
.about h2{color:var(--navy)}
article{max-width:720px;margin:0 auto;font-family:Georgia,"Times New Roman",serif;font-size:19px}
article h1{font-family:system-ui,sans-serif;font-size:34px;line-height:1.25;color:var(--navy);margin:18px 0 8px}
article .lede{font-size:20px;color:var(--mut);font-style:italic;margin:0 0 20px}
article h2{font-family:system-ui,sans-serif;font-size:24px;color:var(--navy);margin:34px 0 10px;line-height:1.3}
article img{max-width:100%;height:auto;border-radius:10px;margin:14px 0}
article .cover{width:100%;margin:6px 0 18px}
article a{color:var(--navy)}
.meta{font-family:system-ui,sans-serif;font-size:14px;color:var(--mut);margin-bottom:6px}
.more{max-width:720px;margin:30px auto 0;font-family:system-ui,sans-serif}
.more h2{color:var(--navy);font-size:20px}
.more li{margin:6px 0}
.sec-head{display:flex;align-items:baseline;justify-content:space-between;gap:14px;margin:42px 0 2px;border-bottom:3px solid var(--amber);padding-bottom:6px}
.sec-head h2{color:var(--navy);margin:0;font-size:24px}
.sec-head .sec-note{color:var(--mut);font-size:13.5px;white-space:nowrap}
.card .cover-art{background:var(--navy);color:var(--paper);height:170px;display:flex;flex-direction:column;justify-content:center;padding:18px 20px 18px 26px;position:relative;overflow:hidden}
.card .cover-art:before{content:"";position:absolute;left:0;top:0;bottom:0;width:6px;background:var(--amber)}
.cover-art .ca-kicker{display:block;font-size:11.5px;letter-spacing:2.2px;font-weight:700;color:var(--amber);text-transform:uppercase;margin-bottom:6px}
.cover-art .ca-big{display:block;font-size:44px;font-weight:800;line-height:1.05;color:#fff}
.cover-art .ca-line{display:block;font-size:13.5px;color:#c9d4e2;margin-top:7px;line-height:1.45}
.card .ep-tag{display:inline-block;background:var(--amber);color:#231a00;font-size:11.5px;font-weight:700;border-radius:20px;padding:2px 10px;margin-bottom:8px;letter-spacing:.4px}
.card.featured{margin-top:28px}
.card.featured .cover-art{height:250px;padding:26px 32px 26px 38px}
.card.featured .cover-art .ca-big{font-size:66px}
.card.featured .cover-art .ca-line{font-size:15.5px}
.card.featured h3{font-size:25px}
.card.featured p{font-size:15.5px}
@media (max-width:640px){.card.featured .cover-art{height:210px;padding:22px 24px 22px 30px}.card.featured .cover-art .ca-big{font-size:48px}.cover-art .ca-big{font-size:38px}.sec-head .sec-note{white-space:normal}}
.site-footer{border-top:1px solid var(--line);margin-top:44px;padding:22px 20px;text-align:center;color:var(--mut);font-size:14px}
.site-footer a{color:var(--navy)}
@media (max-width:640px){.hero h1{font-size:32px}article{font-size:18px}}
article.report{max-width:880px}
.dossier{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-size:16.5px;line-height:1.65}
.dossier .headline{background:var(--navy);color:#fff;border-radius:14px;padding:22px 24px;margin:24px 0}
.dossier .headline b{color:var(--amber)}
.dossier .headline .big{font-size:21px;line-height:1.5}
.dossier h2{border-bottom:3px solid var(--amber);display:inline-block;padding-bottom:2px}
.dossier table{width:100%;border-collapse:collapse;margin:14px 0;font-size:14.5px;background:#fff}
.dossier th{background:var(--navy);color:#fff;text-align:left;padding:9px 10px}
.dossier td{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
.dossier .v-bad{color:#b3402a;font-weight:700}
.dossier .v-mid{color:#9a6a00;font-weight:700}
.dossier .v-good{color:#1e7a46;font-weight:700}
.dossier .card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin:16px 0}
.dossier .card h3{margin:0 0 6px;color:var(--navy);font-size:18px}
.dossier .tag{display:inline-block;background:var(--amber);color:#231a00;font-size:12px;font-weight:700;border-radius:20px;padding:2px 10px;margin-left:8px;vertical-align:middle}
.dossier .method{background:#fff;border-left:5px solid var(--amber);padding:14px 18px;margin:16px 0;border-radius:0 12px 12px 0}
.dossier .foot{margin-top:40px;color:var(--mut);font-size:13px;border-top:1px solid var(--line);padding-top:14px}
.dossier .muted{color:var(--mut)}
.dossier .small{font-size:13.5px}
@media (max-width:640px){.dossier table{font-size:13px}.dossier td,.dossier th{padding:7px 6px}.dossier .headline .big{font-size:18px}}
'''
with open(os.path.join(ROOT, 'style.css'), 'w') as f:
    f.write(CSS.strip() + '\n')

# ---------- Article 2 & 3 from markdown ----------
ALTS = {
    'chart-forwarders.png': 'Top US importers of HS 3926 plastic articles — freight forwarders Expeditors, Translink, DSV and Hai Wind lead the ranking',
    'chart-vietnam.png': "Vietnam's share of US plastic-parts imports by shipment volume",
    'chart-origins.png': 'Where US plastic-parts shipments originate — top supplier countries by volume',
    'chart-method.png': 'The five-step method for digging real buyers out of US import records',
    'chart-clean.png': 'The cleaned buyer list after removing forwarders, consolidators and notify-party names',
    'chart-fob.png': 'Reference FOB prices in China for the six best-selling export models',
    'chart-domestic-vs-fob.png': 'Domestic China prices vs exporter FOB quotes for the six models',
    'chart-freight.png': 'Freight cost bands to Dubai, Lagos and Almaty by car size',
    'chart-dubai.png': 'Landed cost build-up in Dubai: FOB plus freight plus 5% duty and 5% VAT',
    'chart-lagos.png': 'Landed cost build-up in Lagos: FOB plus freight plus roughly 41% in duties and taxes',
    'chart-almaty.png': 'Landed cost build-up in Almaty: FOB plus rail freight plus 15% EAEU duty and 16% VAT',
    'chart-almaty-stack.png': "Almaty's duty and tax stack — 15% duty, then 16% VAT on the duty-paid value",
    'chart-three-cities.png': 'Port-gate landed cost of the six models in Dubai, Lagos and Almaty, compared',
}

def md_article(md_path, img_src_dir, img_web_dir, img_fs_dir):
    text = open(md_path).read()
    lines = text.split('\n')
    title = lines[0].lstrip('# ').strip()
    rest = '\n'.join(lines[1:]).strip()
    # lede = first paragraph (strip italics markers if present)
    m = re.match(r'(.+?)\n\n', rest, re.S)
    lede_raw = m.group(1).strip()
    lede = lede_raw.strip('*').strip()
    body_md = rest[m.end():]
    # images
    def img_sub(mm):
        fn = mm.group(1)
        if fn == 'cover.png':
            return ''
        shutil.copy(os.path.join(img_src_dir, fn), os.path.join(img_fs_dir, fn))
        alt = ALTS.get(fn, fn.replace('-', ' ').replace('.png', ''))
        return f'\n\n<img src="{img_web_dir}/{fn}" alt="{html.escape(alt)}" loading="lazy">\n\n'
    body_md = re.sub(r'\[IMG: ([^\]]+)\]', img_sub, body_md)
    body_html = markdown.markdown(body_md, extensions=['extra'])
    return title, lede, body_html

def article_page(slug, title, lede, body_html, desc, date, cover_web, others):
    more = '\n'.join(f'<li><a href="{BASE}/{s}/">{t}</a></li>' for s, t in others)
    return f'''{head(title + ' — Tavino', desc, f'/{slug}/', cover_web, {'headline': title, 'date': date})}
<body>
{HEADER}
<main>
<article>
<p class="meta">Tavino research · {date}</p>
<h1>{html.escape(title)}</h1>
<p class="lede">{html.escape(lede)}</p>
<img class="cover" src="{BASE}/{cover_web}" alt="{html.escape(title)} — cover image">
{body_html}
</article>
<section class="more"><h2>More Tavino research</h2><ul>{more}</ul></section>
{SUBSCRIBE}
</main>
{FOOTER}'''

# A2
t2, l2, b2 = md_article(os.path.join(VA, 'medium-article2/article-v2.md'),
                        os.path.join(VA, 'medium-article2'),
                        f'{BASE}/assets/img/a2', os.path.join(ROOT, 'assets/img/a2'))
shutil.copy(os.path.join(VA, 'medium-article2/cover.png'), os.path.join(ROOT, 'assets/img/a2/cover.png'))
# A3
t3, l3, b3 = md_article(os.path.join(CE, 'article3/article.md'),
                        os.path.join(CE, 'article3'),
                        f'{BASE}/assets/img/a3', os.path.join(ROOT, 'assets/img/a3'))
shutil.copy(os.path.join(CE, 'article3/cover.png'), os.path.join(ROOT, 'assets/img/a3/cover.png'))

# Site headlines (2026-11-26 retitle): conclusion-style titles on the site;
# the markdown sources keep their original Medium headlines.
t2 = 'The Top of the US Import Record Is Freight Forwarders, Not Buyers'
t3 = 'A $8,900 Chery Costs $15,020 Landed in Lagos'

# ---------- Article 1: extract body + images from the exact HTML ----------
src = open(os.path.join(VA, 'medium-v2-img/article-exact.html')).read()
body = re.search(r'<body[^>]*>(.*)</body>', src, re.S).group(1)
img_n = [0]
last_heading = ['Cover']
def a1_img(mm):
    img_n[0] += 1
    data = base64.b64decode(mm.group(1))
    fn = f'img-{img_n[0]}.jpg'
    with open(os.path.join(ROOT, 'assets/img/a1', fn), 'wb') as f:
        f.write(data)
    alt = f"{t1_title} — chart: {last_heading[0]}" if img_n[0] > 1 else f'{t1_title} — cover image'
    return f'<img src="{BASE}/assets/img/a1/{fn}" alt="{html.escape(alt)}" loading="lazy">'
# track headings while replacing
parts = re.split(r'(<h2[^>]*>.*?</h2>)', body, flags=re.S)
t1_title = 'Verify a 1688 Supplier Before You Pay: A Five-Step Desk Check'
out = []
for part in parts:
    hm = re.match(r'<h2[^>]*>(.*?)</h2>', part, re.S)
    if hm:
        last_heading[0] = re.sub(r'<[^>]+>', '', hm.group(1)).strip()
        out.append(part)
    else:
        out.append(re.sub(r'<img src="data:image/jpeg;base64,([A-Za-z0-9+/=]+)"[^>]*>', a1_img, part))
body1 = '\n'.join(out)
# split title/lede out of body1
m1 = re.search(r'<h1>(.*?)</h1>\s*<p><em>(.*?)</em></p>', body1, re.S)
lede1 = re.sub(r'<[^>]+>', '', m1.group(2)).strip()
body1 = body1[m1.end():]
# the body's first image is the cover, already rendered by the template
body1 = re.sub(r'<img src="' + re.escape(BASE) + r'/assets/img/a1/img-1\.jpg"[^>]*>', '', body1, count=1)

D1 = 'The shop said nine years; the company behind it was two. A five-step desk check on a real Dongguan supplier — registry, tenure, pricing and verdict — before any money moves.'
D2 = 'The top of the US import record is freight forwarders, not buyers. What 12.2 million plastic-parts bills of lading actually show, and the five-step method to dig out the real buyers.'
D3 = 'The same $8,900 Chery costs $10,910 landed in Dubai and $15,020 in Lagos. Six best-selling Chinese export models priced across three markets: FOB plus freight plus the full duty and tax stack.'
D4 = 'Eight of the nine biggest China-side "suppliers" of US plastic goods are logistics shells — forwarders, NVOCCs and parcel fronts. Exactly one is a real factory. Episode 1 of the Two-Sided Dossier: HS 3925/3926.'
D5 = 'Four of the eight biggest China/HK "suppliers" of US furniture are parcel consolidators holding ~86% of the bills — and the #1 averages 2.6 kg per "metal furniture" shipment. Episode 2 of the Two-Sided Dossier: HS 9401/9403.'
D6 = 'Six of the eight biggest China/HK "suppliers" of US auto parts are real factories holding 61% of the bill volume — and the #1 name is Advance Auto Parts\' own offshore buying desk, shipping 19-tonne containers. The only parcel shell holds just 13.7%. Episode 3 of the Two-Sided Dossier: HS 8708.'
D7 = 'The #1 "Chinese supplier" of US lighting is a Thai auto-trim factory. Of the top eight names, the two real factories are in Thailand and Vietnam — and no identified Chinese household-lighting factory appears at all. Episode 4 of the Two-Sided Dossier: HS 9405.'

A1 = ('verify-1688-supplier', t1_title, D1, '2026-11-23')
A2 = ('us-import-data-buyers', t2, D2, '2026-11-25')
A3 = ('chinese-suv-landed-cost', t3, D3, '2026-11-25')
R1 = ('who-supplies-americas-plastics', 'Eight of America\'s Top Plastic-Goods "Suppliers" Are Logistics Shells', D4, '2026-11-25')
R2 = ('who-supplies-americas-furniture', 'The 2.6-Kilogram Furniture Company', D5, '2026-11-26')
R3 = ('who-supplies-americas-auto-parts', 'The #1 "Chinese Supplier" of US Auto Parts Is Advance Auto Parts Itself', D6, '2026-11-26')
R4 = ('who-supplies-americas-lighting', 'The #1 "Chinese Supplier" of US Lighting Is a Thai Auto-Parts Factory', D7, '2026-11-26')

with open(os.path.join(ROOT, 'verify-1688-supplier/index.html'), 'w') as f:
    f.write(article_page(A1[0], t1_title, lede1, body1, D1, '2026-11-23',
                         'assets/img/a1/img-1.jpg',
                         [(R4[0], R4[1]), (R3[0], R3[1]), (R2[0], R2[1]), (R1[0], R1[1]), (A2[0], t2), (A3[0], t3)]))
with open(os.path.join(ROOT, 'us-import-data-buyers/index.html'), 'w') as f:
    f.write(article_page(A2[0], t2, l2, b2, D2, '2026-11-25',
                         'assets/img/a2/cover.png',
                         [(R4[0], R4[1]), (R3[0], R3[1]), (R2[0], R2[1]), (R1[0], R1[1]), (A1[0], t1_title), (A3[0], t3)]))
with open(os.path.join(ROOT, 'chinese-suv-landed-cost/index.html'), 'w') as f:
    f.write(article_page(A3[0], t3, l3, b3, D3, '2026-11-25',
                         'assets/img/a3/cover.png',
                         [(R4[0], R4[1]), (R3[0], R3[1]), (R2[0], R2[1]), (R1[0], R1[1]), (A1[0], t1_title), (A2[0], t2)]))

# ---------- Two-Sided Dossier reports (body extracted from the定版 samples) ----------
def dossier_body(path):
    src = open(path).read()
    content = src.split('<div class="wrap">', 1)[1]
    content = content.rsplit('</div>', 1)[0]
    content = re.sub(r'<div class="kicker">.*?</div>', '', content, flags=re.S)
    content = re.sub(r'<h1>.*?</h1>', '', content, flags=re.S)
    content = re.sub(r'<p class="sub">.*?</p>', '', content, flags=re.S)
    # public-site wording polish (internal file references / "sample" framing)
    content = content.replace('What this sample proves', 'What this episode proves')
    content = content.replace('This sample is a remote desk check', 'This dossier is a remote desk check')
    content = re.sub(r'Full evidence per company:.*?</p>',
                     'Every verdict above is backed by the underlying pull and identity files in our research archive.</p>',
                     content, flags=re.S)
    return content.strip()

def report_page(slug, title, lede, body_html, desc, date, og_img, others, pack_file, pack_desc):
    ep = re.search(r'(ep\d)', pack_file).group(1)
    more = '\n'.join(f'<li><a href="{BASE}/{s}/">{t}</a></li>' for s, t in others)
    return f'''{head(title + ' — Tavino', desc, f'/{slug}/', og_img, {'headline': title, 'date': date})}
<body>
{HEADER}
<main>
<article class="report">
<p class="meta">Tavino research · Two-Sided Dossier · {date}</p>
<h1>{html.escape(title)}</h1>
<p class="lede">{html.escape(lede)}</p>
<div class="dossier">
{body_html}
</div>
</article>
<section class="more"><h2>More Tavino research</h2><ul>{more}</ul></section>
{datapack_block(pack_file, pack_desc)}
{clarity_track_script(ep)}
</main>
{FOOTER}'''

CS = os.path.join(VA, 'combined-sample')
shutil.copy(os.path.join(CS, 'chart-kg-test.png'), os.path.join(ROOT, 'assets/img/reports/kg-test.png'))
# data packs (email-gated lead magnets; links go out via the Beehiiv welcome email)
for z in ['tavino-dossier-ep1-plastics-data.zip', 'tavino-dossier-ep2-furniture-data.zip',
          'tavino-dossier-ep3-autoparts-data.zip', 'tavino-dossier-ep4-lighting-data.zip']:
    shutil.copy(os.path.join(ROOT, 'downloads-src', z), os.path.join(ROOT, 'assets/downloads', z))
r1_body = dossier_body(os.path.join(CS, 'sample-hs3925-3926.html'))
r2_body = dossier_body(os.path.join(CS, 'sample-hs9401-9403-furniture.html'))
r3_body = dossier_body(os.path.join(CS, 'sample-hs8708-autoparts.html'))
r4_body = dossier_body(os.path.join(CS, 'sample-hs9405-lighting.html'))
R1_LEDE = 'US import records (demand side) × China-side identity check (supply side) — HS 3925 & 3926, US sea bills of lading, Jan 2015 – Nov 2026. Episode 1 of the Two-Sided Dossier series.'
R2_LEDE = 'US import records (demand side) × China-side identity check (supply side) — HS 9401 (seats) & HS 9403 (other furniture). Episode 2 of the Two-Sided Dossier series.'
PACK1 = 'The full data pack for this episode — the 9 identified shippers with verdicts and evidence, the real US buyers, and the PVC-blinds price band — as CSVs with a sources README.'
PACK2 = 'The full data pack for this episode — the 8 identified shippers with verdicts and evidence, the top-10 US importers for HS 9401 and HS 9403, and the Anji chair price band — as CSVs with a sources README.'
R3_LEDE = 'US import records (demand side) × China-side identity check (supply side) — HS 8708 (parts and accessories of motor vehicles). Episode 3 of the Two-Sided Dossier series.'
PACK3 = 'The full data pack for this episode — the 8 identified shippers with verdicts and evidence (plus the names just below the cut), the top-10 US importers for HS 8708, and the brake-disc price band — as CSVs with a sources README.'
R4_LEDE = 'US import records (demand side) × China-side identity check (supply side) — HS 9405 (luminaires and lighting fittings). Episode 4 of the Two-Sided Dossier series.'
PACK4 = 'The full data pack for this episode — the 8 identified shippers with verdicts and evidence (plus the names just below the cut), the top US importers for HS 9405, and the six export-listing price bands — as CSVs with a sources README.'
with open(os.path.join(ROOT, 'who-supplies-americas-plastics/index.html'), 'w') as f:
    f.write(report_page(R1[0], R1[1], R1_LEDE, r1_body, D4, '2026-11-25',
                        'assets/img/a2/cover.png',
                        [(R4[0], R4[1]), (R3[0], R3[1]), (R2[0], R2[1]), (A2[0], t2), (A1[0], t1_title), (A3[0], t3)],
                        'tavino-dossier-ep1-plastics-data.zip', PACK1))
with open(os.path.join(ROOT, 'who-supplies-americas-furniture/index.html'), 'w') as f:
    f.write(report_page(R2[0], R2[1], R2_LEDE, r2_body, D5, '2026-11-26',
                        'assets/img/reports/kg-test.png',
                        [(R4[0], R4[1]), (R3[0], R3[1]), (R1[0], R1[1]), (A2[0], t2), (A1[0], t1_title), (A3[0], t3)],
                        'tavino-dossier-ep2-furniture-data.zip', PACK2))
with open(os.path.join(ROOT, 'who-supplies-americas-auto-parts/index.html'), 'w') as f:
    f.write(report_page(R3[0], R3[1], R3_LEDE, r3_body, D6, '2026-11-26',
                        'assets/img/a2/cover.png',
                        [(R4[0], R4[1]), (R2[0], R2[1]), (R1[0], R1[1]), (A2[0], t2), (A1[0], t1_title), (A3[0], t3)],
                        'tavino-dossier-ep3-autoparts-data.zip', PACK3))
with open(os.path.join(ROOT, 'who-supplies-americas-lighting/index.html'), 'w') as f:
    f.write(report_page(R4[0], R4[1], R4_LEDE, r4_body, D7, '2026-11-26',
                        'assets/img/a2/cover.png',
                        [(R3[0], R3[1]), (R2[0], R2[1]), (R1[0], R1[1]), (A2[0], t2), (A1[0], t1_title), (A3[0], t3)],
                        'tavino-dossier-ep4-lighting-data.zip', PACK4))

# ---------- Thanks page (post-subscribe landing; not indexed, not in sitemap) ----------
thanks_head = head('Thanks — your data packs — Tavino',
                   'Thanks for subscribing. Your Tavino data packs are here.',
                   '/thanks/', 'assets/img/reports/kg-test.png')
thanks_head = thanks_head.replace('</head>', '<meta name="robots" content="noindex">\n</head>')
thanks = f'''{thanks_head}
<body>
{HEADER}
<main>
<article>
<p class="meta">Tavino research</p>
<h1>You're in — here are your data packs</h1>
<p class="lede">All episode packs, as CSVs with a sources README. Save them now; they are also in your welcome email.</p>
<ul>
<li><a href="{BASE}/who-supplies-americas-lighting/">Episode 4 — The #1 "Chinese Supplier" of US Lighting Is a Thai Auto-Parts Factory</a><br><a href="{BASE}/assets/downloads/tavino-dossier-ep4-lighting-data.zip">Download the lighting data pack (HS 9405, ZIP)</a> — 8 identified shippers, top US importers, six export-listing price bands</li>
<li><a href="{BASE}/who-supplies-americas-auto-parts/">Episode 3 — The #1 "Chinese Supplier" of US Auto Parts Is Advance Auto Parts Itself</a><br><a href="{BASE}/assets/downloads/tavino-dossier-ep3-autoparts-data.zip">Download the auto parts data pack (HS 8708, ZIP)</a> — 8 identified shippers, top-10 US importers, brake-disc price band</li>
<li><a href="{BASE}/who-supplies-americas-furniture/">Episode 2 — The 2.6-Kilogram Furniture Company</a><br><a href="{BASE}/assets/downloads/tavino-dossier-ep2-furniture-data.zip">Download the furniture data pack (HS 9401/9403, ZIP)</a> — 8 identified shippers, top-10 US importers, Anji chair price band</li>
<li><a href="{BASE}/who-supplies-americas-plastics/">Episode 1 — Eight of America's Top Plastic-Goods "Suppliers" Are Logistics Shells</a><br><a href="{BASE}/assets/downloads/tavino-dossier-ep1-plastics-data.zip">Download the plastics data pack (HS 3925/3926, ZIP)</a> — 9 identified shippers, real US buyers, PVC-blinds price band</li>
</ul>
<p><a href="{BASE}/">← Back to the research</a></p>
</article>
</main>
<script>
document.addEventListener("click", function(e){{
  var a = e.target.closest ? e.target.closest('a[href*="/assets/downloads/"]') : null;
  if (!a || !window.clarity) return;
  var m = (a.getAttribute("href") || "").match(/ep(\d)/);
  clarity("event", "datapack_click_ep" + (m ? m[1] : "x"));
}});
</script>
{FOOTER}'''
with open(os.path.join(ROOT, 'thanks/index.html'), 'w') as f:
    f.write(thanks)

# ---------- Homepage ----------
def cover_art(kicker, big, line):
    return (f'<div class="cover-art"><span class="ca-kicker">{html.escape(kicker)}</span>'
            f'<span class="ca-big">{html.escape(big)}</span>'
            f'<span class="ca-line">{html.escape(line)}</span></div>')

def dossier_card(slug, t, d, ep_label, big, line):
    return (f'<a class="card" href="{BASE}/{slug}/">{cover_art("Two-Sided Dossier", big, line)}'
            f'<div><span class="ep-tag">{html.escape(ep_label)}</span>'
            f'<h3>{html.escape(t)}</h3><p>{html.escape(d)}</p></div></a>\n')

def guide_card(slug, t, d, kicker, big, line):
    return (f'<a class="card" href="{BASE}/{slug}/">{cover_art(kicker, big, line)}'
            f'<div><h3>{html.escape(t)}</h3><p>{html.escape(d)}</p></div></a>\n')

featured = (f'<a class="card featured" href="{BASE}/{R4[0]}/">'
            + cover_art('Two-Sided Dossier · Latest', '0',
                        "identified Chinese household-lighting factories in the top eight")
            + f'<div><span class="ep-tag">Episode 4 · HS 9405</span>'
              f'<h3>{html.escape(R4[1])}</h3><p>{html.escape(D7)}</p></div></a>\n')

dossier_cards = ''
dossier_cards += dossier_card(R3[0], R3[1], D6, 'Episode 3 · HS 8708', '6 of 8',
                              'top suppliers are real factories — a first for this series')
dossier_cards += dossier_card(R2[0], R2[1], D5, 'Episode 2 · HS 9401/9403', '2.6 kg',
                              "average weight of one 'metal furniture' shipment by the #1 shipper")
dossier_cards += dossier_card(R1[0], R1[1], D4, 'Episode 1 · HS 3925/3926', '8 of 9',
                              'top shippers are logistics shells, not factories')

guide_cards = ''
guide_cards += guide_card(A2[0], t2, D2, 'Field note', '12.2M',
                          'plastic-parts bills of lading in the record — the buyers are not who the ranking says')
guide_cards += guide_card(A3[0], t3, D3, 'Field note', '$15,020',
                          'what an $8,900 Chery costs landed in Lagos — FOB, freight and the full tax stack')
guide_cards += guide_card(A1[0], t1_title, D1, 'Guide', '5 steps',
                          'the desk check to run on any 1688 supplier before money moves')
home_desc = 'Tavino researches China sourcing with real data: supplier verification, 1688 price snapshots and US import records. Get the free weekly brief.'
home = f'''{head('Tavino — China sourcing, verified', home_desc, '/', 'assets/img/a1/img-1.jpg')}
<body>
{HEADER}
<main>
<section class="hero">
<h1>China sourcing, verified.</h1>
<p class="lede">We check suppliers, track 1688 prices and read the import record — then publish what the data actually shows.</p>
</section>
<section id="research">
{featured}
<div class="sec-head"><h2>The Two-Sided Dossier</h2><span class="sec-note">Episode 4 is featured above</span></div>
<div class="cards">
{dossier_cards}</div>
<div class="sec-head"><h2>Guides &amp; Field Notes</h2></div>
<div class="cards">
{guide_cards}</div>
</section>
<section class="about">
<h2>What Tavino does</h2>
<p>Tavino is a China sourcing research desk for importers and online sellers. We verify suppliers before money moves, keep dated price snapshots of 1688 and Alibaba listings, and mine public import records to find who is really buying what. The research is published here first, and readers who want it in their inbox can subscribe at the bottom of any article.</p>
</section>
</main>
{FOOTER}'''
home = home.replace('<script type="text/javascript" async src="https://subscribe-forms.beehiiv.com/attribution.js"></script>', '')
with open(os.path.join(ROOT, 'index.html'), 'w') as f:
    f.write(home)

# ---------- sitemap + robots ----------
urls = ['/', '/who-supplies-americas-lighting/', '/who-supplies-americas-auto-parts/', '/who-supplies-americas-furniture/', '/who-supplies-americas-plastics/',
        '/verify-1688-supplier/', '/us-import-data-buyers/', '/chinese-suv-landed-cost/']
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u in urls:
    sm += f'<url><loc>{BASE}{u}</loc></url>\n'
sm += '</urlset>\n'
with open(os.path.join(ROOT, 'sitemap.xml'), 'w') as f:
    f.write(sm)
with open(os.path.join(ROOT, 'robots.txt'), 'w') as f:
    f.write(f'User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n')
open(os.path.join(ROOT, '.nojekyll'), 'w').write('')

print('BUILD OK')
for dirpath, _, files in os.walk(ROOT):
    for fn in sorted(files):
        p = os.path.join(dirpath, fn)
        print(os.path.relpath(p, ROOT), os.path.getsize(p))
