#!/usr/bin/env python3
"""Post-process the wget snapshot of https://monaf.ai into a self-contained static backup.

- copies the new favicon set (brand/) into the site root and declares it in every page
- canonical / og:url / hreflang always point at https://monaf.ai (never the mirror)
- robots meta -> noindex,follow and a Disallow-all robots.txt (backup, not a duplicate)
- strips client JS (SSR HTML is complete; hydrating under /mondex-mirror/ fails) so the
  backup renders the same content with zero requests to monaf.ai / *.grok.me
- rewrites any remaining absolute monaf.ai asset URLs to relative paths
"""
import os, re, shutil, sys, json, posixpath

SITE = sys.argv[1] if len(sys.argv) > 1 else "site"
ORIGIN = "https://monaf.ai"
BRAND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "brand")

for f in os.listdir(BRAND):
    shutil.copy(os.path.join(BRAND, f), os.path.join(SITE, f))

def route_for(rel):
    r = rel[:-5]  # strip .html
    if r == "index": return "/"
    if r.endswith("/index"): r = r[:-6]
    return "/" + r

def relprefix(rel):
    depth = rel.count("/")
    return "../" * depth

ICON_RE = re.compile(r'<link\b[^>]*\brel="(?:icon|shortcut icon|apple-touch-icon)"[^>]*/?>', re.I)
SCRIPT_RE = re.compile(r'<script\b(?![^>]*application/ld\+json)[^>]*>.*?</script>', re.I | re.S)
PRELOAD_RE = re.compile(r'<link\b[^>]*\brel="modulepreload"[^>]*/?>', re.I)

n = 0
for root, _, files in os.walk(SITE):
    for f in files:
        if not f.endswith(".html"): continue
        path = os.path.join(root, f)
        rel = os.path.relpath(path, SITE).replace(os.sep, "/")
        route = route_for(rel)
        url = ORIGIN + route if route != "/" else ORIGIN + "/"
        p = relprefix(rel)
        h = open(path, encoding="utf-8", errors="replace").read()
        h = ICON_RE.sub("", h)
        h = SCRIPT_RE.sub("", h)
        h = PRELOAD_RE.sub("", h)
        h = re.sub(r'<link\b[^>]*\brel="canonical"[^>]*/?>', "", h, flags=re.I)
        h = re.sub(r'<link\b[^>]*\brel="alternate"[^>]*hrefLang[^>]*/?>', "", h, flags=re.I)
        h = re.sub(r'<meta\b[^>]*\bname="robots"[^>]*/?>', "", h, flags=re.I)
        h = re.sub(r'<meta\b[^>]*\bproperty="og:url"[^>]*/?>', "", h, flags=re.I)
        # absolute asset URLs on monaf.ai / mondex.grok.me -> relative (only in src/href)
        def fix(m):
            attr, u = m.group(1), m.group(2)
            local = u.split("://", 1)[1].split("/", 1)[1] if "/" in u.split("://", 1)[1] else ""
            local = local.split("?")[0]
            if local and os.path.exists(os.path.join(SITE, local)):
                return f'{attr}="{p}{local}"'
            return m.group(0)
        h = re.sub(r'\b(src|href)="(https://(?:monaf\.ai|mondex\.grok\.me)/[^"]*)"', fix, h)
        head = (
            f'<link rel="canonical" href="{url}"/>'
            f'<link rel="alternate" hreflang="en" href="{url}"/>'
            f'<meta name="robots" content="noindex, follow"/>'
            f'<meta property="og:url" content="{url}"/>'
            f'<link rel="icon" href="{p}favicon.ico" sizes="any"/>'
            f'<link rel="icon" type="image/png" sizes="32x32" href="{p}favicon-32.png"/>'
            f'<link rel="icon" type="image/png" sizes="192x192" href="{p}favicon-192.png"/>'
            f'<link rel="apple-touch-icon" sizes="180x180" href="{p}apple-touch-icon.png"/>'
        )
        h = re.sub(r"<head\b[^>]*>", lambda m: m.group(0) + head, h, count=1, flags=re.I)
        open(path, "w", encoding="utf-8").write(h)
        n += 1

# manifest: relative icon paths so it works under /mondex-mirror/
mf = os.path.join(SITE, "__grok", "manifest.webmanifest")
if os.path.exists(mf):
    try:
        m = json.load(open(mf))
    except Exception:
        m = {"name": "MONAF"}
    m["icons"] = [
        {"src": "../favicon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "../icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "../apple-touch-icon.png", "sizes": "180x180", "type": "image/png"},
    ]
    m["start_url"] = "../"; m["scope"] = "../"; m.pop("id", None)
    json.dump(m, open(mf, "w"), indent=2)

open(os.path.join(SITE, "robots.txt"), "w").write(
    "# Read-only backup of https://monaf.ai - not for indexing\nUser-agent: *\nDisallow: /\n")
open(os.path.join(SITE, "404.html"), "w").write(
    '<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex">'
    '<title>MONAF backup</title><link rel="icon" href="/mondex-mirror/favicon.ico">'
    '<p>Not in the backup. <a href="https://monaf.ai/">monaf.ai</a> · <a href="./">backup home</a></p>')
print(f"postprocessed {n} html files")
