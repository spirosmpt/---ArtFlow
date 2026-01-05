"""

Λειτουργίες πρόσβασης στη βάση (SQLite) για την εφαρμογή:
- Δημιουργία/αναβάθμιση schema (init_db)
- CRUD για προσωπικό, καλλιτέχνες, έργα, εκθέσεις, δανεισμούς, συντήρηση, ξεναγήσεις, εισιτήρια
- Reports / στατιστικά
"""

from __future__ import annotations

import random
import sqlite3
import hashlib
from datetime import date, timedelta, datetime

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "staff.db")


def hash_password(password: str) -> str:
    """Επιστρέφει SHA-256 hash για τον κωδικό πρόσβασης."""

    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def connect_db():
    """Ανοίγει σύνδεση SQLite στη βάση της εφαρμογής."""

    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Δημιουργεί όλους τους πίνακες και βάζει demo δεδομένα αν λείπουν."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()



   
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT  NOT NULL,
            conservator_id INTEGER,
            condition   TEXT NOT NULL,
            start DATE,
            end   DATE,
            notes TEXT,
            work_id INTEGER NOT NULL,
            FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE,
            FOREIGN KEY (conservator_id) REFERENCES conservators(staff_id)
       
        )
        """ 
    )
    
   

    # -------- staff --------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name    TEXT NOT NULL,
            last_name    TEXT NOT NULL,
            pn           varchar(10),
            wage        INTEGER,
            email       varchar(100),
            address     TEXT,
            staff_type TEXT
            
        )
        """
    )
    cur.execute("PRAGMA table_info(staff)")
    columns = [col[1] for col in cur.fetchall()]
    if "staff_type" not in columns:
        cur.execute("ALTER TABLE staff ADD COLUMN staff_type TEXT")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS guides (
            staff_id INTEGER PRIMARY KEY,
            language TEXT,
            num INTEGER,
            FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE

        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS conservators (
            staff_id INTEGER PRIMARY KEY,
            specialization TEXT ,
            FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
            
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS admins (
            staff_id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
        )


        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS curators (
            staff_id INTEGER PRIMARY KEY,
            specialization TEXT,
            exp varchar(100),
            FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
            
        )
        """
    )

    # halls (Αίθουσες) 
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS halls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL,
            floor TEXT,
            notes TEXT
        )
        """
    )

    # ΕΙΣΙΤΗΡΙΑ (Tickets)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ticket_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL DEFAULT 0,
            active INTEGER NOT NULL DEFAULT 1,
            online_enabled INTEGER NOT NULL DEFAULT 1,
            requires_proof INTEGER NOT NULL DEFAULT 0,
            notes TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ticket_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            channel TEXT NOT NULL DEFAULT 'cashier',      -- cashier / online
            customer_email TEXT,
            payment_method TEXT NOT NULL DEFAULT 'cash',  -- cash / card / online
            status TEXT NOT NULL DEFAULT 'paid',          -- paid / canceled / refunded
            total REAL NOT NULL DEFAULT 0,
            cashier_staff_id INTEGER,
            refund_reason TEXT,
            refunded_at TEXT,
            FOREIGN KEY (cashier_staff_id) REFERENCES staff(id) ON DELETE SET NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ticket_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            ticket_type_id INTEGER NOT NULL,
            qty INTEGER NOT NULL DEFAULT 1,
            unit_price REAL NOT NULL DEFAULT 0,
            line_total REAL NOT NULL DEFAULT 0,
            visit_date TEXT,                 -- 'YYYY-MM-DD'
            tour_session_id INTEGER,          -- nullable
            exhibition_id INTEGER,            -- nullable
            FOREIGN KEY (order_id) REFERENCES ticket_orders(id) ON DELETE CASCADE,
            FOREIGN KEY (ticket_type_id) REFERENCES ticket_types(id) ON DELETE RESTRICT,
            FOREIGN KEY (tour_session_id) REFERENCES tour_sessions(id) ON DELETE SET NULL, 
            FOREIGN KEY (exhibition_id) REFERENCES exhibitions(id) ON DELETE SET NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            ticket_code TEXT NOT NULL UNIQUE,
            ticket_type_id INTEGER NOT NULL,
            visit_date TEXT NOT NULL,         -- 'YYYY-MM-DD'
            status TEXT NOT NULL DEFAULT 'valid',   -- valid / used / canceled
            checked_in_at TEXT,
            checkin_staff_id INTEGER,
            tour_session_id INTEGER,
            exhibition_id INTEGER,
            FOREIGN KEY (order_id) REFERENCES ticket_orders(id) ON DELETE CASCADE,
            FOREIGN KEY (ticket_type_id) REFERENCES ticket_types(id) ON DELETE RESTRICT,
            FOREIGN KEY (checkin_staff_id) REFERENCES staff(id) ON DELETE SET NULL,
            FOREIGN KEY (tour_session_id) REFERENCES tour_sessions(id) ON DELETE SET NULL,
            FOREIGN KEY (exhibition_id) REFERENCES exhibitions(id) ON DELETE SET NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ticket_scan_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scanned_at TEXT DEFAULT CURRENT_TIMESTAMP,
            code TEXT,
            result TEXT,          -- VALID / USED / INVALID / CANCELED / WRONG_DATE / UNDO
            staff_id INTEGER,
            notes TEXT,
            FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE SET NULL
        )
    """)


    # ΞΕΝΑΓΗΣΕΙΣ (Tour Sessions)
   
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tour_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            start_dt TEXT NOT NULL,      -- ISO: 'YYYY-MM-DD HH:MM'
            end_dt   TEXT NOT NULL,      -- ISO: 'YYYY-MM-DD HH:MM'
            language TEXT,
            guide_staff_id INTEGER,
            tour_type TEXT,
            capacity INTEGER DEFAULT 0,
            status TEXT DEFAULT 'scheduled',  -- scheduled / in-progress / completed / canceled
            exhibition_id INTEGER,
            hall_id INTEGER,
            notes TEXT,
            cancellation_reason TEXT,
            checklist_json TEXT,
            FOREIGN KEY (guide_staff_id) REFERENCES staff(id) ON DELETE SET NULL,
            FOREIGN KEY (exhibition_id) REFERENCES exhibitions(id) ON DELETE SET NULL,
            FOREIGN KEY (hall_id) REFERENCES halls(id) ON DELETE SET NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tour_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            group_name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            people_count INTEGER DEFAULT 1,
            language_pref TEXT,
            payment_status TEXT DEFAULT 'unpaid',  -- unpaid / paid / comp
            comments TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES tour_sessions(id) ON DELETE CASCADE
        )
        """
    )


    # default αίθουσες 
    cur.execute("SELECT COUNT(*) FROM halls")
    if cur.fetchone()[0] == 0:
        halls_sample = [
    (
        "Αίθουσα 1 – Πριν το 1800-από αρχαιότητα έως 18ο αιώνα",
        "1",
        "Μικτή έκθεση (πίνακες & γλυπτά) από αρχαιότητα έως 18ο αιώνα."
    ),
    (
        "Αίθουσα 2 – 19ος–αρχές 20ού αιώνα",
        "2",
        "Μικτή έκθεση (πίνακες & γλυπτά) 19ος–αρχές 20ού αιώνα."
    ),
    (
        "Αίθουσα 3 – 1945–Σήμερα,μεταπολεμική, μοντέρνα & σύγχρονη τέχνη",
        "2",
        "Μικτή έκθεση (πίνακες & γλυπτά) μεταπολεμική, μοντέρνα & σύγχρονη τέχνη."
    ),
]

        cur.executemany(
            "INSERT INTO halls (name, floor, notes) VALUES (?, ?, ?)",
            halls_sample,
        )



     

    # -------- exhibitions --------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS exhibitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            start_date  TEXT NOT NULL,
            end_date    TEXT,
            num_works   INTEGER DEFAULT 0,
            curator_id INTEGER,
            max_seats  INTEGER,
            description TEXT,
            FOREIGN KEY (curator_id) REFERENCES staff(id) ON DELETE SET NULL
        )

        """
    )

    # migrations για exhibitions
    
    cur.execute("PRAGMA table_info(exhibitions)")
    cols = {row[1] for row in cur.fetchall()}
    if "end_date" not in cols:
        cur.execute("ALTER TABLE exhibitions ADD COLUMN end_date TEXT")
    if "num_works" not in cols:
        cur.execute("ALTER TABLE exhibitions ADD COLUMN num_works INTEGER DEFAULT 0")
    if "curator_id" not in cols:
        cur.execute("ALTER TABLE exhibitions ADD COLUMN curator_id INTEGER")
    if "max_seats" not in cols:
        cur.execute("ALTER TABLE exhibitions ADD COLUMN max_seats INTEGER")


    # exhibition_works (σύνδεση εκθέσεων με έργα) 
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS exhibition_works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exhibition_id INTEGER NOT NULL,
            work_id INTEGER NOT NULL,
            note TEXT,
            display_order INTEGER DEFAULT 0,
            FOREIGN KEY (exhibition_id) REFERENCES exhibitions(id) ON DELETE CASCADE,
            FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE,
            UNIQUE(exhibition_id, work_id)
        )
        """
    )



    # -------- artists --------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name   TEXT,
            last_name    TEXT NOT NULL,
            birth_date   TEXT,      -- 'YYYY-MM-DD'
            death_date   TEXT,      -- 'YYYY-MM-DD'
            nationality  TEXT,
            specialty    TEXT,      -- ζωγράφος, γλύπτης 
            info         TEXT
        )

        """
    )
        # migration για specialty αν λείπει
    cur.execute("PRAGMA table_info(artists)")
    acols = {row[1] for row in cur.fetchall()}
    if "specialty" not in acols:
        cur.execute("ALTER TABLE artists ADD COLUMN specialty TEXT")


    # -------- works --------

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title            TEXT NOT NULL,
            year             INTEGER,
            height_cm        REAL,
            width_cm         REAL,
            depth_cm         REAL,
            weight_kg        REAL,
            condition        TEXT,
            production_place TEXT,
            artist_id        INTEGER,
            notes            TEXT,
            image_path       TEXT,
            category         TEXT,  -- Πίνακας, Γλυπτό, ...
            material         TEXT,  -- Υλικό
            technique        TEXT,  -- Τεχνική
            hall_id          INTEGER,
            FOREIGN KEY (artist_id) REFERENCES artists(id),
            FOREIGN KEY (hall_id) REFERENCES halls(id)
        )
        """
    )
    cur.execute("PRAGMA table_info(works)")
    columns = [col[1] for col in cur.fetchall()]

    if "date_added" not in columns:
        cur.execute("ALTER TABLE works ADD COLUMN date_added TEXT")


    # migration για image_path / category / material / technique
    cur.execute("PRAGMA table_info(works)")
    wcols = {row[1] for row in cur.fetchall()}
    if "image_path" not in wcols:
        cur.execute("ALTER TABLE works ADD COLUMN image_path TEXT")
    if "category" not in wcols:
        cur.execute("ALTER TABLE works ADD COLUMN category TEXT")
    if "material" not in wcols:
        cur.execute("ALTER TABLE works ADD COLUMN material TEXT")
    if "technique" not in wcols:
        cur.execute("ALTER TABLE works ADD COLUMN technique TEXT")
    if "hall_id" not in wcols:
        cur.execute("ALTER TABLE works ADD COLUMN hall_id INTEGER")




    # migration για image_path (αν έχεις παλιά έκδοση works)
    cur.execute("PRAGMA table_info(works)")
    wcols = {row[1] for row in cur.fetchall()}
    if "image_path" not in wcols:
        cur.execute("ALTER TABLE works ADD COLUMN image_path TEXT")


    # DEFAULT δεδομένα


    # staff

    cur.execute(
        """
        INSERT OR IGNORE INTO staff (username, password_hash, first_name, last_name, pn, wage, email, address)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("worker1", hash_password("1234"), "Worker", "One", None, None, None, None),
    )



    # default ticket types 
    cur.execute("SELECT COUNT(*) FROM ticket_types")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO ticket_types (name, price, active, online_enabled, requires_proof, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            ("Adult",   10.0, 1, 1, 0, ""),
            ("Student",  6.0, 1, 1, 1, "Απαιτείται φοιτητική ταυτότητα"),
            ("Child",    4.0, 1, 1, 0, ""),
            ("Group",    8.0, 1, 0, 0, "Τιμή ανά άτομο για ομάδες"),
        ])



    # exhibitions
    cur.execute("SELECT COUNT(*)     FROM exhibitions")
    if cur.fetchone()[0] == 0:
        from datetime import date, timedelta
        today = date.today()
        sample = [
            (
                "Έκθεση Φωτογραφίας",
                (today + timedelta(days=1)).isoformat(),
                (today + timedelta(days=10)).isoformat(),
                40,
                "Σύγχρονη φωτογραφία από Έλληνες καλλιτέχνες.",
            ),
            (
                "Αρχαιολογικά Ευρήματα",
                (today + timedelta(days=3)).isoformat(),
                (today + timedelta(days=20)).isoformat(),
                60,
                "Νέα ευρήματα από πρόσφατες ανασκαφές.",
            ),
            (
                "Σύγχρονη Τέχνη",
                (today + timedelta(days=10)).isoformat(),
                (today + timedelta(days=25)).isoformat(),
                25,
                "Έκθεση νέων δημιουργών.",
            ),
        ]
        cur.executemany(
            """
            INSERT INTO exhibitions (title, start_date, end_date, num_works, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            sample,
        )


    #artists
    cur.execute("SELECT COUNT(*) FROM artists")
    if cur.fetchone()[0] == 0:
        artists_sample = [
            ("Γιάννης", "Παπαδόπουλος", "1970-05-10", None,
             "Ελληνική", "Ζωγράφος",
             "Σύγχρονος Έλληνας ζωγράφος."),
            ("Μαρία", "Νικολάου", "1982-09-21", None,
             "Ελληνική", "Φωτογράφος",
             "Φωτογράφος, ειδικεύεται σε αστικό τοπίο."),
        ]
        cur.executemany(
            """
            INSERT INTO artists
                (first_name, last_name, birth_date, death_date, nationality, specialty, info)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            artists_sample,
        )


    #works
    cur.execute("SELECT COUNT(*) FROM works")
    if cur.fetchone()[0] == 0:
        cur.execute("SELECT id FROM artists ORDER BY id ASC")
        artist_ids = [row[0] for row in cur.fetchall()]
        a1 = artist_ids[0] if len(artist_ids) > 0 else None
        a2 = artist_ids[1] if len(artist_ids) > 1 else None

        works_sample = [
            ("Θάλασσα", 2010, 80.0, 120.0, None, 5.5, "Καλή",
             "Αθήνα", a1, "Λάδι σε καμβά.", None),
            ("Νύχτα στην πόλη", 2018, 60.0, 90.0, None, 4.2, "Άριστη",
             "Θεσσαλονίκη", a2, "Φωτογραφία μεγάλης ανάλυσης.", None),
        ]
        cur.executemany(
            """
            INSERT INTO works
                (title, year, height_cm, width_cm, depth_cm, weight_kg,
                 condition, production_place, artist_id, notes, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            works_sample,
        )


    #  borrowers (δανειστές) 
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS borrowers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,   -- Επωνυμία / Όνομα
            borrower_type TEXT,            -- Ιδιώτης, Μουσείο, Πινακοθήκη, Ίδρυμα
            country       TEXT,
            email         TEXT,
            address       TEXT,
            phone         TEXT,
            notes         TEXT
        )
        """
    )

    # - loans (δανεισμοί)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_id      INTEGER NOT NULL,
            borrower_id  INTEGER NOT NULL,
            start_date   TEXT NOT NULL,  -- 'YYYY-MM-DD'
            end_date     TEXT,           -- προγραμματισμένη λήξη
            return_date  TEXT,           -- πραγματική επιστροφή
            notes        TEXT,
            FOREIGN KEY (work_id)     REFERENCES works(id) ON DELETE CASCADE,
            FOREIGN KEY (borrower_id) REFERENCES borrowers(id) ON DELETE CASCADE
        )
        """
    )
    ensure_schema()
    # Επιτρέπουμε μόνο 1 ενεργό δανεισμό ανά έργο (return_date IS NULL)
    cur.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_loans_one_active ON loans(work_id) WHERE return_date IS NULL"
    )


    # migration: is_external (εξωτερικό έργο που είναι δανεισμένο σε εμάς)
    cur.execute("PRAGMA table_info(works)")
    wcols = {row[1] for row in cur.fetchall()}
    if "is_external" not in wcols:
        cur.execute("ALTER TABLE works ADD COLUMN is_external INTEGER NOT NULL DEFAULT 0")
    # migration: is_archived (soft delete)
    cur.execute("PRAGMA table_info(works)")
    wcols = {row[1] for row in cur.fetchall()}
    if "is_archived" not in wcols:
        cur.execute("ALTER TABLE works ADD COLUMN is_archived INTEGER NOT NULL DEFAULT 0")




    # migration: direction (IN/OUT)
    cur.execute("PRAGMA table_info(loans)")
    lcols = {row[1] for row in cur.fetchall()}
    if "direction" not in lcols:
        cur.execute("ALTER TABLE loans ADD COLUMN direction TEXT NOT NULL DEFAULT 'OUT'")
        cur.execute("UPDATE loans SET direction='OUT' WHERE direction IS NULL")


    # Default borrowers 
    cur.execute("SELECT COUNT(*) FROM borrowers")
    if cur.fetchone()[0] == 0:
        borrowers_sample = [
            ("Εθνική Πινακοθήκη", "Πινακοθήκη", "Ελλάδα", "info@example.com", "Αθήνα", "2100000000", "Demo δανειστής"),
            ("Museum of Modern Art", "Μουσείο", "USA", "contact@example.com", "New York", "0000000000", ""),
        ]
        cur.executemany(
            """
            INSERT INTO borrowers (name, borrower_type, country, email, address, phone, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            borrowers_sample,
        )

     # migration: tour_bookings link με ticket orders + status 
    cur.execute("PRAGMA table_info(tour_bookings)")
    bcols = {row[1] for row in cur.fetchall()}
    if "ticket_order_id" not in bcols:
        cur.execute("ALTER TABLE tour_bookings ADD COLUMN ticket_order_id INTEGER")
    if "status" not in bcols:
        cur.execute("ALTER TABLE tour_bookings ADD COLUMN status TEXT NOT NULL DEFAULT 'active'")



    #cur.execute("DELETE FROM staff")
    
    conn.commit()
    conn.close()




#Staff helpers 


def get_user_if_valid(username: str, password: str):
    """Επιστρέφει dict με στοιχεία χρήστη αν είναι σωστός, αλλιώς None."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, first_name,last_name, password_hash FROM staff WHERE username = ?",
        (username,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    user_id, uname, first_name,last_name, pwd_hash = row
    if pwd_hash != hash_password(password):
        return None
    full_name = f"{first_name} {last_name}".strip()

    return {"id": user_id, "username": uname, "full_name": full_name}


# ---------------- Exhibitions helpers ---------------------
def get_exhibition_work_items(exhibition_id: int):
    """
    Επιστρέφει μόνο τα items που είναι συνδεδεμένα σε μια έκθεση:
    [{"work_id": 1, "note": "...", "order": 1}, ...]
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT work_id, note, display_order
        FROM exhibition_works
        WHERE exhibition_id = ?
        ORDER BY display_order ASC, id ASC
    """, (exhibition_id,))
    rows = cur.fetchall()
    conn.close()

    return [
        {"work_id": r[0], "note": r[1] or "", "order": int(r[2] or 0)}
        for r in rows
    ]


def get_upcoming_exhibitions(days_ahead=30, limit=5):
    """Επιστρέφει επερχόμενες εκθέσεις (>= σήμερα, μέχρι days_ahead) για notifications."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT title, start_date, end_date, num_works, description
        FROM exhibitions
        ORDER BY start_date ASC
        """
    )
    rows = cur.fetchall()
    conn.close()

    today = date.today()
    upcoming = []

    for title, start_date, end_date, num_works, description in rows:
        try:
            ev_date = date.fromisoformat(start_date)
        except Exception:
            continue

        delta_days = (ev_date - today).days
        if 0 <= delta_days <= days_ahead:
            upcoming.append(
                {
                    "title": title,
                    "start_date": start_date,
                    "end_date": end_date,
                    "num_works": num_works or 0,
                    "description": description or "",
                }
            )

    return upcoming[:limit]

def get_exhibitions_count_this_month_upcoming() -> int:
    """Πόσες εκθέσεις υπάρχουν από σήμερα μέχρι τέλος του μήνα,
    συμπεριλαμβάνοντας όσες ξεκίνησαν παλιότερα αλλά τρέχουν ακόμα."""
    today = date.today()

    #1η μέρα του επόμενου μήνα
    if today.month == 12:
        first_next_month = date(today.year + 1, 1, 1)
    else:
        first_next_month = date(today.year, today.month + 1, 1)

    end_of_month = first_next_month - timedelta(days=1)

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM exhibitions
        WHERE start_date <= ?
          AND (CASE
                 WHEN end_date IS NULL OR TRIM(end_date) = '' THEN start_date
                 ELSE end_date
               END) >= ?
        """,
        (end_of_month.isoformat(), today.isoformat()),
    )

    count = int(cur.fetchone()[0] or 0)
    conn.close()
    return count




def get_all_exhibition_dates():
    """Επιστρέφει όλες τις ημερομηνίες ΕΝΑΡΞΗΣ εκθέσεων (για calendar highlight)."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT start_date, title FROM exhibitions")
    rows = cur.fetchall()
    conn.close()
    return rows  # list of (date_str, title)


def get_exhibitions_count():
    """Πόσες εκθέσεις υπάρχουν συνολικά στη βάση."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM exhibitions")
    count = cur.fetchone()[0]
    conn.close()
    return count


def get_exhibition_works(exhibition_id: int):
    """Ανάκτηση δεδομένων από τη βάση (SELECT)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    cur.execute("""
        SELECT
            ew.work_id,
            ew.note,
            ew.display_order,
            w.title,
            w.year,
            a.first_name,
            a.last_name
        FROM exhibition_works ew
        JOIN works w ON w.id = ew.work_id
        LEFT JOIN artists a ON a.id = w.artist_id
        WHERE ew.exhibition_id = ?
        ORDER BY ew.display_order ASC, w.title ASC
    """, (exhibition_id,))

    rows = cur.fetchall()
    conn.close()

    out = []
    for work_id, note, display_order, title, year, fn, ln in rows:
        artist = f"{(fn or '').strip()} {(ln or '').strip()}".strip()
        out.append({
            "work_id": work_id,
            "note": note or "",
            "order": display_order or 0,
            "title": title,
            "year": year,
            "artist_name": artist
        })
    return out



def get_all_exhibitions():
    """Επιστρέφει ΟΛΕΣ τις εκθέσεις με id, για πίνακες κλπ."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT e.id, e.title, e.start_date, e.end_date, e.num_works, e.description,
               e.curator_id,
               (CASE WHEN s.id IS NULL THEN '' ELSE (COALESCE(s.last_name,'') || ' ' || COALESCE(s.first_name,'')) END) AS curator_name,
               e.max_seats,
               (SELECT COUNT(*) FROM tickets t
                 WHERE t.exhibition_id = e.id
                   AND LOWER(COALESCE(t.status,'valid')) != 'canceled') AS reserved_seats
        FROM exhibitions e
        LEFT JOIN staff s ON s.id = e.curator_id
        ORDER BY e.start_date ASC
    """)

    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "title": r[1],
            "start_date": r[2],
            "end_date": r[3],
            "curator_id": r[6],
            "curator_name": (r[7] or "").strip(),
            "max_seats": r[8],
            "reserved_seats": r[9] or 0,
            "num_works": r[4] or 0,
            "description": r[5] or "",
        }
        for r in rows
    ]


def add_exhibition(title: str, start_date: str, end_date: str, num_works: int, description: str,
                  curator_id=None, max_seats=None):
    """Εισάγει νέα εγγραφή στη βάση (INSERT)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO exhibitions (title, start_date, end_date, num_works, curator_id, max_seats, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (title, start_date, end_date, num_works, curator_id, max_seats, description),
    )
    conn.commit()
    conn.close()






def delete_exhibition(ex_id: int):
    """Διαγράφει/αρχειοθετεί εγγραφή στη βάση."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM exhibitions WHERE id = ?", (ex_id,))
    conn.commit()
    conn.close()


def add_exhibition_returning_id(title: str, start_date: str, end_date: str, num_works: int, description: str,
                                curator_id=None, max_seats=None):
    """Εισάγει νέα εγγραφή στη βάση (INSERT)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    cur.execute(
        """
        INSERT INTO exhibitions (title, start_date, end_date, num_works, curator_id, max_seats, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (title, start_date, end_date, num_works, curator_id, max_seats, description),
    )
    ex_id = cur.lastrowid
    conn.commit()
    conn.close()
    return ex_id


def add_exhibition_works(exhibition_id: int, items: list[dict]):
    """
    items: [{"work_id": 12, "note": "...", "order": 1}, ...]
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    rows = []
    for it in items:
        work_id = int(it["work_id"])
        note = it.get("note", "")
        order = int(it.get("order", 0))
        rows.append((exhibition_id, work_id, note, order))

    cur.executemany(
        """
        INSERT OR IGNORE INTO exhibition_works (exhibition_id, work_id, note, display_order)
        VALUES (?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    conn.close()


def update_exhibition(ex_id: int, title: str, start_date: str, end_date: str, num_works: int, description: str,
                      curator_id=None, max_seats=None):
    """Ενημερώνει υπάρχουσα εγγραφή στη βάση (UPDATE)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE exhibitions
        SET title = ?, start_date = ?, end_date = ?, num_works = ?, curator_id = ?, max_seats = ?, description = ?
        WHERE id = ?
        """,
        (title, start_date, end_date, num_works, curator_id, max_seats, description, ex_id),
    )
    conn.commit()
    conn.close()



def set_exhibition_works(exhibition_id: int, items):
    """
    items: [{"work_id": 1, "note": "...", "order": 1}, ...]
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    # καθάρισμα παλιών
    cur.execute("DELETE FROM exhibition_works WHERE exhibition_id = ?", (exhibition_id,))

    # insert νέων
    rows = []
    for it in (items or []):
        rows.append((
            exhibition_id,
            int(it["work_id"]),
            it.get("note", ""),
            int(it.get("order", 0))
        ))

    cur.executemany("""
        INSERT INTO exhibition_works (exhibition_id, work_id, note, display_order)
        VALUES (?, ?, ?, ?)
    """, rows)

    # ενημέρωση num_works
    cur.execute("""
        UPDATE exhibitions
        SET num_works = (SELECT COUNT(*) FROM exhibition_works WHERE exhibition_id = ?)
        WHERE id = ?
    """, (exhibition_id, exhibition_id))

    conn.commit()
    conn.close()

# ---------------- Artists helpers -------------------------


def get_all_artists():
    """Ανάκτηση δεδομένων από τη βάση (SELECT)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, first_name, last_name, birth_date, death_date,
               nationality, specialty, info
        FROM artists
        ORDER BY last_name, first_name
        """
    )

    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "first_name": r[1] or "",
            "last_name": r[2] or "",
            "birth_date": r[3],
            "death_date": r[4],
            "nationality": r[5] or "",
            "specialty": r[6] or "",
            "info": r[7] or "",
        }
        for r in rows
    ]



def add_artist(first_name, last_name, birth_date, death_date, nationality, specialty, info):
    """Εισάγει νέα εγγραφή στη βάση (INSERT)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO artists
            (first_name, last_name, birth_date, death_date, nationality, specialty, info)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (first_name, last_name, birth_date, death_date, nationality, specialty, info),
    )
    conn.commit()
    conn.close()



def update_artist(artist_id, first_name, last_name, birth_date, death_date, nationality, specialty, info):
    """Ενημερώνει υπάρχουσα εγγραφή στη βάση (UPDATE)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE artists
        SET first_name = ?, last_name = ?, birth_date = ?, death_date = ?,
            nationality = ?, specialty = ?, info = ?
        WHERE id = ?
        """,
        (first_name, last_name, birth_date, death_date, nationality, specialty, info, artist_id),
    )
    conn.commit()
    conn.close()



def delete_artist(artist_id):
    """Διαγράφει/αρχειοθετεί εγγραφή στη βάση."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM artists WHERE id = ?", (artist_id,))
    conn.commit()
    conn.close()

# ---------------- Works (Έργα) helpers --------------------


def get_all_works():
    """Επιστρέφει όλα τα έργα μαζί με καλλιτέχνη και αίθουσα."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT
            w.id, w.title, w.year,
            w.height_cm, w.width_cm, w.depth_cm, w.weight_kg,
            w.condition, w.production_place,
            w.artist_id,
            w.notes,
            w.image_path,
            w.category,
            w.material,
            w.technique,
            w.hall_id,
            COALESCE(w.is_external, 0) AS is_external,
            a.first_name, a.last_name,
            a.specialty,
            h.name,
            l.id,            -- active_loan_id
            l.direction,     -- loan_direction
            l.start_date,    -- loan_start_date
            l.end_date,      -- loan_end_date
            b.name           -- borrower_name
        FROM works w
        LEFT JOIN artists a   ON w.artist_id = a.id
        LEFT JOIN halls   h   ON w.hall_id = h.id
        LEFT JOIN loans   l   ON l.work_id = w.id AND l.return_date IS NULL
        LEFT JOIN borrowers b ON b.id = l.borrower_id
        WHERE COALESCE(w.is_archived,0) = 0
        ORDER BY w.title ASC
    """)


    rows = cur.fetchall()
    conn.close()

    works = []
    for r in rows:
        is_external = int(r[16] or 0)
        artist_first = (r[17] or "").strip()
        artist_last = (r[18] or "").strip()
        artist_name = ""
        if artist_first or artist_last:
            artist_name = f"{artist_first} {artist_last}".strip()

        works.append(
            {
                "id": r[0],
                "title": r[1],
                "year": r[2],
                "height_cm": r[3],
                "width_cm": r[4],
                "depth_cm": r[5],
                "weight_kg": r[6],
                "condition": r[7] or "",
                "production_place": r[8] or "",
                "artist_id": r[9],
                "notes": r[10] or "",
                "image_path": r[11],
                "category": r[12] or "",
                "material": r[13] or "",
                "technique": r[14] or "",
                "hall_id": r[15],
    
                "artist_first_name": artist_first,
                "artist_last_name": artist_last,
                "artist_name": artist_name,
                "artist_specialty": (r[19] or "").strip(),
                "hall_name": (r[20] or "").strip() if r[20] else "",

                "active_loan_id": r[21],
                "loan_direction": (r[22] or "OUT").strip().upper(),   # ✅ ΝΕΟ (και σωστό)
                "loan_start_date": r[23] or "",
                "loan_end_date": r[24] or "",
                "borrower_name": (r[25] or "").strip(),

                "is_external": bool(is_external),


            }
        )
    return works





def add_work(title, year, height_cm, width_cm, depth_cm, weight_kg,
             condition, production_place, artist_id, notes,
             image_path, category, material, technique, hall_id,is_external=0):

    """Εισάγει νέα εγγραφή στη βάση (INSERT)."""

    conn = sqlite3.connect(DB_NAME)
    today = date.today()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO works
            (title, year, height_cm, width_cm, depth_cm, weight_kg,
             condition, production_place, artist_id, notes,
             image_path, category, material, technique, hall_id,is_external,date_added)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?)
        """,
        (title, year, height_cm, width_cm, depth_cm, weight_kg,
         condition, production_place, artist_id, notes,
         image_path, category, material, technique, hall_id,is_external,today),
    )
    work_id = cur.lastrowid  # παίρνουμε το ID του νέου
    if condition in ("Μέτρια", "Κακή", "Χρειάζεται"):
        if category == "Πίνακας":
            spec = "Συντήρηση Ζωγραφικής"
            maint_type = "Καθαρισμός καμβά / επιφάνειας"
        elif category == "Γλυπτό":
            spec = "Συντήρηση Γλυπτών"
            maint_type = "Καθαρισμός γλυπτού / σταθεροποίηση"
        else:
            spec = None
            maint_type = "Καθαρισμός επιφανείας"
        cur.execute("""
        SELECT staff_id 
        FROM conservators
        WHERE specialization = ?
        """, (spec,))
        eligible = cur.fetchall()
    
        conservator_id = random.choice(eligible)[0] if eligible else None
        cur.execute("SELECT COUNT(*) FROM maintenance")
        total_maint = cur.fetchone()[0]
        batch_index = total_maint // 10
        start_date = today + timedelta(days=7 * (batch_index + 1))



        cur.execute(
        """
        INSERT INTO maintenance (type, condition, start, notes, work_id,conservator_id)
        VALUES (?, ?, ?, ?, ?,?)
        """,
        (maint_type, condition, start_date, "", work_id,conservator_id)
        )
    conn.commit()
    conn.close()
    return work_id





def update_work(work_id, title, year, height_cm, width_cm, depth_cm, weight_kg,
                condition, production_place, artist_id, notes,
                image_path, category, material, technique, hall_id, is_external=0):

    """Ενημερώνει υπάρχουσα εγγραφή στη βάση (UPDATE)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Update το έργο
    cur.execute(
        """
        UPDATE works
        SET title = ?, year = ?, height_cm = ?, width_cm = ?, depth_cm = ?,
            weight_kg = ?, condition = ?, production_place = ?,
            artist_id = ?, notes = ?, image_path = ?,
            category = ?, material = ?, technique = ?, hall_id = ?, is_external = ?
        WHERE id = ?
        """,
        (title, year, height_cm, width_cm, depth_cm, weight_kg,
         condition, production_place, artist_id, notes,
         image_path, category, material, technique, hall_id, is_external, work_id),
    )
    # --- AUTO maintenance based on condition (EDIT
    today = date.today()

    # Αν έγινε Καλή/Άριστη -> κλείσε (end) ό,τι maintenance είναι ανοιχτό για αυτό το έργο
    if condition in ("Καλή", "Άριστη"):
        cur.execute(
            "UPDATE maintenance SET end = ? WHERE work_id = ? AND end IS NULL",
            (today, work_id),
        )

    # Αν έγινε Μέτρια/Κακή/Χρειάζεται -> αν δεν υπάρχει ανοιχτό maintenance, φτιάξε ένα
    if condition in ("Μέτρια", "Κακή", "Χρειάζεται"):
        cur.execute(
            "SELECT id FROM maintenance WHERE work_id = ? AND end IS NULL LIMIT 1",
            (work_id,),
        )
        exists = cur.fetchone()

        if not exists:
            # specialization + type ανά κατηγορία
            if category == "Πίνακας":
                spec = "Συντήρηση Ζωγραφικής"
                maint_type = "Καθαρισμός καμβά / επιφάνειας"
            elif category == "Γλυπτό":
                spec = "Συντήρηση Γλυπτών"
                maint_type = "Καθαρισμός γλυπτού / σταθεροποίηση"
            else:
                spec = None
                maint_type = "Καθαρισμός επιφανείας"

            eligible = []
            if spec:
                cur.execute(
                    "SELECT staff_id FROM conservators WHERE specialization = ?",
                    (spec,),
                )
                eligible = cur.fetchall()

            conservator_id = random.choice(eligible)[0] if eligible else None

            # σπάσιμο ημερομηνιών: 10 συντηρήσεις ανά εβδομάδα
            cur.execute("SELECT COUNT(*) FROM maintenance")
            total_maint = cur.fetchone()[0] or 0
            batch_index = total_maint // 10
            start_date = today + timedelta(days=7 * (batch_index + 1))

            cur.execute(
                """
                INSERT INTO maintenance (type, condition, start, notes, work_id, conservator_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (maint_type, condition, start_date, "", work_id, conservator_id),
            )
        else:
            # υπάρχει ήδη ανοιχτό maintenance -> απλά ενημέρωσε την condition
            cur.execute(
                "UPDATE maintenance SET condition = ? WHERE work_id = ? AND end IS NULL",
                (condition, work_id),
            )


    conn.commit()
    conn.close()






def delete_work(work_id):
    """Διαγράφει/αρχειοθετεί εγγραφή στη βάση."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM maintenance WHERE work_id = ?", (work_id,))
    cur.execute("DELETE FROM works WHERE id = ?", (work_id,))
    conn.commit()
    conn.close()



    
def get_works_overview_stats():
    """
    Επιστρέφει stats για dashboard:
    - total_active: όλα τα έργα που είναι ενεργά (όχι archived)
    - owned_active: ενεργά έργα που είναι δικά μας (is_external=0)
    - borrowed_in_active: ενεργά έργα που είναι δανεισμένα σε εμάς (is_external=1)
    - loaned_out_active: πόσοι ενεργοί δανεισμοί OUT (δανείζουμε εμείς) χωρίς return_date
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # όλα τα ενεργά έργα (όχι archived)
    cur.execute("SELECT COUNT(*) FROM works WHERE is_archived=0")
    total_active = cur.fetchone()[0] or 0

    # σύνολο δικών μας (ανεξάρτητα αν είναι OUT)
    cur.execute("SELECT COUNT(*) FROM works WHERE is_archived=0 AND COALESCE(is_external,0)=0")
    owned_total_active = cur.fetchone()[0] or 0

    # δικά μας ΕΝΤΟΣ (δηλ. όχι ενεργό OUT loan)
    cur.execute("""
        SELECT COUNT(*)
        FROM works w
        LEFT JOIN loans l
               ON l.work_id = w.id
              AND l.return_date IS NULL
              AND UPPER(COALESCE(l.direction,'OUT'))='OUT'
        WHERE w.is_archived=0
          AND COALESCE(w.is_external,0)=0
          AND l.id IS NULL
    """)
    owned_in_house_active = cur.fetchone()[0] or 0

    # έργα που δανειζόμαστε (όπως το είχες)
    cur.execute("SELECT COUNT(*) FROM works WHERE is_archived=0 AND COALESCE(is_external,0)=1")
    borrowed_in_active = cur.fetchone()[0] or 0

    # OUT: μέτρα ΜΟΝΟ loans που αντιστοιχούν σε υπαρκτό, ενεργό work (για να μη σε χαλάνε παλιά/σβησμένα)
    cur.execute("""
        SELECT COUNT(DISTINCT l.work_id)
        FROM loans l
        JOIN works w ON w.id = l.work_id
        WHERE w.is_archived=0
          AND l.return_date IS NULL
          AND UPPER(COALESCE(l.direction,'OUT'))='OUT'
    """)
    loaned_out_active = cur.fetchone()[0] or 0

    conn.close()

    return {
        "total_active": total_active,
        # για συμβατότητα: κάνουμε το owned_active = "δικά μας εντός"
        "owned_active": owned_in_house_active,
        # και κρατάμε και το σύνολο δικών μας αν θες να το δείχνεις
        "owned_total_active": owned_total_active,
        "borrowed_in_active": borrowed_in_active,
        "loaned_out_active": loaned_out_active,
    }

def get_staff_count() -> int:
    """Σύνολο προσωπικού."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM staff")
    count = int(cur.fetchone()[0] or 0)
    conn.close()
    return count


def get_staff_overview_stats() -> dict:
    """
    Breakdown προσωπικού ανά τύπο (guide/conservator/curator/admins).
    Βασίζεται στο staff.staff_type που αποθηκεύεις (guide, conservator, curator, admins).
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM staff")
    total = int(cur.fetchone()[0] or 0)

    def count_type(t):
        """Βοηθητική συνάρτηση βάσης δεδομένων."""

        cur.execute("SELECT COUNT(*) FROM staff WHERE LOWER(COALESCE(staff_type,'')) = ?", (t,))
        return int(cur.fetchone()[0] or 0)

    guides = count_type("guide")
    conservators = count_type("conservator")
    curators = count_type("curator")
    admins = count_type("admins")

    conn.close()
    return {
        "total": total,
        "guides": guides,
        "conservators": conservators,
        "curators": curators,
        "admins": admins,
    }




def get_all_halls():
    """Ανάκτηση δεδομένων από τη βάση (SELECT)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, name, floor, notes FROM halls ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "name": r[1],
            "floor": r[2] or "",
            "notes": r[3] or "",
        }
        for r in rows
    ]


def get_hall_name_by_id(hall_id):
    """Ανάκτηση δεδομένων από τη βάση (SELECT)."""

    if hall_id is None:
        return ""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT name FROM halls WHERE id = ?", (hall_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else ""



            #------------------------------------------------------------
            # ----------------MANAGE STAFF------------------------------
            #   ----------------------------------------------------------
def get_staff():
    """Ανάκτηση δεδομένων από τη βάση (SELECT)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, first_name, last_name, pn, wage, email, address, staff_type
        FROM staff
        ORDER BY last_name, first_name
    """)
    rows = cur.fetchall()

    out = []

    for r in rows:
        staff_id = r[0]
        staff_type = r[7]

        specialization = None
        language = None

        if staff_type == "conservator":
            cur.execute(
                "SELECT specialization FROM conservators WHERE staff_id=?",
                (staff_id,)
            )
            row = cur.fetchone()
            if row:
                specialization = row[0]

        elif staff_type == "guide":
            cur.execute(
                "SELECT language FROM guides WHERE staff_id=?",
                (staff_id,)
            )
            row = cur.fetchone()
            if row:
                language = row[0]

        elif staff_type == "curator":
            cur.execute(
                "SELECT specialization FROM curators WHERE staff_id=?",
                (staff_id,)
            )
            row = cur.fetchone()
            if row:
                specialization = row[0]

        out.append({
            "id": staff_id,
            "first_name": r[1],
            "last_name": r[2],
            "pn": r[3],
            "wage": r[4],
            "email": r[5],
            "address": r[6],
            "staff_type": staff_type,
            "specialization": specialization,
            "language": language
        })

    conn.close()
    return out




def get_staff_by_id(staff_id: int):
    """Ανάκτηση δεδομένων από τη βάση (SELECT)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, username, first_name, last_name, pn, wage, email, address, staff_type
        FROM staff
        WHERE id=?
    """, (staff_id,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return None

    staff_type = r[8]
    staff = {
        "id": r[0],
        "username": r[1],
        "first_name": r[2],
        "last_name": r[3],
        "pn": r[4],
        "wage": r[5],
        "email": r[6],
        "address": r[7],
        "staff_type": staff_type,
        "specialization": None,
        "language": None
    }

    if staff_type == "conservator":
        cur.execute("SELECT specialization FROM conservators WHERE staff_id=?", (staff_id,))
        c = cur.fetchone()
        if c:
            staff["specialization"] = c[0]

    elif staff_type == "guide":
        cur.execute("SELECT language FROM guides WHERE staff_id=?", (staff_id,))
        g = cur.fetchone()
        if g:
            staff["language"] = g[0]

    elif staff_type == "curator":
        cur.execute("SELECT specialization FROM curators WHERE staff_id=?", (staff_id,))
        c = cur.fetchone()
        if c:
            staff["specialization"] = c[0]

    conn.close()
    return staff


   
    
    



def add_staff_member(first_name, last_name, pn, wage, email, address,
                     staff_type=None, specialization=None, language=None, username=None, password=None):
    """Εισάγει νέα εγγραφή στη βάση (INSERT)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    # Δημιουργία username και password αν δεν δοθούν
    username = username or f"user_{random.randint(1000, 9999)}"
    default_password = hashlib.sha256("1234".encode()).hexdigest()
    password_hash = hash_password(password) if password else default_password

    # Εισαγωγή στον πίνακα staff
    cur.execute(
        """
        INSERT INTO staff (first_name, last_name, pn, wage, email, address, username, password_hash, staff_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (first_name, last_name, pn, wage, email, address, username, password_hash, staff_type)
    )
    staff_id = cur.lastrowid

    # Ανάλογα με τον τύπο προσωπικού, εισαγωγή στα επιμέρους tables
    staff_type_lower = staff_type.lower() if staff_type else None

    if staff_type_lower == "conservator" and specialization:
        cur.execute(
            "INSERT INTO conservators (staff_id, specialization) VALUES (?, ?)",
            (staff_id, specialization)
        )
    elif staff_type_lower == "guide" and language:
        cur.execute(
            "INSERT INTO guides (staff_id, language, num) VALUES (?, ?, ?)",
            (staff_id, language, 0)
        )
    elif staff_type_lower == "curator" and specialization:
        cur.execute(
            "INSERT INTO curators (staff_id, specialization, exp) VALUES (?, ?, ?)",
            (staff_id, specialization, None)
        )
    elif staff_type_lower == "admins":
        cur.execute(
            "INSERT INTO admins (staff_id, username, password) VALUES (?, ?, ?)",
            (staff_id, username, password_hash)
        )
    elif staff_type_lower not in ("conservator", "guide", "curator", "admins"):
        print("Warning: Invalid staff type!")

    conn.commit()
    conn.close()


def del_pros(staff_id: int):
    """Βοηθητική συνάρτηση βάσης δεδομένων."""

    from PySide6.QtWidgets import  QMessageBox
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor() 
    try:
        cur.execute("PRAGMA foreign_keys = ON;")
        cur.execute("DELETE FROM staff WHERE id = ?", (staff_id,))
        conn.commit()
    except sqlite3.IntegrityError as e:
        QMessageBox.warning(None, "Σφάλμα", f"Δεν μπορεί να διαγραφεί ο/η εργαζόμενος/η:\n{str(e)}")
    finally:
        conn.close()

    
def update_staff_member(staff_id, first_name, last_name, pn, wage, email,
                        address, specialization, language, staff_type):
    
    """Ενημερώνει υπάρχουσα εγγραφή στη βάση (UPDATE)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    # Ενημέρωση βασικού πίνακα staff
    cur.execute("""
        UPDATE staff SET
        first_name=?, last_name=?, pn=?, wage=?, email=?, address=?, staff_type=?
        WHERE id=?
    """, (first_name, last_name, pn, wage, email, address, staff_type, staff_id))
    
    # Διαγραφή προηγούμενων εγγραφών μόνο αν αλλάζει τύπος
    cur.execute("DELETE FROM conservators WHERE staff_id=?", (staff_id,))
    cur.execute("DELETE FROM guides WHERE staff_id=?", (staff_id,))
    cur.execute("DELETE FROM curators WHERE staff_id=?", (staff_id,))

    # Εισαγωγή στη σωστή υποκατηγορία
    if staff_type == "conservator":
        cur.execute("INSERT INTO conservators (staff_id, specialization) VALUES (?, ?)", (staff_id, specialization))
    elif staff_type == "guide":
        cur.execute("INSERT INTO guides (staff_id, language, num) VALUES (?, ?, 0)", (staff_id, language))
    elif staff_type == "curator":
        cur.execute("INSERT INTO curators (staff_id, specialization, exp) VALUES (?, ?, NULL)", (staff_id, specialization))

    conn.commit()
    conn.close()






from datetime import date, timedelta
import sqlite3

def get_all_borrowers():
    """Ανάκτηση δεδομένων από τη βάση (SELECT)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, borrower_type, country, email, address, phone, notes
        FROM borrowers
        ORDER BY name ASC
    """)
    rows = cur.fetchall()
    conn.close()

    out = []
    for r in rows:
        out.append({
            "id": r[0],
            "name": r[1] or "",
            "borrower_type": r[2] or "",
            "country": r[3] or "",
            "email": r[4] or "",
            "address": r[5] or "",
            "phone": r[6] or "",
            "notes": r[7] or "",
        })
    return out


def add_borrower(data: dict) -> int:
    """Εισάγει νέα εγγραφή στη βάση (INSERT)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO borrowers (name, borrower_type, country, email, address, phone, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("name","").strip(),
        data.get("borrower_type","").strip(),
        data.get("country","").strip(),
        data.get("email","").strip(),
        data.get("address","").strip(),
        data.get("phone","").strip(),
        data.get("notes","").strip(),
    ))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_borrower(borrower_id: int, data: dict):
    """Ενημερώνει υπάρχουσα εγγραφή στη βάση (UPDATE)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        UPDATE borrowers
        SET name=?, borrower_type=?, country=?, email=?, address=?, phone=?, notes=?
        WHERE id=?
    """, (
        data.get("name","").strip(),
        data.get("borrower_type","").strip(),
        data.get("country","").strip(),
        data.get("email","").strip(),
        data.get("address","").strip(),
        data.get("phone","").strip(),
        data.get("notes","").strip(),
        borrower_id
    ))
    conn.commit()
    conn.close()


def delete_borrower(borrower_id: int):
    """Διαγράφει/αρχειοθετεί εγγραφή στη βάση."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM borrowers WHERE id=?", (borrower_id,))
    conn.commit()
    conn.close()


def get_loan_by_id(loan_id: int):
    """Ανάκτηση δεδομένων από τη βάση (SELECT)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # δες αν υπάρχει direction (για safety)
    cur.execute("PRAGMA table_info(loans)")
    cols = {row[1] for row in cur.fetchall()}
    has_direction = "direction" in cols

    if has_direction:
        cur.execute("""
            SELECT id, work_id, borrower_id, start_date, end_date, return_date, notes, direction
            FROM loans
            WHERE id=?
        """, (loan_id,))
    else:
        cur.execute("""
            SELECT id, work_id, borrower_id, start_date, end_date, 
                   return_date, notes
            FROM loans
            WHERE id=?
        """, (loan_id,))

    r = cur.fetchone()
    conn.close()
    if not r:
        return None

    if has_direction:
        return {
            "id": r[0],
            "work_id": r[1],
            "borrower_id": r[2],
            "start_date": r[3],
            "end_date": r[4],
            "return_date": r[5],
            "notes": r[6] or "",
            "direction": r[7] or "OUT",
        }

    # fallback
    return {
        "id": r[0],
        "work_id": r[1],
        "borrower_id": r[2],
        "start_date": r[3],
        "end_date": r[4],
        "return_date": r[5],
        "notes": r[6] or "",
        "direction": "OUT",
    }



def get_active_loan_for_work(work_id: int):
    """Ανάκτηση δεδομένων από τη βάση (SELECT)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # υπάρχει direction;
    cur.execute("PRAGMA table_info(loans)")
    cols = {row[1] for row in cur.fetchall()}
    has_direction = "direction" in cols

    if has_direction:
        cur.execute("""
            SELECT id, work_id, borrower_id, start_date, end_date, return_date, notes, direction
            FROM loans
            WHERE work_id=? AND return_date IS NULL
            ORDER BY id DESC
            LIMIT 1
        """, (work_id,))
    else:
        cur.execute("""
            SELECT id, work_id, borrower_id, start_date, end_date, return_date, notes
            FROM loans
            WHERE work_id=? AND return_date IS NULL
            ORDER BY id DESC
            LIMIT 1
        """, (work_id,))

    r = cur.fetchone()
    conn.close()

    if not r:
        return None

    if has_direction:
        return {
            "id": r[0],
            "work_id": r[1],
            "borrower_id": r[2],
            "start_date": r[3],
            "end_date": r[4],
            "return_date": r[5],
            "notes": r[6] or "",
            "direction": r[7] or "OUT",
        }

    return {
        "id": r[0],
        "work_id": r[1],
        "borrower_id": r[2],
        "start_date": r[3],
        "end_date": r[4],
        "return_date": r[5],
        "notes": r[6] or "",
        "direction": "OUT",
    }



def add_loan(work_id: int, borrower_id: int, start_date: str, end_date: str | None = None, notes: str = "",direction="OUT") -> int:
    """Εισάγει νέα εγγραφή στη βάση (INSERT)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # μπλοκάρουμε δεύτερο ενεργό δανεισμό στο ίδιο έργο
    cur.execute("SELECT id FROM loans WHERE work_id=? AND return_date IS NULL", (work_id,))
    if cur.fetchone():
        conn.close()
        raise ValueError("Υπάρχει ήδη ενεργός δανεισμός για αυτό το έργο.")

    cur.execute("""
        INSERT INTO loans (work_id, borrower_id, start_date, end_date, return_date, notes,direction)
        VALUES (?, ?, ?, ?, NULL, ?, ?)
    """, (work_id, borrower_id, start_date, end_date, notes,direction))
        # ✅ Αν είναι IN (δανειζόμαστε), μαρκάρουμε το έργο ως εξωτερικό
    if direction == "IN":
        cur.execute("UPDATE works SET is_external=1 WHERE id=?", (work_id,))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_loan(loan_id: int, borrower_id: int, start_date: str, end_date: str | None, notes: str, direction="OUT"):
    """Ενημερώνει υπάρχουσα εγγραφή στη βάση (UPDATE)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # βρίσκουμε το work_id αυτού του loan
    cur.execute("SELECT work_id FROM loans WHERE id=?", (loan_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("Δεν βρέθηκε ο δανεισμός.")

    work_id = row[0]

    # update loan
    cur.execute("""
        UPDATE loans
        SET borrower_id=?, start_date=?, end_date=?, notes=?, direction=?
        WHERE id=?
    """, (borrower_id, start_date, end_date, notes, direction, loan_id))

    # ✅ sync έργου με βάση το direction
    if direction == "IN":
        cur.execute("UPDATE works SET is_external=1 WHERE id=?", (work_id,))
    else:
        cur.execute("UPDATE works SET is_external=0 WHERE id=?", (work_id,))

    conn.commit()
    conn.close()




def mark_loan_returned(loan_id: int, return_date: str | None = None):
    """Ενημερώνει υπάρχουσα εγγραφή στη βάση (UPDATE)."""

    if return_date is None:
        return_date = date.today().isoformat()

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE loans SET return_date=? WHERE id=?", (return_date, loan_id))
    conn.commit()
    conn.close()


def delete_loan(loan_id: int):
    """Διαγράφει/αρχειοθετεί εγγραφή στη βάση."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM loans WHERE id=?", (loan_id,))
    conn.commit()
    conn.close()


def archive_work(work_id: int):
    """
    Soft-delete: κρύβει το έργο από τη συλλογή αλλά το κρατά στη DB,
    ώστε να ΜΗΝ χαθεί το ιστορικό δανεισμών.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # αν θες να μη σου γεμίζει η συντήρηση με “δανεισμένα-in” που έφυγαν:
    cur.execute("DELETE FROM maintenance WHERE work_id = ?", (work_id,))

    cur.execute("UPDATE works SET is_archived=1, hall_id=NULL WHERE id=?", (work_id,))
    conn.commit()
    conn.close()


def get_loans(search_text: str = "", status: str = "Όλα", direction: str | None = None):
    """
    Επιστρέφει list of dict με join σε works & borrowers.
    status: Όλα | Ενεργά | Λήγουν σύντομα | Εκπρόθεσμα | Ολοκληρωμένα
    direction: None | "OUT" | "IN"
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # ✅ Ελέγχουμε αν υπάρχει η στήλη direction στο loans (ώστε να μην σκάσει σε παλιά DB)
    cur.execute("PRAGMA table_info(loans)")
    loan_cols = {row[1] for row in cur.fetchall()}
    has_direction = "direction" in loan_cols

    search_text = (search_text or "").strip().lower()

    if has_direction:
        cur.execute("""
            SELECT
                l.id,
                l.direction,
                l.work_id,
                w.title,
                l.borrower_id,
                b.name,
                l.start_date,
                l.end_date,
                l.return_date,
                l.notes
            FROM loans l
            JOIN works w ON w.id = l.work_id
            JOIN borrowers b ON b.id = l.borrower_id
            ORDER BY l.id DESC
        """)
        rows = cur.fetchall()
    else:
        # fallback για παλιές βάσεις χωρίς direction
        cur.execute("""
            SELECT
                l.id,
                l.work_id,
                w.title,
                l.borrower_id,
                b.name,
                l.start_date,
                l.end_date,
                l.return_date,
                l.notes
            FROM loans l
            JOIN works w ON w.id = l.work_id
            JOIN borrowers b ON b.id = l.borrower_id
            ORDER BY l.id DESC
        """)
        rows = cur.fetchall()

    conn.close()

    today = date.today()
    soon = today + timedelta(days=7)

    out = []
    for r in rows:
        if has_direction:
            loan_id, loan_direction, work_id, work_title, borrower_id, borrower_name, start_date, end_date, return_date, notes = r
        else:
            loan_id, work_id, work_title, borrower_id, borrower_name, start_date, end_date, return_date, notes = r
            loan_direction = "OUT"  # default

        # ✅ direction filter (IN/OUT)
        if direction in ("IN", "OUT") and loan_direction != direction:
            continue

        # status calc
        if return_date:
            st = "Ολοκληρωμένο"
        else:
            if end_date:
                try:
                    y, m, d = map(int, end_date.split("-"))
                    ed = date(y, m, d)
                    if ed < today:
                        st = "Εκπρόθεσμο"
                    elif ed <= soon:
                        st = "Λήγει σύντομα"
                    else:
                        st = "Ενεργό"
                except Exception:
                    st = "Ενεργό"
            else:
                st = "Ενεργό"

        # text filter
        row_text = f"{loan_id} {work_title} {borrower_name} {start_date} {end_date or ''} {return_date or ''} {notes or ''}".lower()
        if search_text and search_text not in row_text:
            continue

        # status filter
        if status != "Όλα":
            if status == "Ενεργά" and st != "Ενεργό":
                continue
            if status == "Λήγουν σύντομα" and st != "Λήγει σύντομα":
                continue
            if status == "Εκπρόθεσμα" and st != "Εκπρόθεσμο":
                continue
            if status == "Ολοκληρωμένα" and st != "Ολοκληρωμένο":
                continue

        out.append({
            "id": loan_id,
            "direction": loan_direction,  # ✅ ΝΕΟ
            "work_id": work_id,
            "work_title": work_title or "",
            "borrower_id": borrower_id,
            "borrower_name": borrower_name or "",
            "start_date": start_date or "",
            "end_date": end_date or "",
            "return_date": return_date or "",
            "status": st,
            "notes": notes or "",
        })

    return out



def set_work_hall(work_id: int, hall_id):
    """Αλλάζει μόνο την αίθουσα ενός έργου."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE works SET hall_id=? WHERE id=?", (hall_id, work_id))
    conn.commit()
    conn.close()


def get_exhibitions_for_work(work_id: int, from_today: bool = True):
    """
    Επιστρέφει εκθέσεις στις οποίες συμμετέχει το έργο.
    Αν from_today=True, επιστρέφει μόνο όσες δεν έχουν τελειώσει (end_date >= σήμερα).
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT e.id, e.title, e.start_date, e.end_date
        FROM exhibitions e
        JOIN exhibition_works ew ON ew.exhibition_id = e.id
        WHERE ew.work_id = ?
        ORDER BY e.start_date ASC
    """, (work_id,))
    rows = cur.fetchall()
    conn.close()

    if not from_today:
        return [{"id": r[0], "title": r[1], "start_date": r[2], "end_date": r[3]} for r in rows]

    today = date.today()
    out = []
    for ex_id, title, start_date, end_date in rows:
        try:
            if end_date:
                y, m, d = map(int, end_date.split("-"))
                if date(y, m, d) < today:
                    continue
        except Exception:
            # αν δεν parse-άρεται, μην το κόβεις
            pass
        out.append({"id": ex_id, "title": title, "start_date": start_date, "end_date": end_date})
    return out


def ensure_schema():
    """Βοηθητική συνάρτηση βάσης δεδομένων."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # works.is_external
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='works'")
    if cur.fetchone():
        cur.execute("PRAGMA table_info(works)")
        works_cols = {r[1] for r in cur.fetchall()}
        if "is_external" not in works_cols:
            cur.execute("ALTER TABLE works ADD COLUMN is_external INTEGER NOT NULL DEFAULT 0")

    # works.is_archived
    cur.execute("PRAGMA table_info(works)")
    works_cols = [r[1] for r in cur.fetchall()]
    if "is_archived" not in works_cols:
        cur.execute("ALTER TABLE works ADD COLUMN is_archived INTEGER NOT NULL DEFAULT 0")


    # loans.direction
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='loans'")
    if cur.fetchone():
        cur.execute("PRAGMA table_info(loans)")
        loans_cols = {r[1] for r in cur.fetchall()}
        if "direction" not in loans_cols:
            cur.execute("ALTER TABLE loans ADD COLUMN direction TEXT NOT NULL DEFAULT 'OUT'")
            cur.execute("UPDATE loans SET direction='OUT' WHERE direction IS NULL")

    conn.commit()
    conn.close()


# Ξεναγήσεις / Ξεναγοί / Κρατήσεις


def _parse_iso_dt(dt_str: str) -> datetime:
    """Παίρνει 'YYYY-MM-DD HH:MM' ή ISO και επιστρέφει datetime."""
    dt_str = (dt_str or "").replace("T", " ").strip()
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")


def get_tour_overview_stats(target_date: str | None = None) -> dict:
    """Στατιστικά για τα overview cards.
    target_date: 'YYYY-MM-DD' (προαιρετικό)
    """
    d0 = date.fromisoformat(target_date) if target_date else date.today()
    d7 = d0 + timedelta(days=7)
    d30 = d0 - timedelta(days=30)

    conn = connect_db()
    cur = conn.cursor()

    # Σήμερα
    cur.execute(
        """
        SELECT COUNT(*)
        FROM tour_sessions
        WHERE date(start_dt) = ?
        """,
        (d0.isoformat(),),
    )
    today_count = int(cur.fetchone()[0] or 0)

    # Επόμενες 7 ημέρες (incl. σήμερα)
    cur.execute(
        """
        SELECT COUNT(*)
        FROM tour_sessions
        WHERE date(start_dt) BETWEEN ? AND ?
        """,
        (d0.isoformat(), d7.isoformat()),
    )
    next7_count = int(cur.fetchone()[0] or 0)

    # Ακυρώσεις (τελευταίες 30 ημέρες)
    cur.execute(
        """
        SELECT COUNT(*)
        FROM tour_sessions
        WHERE status = 'canceled' AND date(start_dt) BETWEEN ? AND ?
        """,
        (d30.isoformat(), d0.isoformat()),
    )
    canceled_30d = int(cur.fetchone()[0] or 0)

    # Διαθέσιμοι ξεναγοί σήμερα (δεν έχουν session σήμερα που δεν είναι canceled)
    cur.execute(
        """
        SELECT COUNT(*)
        FROM staff s
        JOIN guides g ON g.staff_id = s.id
        LEFT JOIN tour_sessions ts
               ON ts.guide_staff_id = s.id
              AND date(ts.start_dt) = ?
              AND ts.status != 'canceled'
        WHERE s.staff_type = 'guide'
          AND ts.id IS NULL
        """,
        (d0.isoformat(),),
    )
    available_guides = int(cur.fetchone()[0] or 0)

    conn.close()
    return {
        "today_sessions": today_count,
        "next7_sessions": next7_count,
        "available_guides": available_guides,
        "canceled_30d": canceled_30d,
    }


def has_tour_conflict(guide_staff_id: int, start_dt: str, end_dt: str, exclude_session_id: int | None = None) -> bool:
    """Ελέγχει αν ο ξεναγός έχει άλλη ξενάγηση που επικαλύπτεται χρονικά."""
    conn = connect_db()
    cur = conn.cursor()

    q = """
        SELECT COUNT(*)
        FROM tour_sessions
        WHERE guide_staff_id = ?
          AND status != 'canceled'
          AND NOT (datetime(end_dt) <= datetime(?) OR datetime(start_dt) >= datetime(?))
    """
    params = [guide_staff_id, start_dt, end_dt]

    if exclude_session_id is not None:
        q += " AND id != ?"
        params.append(exclude_session_id)

    cur.execute(q, tuple(params))
    n = int(cur.fetchone()[0] or 0)
    conn.close()
    return n > 0


def get_tour_sessions(filter_mode: str = "all") -> list[dict]:
    """Επιστρέφει sessions με extra πεδία (guide_name, booked_people).
    filter_mode: all | today | week | canceled | available
    """
    conn = connect_db()
    cur = conn.cursor()

    where = ""
    params: list = []

    if filter_mode == "today":
        where = "WHERE date(ts.start_dt) = date('now')"
    elif filter_mode == "week":
        where = "WHERE date(ts.start_dt) BETWEEN date('now') AND date('now','+7 day')"
    elif filter_mode == "canceled":
        where = "WHERE ts.status = 'canceled'"
    elif filter_mode == "available":
        where = "WHERE ts.capacity > IFNULL((SELECT SUM(people_count) FROM tour_bookings b WHERE b.session_id = ts.id), 0)"

    cur.execute(
        f"""
        SELECT
            ts.id,
            ts.title,
            ts.start_dt,
            ts.end_dt,
            ts.language,
            ts.tour_type,
            ts.capacity,
            IFNULL((
  SELECT SUM(people_count)
  FROM tour_bookings b
  WHERE b.session_id = ts.id
    AND COALESCE(b.status,'active') != 'canceled'
), 0) AS booked_people,
            ts.status,
            ts.notes,
            ts.cancellation_reason,
            ts.checklist_json,
            ts.exhibition_id,
            e.title AS exhibition_title,
            ts.guide_staff_id,
            s.first_name,
            s.last_name
        FROM tour_sessions ts
        LEFT JOIN exhibitions e ON e.id = ts.exhibition_id
        LEFT JOIN staff s ON s.id = ts.guide_staff_id
        {where}
        ORDER BY datetime(ts.start_dt) ASC
        """,
        tuple(params),
    )
    rows = cur.fetchall()
    conn.close()

    out = []
    for r in rows:
        guide_name = ""
        if r[15] or r[16]:
            guide_name = f"{(r[15] or '').strip()} {(r[16] or '').strip()}".strip()

        out.append({
            "id": r[0],
            "title": r[1],
            "start_dt": r[2],
            "end_dt": r[3],
            "language": r[4] or "",
            "tour_type": r[5] or "",
            "capacity": int(r[6] or 0),
            "booked_people": int(r[7] or 0),
            "status": r[8] or "scheduled",
            "notes": r[9] or "",
            "cancellation_reason": r[10] or "",
            "checklist_json": r[11] or "",
            "exhibition_id": r[12],
            "exhibition_title": r[13] or "",
            "guide_staff_id": r[14],
            "guide_name": guide_name,
        })
    return out


def get_tour_session_capacity_and_booked(session_id: int) -> tuple[int, int]:
    """Επιστρέφει (capacity, booked_people) για session, μετρώντας μόνο active bookings."""
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT capacity FROM tour_sessions WHERE id=?", (int(session_id),))
    row = cur.fetchone()
    capacity = int(row[0] or 0) if row else 0

    cur.execute("""
        SELECT IFNULL(SUM(people_count),0)
        FROM tour_bookings
        WHERE session_id=?
          AND COALESCE(status,'active')!='canceled'
    """, (int(session_id),))
    booked = int(cur.fetchone()[0] or 0)

    conn.close()
    return capacity, booked


def add_tour_session(session: dict) -> int:
    """Προσθέτει νέα ξενάγηση και επιστρέφει id."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO tour_sessions
            (title, start_dt, end_dt, language, guide_staff_id, tour_type, capacity, status, exhibition_id, hall_id, notes, cancellation_reason, checklist_json)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session.get("title", "").strip() or "Ξενάγηση",
            session.get("start_dt"),
            session.get("end_dt"),
            session.get("language", ""),
            session.get("guide_staff_id"),
            session.get("tour_type", ""),
            int(session.get("capacity") or 0),
            session.get("status", "scheduled"),
            session.get("exhibition_id"),
            session.get("hall_id"),
            session.get("notes", ""),
            session.get("cancellation_reason", ""),
            session.get("checklist_json", ""),
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return int(new_id)


def update_tour_session(session_id: int, session: dict) -> None:
    """Ενημερώνει υπάρχουσα εγγραφή στη βάση (UPDATE)."""

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE tour_sessions
        SET title=?, start_dt=?, end_dt=?, language=?, guide_staff_id=?, tour_type=?, capacity=?, status=?, exhibition_id=?, hall_id=?, notes=?, cancellation_reason=?, checklist_json=?
        WHERE id=?
        """,
        (
            session.get("title", "").strip() or "Ξενάγηση",
            session.get("start_dt"),
            session.get("end_dt"),
            session.get("language", ""),
            session.get("guide_staff_id"),
            session.get("tour_type", ""),
            int(session.get("capacity") or 0),
            session.get("status", "scheduled"),
            session.get("exhibition_id"),
            session.get("hall_id"),
            session.get("notes", ""),
            session.get("cancellation_reason", ""),
            session.get("checklist_json", ""),
            int(session_id),
        ),
    )
    conn.commit()
    conn.close()


def delete_tour_session(session_id: int) -> None:
    """Διαγράφει/αρχειοθετεί εγγραφή στη βάση."""

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tour_sessions WHERE id=?", (int(session_id),))
    conn.commit()
    conn.close()


def get_tour_bookings(session_id: int | None = None) -> list[dict]:
    """Επιστρέφει κρατήσεις. Αν session_id=None, φέρνει όλες."""
    conn = connect_db()
    cur = conn.cursor()

    if session_id is None:
        cur.execute(
            """
            SELECT b.id, b.session_id, b.group_name, b.phone, b.email, b.people_count,
                   b.language_pref, b.payment_status, b.comments,
                   ts.start_dt, ts.title,
                   COALESCE(b.status,'active') AS status
            FROM tour_bookings b
            LEFT JOIN tour_sessions ts ON ts.id = b.session_id
            ORDER BY datetime(ts.start_dt) DESC, b.id DESC
            """
        )
    else:
        cur.execute(
            """
            SELECT b.id, b.session_id, b.group_name, b.phone, b.email, b.people_count,
                   b.language_pref, b.payment_status, b.comments,
                   ts.start_dt, ts.title
            FROM tour_bookings b
            LEFT JOIN tour_sessions ts ON ts.id = b.session_id
            WHERE b.session_id=?
            ORDER BY b.id DESC
            """,
            (int(session_id),),
        )

    rows = cur.fetchall()
    conn.close()

    out = []
    for r in rows:
        out.append({
            "id": r[0],
            "session_id": r[1],
            "group_name": r[2] or "",
            "phone": r[3] or "",
            "email": r[4] or "",
            "people_count": int(r[5] or 0),
            "language_pref": r[6] or "",
            "payment_status": r[7] or "unpaid",
            "comments": r[8] or "",
            "session_start_dt": r[9] or "",
            "session_title": r[10] or "",
            "status": r[11] or "active",

        })
    return out


def add_tour_booking(booking: dict) -> int:
    """Εισάγει νέα εγγραφή στη βάση (INSERT)."""

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO tour_bookings
            (session_id, group_name, phone, email, people_count, language_pref, payment_status, comments)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(booking["session_id"]),
            booking.get("group_name", "").strip() or "Ομάδα",
            booking.get("phone", ""),
            booking.get("email", ""),
            int(booking.get("people_count") or 1),
            booking.get("language_pref", ""),
            booking.get("payment_status", "unpaid"),
            booking.get("comments", ""),
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return int(new_id)


def update_tour_booking(booking_id: int, booking: dict) -> None:
    """Ενημερώνει υπάρχουσα εγγραφή στη βάση (UPDATE)."""

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE tour_bookings
        SET session_id=?, group_name=?, phone=?, email=?, people_count=?, language_pref=?, payment_status=?, comments=?
        WHERE id=?
        """,
        (
            int(booking["session_id"]),
            booking.get("group_name", "").strip() or "Ομάδα",
            booking.get("phone", ""),
            booking.get("email", ""),
            int(booking.get("people_count") or 1),
            booking.get("language_pref", ""),
            booking.get("payment_status", "unpaid"),
            booking.get("comments", ""),
            int(booking_id),
        ),
    )
    conn.commit()
    conn.close()


def delete_tour_booking(booking_id: int) -> None:
    """Διαγράφει/αρχειοθετεί εγγραφή στη βάση."""

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tour_bookings WHERE id=?", (int(booking_id),))
    conn.commit()
    conn.close()




#--------Tickets--------

    
import string

def _make_ticket_code(prefix="T"):
    # π.χ. T-20251222-8F3K2D1A
    """Βοηθητική συνάρτηση βάσης δεδομένων."""

    rand = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    return f"{prefix}-{date.today().strftime('%Y%m%d')}-{rand}"


# ---------------- Ticket Types ----------------

def get_ticket_types(include_inactive=True):
    """Ανάκτηση δεδομένων από τη βάση (SELECT)."""

    conn = connect_db()
    cur = conn.cursor()
    if include_inactive:
        cur.execute("""
            SELECT id, name, price, active, online_enabled, requires_proof, notes
            FROM ticket_types
            ORDER BY active DESC, name ASC
        """)
    else:
        cur.execute("""
            SELECT id, name, price, active, online_enabled, requires_proof, notes
            FROM ticket_types
            WHERE active=1
            ORDER BY name ASC
        """)
    rows = cur.fetchall()
    conn.close()
    return [{
        "id": r[0], "name": r[1], "price": float(r[2] or 0),
        "active": int(r[3] or 0),
        "online_enabled": int(r[4] or 0),
        "requires_proof": int(r[5] or 0),
        "notes": r[6] or ""
    } for r in rows]


def add_ticket_type(data: dict) -> int:
    """Εισάγει νέα εγγραφή στη βάση (INSERT)."""

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ticket_types (name, price, active, online_enabled, requires_proof, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data.get("name","").strip(),
        float(data.get("price") or 0),
        int(data.get("active", 1)),
        int(data.get("online_enabled", 1)),
        int(data.get("requires_proof", 0)),
        data.get("notes","").strip(),
    ))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return int(new_id)


def update_ticket_type(type_id: int, data: dict):
    """Ενημερώνει υπάρχουσα εγγραφή στη βάση (UPDATE)."""

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE ticket_types
        SET name=?, price=?, active=?, online_enabled=?, requires_proof=?, notes=?
        WHERE id=?
    """, (
        data.get("name","").strip(),
        float(data.get("price") or 0),
        int(data.get("active", 1)),
        int(data.get("online_enabled", 1)),
        int(data.get("requires_proof", 0)),
        data.get("notes","").strip(),
        int(type_id),
    ))
    conn.commit()
    conn.close()


def set_ticket_type_active(type_id: int, active: int):
    """Ενημερώνει υπάρχουσα εγγραφή στη βάση (UPDATE)."""

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("UPDATE ticket_types SET active=? WHERE id=?", (int(active), int(type_id)))
    conn.commit()
    conn.close()


# ---------------- Orders / Sales ----------------

def create_ticket_order(order: dict, items: list[dict]) -> int:
    """
    order: {channel, customer_email, payment_method, status, cashier_staff_id}
    items: list of {ticket_type_id, qty, unit_price(optional), visit_date, tour_session_id(optional), exhibition_id(optional)}
    Δημιουργεί order + items + tickets (ένα ticket ανά άτομο) και επιστρέφει order_id
    """
    conn = connect_db()
    cur = conn.cursor()

    # υπολογισμός total
    total = 0.0
    normalized_items = []
    for it in items:
        qty = int(it.get("qty") or 1)
        type_id = int(it["ticket_type_id"])
        visit_date = it.get("visit_date") or date.today().isoformat()

        # unit price από ticket_types αν δεν δόθηκε
        if it.get("unit_price") is None:
            cur.execute("SELECT price FROM ticket_types WHERE id=?", (type_id,))
            row = cur.fetchone()
            unit_price = float(row[0] if row else 0)
        else:
            unit_price = float(it.get("unit_price") or 0)

        line_total = unit_price * qty
        total += line_total

        normalized_items.append({
            "ticket_type_id": type_id,
            "qty": qty,
            "unit_price": unit_price,
            "line_total": line_total,
            "visit_date": visit_date,
            "tour_session_id": it.get("tour_session_id"),
            "exhibition_id": it.get("exhibition_id"),
        })

    
    # Capacity check για Εκθέσεις (max_seats)
    ex_qty = {}
    for it in normalized_items:
        ex_id = it.get("exhibition_id")
        if ex_id:
            ex_id = int(ex_id)
            ex_qty[ex_id] = ex_qty.get(ex_id, 0) + int(it.get("qty") or 1)

    for ex_id, req_qty in ex_qty.items():
        cur.execute("SELECT title, max_seats FROM exhibitions WHERE id=?", (ex_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Η έκθεση (id={ex_id}) δεν βρέθηκε.")

        ex_title, max_seats = row[0], row[1]

        # αν δεν έχει max_seats (None ή 0) -> απεριόριστο
        if max_seats is None or int(max_seats) == 0:
            continue

        max_seats = int(max_seats)

        cur.execute(
            """
            SELECT COUNT(*)
            FROM tickets
            WHERE exhibition_id = ?
              AND LOWER(COALESCE(status,'valid')) != 'canceled'
            """,
            (ex_id,),
        )
        reserved = int(cur.fetchone()[0] or 0)
        remaining = max_seats - reserved

        if req_qty > remaining:
            conn.close()
            raise ValueError(
                f'Η έκθεση "{ex_title}" δεν έχει αρκετές θέσεις. '
                f'Διαθέσιμες: {max(0, remaining)} από {max_seats}.'
            )


    # 1) insert order
    cur.execute("""
        INSERT INTO ticket_orders (channel, customer_email, payment_method, status, total, cashier_staff_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        order.get("channel", "cashier"),
        (order.get("customer_email") or "").strip() or None,
        order.get("payment_method", "cash"),
        order.get("status", "paid"),
        float(total),
        order.get("cashier_staff_id"),
    ))

    order_id = int(cur.lastrowid)

    # 2) insert items + tickets + (ΑΝ υπάρχει session) γράψε booking στις Ξεναγήσεις
    for it in normalized_items:
        tour_session_id = it.get("tour_session_id")
        if tour_session_id:
            # ✅ Μην επιτρέπεις πώληση σε canceled/completed session
            cur.execute("SELECT status FROM tour_sessions WHERE id=?", (int(tour_session_id),))
            r = cur.fetchone()
            st = (r[0] if r else "") or ""
            st = st.strip().lower()
            if st in ("canceled", "completed"):
                conn.rollback()
                conn.close()
                raise ValueError("Η επιλεγμένη ξενάγηση είναι ακυρωμένη/ολοκληρωμένη. Δεν μπορείς να πουλήσεις εισιτήρια.")

        # ✅ capacity check αν το item είναι για ξενάγηση
        tour_session_id = it.get("tour_session_id")
        if tour_session_id:
            cap, booked = get_tour_session_capacity_and_booked(int(tour_session_id))
            qty_add = int(it.get("qty") or 0)
            if cap > 0 and (booked + qty_add) > cap:
                conn.rollback()
                conn.close()
                raise ValueError(f"Δεν υπάρχουν αρκετές θέσεις στη ξενάγηση (χωρητικότητα {cap}, κρατήσεις {booked}, ζητάς +{qty_add}).")

        cur.execute("""
            INSERT INTO ticket_order_items
                (order_id, ticket_type_id, qty, unit_price, line_total, visit_date, tour_session_id, exhibition_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id,
            it["ticket_type_id"],
            it["qty"],
            it["unit_price"],
            it["line_total"],
            it["visit_date"],
            it.get("tour_session_id"),
            it.get("exhibition_id"),
        ))

        # ✅ γράψε booking μόνο αν έχει tour_session_id
        tour_session_id = it.get("tour_session_id")
        if tour_session_id:
            add_tour_booking_from_ticket_order(
                order_id=order_id,
                session_id=int(tour_session_id),
                qty=int(it.get("qty") or 1),
                customer_email=order.get("customer_email"),
                payment_status="paid" if order.get("status") == "paid" else "unpaid",
                comments=f"Tickets order #{order_id}",
                _cur=cur  # ✅ ΚΡΙΣΙΜΟ: γράφει στο ίδιο transaction, δεν ανοίγει νέο conn
            )

        # generate tickets: 1 per person
        for _ in range(it["qty"]):
            code = _make_ticket_code("T")
            cur.execute("""
                INSERT INTO tickets
                    (order_id, ticket_code, ticket_type_id, visit_date, status, tour_session_id, exhibition_id)
                VALUES (?, ?, ?, ?, 'valid', ?, ?)
            """, (
                order_id, code, it["ticket_type_id"], it["visit_date"],
                it.get("tour_session_id"), it.get("exhibition_id")
            ))

    conn.commit()
    conn.close()
    return order_id


def get_ticket_orders(range_mode: str = "all") -> list[dict]:
    """
    range_mode: all | today | week
    """
    conn = connect_db()
    cur = conn.cursor()

    where = ""
    if range_mode == "today":
        where = "WHERE date(o.created_at) = date('now')"
    elif range_mode == "week":
        where = "WHERE date(o.created_at) BETWEEN date('now','-6 day') AND date('now')"

    cur.execute(f"""
        SELECT o.id, o.created_at, o.channel, o.customer_email, o.total, o.payment_method, o.status,
               s.first_name, s.last_name
        FROM ticket_orders o
        LEFT JOIN staff s ON s.id = o.cashier_staff_id
        {where}
        ORDER BY datetime(o.created_at) DESC
    """)
    rows = cur.fetchall()
    conn.close()

    out = []
    for r in rows:
        cashier = ""
        if r[7] or r[8]:
            cashier = f"{(r[7] or '').strip()} {(r[8] or '').strip()}".strip()
        out.append({
            "id": r[0],
            "created_at": r[1],
            "channel": r[2] or "",
            "customer_email": r[3] or "",
            "total": float(r[4] or 0),
            "payment_method": r[5] or "",
            "status": r[6] or "",
            "cashier_name": cashier,
        })
    return out


def get_ticket_order_details(order_id: int) -> dict:
    """Ανάκτηση δεδομένων από τη βάση (SELECT)."""

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, created_at, channel, customer_email, payment_method, status, total
        FROM ticket_orders
        WHERE id=?
    """, (int(order_id),))
    o = cur.fetchone()
    if not o:
        conn.close()
        return {}

    cur.execute("""
        SELECT i.id, tt.name, i.qty, i.unit_price, i.line_total, i.visit_date,
               i.tour_session_id, ts.title, ts.start_dt,
               i.exhibition_id, e.title
        FROM ticket_order_items i
        JOIN ticket_types tt ON tt.id = i.ticket_type_id
        LEFT JOIN tour_sessions ts ON ts.id = i.tour_session_id
        LEFT JOIN exhibitions e ON e.id = i.exhibition_id
        WHERE i.order_id=?
        ORDER BY i.id ASC
    """, (int(order_id),))
    items = cur.fetchall()

    cur.execute("""
        SELECT t.ticket_code, tt.name, t.visit_date, t.status, t.checked_in_at,
               ts.title, ts.start_dt, e.title
        FROM tickets t
        JOIN ticket_types tt ON tt.id = t.ticket_type_id
        LEFT JOIN tour_sessions ts ON ts.id = t.tour_session_id
        LEFT JOIN exhibitions e ON e.id = t.exhibition_id
        WHERE t.order_id=?
        ORDER BY t.id ASC
    """, (int(order_id),))
    tickets_rows = cur.fetchall()

    conn.close()

    return {
        "order": {
            "id": o[0], "created_at": o[1], "channel": o[2] or "",
            "customer_email": o[3] or "", "payment_method": o[4] or "",
            "status": o[5] or "", "total": float(o[6] or 0)
        },
        "items": [{
            "id": r[0],
            "type_name": r[1] or "",
            "qty": int(r[2] or 0),
            "unit_price": float(r[3] or 0),
            "line_total": float(r[4] or 0),
            "visit_date": r[5] or "",
            "tour_session_id": r[6],
            "tour_title": r[7] or "",
            "tour_start_dt": r[8] or "",
            "exhibition_id": r[9],
            "exhibition_title": r[10] or "",
        } for r in items],
        "tickets": [{
            "code": r[0], "type_name": r[1] or "", "visit_date": r[2] or "",
            "status": r[3] or "", "checked_in_at": r[4] or "",
            "tour_title": r[5] or "", "tour_start_dt": r[6] or "",
            "exhibition_title": r[7] or "",
        } for r in tickets_rows]
    }


def set_order_status(order_id: int, status: str, refund_reason: str = ""):
    """Ενημερώνει υπάρχουσα εγγραφή στη βάση (UPDATE)."""

    conn = connect_db()
    cur = conn.cursor()

    # ✅ αν ακυρώνεται/refund → ακύρωσε και τα tour bookings αυτού του order
    if status in ("canceled", "refunded"):
        cancel_tour_bookings_by_ticket_order(order_id, reason=refund_reason or status)

        cur.execute("""
            UPDATE ticket_orders
            SET status=?, refund_reason=?, refunded_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (status, refund_reason.strip() or None, int(order_id)))

        # ακυρώνουμε όλα τα tickets αυτού του order
        cur.execute("""
            UPDATE tickets
            SET status='canceled'
            WHERE order_id=?
        """, (int(order_id),))
    else:
        cur.execute("UPDATE ticket_orders SET status=? WHERE id=?", (status, int(order_id)))

    conn.commit()
    conn.close()



# ---------------- Check-in ----------------

def check_in_ticket(code: str, staff_id: int | None = None, enforce_date: bool = True) -> dict:
    """
    Επιστρέφει dict: {result, message, ticket(optional)}
    result: VALID / USED / INVALID / CANCELED / WRONG_DATE
    """
    code = (code or "").strip()
    if not code:
        return {"result": "INVALID", "message": "Κενός κωδικός."}

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT t.id, t.ticket_code, t.visit_date, t.status, t.checked_in_at,
               tt.name,
               t.tour_session_id, ts.title, ts.start_dt,
               t.exhibition_id, e.title
        FROM tickets t
        JOIN ticket_types tt ON tt.id = t.ticket_type_id
        LEFT JOIN tour_sessions ts ON ts.id = t.tour_session_id
        LEFT JOIN exhibitions e ON e.id = t.exhibition_id
        WHERE t.ticket_code=?
    """, (code,))
    r = cur.fetchone()

    if not r:
        cur.execute("INSERT INTO ticket_scan_log (code, result, staff_id, notes) VALUES (?, 'INVALID', ?, ?)",
                    (code, staff_id, "Not found"))
        conn.commit()
        conn.close()
        return {"result": "INVALID", "message": "Μη έγκυρο εισιτήριο."}

    ticket_id, tcode, visit_date, status, checked_in_at, type_name, \
        tour_id, tour_title, tour_start, ex_id, ex_title = r

    if status == "canceled":
        cur.execute("INSERT INTO ticket_scan_log (code, result, staff_id, notes) VALUES (?, 'CANCELED', ?, ?)",
                    (code, staff_id, "Canceled ticket"))
        conn.commit()
        conn.close()
        return {"result": "CANCELED", "message": "Το εισιτήριο είναι ακυρωμένο."}

    if checked_in_at:
        cur.execute("INSERT INTO ticket_scan_log (code, result, staff_id, notes) VALUES (?, 'USED', ?, ?)",
                    (code, staff_id, "Already used"))
        conn.commit()
        conn.close()
        return {"result": "USED", "message": "Το εισιτήριο έχει ήδη χρησιμοποιηθεί."}

    if enforce_date:
        if visit_date != date.today().isoformat():
            cur.execute("INSERT INTO ticket_scan_log (code, result, staff_id, notes) VALUES (?, 'WRONG_DATE', ?, ?)",
                        (code, staff_id, f"visit_date={visit_date}"))
            conn.commit()
            conn.close()
            return {"result": "WRONG_DATE", "message": f"Λάθος ημερομηνία (είναι για {visit_date})."}

    # OK -> mark used
    cur.execute("""
        UPDATE tickets
        SET status='used', checked_in_at=CURRENT_TIMESTAMP, checkin_staff_id=?
        WHERE id=?
    """, (staff_id, int(ticket_id)))

    cur.execute("INSERT INTO ticket_scan_log (code, result, staff_id, notes) VALUES (?, 'VALID', ?, ?)",
                (code, staff_id, ""))

    conn.commit()
    conn.close()

    return {
        "result": "VALID",
        "message": "VALID ✅",
        "ticket": {
            "code": tcode,
            "type_name": type_name,
            "visit_date": visit_date,
            "tour_title": tour_title or "",
            "tour_start_dt": tour_start or "",
            "exhibition_title": ex_title or "",
        }
    }


def undo_last_checkin():
    """
    Undo το τελευταίο VALID scan (κάνει ticket ξανά valid + null checked_in_at)
    """
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, code
        FROM ticket_scan_log
        WHERE result='VALID'
        ORDER BY datetime(scanned_at) DESC, id DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    if not row:
        conn.close()
        return False

    log_id, code = row

    # βρες ticket
    cur.execute("SELECT id FROM tickets WHERE ticket_code=?", (code,))
    t = cur.fetchone()
    if not t:
        conn.close()
        return False

    ticket_id = int(t[0])
    cur.execute("""
        UPDATE tickets
        SET status='valid', checked_in_at=NULL, checkin_staff_id=NULL
        WHERE id=?
    """, (ticket_id,))

    cur.execute("INSERT INTO ticket_scan_log (code, result, notes) VALUES (?, 'UNDO', ?)",
                (code, f"Undo of log_id={log_id}"))

    conn.commit()
    conn.close()
    return True


def get_scan_log(limit: int = 20) -> list[dict]:
    """Ανάκτηση δεδομένων από τη βάση (SELECT)."""

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT scanned_at, code, result, notes
        FROM ticket_scan_log
        ORDER BY datetime(scanned_at) DESC, id DESC
        LIMIT ?
    """, (int(limit),))
    rows = cur.fetchall()
    conn.close()
    return [{"scanned_at": r[0], "code": r[1] or "", "result": r[2] or "", "notes": r[3] or ""} for r in rows]


# ---------------- Overview / Reports ----------------

def get_ticket_overview_stats(target_date: str | None = None) -> dict:
    """Ανάκτηση δεδομένων από τη βάση (SELECT)."""

    d0 = date.fromisoformat(target_date) if target_date else date.today()
    d7_from = d0 - timedelta(days=6)

    conn = connect_db()
    cur = conn.cursor()

    # Σήμερα: Πωλήσεις (πλήθος tickets που δημιουργήθηκαν σήμερα)
    cur.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE visit_date=?
    """, (d0.isoformat(),))
    today_tickets = int(cur.fetchone()[0] or 0)

    # Check-ins σήμερα
    cur.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE date(checked_in_at)=?
    """, (d0.isoformat(),))
    today_checkins = int(cur.fetchone()[0] or 0)

    # Σήμερα: Έσοδα (paid orders σήμερα)
    cur.execute("""
        SELECT IFNULL(SUM(total),0)
        FROM ticket_orders
        WHERE status='paid' AND date(created_at)=?
    """, (d0.isoformat(),))
    today_revenue = float(cur.fetchone()[0] or 0)

    # Εβδομάδα: Έσοδα (last 7 days incl today)
    cur.execute("""
        SELECT IFNULL(SUM(total),0)
        FROM ticket_orders
        WHERE status='paid' AND date(created_at) BETWEEN ? AND ?
    """, (d7_from.isoformat(), d0.isoformat()))
    week_revenue = float(cur.fetchone()[0] or 0)

    conn.close()
    return {
        "today_tickets": today_tickets,
        "today_checkins": today_checkins,
        "today_revenue": today_revenue,
        "week_revenue": week_revenue,
    }


def report_sales_by_type(date_from: str, date_to: str):
    """Παράγει αναφορά/σύνοψη (aggregations) από τη βάση."""

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT tt.name, SUM(i.qty) as qty, SUM(i.line_total) as revenue
        FROM ticket_order_items i
        JOIN ticket_orders o ON o.id=i.order_id
        JOIN ticket_types tt ON tt.id=i.ticket_type_id
        WHERE o.status='paid' AND date(o.created_at) BETWEEN ? AND ?
        GROUP BY tt.name
        ORDER BY revenue DESC
    """, (date_from, date_to))
    rows = cur.fetchall()
    conn.close()
    return [{"type": r[0], "qty": int(r[1] or 0), "revenue": float(r[2] or 0)} for r in rows]


def report_sales_by_session(date_from: str, date_to: str):
    """Παράγει αναφορά/σύνοψη (aggregations) από τη βάση."""

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(ts.title,'(χωρίς ξενάγηση)') as session_title,
               COUNT(t.id) as tickets,
               SUM(tt.price) as revenue_est
        FROM tickets t
        JOIN ticket_types tt ON tt.id=t.ticket_type_id
        LEFT JOIN tour_sessions ts ON ts.id=t.tour_session_id
        JOIN ticket_orders o ON o.id=t.order_id
        WHERE o.status='paid' AND date(o.created_at) BETWEEN ? AND ?
        GROUP BY session_title
        ORDER BY tickets DESC
    """, (date_from, date_to))
    rows = cur.fetchall()
    conn.close()
    return [{"session": r[0], "tickets": int(r[1] or 0), "revenue_est": float(r[2] or 0)} for r in rows]



def report_ticket_revenue_by_month(months_back: int = 12):
    """Επιστρέφει έσοδα (paid orders) ανά μήνα, για τους τελευταίους `months_back` μήνες.

    Returns: [{"month": "YYYY-MM", "revenue": float}, ...] (με συμπλήρωση μηδενικών μηνών)
    """
    try:
        months_back = int(months_back or 12)
    except Exception:
        months_back = 12
    months_back = max(1, min(months_back, 60))

    # υπολογισμός αρχικού μήνα (1η μέρα) σε python για να μη βασιζόμαστε σε sqlite date tricks
    today = date.today()
    start_year = today.year
    start_month = today.month - (months_back - 1)
    while start_month <= 0:
        start_month += 12
        start_year -= 1
    start_date = date(start_year, start_month, 1).isoformat()

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT strftime('%Y-%m', o.created_at) AS ym,
               COALESCE(SUM(o.total), 0) AS revenue
        FROM ticket_orders o
        WHERE o.status='paid' AND date(o.created_at) >= date(?)
        GROUP BY ym
        ORDER BY ym
    """, (start_date,))
    rows = cur.fetchall()
    conn.close()

    rev_map = {str(r[0]): float(r[1] or 0) for r in rows if r and r[0]}

    # συμπλήρωση κενών μηνών
    out = []
    y, m = start_year, start_month
    for _ in range(months_back):
        ym = f"{y:04d}-{m:02d}"
        out.append({"month": ym, "revenue": float(rev_map.get(ym, 0.0))})
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out
def report_ticket_revenue_by_day(date_from: str, date_to: str):
    """Επιστρέφει έσοδα (paid orders) ανά ημέρα για custom date range.

    Returns: [{"day": "YYYY-MM-DD", "revenue": float}, ...] (με συμπλήρωση μηδενικών ημερών)
    """
    # normalize / parse
    try:
        d1 = date.fromisoformat(str(date_from))
        d2 = date.fromisoformat(str(date_to))
    except Exception:
        # fallback: σήμερα μόνο
        d1 = d2 = date.today()

    if d1 > d2:
        d1, d2 = d2, d1

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT date(o.created_at) AS d,
               COALESCE(SUM(o.total), 0) AS revenue
        FROM ticket_orders o
        WHERE o.status='paid' AND date(o.created_at) BETWEEN date(?) AND date(?)
        GROUP BY d
        ORDER BY d
    """, (d1.isoformat(), d2.isoformat()))
    rows = cur.fetchall()
    conn.close()

    rev_map = {str(r[0]): float(r[1] or 0) for r in rows if r and r[0]}

    out = []
    cur_day = d1
    while cur_day <= d2:
        key = cur_day.isoformat()
        out.append({"day": key, "revenue": float(rev_map.get(key, 0.0))})
        cur_day += timedelta(days=1)
    return out


def report_ticket_revenue_by_month_range(date_from: str, date_to: str):
    """Επιστρέφει έσοδα (paid orders) ανά μήνα για custom date range.

    Returns: [{"month": "YYYY-MM", "revenue": float}, ...] (με συμπλήρωση μηδενικών μηνών)
    """
    try:
        d1 = date.fromisoformat(str(date_from))
        d2 = date.fromisoformat(str(date_to))
    except Exception:
        d1 = d2 = date.today()

    if d1 > d2:
        d1, d2 = d2, d1

    # αρχή/τέλος σε επίπεδο μήνα
    start = date(d1.year, d1.month, 1)
    end = date(d2.year, d2.month, 1)

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT strftime('%Y-%m', o.created_at) AS ym,
               COALESCE(SUM(o.total), 0) AS revenue
        FROM ticket_orders o
        WHERE o.status='paid' AND date(o.created_at) BETWEEN date(?) AND date(?)
        GROUP BY ym
        ORDER BY ym
    """, (d1.isoformat(), d2.isoformat()))
    rows = cur.fetchall()
    conn.close()

    rev_map = {str(r[0]): float(r[1] or 0) for r in rows if r and r[0]}

    out = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        ym = f"{y:04d}-{m:02d}"
        out.append({"month": ym, "revenue": float(rev_map.get(ym, 0.0))})
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out

def add_tour_booking_from_ticket_order(
    order_id: int,
    session_id: int,
    qty: int,
    customer_email: str | None = None,
    payment_status: str = "paid",
    comments: str = "",
    _cur=None,   # ✅ αν δοθεί, ΔΕΝ ανοίγουμε νέα σύνδεση
) -> int:
    """
    Δημιουργεί (ή ενημερώνει) booking στο tour_bookings από ticket order.
    Αν ξαναπουληθεί στο ίδιο order/session, αθροίζει.
    Αν _cur δοθεί (cursor από ήδη ανοιχτό transaction), γράφει εκεί για να μην κλειδώσει η DB.
    """
    owns_conn = False
    conn = None
    cur = _cur

    if cur is None:
        conn = connect_db()
        cur = conn.cursor()
        owns_conn = True

    # υπάρχει ήδη booking από αυτό το order για αυτό το session;
    cur.execute("""
        SELECT id, people_count
        FROM tour_bookings
        WHERE ticket_order_id=? AND session_id=? AND COALESCE(status,'active')!='canceled'
        LIMIT 1
    """, (int(order_id), int(session_id)))
    row = cur.fetchone()

    group_name = (customer_email or "").strip() or f"Order #{order_id}"

    if row:
        bid, old_cnt = row
        new_cnt = int(old_cnt or 0) + int(qty or 0)
        cur.execute("""
            UPDATE tour_bookings
            SET people_count=?, payment_status=?, comments=?
            WHERE id=?
        """, (new_cnt, payment_status, (comments or "").strip(), int(bid)))

        if owns_conn:
            conn.commit()
            conn.close()
        return int(bid)

    cur.execute("""
        INSERT INTO tour_bookings
            (session_id, group_name, phone, email, people_count, language_pref,
             payment_status, comments, ticket_order_id, status)
        VALUES
            (?, ?, '', ?, ?, '', ?, ?, ?, 'active')
    """, (
        int(session_id),
        group_name,
        customer_email or "",
        int(qty or 1),
        payment_status,
        (comments or "").strip() or f"From tickets order #{order_id}",
        int(order_id)
    ))

    new_id = int(cur.lastrowid)

    if owns_conn:
        conn.commit()
        conn.close()

    return new_id



def cancel_tour_bookings_by_ticket_order(order_id: int, reason: str = "") -> None:
    """Βοηθητική συνάρτηση βάσης δεδομένων."""

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE tour_bookings
        SET status='canceled',
            payment_status='refunded',
            comments = CASE
                WHEN TRIM(COALESCE(comments,'')) = '' THEN ?
                ELSE TRIM(comments) || ' | ' || ?
            END
        WHERE ticket_order_id=?
          AND COALESCE(status,'active')!='canceled'
    """, (
        f"Refund order #{order_id}: {reason}".strip(),
        f"Refund: {reason}".strip(),
        int(order_id)
    ))
    conn.commit()
    conn.close()


def cancel_tour_session_and_refund(session_id: int, reason: str = "") -> dict:
    """
    Κάνει canceled τη ξενάγηση και κάνει refund/cancel σε όλα τα σχετικά:
    - tour_bookings: status=canceled, payment_status=refunded
    - ticket_orders: status=refunded
    - tickets: status=canceled
    Επιστρέφει counters για UI.
    """
    conn = connect_db()
    cur = conn.cursor()

    reason = (reason or "").strip()
    refund_reason = f"Tour session #{session_id} canceled"
    if reason:
        refund_reason += f": {reason}"

    # 1) cancel session
    cur.execute("""
        UPDATE tour_sessions
        SET status='canceled',
            cancellation_reason=?
        WHERE id=?
    """, (reason or None, int(session_id)))

    # 2) cancel/refund all tour_bookings for this session
    cur.execute("""
        UPDATE tour_bookings
        SET status='canceled',
            payment_status='refunded',
            comments = CASE
                WHEN TRIM(COALESCE(comments,'')) = '' THEN ?
                ELSE TRIM(comments) || ' | ' || ?
            END
        WHERE session_id=?
          AND COALESCE(status,'active')!='canceled'
    """, (refund_reason, refund_reason, int(session_id)))
    bookings_affected = cur.rowcount

    # 3) find related ticket orders (μέσω items)
    cur.execute("""
        SELECT DISTINCT order_id
        FROM ticket_order_items
        WHERE tour_session_id=?
    """, (int(session_id),))
    order_ids = [int(r[0]) for r in cur.fetchall()]

    orders_affected = 0
    tickets_affected = 0

    for oid in order_ids:
        # refund order
        cur.execute("""
            UPDATE ticket_orders
            SET status='refunded',
                refund_reason=?,
                refunded_at=CURRENT_TIMESTAMP
            WHERE id=?
              AND status != 'refunded'
        """, (refund_reason, int(oid)))
        orders_affected += cur.rowcount

        # cancel ALL tickets of the order (όπως το set_order_status σου)
        cur.execute("""
            UPDATE tickets
            SET status='canceled'
            WHERE order_id=?
        """, (int(oid),))
        tickets_affected += cur.rowcount

        # και για συνέπεια: ακύρωσε booking rows που έρχονται από tickets order
        cur.execute("""
            UPDATE tour_bookings
            SET status='canceled',
                payment_status='refunded',
                comments = CASE
                    WHEN TRIM(COALESCE(comments,'')) = '' THEN ?
                    ELSE TRIM(comments) || ' | ' || ?
                END
            WHERE ticket_order_id=?
              AND COALESCE(status,'active')!='canceled'
        """, (refund_reason, refund_reason, int(oid)))

    conn.commit()
    conn.close()

    return {
        "bookings": int(bookings_affected or 0),
        "orders": int(orders_affected or 0),
        "tickets": int(tickets_affected or 0),
    }

def get_tour_sessions_for_ticket_sales(only_with_seats: bool = True) -> list[dict]:
    """
    Επιστρέφει sessions που επιτρέπονται για πώληση εισιτηρίων:
    - status όχι canceled/completed
    - start_dt >= τώρα (προαιρετικά μπορείς να το χαλαρώσεις)
    - (προαιρετικά) μόνο όσα έχουν διαθέσιμες θέσεις
    """
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            ts.id,
            ts.title,
            ts.start_dt,
            ts.end_dt,
            ts.capacity,
            IFNULL((
              SELECT SUM(people_count)
              FROM tour_bookings b
              WHERE b.session_id = ts.id
                AND COALESCE(b.status,'active') != 'canceled'
            ), 0) AS booked_people,
            ts.status
        FROM tour_sessions ts
        WHERE ts.status NOT IN ('canceled','completed')
          AND datetime(ts.start_dt) >= datetime('now')
        ORDER BY datetime(ts.start_dt) ASC
    """)
    rows = cur.fetchall()
    conn.close()

    out = []
    for sid, title, start_dt, end_dt, cap, booked, status in rows:
        cap = int(cap or 0)
        booked = int(booked or 0)
        has_seats = (cap == 0) or (booked < cap)  # cap=0 => χωρίς όριο (αν έτσι το θες)

        if only_with_seats and not has_seats:
            continue

        out.append({
            "id": int(sid),
            "title": title or "Ξενάγηση",
            "start_dt": start_dt or "",
            "end_dt": end_dt or "",
            "capacity": cap,
            "booked_people": booked,
            "status": status or "scheduled",
        })
    return out


def get_curators_for_combo():
    """Ανάκτηση δεδομένων από τη βάση (SELECT)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, first_name, last_name
        FROM staff
        WHERE LOWER(COALESCE(staff_type,'')) = 'curator'
        ORDER BY last_name, first_name
    """)
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "first_name": r[1] or "", "last_name": r[2] or ""} for r in rows]


def get_reserved_seats_for_exhibition(exhibition_id: int) -> int:
    """Ανάκτηση δεδομένων από τη βάση (SELECT)."""

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE exhibition_id = ?
          AND LOWER(COALESCE(status,'valid')) != 'canceled'
    """, (exhibition_id,))
    n = int(cur.fetchone()[0] or 0)
    conn.close()
    return n

def get_due_loans_for_calendar():
    """
    Επιστρέφει δανεισμούς που ΔΕΝ έχουν επιστραφεί (return_date IS NULL)
    και έχουν end_date (due date επιστροφής).
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT
            l.id,
            COALESCE(UPPER(l.direction), 'OUT') AS direction,
            l.end_date,
            w.title,
            COALESCE(b.name, '') AS borrower_name
        FROM loans l
        JOIN works w ON w.id = l.work_id
        LEFT JOIN borrowers b ON b.id = l.borrower_id
        WHERE l.return_date IS NULL
          AND l.end_date IS NOT NULL
          AND TRIM(l.end_date) <> ''
        ORDER BY l.end_date ASC
    """)
    rows = cur.fetchall()
    conn.close()

    out = []
    for loan_id, direction, due_date, work_title, borrower_name in rows:
        out.append({
            "loan_id": loan_id,
            "direction": direction,          # IN / OUT
            "due_date": due_date,            # YYYY-MM-DD
            "work_title": work_title,
            "borrower_name": borrower_name,
        })
    return out


def get_maintenance_for_calendar():
    """
    Επιστρέφει προγραμματισμένη συντήρηση (start→end range).
    Αν end είναι κενό, θεωρείται μονοήμερο.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT
            m.id,
            m.type,
            m.start,
            m.end,
            w.title,
            COALESCE(s.first_name || ' ' || s.last_name, '') AS conservator_name
        FROM maintenance m
        JOIN works w ON w.id = m.work_id
        LEFT JOIN staff s ON s.id = m.conservator_id
        WHERE m.start IS NOT NULL
          AND TRIM(m.start) <> ''
        ORDER BY m.start ASC
    """)
    rows = cur.fetchall()
    conn.close()

    out = []
    for mid, mtype, start, end, work_title, conservator_name in rows:
        out.append({
            "maintenance_id": mid,
            "type": mtype or "",
            "start": start,                 # YYYY-MM-DD
            "end": (end or "").strip(),     # YYYY-MM-DD ή ""
            "work_title": work_title,
            "conservator_name": conservator_name,
        })
    return out


def get_maintenance_overview_stats() -> dict:
    """
    Μετράει τις ΑΝΟΙΧΤΕΣ συντηρήσεις (δηλ. end IS NULL),
    μόνο για έργα που δεν είναι archived.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM maintenance m
        JOIN works w ON w.id = m.work_id
        WHERE m.end IS NULL
          AND COALESCE(w.is_archived, 0) = 0
    """)
    open_count = int(cur.fetchone()[0] or 0)

    conn.close()
    return {"open": open_count}
