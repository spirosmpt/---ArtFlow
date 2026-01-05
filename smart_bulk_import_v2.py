import os
import re
import time
import hashlib
import sqlite3
from typing import Optional, Dict, List, Tuple

import requests
from PIL import Image

"""
Smart bulk import (v2+) για τη βάση σου (db.py).

Τι κάνει:
1) Εξασφαλίζει/ενημερώνει τις demo αίθουσες (χωρίς να δημιουργεί διπλές) με prefix-match "Αίθουσα 1/2/3"
2) Κατεβάζει έργα από MET + Art Institute of Chicago
3) Δημιουργεί/ενημερώνει (upsert) καλλιτέχνες με περισσότερα πεδία (birth/death/nationality/info)
4) Εισάγει works και τα ταξινομεί σε αίθουσες με βάση ΕΠΟΧΗ (year buckets), ώστε σε κάθε αίθουσα να μπαίνουν και πίνακες και γλυπτά
5) (Προαιρετικά) γράφει placements history (αν υπάρχει ο πίνακας)

Σημείωση: Για να μην “βαραίνει” σε re-runs, κάνει early-skip τα works που υπάρχουν ήδη στη DB ΠΡΙΝ κατεβάσει εικόνα.
"""

# =========================
# CONFIG
# =========================
try:
    # ίδιο ακριβώς db file με την εφαρμογή (absolute path από db.py)
    from db import DB_NAME as DB_PATH  # type: ignore
except Exception:
    DB_PATH = "staff.db"  # fallback αν τρέχει standalone

OUT_DIR = "import_out"
IMG_DIR = os.path.join(OUT_DIR, "images")

MAX_IMAGE_PX = 1200
ONLY_PUBLIC_DOMAIN = True
PER_SOURCE_LIMIT = 30
MAX_TOTAL_WORKS = 80  # άλλαξέ το ελεύθερα

os.makedirs(IMG_DIR, exist_ok=True)
HEADERS = {"User-Agent": "ArtGallerySmartAgent/2.1 (educational project)"}

# =========================
# Helpers (generic)
# =========================
def safe_filename(s: str) -> str:
    s = re.sub(r"[^\w\-\. ]+", "", s, flags=re.UNICODE).strip()
    s = re.sub(r"\s+", "_", s)
    return (s[:140] if s else "item")

def normalize_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s]", "", s)
    return s

def split_name(full: str) -> Tuple[str, str]:
    full = (full or "").strip()
    if not full:
        return "", "Unknown"
    parts = full.split()
    if len(parts) == 1:
        return "", parts[0]
    return " ".join(parts[:-1]), parts[-1]

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def download_file(url: str, path: str, timeout=60):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    r = requests.get(url, stream=True, timeout=timeout, headers=HEADERS)
    r.raise_for_status()
    with open(path, "wb") as f:
        for chunk in r.iter_content(1024 * 128):
            if chunk:
                f.write(chunk)

def resize_image_in_place(path: str, max_px: int = 1200):
    with Image.open(path) as im:
        im = im.convert("RGB")
        w, h = im.size
        m = max(w, h)
        if m <= max_px:
            im.save(path, format="JPEG", quality=88, optimize=True)
            return
        scale = max_px / float(m)
        nw, nh = int(w * scale), int(h * scale)
        im = im.resize((nw, nh), Image.LANCZOS)
        im.save(path, format="JPEG", quality=88, optimize=True)

def parse_year(year_text: str) -> Optional[int]:
    if not year_text:
        return None
    m = re.search(r"(\d{4})", year_text)
    if not m:
        return None
    y = int(m.group(1))
    if 1000 <= y <= 2100:
        return y
    return None

def parse_dimensions_to_cm(dim_text: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    if not dim_text:
        return None, None, None
    t = dim_text.lower()
    cm_part = None
    m = re.search(r"([0-9][0-9\.,\s×x]+)\s*cm", t)
    if m:
        cm_part = m.group(1)
    if not cm_part:
        return None, None, None
    nums = re.findall(r"(\d+(?:[.,]\d+)?)", cm_part)
    vals = [float(n.replace(",", ".")) for n in nums[:3]]
    while len(vals) < 3:
        vals.append(None)
    return vals[0], vals[1], vals[2]

def auto_category(medium_or_type: str) -> str:
    """
    Το category το κρατάμε (για UI material/technique), αλλά ΔΕΝ επηρεάζει πλέον την αίθουσα.
    """
    t = normalize_text(medium_or_type)
    if any(k in t for k in ["sculpt", "bronze", "marble", "stone", "wood", "terracotta", "relief"]):
        return "Γλυπτό"
    if any(k in t for k in ["painting", "oil", "canvas", "tempera", "watercolor", "acrylic", "panel"]):
        return "Πίνακας"
    return "Πίνακας"

# =========================
# Helpers (artist enrichment)
# =========================
def parse_int_year(x) -> Optional[int]:
    try:
        y = int(str(x).strip())
        return y if 0 < y < 3000 else None
    except Exception:
        return None

def year_to_date(y: Optional[int], is_death: bool = False) -> Optional[str]:
    if not y:
        return None
    return f"{int(y):04d}-12-31" if is_death else f"{int(y):04d}-01-01"

def parse_life_years_from_text(text: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Πιάνει patterns τύπου '1840–1926' ή '1840-1926' μέσα σε bio strings.
    """
    if not text:
        return None, None
    m = re.search(r"(\d{4})\s*[–-]\s*(\d{4})", text)
    if m:
        return parse_int_year(m.group(1)), parse_int_year(m.group(2))
    return None, None

# =========================
# Sources: MET + AIC
# =========================
MET_BASE = "https://collectionapi.metmuseum.org/public/collection/v1"
AIC_BASE = "https://api.artic.edu/api/v1"

def met_search_ids(query: str) -> List[int]:
    r = requests.get(f"{MET_BASE}/search", params={"q": query, "hasImages": "true"}, timeout=30, headers=HEADERS)
    r.raise_for_status()
    return (r.json().get("objectIDs") or [])

def met_get_object(oid: int) -> Optional[dict]:
    r = requests.get(f"{MET_BASE}/objects/{oid}", timeout=30, headers=HEADERS)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()

def fetch_met(query: str, limit: int) -> List[dict]:
    ids = met_search_ids(query)[:limit]
    out = []
    for oid in ids:
        obj = met_get_object(oid)
        if not obj:
            continue
        img = obj.get("primaryImage") or ""
        if not img:
            continue
        is_pd = bool(obj.get("isPublicDomain", False))
        license_text = "Public Domain" if is_pd else "Unknown/Check Rights"
        out.append({
            "source": "met",
            "source_id": str(oid),
            "title": obj.get("title") or "",
            "artist_name": obj.get("artistDisplayName") or "",
            "year_text": obj.get("objectDate") or "",
            "medium": obj.get("medium") or "",
            "dimensions": obj.get("dimensions") or "",
            "image_url": img,
            "source_url": obj.get("objectURL") or "",
            "license": license_text,
            "credit": obj.get("creditLine") or "",

            # artist enrichment
            "artist_nationality": obj.get("artistNationality") or "",
            "artist_begin_year": obj.get("artistBeginDate") or "",
            "artist_end_year": obj.get("artistEndDate") or "",
            "artist_info": obj.get("artistDisplayBio") or "",
        })
        time.sleep(0.15)
    return out

def aic_search(query: str, limit: int) -> List[dict]:
    params = {
        "q": query,
        "limit": limit,
        "fields": "id,title,artist_title,date_display,medium_display,dimensions,api_link,image_id,is_public_domain"
    }
    r = requests.get(f"{AIC_BASE}/artworks/search", params=params, timeout=30, headers=HEADERS)
    r.raise_for_status()
    return (r.json().get("data") or [])

def aic_image_url(image_id: str, width: int = 2000) -> str:
    return f"https://www.artic.edu/iiif/2/{image_id}/full/{width},/0/default.jpg"

def fetch_aic(query: str, limit: int) -> List[dict]:
    rows = aic_search(query, limit=limit)
    out = []
    for row in rows:
        image_id = row.get("image_id")
        if not image_id:
            continue

        # Enrichment via api_link (artist_display + place_of_origin)
        artist_display = ""
        place_of_origin = ""
        try:
            if row.get("api_link"):
                rr = requests.get(row["api_link"], timeout=30, headers=HEADERS)
                rr.raise_for_status()
                data = (rr.json() or {}).get("data") or {}
                artist_display = data.get("artist_display") or ""
                place_of_origin = data.get("place_of_origin") or ""
        except Exception:
            pass

        is_pd = bool(row.get("is_public_domain", False))
        license_text = "Public Domain" if is_pd else "Unknown/Check Rights"

        out.append({
            "source": "aic",
            "source_id": str(row.get("id")),
            "title": row.get("title") or "",
            "artist_name": row.get("artist_title") or "",
            "year_text": row.get("date_display") or "",
            "medium": row.get("medium_display") or "",
            "dimensions": row.get("dimensions") or "",
            "image_url": aic_image_url(image_id, width=2000),
            "source_url": row.get("api_link") or "",
            "license": license_text,
            "credit": "",

            # artist enrichment (AIC)
            "artist_info": artist_display,
            "artist_nationality": place_of_origin,
            "artist_begin_year": "",
            "artist_end_year": "",
        })
    return out

# =========================
# SQLite helpers
# =========================
def connect_db(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con

def table_cols(con: sqlite3.Connection, table: str) -> set:
    cur = con.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    return {r["name"] for r in cur.fetchall()}

def get_tables(con: sqlite3.Connection) -> set:
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {r[0] for r in cur.fetchall()}

# ---- Halls: ensure + mapping (MIXED) ----
DEFAULT_HALLS = [
    (
        "Αίθουσα 1 – Πριν το 1800",
        "1",
        "Μικτή έκθεση (πίνακες & γλυπτά) από αρχαιότητα έως 18ο αιώνα."
    ),
    (
        "Αίθουσα 2 – 1800–1945",
        "2",
        "Μικτή έκθεση (πίνακες & γλυπτά) 19ος–αρχές 20ού αιώνα."
    ),
    (
        "Αίθουσα 3 – 1945–Σήμερα",
        "2",
        "Μικτή έκθεση (πίνακες & γλυπτά) μεταπολεμική, μοντέρνα & σύγχρονη τέχνη."
    ),
]

def _hall_prefix(name: str) -> str:
    # π.χ. "Αίθουσα 2 – 1800–1945" -> "Αίθουσα 2"
    return (name.split("–")[0]).strip()

def get_or_update_hall_id(con: sqlite3.Connection, name: str, floor: str = "", notes: str = "") -> int:
    """
    1) Αν υπάρχει exact name -> ενημερώνει floor/notes, επιστρέφει id
    2) Αλλιώς, αν υπάρχει κάτι που ξεκινάει με "Αίθουσα X%" -> κάνει UPDATE σε αυτό (rename + floor/notes)
    3) Αλλιώς -> INSERT
    """
    cur = con.cursor()

    # 1) exact match
    cur.execute("SELECT id FROM halls WHERE name = ? LIMIT 1", (name,))
    row = cur.fetchone()
    if row:
        hid = int(row["id"])
        cur.execute("UPDATE halls SET floor = ?, notes = ? WHERE id = ?", (floor, notes, hid))
        return hid

    # 2) prefix match
    prefix = _hall_prefix(name)  # "Αίθουσα 1"
    cur.execute("SELECT id FROM halls WHERE name LIKE ? ORDER BY id LIMIT 1", (prefix + "%",))
    row = cur.fetchone()
    if row:
        hid = int(row["id"])
        cur.execute(
            "UPDATE halls SET name = ?, floor = ?, notes = ? WHERE id = ?",
            (name, floor, notes, hid),
        )
        return hid

    # 3) insert
    cur.execute("INSERT INTO halls (name, floor, notes) VALUES (?, ?, ?)", (name, floor, notes))
    return int(cur.lastrowid)

def ensure_halls(con: sqlite3.Connection, hall_specs=DEFAULT_HALLS) -> Dict[str, int]:
    name_to_id: Dict[str, int] = {}
    for name, floor, notes in hall_specs:
        hid = get_or_update_hall_id(con, name, floor=floor, notes=notes)
        name_to_id[name] = hid
    con.commit()
    return name_to_id

def assign_hall_name(category: str, year: Optional[int]) -> str:
    """
    ΝΕΟΣ κανόνας: ΜΟΝΟ με βάση year (ώστε κάθε αίθουσα να έχει και πίνακες και γλυπτά).

    - year < 1800 -> Αίθουσα 1
    - 1800 <= year < 1945 -> Αίθουσα 2
    - year >= 1945 -> Αίθουσα 3
    - year None -> Αίθουσα 2 (default)
    """
    if year is None:
        return "Αίθουσα 2 – 1800–1945"
    if year < 1800:
        return "Αίθουσα 1 – Πριν το 1800"
    if year < 1945:
        return "Αίθουσα 2 – 1800–1945"
    return "Αίθουσα 3 – 1945–Σήμερα"

# ---- Artists / Works ----
def find_artist_id(con: sqlite3.Connection, first_name: str, last_name: str) -> Optional[int]:
    cur = con.cursor()
    cur.execute(
        "SELECT id FROM artists WHERE lower(first_name) = lower(?) AND lower(last_name) = lower(?) LIMIT 1",
        (first_name or "", last_name or "")
    )
    row = cur.fetchone()
    return int(row["id"]) if row else None

def upsert_artist(
    con: sqlite3.Connection,
    first_name: str,
    last_name: str,
    birth_date: Optional[str] = None,
    death_date: Optional[str] = None,
    nationality: Optional[str] = None,
    specialty: Optional[str] = None,
    info: Optional[str] = None,
) -> Tuple[int, bool]:
    """
    Επιστρέφει (artist_id, was_inserted).
    Αν υπάρχει ήδη, ενημερώνει ΜΟΝΟ τα πεδία που είναι κενά/NULL.
    """
    cur = con.cursor()
    artist_id = find_artist_id(con, first_name, last_name)

    if artist_id is None:
        cur.execute(
            """
            INSERT INTO artists (first_name, last_name, birth_date, death_date, nationality, specialty, info)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                first_name or "",
                last_name or "Unknown",
                birth_date,
                death_date,
                nationality,
                specialty,
                info,
            ),
        )
        return int(cur.lastrowid), True

    cur.execute(
        "SELECT birth_date, death_date, nationality, specialty, info FROM artists WHERE id = ?",
        (artist_id,),
    )
    row = cur.fetchone()

    def is_blank(v) -> bool:
        return v is None or str(v).strip() == ""

    updates = {}
    if birth_date and is_blank(row["birth_date"]):
        updates["birth_date"] = birth_date
    if death_date and is_blank(row["death_date"]):
        updates["death_date"] = death_date
    if nationality and is_blank(row["nationality"]):
        updates["nationality"] = nationality
    if specialty and is_blank(row["specialty"]):
        updates["specialty"] = specialty
    if info and is_blank(row["info"]):
        updates["info"] = info

    if updates:
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        cur.execute(
            f"UPDATE artists SET {set_clause} WHERE id = ?",
            [*updates.values(), artist_id],
        )

    return artist_id, False

def find_work_exists(con: sqlite3.Connection, title: str, artist_id: int, year: Optional[int]) -> bool:
    cur = con.cursor()
    if year is None:
        cur.execute(
            "SELECT 1 FROM works WHERE lower(title)=lower(?) AND artist_id=? AND year IS NULL LIMIT 1",
            (title, artist_id)
        )
    else:
        cur.execute(
            "SELECT 1 FROM works WHERE lower(title)=lower(?) AND artist_id=? AND year=? LIMIT 1",
            (title, artist_id, year)
        )
    return cur.fetchone() is not None

def insert_placement(con: sqlite3.Connection, work_id: int, hall_id: int):
    """
    placements table υπάρχει στη νέα βάση (history τοποθέτησης).
    Αν δεν υπάρχει, το αγνοούμε.
    """
    if "placements" not in get_tables(con):
        return
    cur = con.cursor()
    start_date = time.strftime("%Y-%m-%d")
    cur.execute(
        "INSERT INTO placements (work_id, hall_id, start_date, end_date) VALUES (?, ?, ?, NULL)",
        (work_id, hall_id, start_date)
    )

def insert_work(con: sqlite3.Connection, w: dict) -> int:
    """
    Insert στο works με column-list ώστε να μην σπάει αν υπάρχουν extra columns.
    Για UI:
    - Πίνακας: technique = medium, material = ""
    - Γλυπτό: material = medium, technique = ""
    """
    works_cols = table_cols(con, "works")

    cols = [
        "title", "year", "height_cm", "width_cm", "depth_cm", "weight_kg",
        "condition", "production_place", "artist_id", "notes", "image_path",
        "category", "material", "technique", "hall_id"
    ]
    vals = [
        w["title"], w.get("year"), w.get("height_cm"), w.get("width_cm"), w.get("depth_cm"), w.get("weight_kg"),
        w.get("condition"), w.get("production_place"), w.get("artist_id"), w.get("notes"), w.get("image_path"),
        w.get("category"), w.get("material"), w.get("technique"), w.get("hall_id")
    ]

    if "is_external" in works_cols:
        cols.append("is_external")
        vals.append(int(w.get("is_external", 0)))

    if "is_archived" in works_cols:
        cols.append("is_archived")
        vals.append(0)

    cur = con.cursor()
    placeholders = ",".join(["?"] * len(cols))
    cur.execute(
        f"INSERT INTO works ({','.join(cols)}) VALUES ({placeholders})",
        vals
    )
    return int(cur.lastrowid)

# =========================
# Main import
# =========================
def canonical_key(src: dict) -> str:
    return "|".join([
        normalize_text(src.get("title", "")),
        normalize_text(src.get("artist_name", "")),
        normalize_text(src.get("year_text", ""))[:8],
    ])

def run_bulk_import(queries: List[str]):
    con = connect_db(DB_PATH)
    tables = get_tables(con)
    if "halls" not in tables or "artists" not in tables or "works" not in tables:
        raise RuntimeError("Η βάση δεν φαίνεται αρχικοποιημένη. Τρέξε πρώτα την εφαρμογή σου ή το init_db().")

    hall_map = ensure_halls(con)
    seen_keys = set()
    seen_hashes = set()

    inserted_artists = 0
    inserted_works = 0
    skipped_pd = 0
    skipped_dupe = 0
    skipped_fail = 0

    for q in queries:
        items: List[dict] = []
        items += fetch_met(q, PER_SOURCE_LIMIT)
        items += fetch_aic(q, PER_SOURCE_LIMIT)

        for src in items:
            if ONLY_PUBLIC_DOMAIN and src.get("license") != "Public Domain":
                skipped_pd += 1
                continue

            key = canonical_key(src)
            if key in seen_keys:
                skipped_dupe += 1
                continue

            title = (src.get("title") or "").strip()
            if not title:
                skipped_fail += 1
                continue

            # ---- artist upsert (με enrichment) ----
            artist_display = (src.get("artist_name") or "").strip() or "Unknown"
            first_name, last_name = split_name(artist_display)

            by = parse_int_year(src.get("artist_begin_year"))
            dy = parse_int_year(src.get("artist_end_year"))

            # Αν AIC: συνήθως τα χρόνια είναι μέσα στο artist_info (artist_display)
            if (by is None or dy is None) and src.get("artist_info"):
                tby, tdy = parse_life_years_from_text(src["artist_info"])
                by = by or tby
                dy = dy or tdy

            birth_date = year_to_date(by, is_death=False)
            death_date = year_to_date(dy, is_death=True)

            nationality = (src.get("artist_nationality") or "").strip() or None
            info = (src.get("artist_info") or "").strip() or None

            artist_id, was_inserted = upsert_artist(
                con,
                first_name=first_name,
                last_name=last_name,
                birth_date=birth_date,
                death_date=death_date,
                nationality=nationality,
                specialty="καλλιτέχνης",
                info=info,
            )
            if was_inserted:
                inserted_artists += 1

            # ---- early dupe skip (πριν κατεβάσεις εικόνα) ----
            year_int = parse_year(src.get("year_text") or "")
            if find_work_exists(con, title, artist_id, year_int):
                skipped_dupe += 1
                seen_keys.add(key)
                continue

            # ---- download image ----
            try:
                fn = safe_filename(f"{src['source']}_{src['source_id']}_{title}_{last_name}") + ".jpg"
                img_path = os.path.join(IMG_DIR, fn)
                download_file(src["image_url"], img_path)
                resize_image_in_place(img_path, max_px=MAX_IMAGE_PX)
                img_hash = sha256_file(img_path)
            except Exception:
                skipped_fail += 1
                continue

            if img_hash in seen_hashes:
                try:
                    os.remove(img_path)
                except Exception:
                    pass
                skipped_dupe += 1
                seen_keys.add(key)
                continue

            # ---- parse metadata ----
            h_cm, w_cm, d_cm = parse_dimensions_to_cm(src.get("dimensions") or "")
            category = auto_category(src.get("medium") or "")

            # ---- hall assignment (year-based) ----
            hall_name = assign_hall_name(category, year_int)
            hall_id = hall_map.get(hall_name)
            if hall_id is None:
                hall_id = next(iter(hall_map.values()))

            # notes / provenance
            notes_lines = []
            if src.get("source_url"):
                notes_lines.append(f"Source URL: {src['source_url']}")
            notes_lines.append(f"Source: {src.get('source')} id={src.get('source_id')}")
            if src.get("license"):
                notes_lines.append(f"License: {src['license']}")
            if src.get("credit"):
                notes_lines.append(f"Credit: {src['credit']}")
            notes = "\n".join(notes_lines)

            medium = (src.get("medium") or "").strip()

            # UI-friendly material/technique mapping
            if category == "Πίνακας":
                technique = medium or ""
                material = ""
            else:
                material = medium or ""
                technique = ""

            work_obj = {
                "title": title,
                "year": year_int,
                "height_cm": h_cm,
                "width_cm": w_cm,
                "depth_cm": d_cm,
                "weight_kg": None,
                "condition": None,
                "production_place": None,
                "artist_id": artist_id,
                "notes": notes,
                "image_path": img_path.replace("\\", "/"),
                "category": category,
                "material": material,
                "technique": technique,
                "hall_id": hall_id,
                "is_external": 0,
            }

            work_id = insert_work(con, work_obj)
            inserted_works += 1



            seen_keys.add(key)
            seen_hashes.add(img_hash)

            if inserted_works >= MAX_TOTAL_WORKS:
                con.commit()
                con.close()
                print(f"Reached MAX_TOTAL_WORKS={MAX_TOTAL_WORKS}. Stopping.")
                print("=== IMPORT SUMMARY ===")
                print(f"Inserted artists: {inserted_artists}")
                print(f"Inserted works:   {inserted_works}")
                print(f"Skipped (not PD): {skipped_pd}")
                print(f"Skipped (dupe):   {skipped_dupe}")
                print(f"Skipped (fail):   {skipped_fail}")
                print(f"Images saved in:  {IMG_DIR}")
                return

        con.commit()

    con.close()
    print("=== IMPORT SUMMARY ===")
    print(f"Inserted artists: {inserted_artists}")
    print(f"Inserted works:   {inserted_works}")
    print(f"Skipped (not PD): {skipped_pd}")
    print(f"Skipped (dupe):   {skipped_dupe}")
    print(f"Skipped (fail):   {skipped_fail}")
    print(f"Images saved in:  {IMG_DIR}")

if __name__ == "__main__":
    queries = [
        "claude monet",
        "vincent van gogh",
        "pablo picasso",
        "caravaggio",
        "auguste rodin",
    ]
    run_bulk_import(queries)
