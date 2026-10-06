#!/usr/bin/env python3
"""Récupère classement + score des participants Hash Code 2017 depuis la Wayback Machine.

Usage :
    pip install requests beautifulsoup4
    python hashcode_scraper.py                 # affiche + écrit hashcode_2017.csv
    python hashcode_scraper.py --dump          # inspecte la structure de la page
    python hashcode_scraper.py --file page.html  # parse un HTML déjà téléchargé
"""
import argparse
import csv
import re
import sys

import requests
from bs4 import BeautifulSoup

# "id_" après le timestamp = HTML brut, sans la barre / réécriture de liens de la Wayback Machine
URL = ("https://web.archive.org/web/20170301161741id_/"
       "https://hashcode.withgoogle.com/hashcode_2017.html")

INT_RE = re.compile(r"^\d+$")
SCORE_RE = re.compile(r"^\d{1,3}(?:[ ,.\u202f\u00a0]\d{3})*$|^\d+$")


def fetch(url: str) -> str:
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    r.raise_for_status()
    return r.text


def to_int(text: str) -> int:
    return int(re.sub(r"\D", "", text))


def parse_row(cells: list[str]):
    """Devine rang / nom / score à partir des cellules d'une ligne."""
    cells = [c for c in (c.strip() for c in cells) if c]
    if len(cells) < 2:
        return None
    rank = next((c for c in cells if INT_RE.match(c)), None)
    if rank is None:
        return None
    rest = list(cells)
    rest.remove(rank)  # retire uniquement la première occurrence
    # score = la cellule numérique la plus grande parmi les restantes
    numeric = [c for c in rest if SCORE_RE.match(c)]
    if not numeric:
        return None
    score = max(numeric, key=to_int)
    names = [c for c in rest if c != score]
    name = max(names, key=len) if names else ""
    return {"rank": int(rank), "team": name, "score": to_int(score)}


def parse_tables(soup: BeautifulSoup):
    rows = []
    for tr in soup.select("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
        row = parse_row(cells)
        if row:
            rows.append(row)
    return rows


def parse_divs(soup: BeautifulSoup):
    """Fallback si le classement n'est pas dans un <table> (div/li avec classes)."""
    rows = []
    for el in soup.find_all(["li", "div"], class_=re.compile(r"row|team|rank|entry|item", re.I)):
        children = [c.get_text(" ", strip=True) for c in el.find_all(recursive=False)]
        row = parse_row(children)
        if row:
            rows.append(row)
    return rows


def dump(soup: BeautifulSoup):
    print(f"<title> : {soup.title.string if soup.title else None}")
    print(f"Tables : {len(soup.find_all('table'))}, lignes <tr> : {len(soup.find_all('tr'))}")
    print("\n--- Scripts / JSON potentiels ---")
    for s in soup.find_all("script", src=True):
        print(" script:", s["src"])
    for a in soup.find_all("a", href=re.compile(r"\.(json|csv)", re.I)):
        print(" lien  :", a["href"])
    print("\n--- Début du <body> ---")
    body = soup.body or soup
    print(body.prettify()[:3000])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="fichier HTML local au lieu de télécharger")
    ap.add_argument("--dump", action="store_true", help="afficher la structure de la page")
    ap.add_argument("--out", default="hashcode_2017.csv")
    args = ap.parse_args()

    html = open(args.file, encoding="utf-8").read() if args.file else fetch(URL)
    soup = BeautifulSoup(html, "html.parser")

    if args.dump:
        dump(soup)
        return

    rows = parse_tables(soup) or parse_divs(soup)
    if not rows:
        sys.exit("Aucun classement trouvé dans le HTML. Le tableau est probablement chargé en "
                 "JavaScript : relance avec --dump pour repérer un fichier JSON à récupérer.")

    rows.sort(key=lambda r: r["rank"])
    for r in rows:
        print(f"{r['rank']:>5}  {r['score']:>10}  {r['team']}")

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["rank", "team", "score"])
        w.writeheader()
        w.writerows(rows)
    print(f"\n{len(rows)} lignes écrites dans {args.out}")


if __name__ == "__main__":
    main()
