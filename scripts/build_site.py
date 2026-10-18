"""Wrap the artifact-format page in a real HTML document for standalone hosting.

Also points the page at the /api/* routes CloudFront serves from API Gateway.

The Artifact platform injects <!doctype>, <head>, charset and viewport at publish
time, so web/index.html deliberately has none. Any other host needs them.

    python scripts/build_site.py
"""
import os, re, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, "web", "index.html")
DIST = os.path.join(ROOT, "dist")

DESC = ("Compare negotiated hospital prices across Lehigh Valley Health Network "
        "and St. Luke's by insurer, procedure and ZIP code.")


src = open(SRC, encoding="utf-8").read()

# Everything before the page body is head material (<title>, fonts, <style>).
split = src.index('<div class="wrap">')
head, body = src[:split].strip(), src[split:].strip()

title = re.search(r"<title>(.*?)</title>", head).group(1)

doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{DESC}">
<meta name="color-scheme" content="light dark">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{DESC}">
<meta property="og:type" content="website">
<style>
  :root {{ color-scheme: light; padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }}
  body {{ margin: 0; }}
  img {{ max-width: 100%; }}
  [hidden] {{ display: none !important; }}
</style>
{head}
</head>
<body>
{body}
</body>
</html>
"""

os.makedirs(DIST, exist_ok=True)
open(os.path.join(DIST, "index.html"), "w", encoding="utf-8").write(doc)
for data in ("prices.json", "i18n.json"):
    shutil.copy(os.path.join(ROOT, "web", data), os.path.join(DIST, data))

for f in sorted(os.listdir(DIST)):
    print(f"  dist/{f:<14} {os.path.getsize(os.path.join(DIST, f)) / 1024:>7.0f} KB")
