# dialogs.py
import re
from PySide6.QtWidgets import QHeaderView
from PySide6.QtWidgets import QComboBox
from db import get_all_artists, add_artist 
from PySide6.QtWidgets import QComboBox, QFileDialog
import sqlite3
from datetime import date, timedelta
from db import DB_NAME, get_all_artists, add_artist
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QFrame, QListWidget, QListWidgetItem, QTextEdit,
    QGraphicsDropShadowEffect
)
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QDateEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt, QDate

from db import get_all_works
from db import add_work, update_work
from db import get_loan_by_id, delete_work
from db import archive_work
from PySide6.QtWidgets import QDateTimeEdit
from PySide6.QtCore import QDateTime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QSpinBox,
    QHeaderView, QAbstractItemView, QMessageBox
)
from PySide6.QtWidgets import QGroupBox, QLabel
from PySide6.QtWidgets import QMessageBox, QDialog
from db import add_artist, update_artist, delete_artist
from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QPushButton, QComboBox, QDateEdit, QMessageBox, QTableWidget, QTableWidgetItem
)

from db import (
    get_active_loan_for_work, get_loan_by_id,
    get_all_borrowers, add_loan, update_loan, mark_loan_returned,
    set_work_hall, get_exhibitions_for_work, DB_NAME
)

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QDateEdit,
    QTextEdit,
    QSpinBox,
)

from db import get_user_if_valid,get_all_halls, get_hall_name_by_id


class LoginDialog(QDialog):
    """Απλό login για προσωπικό."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Σύνδεση προσωπικού")
        self.setFixedSize(320, 200)

        self.user = None  # εδώ θα κρατήσουμε τον εργαζόμενο που συνδέθηκε

        layout = QVBoxLayout(self)

        title = QLabel("Σύνδεση προσωπικού")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        form = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)

        form.addRow("Χρήστης:", self.username_edit)
        form.addRow("Κωδικός:", self.password_edit)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        login_btn = QPushButton("Είσοδος")
        cancel_btn = QPushButton("Έξοδος")

        btn_layout.addStretch()
        btn_layout.addWidget(login_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        login_btn.clicked.connect(self.handle_login)
        cancel_btn.clicked.connect(self.reject)

        

    def handle_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        if not username or not password:
            QMessageBox.warning(self, "Σφάλμα", "Συμπλήρωσε χρήστη και κωδικό.")
            return

        user = get_user_if_valid(username, password)
        if user:
            self.user = user
            self.accept()
        else:
            QMessageBox.warning(self, "Σφάλμα", "Λάθος στοιχεία σύνδεσης.")


class ExhibitionDialog(QDialog):
    """Dialog για Νέα / Επεξεργασία έκθεσης, με 2 ημερομηνίες + αριθμό έργων + rich text περιγραφή."""

    def __init__(self, parent=None, exhibition=None):
        super().__init__(parent)

        self.setWindowTitle("Νέα έκθεση" if exhibition is None else "Επεξεργασία έκθεσης")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        # ID (read-only)
        self.id_label = QLabel()
        form.addRow("ID:", self.id_label)
        
        self.title_edit = QLineEdit()

        # Ημερομηνίες
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("dd/MM/yyyy")

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("dd/MM/yyyy")

        # Αριθμός έργων
        self.num_works_spin = QSpinBox()
        self.num_works_spin.setRange(0, 10000)
        self.num_works_spin.setValue(0)
        self.num_works_spin.setEnabled(False)

        # Επιμελητής (προαιρετικό)
        self.curator_combo = QComboBox()
        self.curator_combo.addItem("— Χωρίς επιμελητή —", None)
        try:
            from db import get_curators_for_combo
            curators = get_curators_for_combo()
            for c in curators:
                name = f"{c['last_name']} {c['first_name']}".strip()
                self.curator_combo.addItem(name if name else f"ID {c['id']}", c["id"])
        except Exception:
            pass

        # Μέγιστες θέσεις (προαιρετικό)
        self.max_seats_spin = QSpinBox()
        self.max_seats_spin.setRange(0, 1000000)
        self.max_seats_spin.setSpecialValueText("—")
        self.max_seats_spin.setValue(0)

        # Κρατημένες θέσεις (από tickets) - read only
        self.reserved_label = QLabel("0")



        # Περιγραφή
        self.desc_edit = QTextEdit()
        self.desc_edit.setFixedHeight(140)
        self.desc_edit.setAcceptRichText(True)
        self.desc_edit.setPlaceholderText(
            "Περιγραφή έκθεσης...\n"
            "Μπορείς να κάνεις copy-paste μορφοποιημένο κείμενο (bold, λίστες κλπ)."
        )

        form.addRow("Τίτλος:", self.title_edit)
        form.addRow("Έναρξη:", self.start_date_edit)
        form.addRow("Λήξη:", self.end_date_edit)
        form.addRow("Επιμελητής:", self.curator_combo)
        form.addRow("Μέγιστες θέσεις:", self.max_seats_spin)
        form.addRow("Κρατημένες θέσεις:", self.reserved_label)

        form.addRow("Αριθμός έργων:", self.num_works_spin)
        form.addRow("Περιγραφή:", self.desc_edit)

        layout.addLayout(form)
        
        # --- Selected works state (κρατάει τα επιλεγμένα έργα για την έκθεση)
        self.selected_works = []   # [{"work_id":..,"order":..,"note":..}, ...]

        # --- κουμπί επιλογής έργων
        self.pick_works_btn = QPushButton("🖼️ Επιλογή έργων…")
        self.pick_works_btn.setCursor(Qt.PointingHandCursor)
        self.pick_works_btn.setStyleSheet("""
        QPushButton {
            background-color: #111827;
            color: white;
            border-radius: 12px;
            padding: 8px 12px;
            font-weight: 600;
        }
        QPushButton:hover { background-color: #0b1220; }
        """)
        layout.addWidget(self.pick_works_btn)


        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Αποθήκευση")
        cancel_btn = QPushButton("Άκυρο")
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        save_btn.clicked.connect(self.on_save_clicked)
        cancel_btn.clicked.connect(self.reject)
        self.pick_works_btn.clicked.connect(self.open_works_picker)



        # Αν είναι edit, προ-συμπληρώνουμε
        if exhibition is not None:
            self.id_label.setText(str(exhibition["id"]))

            self.title_edit.setText(exhibition["title"])
            self.desc_edit.setHtml(exhibition["description"])

            try:
                y1, m1, d1 = map(int, exhibition["start_date"].split("-"))
                self.start_date_edit.setDate(QDate(y1, m1, d1))
            except Exception:
                self.start_date_edit.setDate(QDate.currentDate())

            end_str = exhibition.get("end_date") or exhibition["start_date"]
            try:
                y2, m2, d2 = map(int, end_str.split("-"))
                self.end_date_edit.setDate(QDate(y2, m2, d2))
            except Exception:
                self.end_date_edit.setDate(self.start_date_edit.date())

            self.num_works_spin.setValue(exhibition.get("num_works", 0) or 0)
            self.desc_edit.setHtml(exhibition["description"])
                # ✅ Φόρτωσε τα ήδη επιλεγμένα έργα της έκθεσης (για preselect στον picker)
            try:
                from db import get_exhibition_work_items
                self.selected_works = get_exhibition_work_items(exhibition["id"]) or []
                self.num_works_spin.setValue(len(self.selected_works))
            except Exception as e:
                # αν κάτι πάει στραβά, μην σπάει το dialog
                self.selected_works = []
            # Prefill επιμελητή
            cur_id = exhibition.get("curator_id", None)
            if cur_id is None:
                self.curator_combo.setCurrentIndex(0)
            else:
                for i in range(self.curator_combo.count()):
                    if self.curator_combo.itemData(i) == cur_id:
                        self.curator_combo.setCurrentIndex(i)
                        break

            # Prefill max seats
            ms = exhibition.get("max_seats", None)
            self.max_seats_spin.setValue(int(ms) if ms else 0)

            # Prefill reserved seats (από get_all_exhibitions -> reserved_seats)
            self.reserved_label.setText(str(exhibition.get("reserved_seats", 0) or 0))


        else:
            self.id_label.setText("Θα δοθεί αυτόματα")
            today = QDate.currentDate()
            self.start_date_edit.setDate(today)
            self.end_date_edit.setDate(today.addDays(7))


    def on_save_clicked(self):
        title = self.title_edit.text().strip()
        if len(getattr(self, "selected_works", [])) == 0:
            QMessageBox.warning(self, "Σφάλμα", "Πρέπει να επιλέξεις τουλάχιστον 1 έργο.")
            return


        if not title:
            QMessageBox.warning(self, "Σφάλμα", "Ο τίτλος είναι υποχρεωτικός.")
            return

        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()

        if end_date < start_date:
            QMessageBox.warning(
                self,
                "Σφάλμα",
                "Η ημερομηνία λήξης δεν μπορεί να είναι πριν από την ημερομηνία έναρξης.",
            )
            return

        # (προαιρετικό) προειδοποίηση αν η έναρξη είναι στο παρελθόν
        # from PySide6.QtCore import QDate στην κορυφή του αρχείου
        #
        # if start_date < QDate.currentDate():
        #     reply = QMessageBox.question(
        #         self,
        #         "Προειδοποίηση",
        #         "Η ημερομηνία έναρξης είναι στο παρελθόν.\n"
        #         "Θέλεις σίγουρα να συνεχίσεις;",
        #         QMessageBox.Yes | QMessageBox.No,
        #     )
        #     if reply == QMessageBox.No:
        #         return

        self.accept()

    def open_works_picker(self):
        # imports εδώ για να μην κάνεις κυκλικά imports στην κορυφή
        from db import get_all_works
        from dialogs import ExhibitionWorksPickerDialog  # αν είναι στο ίδιο αρχείο, μπορείς να το αφαιρέσεις

        all_works = get_all_works()
        pick = ExhibitionWorksPickerDialog(self, all_works=all_works, selected_items=self.selected_works)
        if pick.exec() == QDialog.Accepted:
            self.selected_works = pick.get_selected_items()            
            self.num_works_spin.setValue(len(self.selected_works))     



    def get_data(self):
        title = self.title_edit.text().strip()
        qs = self.start_date_edit.date()
        qe = self.end_date_edit.date()
        start_str = qs.toString("yyyy-MM-dd")
        end_str = qe.toString("yyyy-MM-dd")
        num_works = int(self.num_works_spin.value())
        desc = self.desc_edit.toHtml().strip()

        curator_id = self.curator_combo.currentData()
        if curator_id in ("", 0):
            curator_id = None

        max_seats_val = int(self.max_seats_spin.value())
        max_seats = None if max_seats_val == 0 else max_seats_val

        return title, start_str, end_str, num_works, desc, curator_id, max_seats



class ArtistDialog(QDialog):
    """Διάλογος για Νέο / Επεξεργασία Καλλιτέχνη."""

    def __init__(self, parent=None, artist=None):
        super().__init__(parent)
        self.setWindowTitle("Νέος καλλιτέχνης" if artist is None else "Επεξεργασία καλλιτέχνη")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.first_name_edit = QLineEdit()
        self.last_name_edit = QLineEdit()

        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setDisplayFormat("dd/MM/yyyy")

        self.death_date_edit = QDateEdit()
        self.death_date_edit.setCalendarPopup(True)
        self.death_date_edit.setDisplayFormat("dd/MM/yyyy")

        self.nationality_edit = QLineEdit()
        self.specialty_edit = QLineEdit()
        self.info_edit = QTextEdit()
        self.info_edit.setFixedHeight(100)

        form.addRow("Όνομα:", self.first_name_edit)
        form.addRow("Επώνυμο:", self.last_name_edit)
        form.addRow("Ημ. γέννησης:", self.birth_date_edit)
        form.addRow("Ημ. θανάτου:", self.death_date_edit)
        form.addRow("Εθνικότητα:", self.nationality_edit)
        form.addRow("Ειδικότητα:", self.specialty_edit)
        form.addRow("Πληροφορίες:", self.info_edit)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Αποθήκευση")
        cancel_btn = QPushButton("Άκυρο")
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        save_btn.clicked.connect(self.on_save_clicked)
        cancel_btn.clicked.connect(self.reject)

        if artist is not None:
            self.first_name_edit.setText(artist["first_name"])
            self.last_name_edit.setText(artist["last_name"])
            self.specialty_edit.setText(artist.get("specialty", ""))


            if artist["birth_date"]:
                y, m, d = map(int, artist["birth_date"].split("-"))
                self.birth_date_edit.setDate(QDate(y, m, d))
            else:
                self.birth_date_edit.setDate(QDate.currentDate())

            if artist["death_date"]:
                y, m, d = map(int, artist["death_date"].split("-"))
                self.death_date_edit.setDate(QDate(y, m, d))
            else:
                self.death_date_edit.setDate(self.birth_date_edit.date())

            self.nationality_edit.setText(artist["nationality"])
            self.info_edit.setPlainText(artist["info"])
        else:
            today = QDate.currentDate()
            self.birth_date_edit.setDate(today)
            self.death_date_edit.setDate(today)

    def on_save_clicked(self):
        if not self.last_name_edit.text().strip():
            QMessageBox.warning(self, "Σφάλμα", "Το επώνυμο είναι υποχρεωτικό.")
            return
        self.accept()

    def get_data(self):
        fn = self.first_name_edit.text().strip()
        ln = self.last_name_edit.text().strip()

        bd = self.birth_date_edit.date().toString("yyyy-MM-dd")
        dd = self.death_date_edit.date().toString("yyyy-MM-dd")
        nat = self.nationality_edit.text().strip()
        spec = self.specialty_edit.text().strip()
        info = self.info_edit.toPlainText().strip()
        return fn, ln, bd, dd, nat, spec, info



class WorkDialog(QDialog):
    """Διάλογος για Νέο / Επεξεργασία Έργου."""

    def __init__(self, parent=None, work=None):
        super().__init__(parent)
        self.work = work  

        self.setWindowTitle("Νέο έργο" if work is None else "Επεξεργασία έργου")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_edit = QLineEdit()
        self.year_edit = QLineEdit()
        self.height_edit = QLineEdit()
        self.width_edit = QLineEdit()
        self.depth_edit = QLineEdit()
        self.weight_edit = QLineEdit()
        self.condition_edit = QComboBox()
        self.condition_edit.addItems(["Άριστη", "Καλή", "Μέτρια", "Κακή", "Χρειάζεται"])
        self.condition_edit.setCurrentIndex(1)  # default: "Καλή"
        self.production_place_edit = QLineEdit()

        self.artist_combo = QComboBox()
        self.artist_ids = []

        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(120)
        
        self.production_place_edit = QLineEdit()

        self.image_path_edit = QLineEdit()
        self.image_browse_btn = QPushButton("...")

        img_layout = QHBoxLayout()
        img_layout.addWidget(self.image_path_edit)
        img_layout.addWidget(self.image_browse_btn)

        self.category_combo = QComboBox()
        self.category_combo.addItem("—", userData="")
        self.category_combo.addItem("Πίνακας", userData="Πίνακας")
        self.category_combo.addItem("Γλυπτό", userData="Γλυπτό")

        self.material_label = QLabel("Υλικό:")
        self.material_edit = QLineEdit()

        self.technique_label = QLabel("Τεχνική:")
        self.technique_edit = QLineEdit()

        self.hall_combo = QComboBox()

        # επιλογή για None hall_id
        self.hall_combo.addItem("— Εκτός Αίθουσας —", userData=None)

        #γέμισμα από DB
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM halls ORDER BY name")
        for row in cur.fetchall():
            self.hall_combo.addItem(row[1], userData=row[0])
        conn.close()


        form.addRow("Αίθουσα:", self.hall_combo)
        self.chk_external = QCheckBox("Εξωτερικό (δανεισμένο σε εμάς)")
        form.addRow(self.chk_external)

        # γέμισμα artists στο combo
        artists = get_all_artists()
        self.artist_combo.addItem("— Χωρίς καλλιτέχνη —", userData=None)
        self.artist_ids.append(None)
        for a in artists:
            # Γιάννης Τάδε (1890–1956, Έλληνας ζωγράφος)
            first = (a["first_name"] or "").strip()
            last = (a["last_name"] or "").strip()
            name = f"{first} {last}".strip() or "(χωρίς όνομα)"

            years_part = ""
            if a["birth_date"] and a["death_date"]:
                by = a["birth_date"].split("-")[0]
                dy = a["death_date"].split("-")[0]
                years_part = f"{by}–{dy}"
            elif a["birth_date"]:
                by = a["birth_date"].split("-")[0]
                years_part = f"γεν. {by}"

            desc_parts = []
            if a["nationality"]:
                desc_parts.append(a["nationality"])
            if a["specialty"]:
                desc_parts.append(a["specialty"].lower())

            inner = ""
            if years_part and desc_parts:
                inner = f"{years_part}, " + ", ".join(desc_parts)
            elif years_part:
                inner = years_part
            elif desc_parts:
                inner = ", ".join(desc_parts)

            label = f"{name} ({inner})" if inner else name

            self.artist_combo.addItem(label, userData=a["id"])
            self.artist_ids.append(a["id"])


        form.addRow("Τίτλος:", self.title_edit)
        form.addRow("Έτος:", self.year_edit)
        form.addRow("Ύψος (cm):", self.height_edit)
        form.addRow("Πλάτος (cm):", self.width_edit)
        form.addRow("Βάθος (cm):", self.depth_edit)
        form.addRow("Βάρος (kg):", self.weight_edit)
        form.addRow("Κατάσταση:", self.condition_edit)
        form.addRow("Τόπος παραγωγής:", self.production_place_edit)
        form.addRow("Καλλιτέχνης:", self.artist_combo)
        form.addRow("Κατηγορία:", self.category_combo)
        form.addRow(self.material_label, self.material_edit)
        form.addRow(self.technique_label, self.technique_edit)
        form.addRow("Εικόνα:", img_layout)



        form.addRow("Σημειώσεις:", self.notes_edit)


        layout.addLayout(form)

        # Δανεισμός

        self.loan_group = QGroupBox("Δανεισμός")
        loan_layout = QVBoxLayout(self.loan_group)

        self.loan_status_label = QLabel("Κατάσταση: —")
        self.loan_status_label.setStyleSheet("font-weight: 600;")

        btn_row = QHBoxLayout()
        self.btn_manage_loan = QPushButton("Διαχείριση δανεισμού…")
        self.btn_return_loan = QPushButton("Καταχώρηση επιστροφής")
        btn_row.addWidget(self.btn_manage_loan)
        btn_row.addWidget(self.btn_return_loan)
        btn_row.addStretch()

        loan_layout.addWidget(self.loan_status_label)
        loan_layout.addLayout(btn_row)

        layout.addWidget(self.loan_group)

        self.btn_manage_loan.clicked.connect(self._open_manage_loan)
        self.btn_return_loan.clicked.connect(self._return_loan)


        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Αποθήκευση")
        cancel_btn = QPushButton("Άκυρο")
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        save_btn.clicked.connect(self.on_save_clicked)
        cancel_btn.clicked.connect(self.reject)
        self.image_browse_btn.clicked.connect(self.browse_image)
        


        if work is not None:
            self.image_path_edit.setText(work.get("image_path") or "")

            self.title_edit.setText(work["title"])
            self.year_edit.setText(str(work["year"] or ""))

            self.height_edit.setText("" if work["height_cm"] is None else str(work["height_cm"]))
            self.width_edit.setText("" if work["width_cm"] is None else str(work["width_cm"]))
            self.depth_edit.setText("" if work["depth_cm"] is None else str(work["depth_cm"]))
            self.weight_edit.setText("" if work["weight_kg"] is None else str(work["weight_kg"]))

            saved = (work.get("condition") or "").strip()
            idx = self.condition_edit.findText(saved)
            if idx >= 0:
                self.condition_edit.setCurrentIndex(idx)
            else:
                self.condition_edit.setCurrentIndex(1)  # αν δεν ταιριάξει, "Καλή"
            self.production_place_edit.setText(work["production_place"])
            self.notes_edit.setPlainText(work["notes"])
            # κατηγορία / υλικό / τεχνική
            category = work.get("category") or ""
            idx = self.category_combo.findData(category)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)

            self.material_edit.setText(work.get("material") or "")
            self.technique_edit.setText(work.get("technique") or "")
            
            # επιλέγουμε αίθουσα
            hall_id = work.get("hall_id")
            if hall_id is not None:
                idx = self.hall_combo.findData(hall_id)
                if idx >= 0:
                    self.hall_combo.setCurrentIndex(idx)

            # επιλέγουμε καλλιτέχνη
            aid = work["artist_id"]
            if aid is not None:
                index = self.artist_combo.findData(aid)
                if index >= 0:
                    self.artist_combo.setCurrentIndex(index)
            self.chk_external.setChecked(bool(self.work.get("is_external")))
        
        self._refresh_loan_section()

        self.category_combo.currentIndexChanged.connect(self.update_category_fields)
        self.update_category_fields()


    def update_category_fields(self):
        cat = self.category_combo.currentData()
        is_painting = (cat == "Πίνακας")
        is_sculpture = (cat == "Γλυπτό")

        # Υλικό μόνο για γλυπτά
        self.material_label.setVisible(is_sculpture)
        self.material_edit.setVisible(is_sculpture)

        # Τεχνική μόνο για πίνακες
        self.technique_label.setVisible(is_painting)
        self.technique_edit.setVisible(is_painting)


    def on_save_clicked(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Σφάλμα", "Ο τίτλος είναι υποχρεωτικός.")
            return

        (title, year, h, w, d, weight,
         cond, place, artist_id, notes,
         image_path, category, material, technique, hall_id, is_external) = self.get_data()

        try:
            if self.work is None or not self.work.get("id"):
                # ✅ INSERT
                new_id = add_work(title, year, h, w, d, weight,
                                  cond, place, artist_id, notes,
                                  image_path, category, material, technique, hall_id,is_external)

                # ✅ τώρα το dialog "ξέρει" το id, άρα ξεκλειδώνει ο δανεισμός
                self.work = {"id": new_id, "title": title,"is_external": bool(is_external)}

                self._refresh_loan_section()
                QMessageBox.information(self, "OK", f"Το έργο αποθηκεύτηκε (ID: {new_id}).")

                # ⛔ ΜΗΝ κάνεις accept εδώ → μένει ανοιχτό
                return

            else:
                # ✅ UPDATE
                work_id = self.work["id"]
                update_work(work_id, title, year, h, w, d, weight,
                            cond, place, artist_id, notes,
                            image_path, category, material, technique, hall_id,is_external)

                self.work["title"] = title
                self.work["is_external"] = bool(is_external)
                self._refresh_loan_section()
                QMessageBox.information(self, "OK", "Οι αλλαγές αποθηκεύτηκαν.")
                return

        except Exception as e:
            QMessageBox.warning(self, "Σφάλμα", str(e))


    def _parse_float(self, text):
        text = text.strip().replace(",", ".")
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def _parse_int(self, text):
        text = text.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None

    def browse_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Επιλογή εικόνας έργου",
            "",
            "Εικόνες (*.png *.jpg *.jpeg *.bmp);;Όλα τα αρχεία (*)",
        )
        if path:
            self.image_path_edit.setText(path)

    def _get_borrower_name(self, borrower_id: int) -> str:
        if not borrower_id:
            return ""
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT name FROM borrowers WHERE id=?", (borrower_id,))
        r = cur.fetchone()
        conn.close()
        return (r[0] if r else "") or ""

    def _refresh_loan_section(self):
        # new work -> δεν έχει id ακόμα
        if not self.work or not self.work.get("id"):
            self.loan_status_label.setText("Κατάσταση: (Αποθήκευσε πρώτα το έργο για δανεισμό)")
            self.btn_manage_loan.setEnabled(False)
            self.btn_return_loan.setEnabled(False)
            return

        self.btn_manage_loan.setEnabled(True)

        work_id = self.work["id"]
        active = get_active_loan_for_work(work_id)

        if not active:
            self.loan_status_label.setText("Κατάσταση: Διαθέσιμο")
            self.btn_return_loan.setEnabled(False)

            # ✅ επιτρέπουμε κανονικά αίθουσα
            self.hall_combo.setEnabled(True)
            self.hall_combo.setToolTip("")
            return

        borrower_name = self._get_borrower_name(active["borrower_id"])
        end_date = (active.get("end_date") or "").strip()

        txt = "Κατάσταση: Δανεισμένο"
        if end_date:
            txt += f" έως {end_date}"
        if borrower_name:
            txt += f" · Δανειστής: {borrower_name}"

        self.loan_status_label.setText(txt)
        self.btn_return_loan.setEnabled(True)

        # ✅ Validation: όταν είναι δανεισμένο, δεν αλλάζουμε αίθουσα (είναι εκτός χώρου)
        self.hall_combo.setEnabled(False)
        self.hall_combo.setToolTip("Το έργο είναι δανεισμένο — θεωρείται εκτός αίθουσας.")

    def _open_manage_loan(self):
        if not self.work or not self.work.get("id"):
            QMessageBox.information(self, "Info", "Πρώτα αποθήκευσε το έργο.")
            return

        work_id = self.work["id"]
        active = get_active_loan_for_work(work_id)

        borrowers = get_all_borrowers()
        works_for_dialog = [{"id": work_id, "title": self.work.get("title", "")}]

        loan_data = None
        if active:
            # παίρνουμε πλήρες loan record
            loan_data = get_loan_by_id(active["id"])
            
        direction = "IN" if self.work.get("is_external") else "OUT"
        dlg = LoanDialog(
            self,
            works=works_for_dialog,
            borrowers=borrowers,
            loan_data=loan_data,
            lock_work=True
        )
        # κλείδωμα
        idx = dlg.direction_combo.findData(direction)
        if idx >= 0:
            dlg.direction_combo.setCurrentIndex(idx)
        dlg.direction_combo.setEnabled(False)

        if dlg.exec() != QDialog.Accepted:
            return

        d = dlg.get_data()

        try:
            if not active:
                # ✅ Validation: αν το έργο είναι σε (τρέχουσα/επερχόμενη) έκθεση → warning/μπλοκ
                ex_list = get_exhibitions_for_work(work_id, from_today=True)
                if ex_list:
                    ex_titles = "\n".join([f"• {x['title']} ({x['start_date']} – {x['end_date']})" for x in ex_list])
                    ans = QMessageBox.question(
                        self,
                        "Προειδοποίηση",
                        "Το έργο είναι προγραμματισμένο/ενεργό σε έκθεση:\n\n"
                        f"{ex_titles}\n\n"
                        "Θες να συνεχίσεις με δανεισμό;",
                    )
                    if ans != QMessageBox.Yes:
                        return

                add_loan(
                    work_id=work_id,
                    borrower_id=d["borrower_id"],
                    start_date=d["start_date"],
                    end_date=d["end_date"] or None,
                    notes=d["notes"], direction=d["direction"]
                )

                # ✅ Validation: όταν δανειστεί, το βγάζουμε εκτός αίθουσας
                #OUT → το βγάζεις από αίθουσαIN → δεν το πειράζεις, μένει στην αίθουσα που έβαλες
                direction = d["direction"]  # από LoanDialog (OUT/IN)

                if direction == "OUT":
                    
                    set_work_hall(work_id, None)
                    self.hall_combo.setCurrentIndex(0)



            else:
                update_loan(
                    loan_id=active["id"],
                    borrower_id=d["borrower_id"],
                    start_date=d["start_date"],
                    end_date=d["end_date"] or None,
                    notes=d["notes"], direction=d["direction"]
                )

            # refresh UI
            self._refresh_loan_section()

            # ενημέρωσε main window αν υπάρχει
            p = self.parent()
            if p and hasattr(p, "load_works_gallery"):
                p.load_works_gallery()
            if p and hasattr(p, "reload_loans_table"):
                p.reload_loans_table()

        except Exception as e:
            QMessageBox.warning(self, "Σφάλμα", str(e))

    def _return_loan(self):
        if not self.work or not self.work.get("id"):
            return

        work_id = self.work["id"]
        active = get_active_loan_for_work(work_id)
        if not active:
            QMessageBox.information(self, "Info", "Δεν υπάρχει ενεργός δανεισμός.")
            return

        if QMessageBox.question(self, "Επιβεβαίωση", "Καταχώρηση επιστροφής;") != QMessageBox.Yes:
            return

        try:
            # ✅ Φέρνουμε τον δανεισμό για να δούμε direction (IN/OUT)
            loan = get_loan_by_id(active["id"])
            direction = (loan or {}).get("direction", "OUT")

            # 1) κλείνουμε τον δανεισμό
            mark_loan_returned(active["id"])

            # 2) Αν είναι IN (δανειζόμαστε) -> το έργο πρέπει να φύγει από τη βάση
            if direction == "IN":
                archive_work(work_id)

                # refresh parent πριν κλείσουμε
                p = self.parent()
                if p and hasattr(p, "load_works_gallery"):
                    p.load_works_gallery()
                if p and hasattr(p, "load_works_maintenance"):
                    p.load_works_maintenance()
                if p and hasattr(p, "reload_loans_table"):
                    p.reload_loans_table()

                # ✅ το έργο δεν υπάρχει πια, άρα κλείνουμε το WorkDialog
                self.reject()
                return

            # 3) OUT: απλά refresh (το έργο μένει στη συλλογή)
            self._refresh_loan_section()

            p = self.parent()
            if p and hasattr(p, "load_works_gallery"):
                p.load_works_gallery()
            if p and hasattr(p, "load_works_maintenance"):
                p.load_works_maintenance()
            if p and hasattr(p, "reload_loans_table"):
                p.reload_loans_table()

        except Exception as e:
            QMessageBox.warning(self, "Σφάλμα", str(e))


    def get_data(self):
        title = self.title_edit.text().strip()
        year = self._parse_int(self.year_edit.text())
        h = self._parse_float(self.height_edit.text())
        w = self._parse_float(self.width_edit.text())
        d = self._parse_float(self.depth_edit.text())
        weight = self._parse_float(self.weight_edit.text())
        cond = self.condition_edit.currentText().strip()
        place = self.production_place_edit.text().strip()
        notes = self.notes_edit.toPlainText().strip()
        artist_id = self.artist_combo.currentData()
        image_path = self.image_path_edit.text().strip()
        category = self.category_combo.currentData() or ""
        material = self.material_edit.text().strip()
        technique = self.technique_edit.text().strip()
        hall_id = self.hall_combo.currentData()
        is_external = self.chk_external.isChecked()
        
        
        return (title, year, h, w, d, weight, cond, place, artist_id, notes,
                image_path, category, material, technique, hall_id,is_external)





class StaffDialog(QDialog):
    def __init__(self, parent=None, staff_data=None):
        super().__init__(parent)
        self.setWindowTitle("Νέο Προσωπικό")
        self.setMinimumWidth(380)
        self.staff_data = staff_data

        layout = QVBoxLayout(self)
        self.form = QFormLayout()
       

     # ----------------- Γενικά------------------------
        self.error_style = """
QLineEdit {
    border: 1px solid #E53935;
    border-radius: 6px;
    padding: 6px;
}
"""
        self.normal_style = """
QLineEdit {
    border: 1px solid #ccc;
    border-radius: 6px;
    padding: 6px;
}
"""


        self.first_name_edit = QLineEdit()
        self.last_name_edit = QLineEdit()
        self.pn_edit = QLineEdit()
        self.wage_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.first_name_edit.textChanged.connect(
        lambda: self.validate_field(
        self.first_name_edit,
        r"[Α-Ωα-ωA-Za-zΆ-Ώά-ώ\s'-]+",
        "Το όνομα πρέπει να περιέχει μόνο γράμματα"
    )
)

        self.last_name_edit.textChanged.connect(
        lambda: self.validate_field(
        self.last_name_edit,
        r"[Α-Ωα-ωA-Za-zΆ-Ώά-ώ\s'-]+",
        "Το επώνυμο πρέπει να περιέχει μόνο γράμματα"
    )
)

        self.pn_edit.textChanged.connect(
        lambda: self.validate_field(
        self.pn_edit,
        r"\d{10}",
        "Το τηλέφωνο πρέπει να έχει 10 ψηφία",
        optional=True
    )
)

        self.email_edit.textChanged.connect(
        lambda: self.validate_field(
        self.email_edit,
        r"[^@]+@[^@]+\.[^@]+",
        "Μη έγκυρο email",
        optional=True
    )
)

        self.wage_edit.textChanged.connect(self.validate_wage_live)

        # Combo box για γλώσσες (ξεναγός)
        self.language_combo = QComboBox()
        self.language_combo.addItems([
             "Αγγλικά", "Γαλλικά", "Γερμανικά", "Ιταλικά",
             "Ισπανικά", "Ρωσικά", "Κινέζικα"
             ])

        self.specialization_combo = QComboBox()

        

        self.form.addRow("Όνομα:", self.first_name_edit)
        self.form.addRow("Επώνυμο:", self.last_name_edit)
        self.form.addRow("Τηλέφωνο:", self.pn_edit)
        self.form.addRow("Μισθός:", self.wage_edit)
        self.form.addRow("Email:", self.email_edit)
        self.form.addRow("Διεύθυνση:", self.address_edit)

        # ----------------- Τύπος Προσωπικού -----------------

        self.staff_type_combo = QComboBox()
        self.staff_type_combo.addItems(["Συντηρητής", "Ξεναγός", "Επιμελητής"])
        self.form.addRow("Τύπος Προσωπικού:", self.staff_type_combo)

        
        # Προσθήκη ειδικότητας, γλώσσας και σπουδών στη φόρμα
        self.form.addRow("Ειδικότητα:", self.specialization_combo)
        self.form.addRow("Γλώσσα:", self.language_combo)

        self.specialization_combo.hide()
        self.language_combo.hide()

        layout.addLayout(self.form)

        # ----------------- Προκαθορισμένες ειδικότητες -----------------
    
        self.specializations = {
            "Συντηρητής":[
                "Συντήρηση Ζωγραφικής",
                "Συντήρηση Γλυπτών",
            ],
            "Επιμελητής":[
                "Σύγχρονη Τέχνη",
                "Αρχαιολογικές Συλλογές",
                "Ιστορία Τέχνης"
            ]
        }
        # ----------------- Κουμπιά Αποθήκευσης/Ακύρωσης -----------------
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Αποθήκευση")
        cancel_btn = QPushButton("Άκυρο")
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # Σύνδεση κουμπιών
        save_btn.clicked.connect(self.on_save_clicked)
        cancel_btn.clicked.connect(self.reject)

        # -----------------  Aλλαγή τύπου προσωπικού -----------------
        self.staff_type_combo.currentIndexChanged.connect(self.on_staff_type_changed)

        # Αν είναι νέο μέλος, δείξε default πεδία
        if self.staff_data is None:
            self.on_staff_type_changed(self.staff_type_combo.currentIndex())

        # Αν υπάρχει staff_data, γέμισε τα πεδία
        if self.staff_data:
            self.populate_fields()

    def validate_field(self, widget, pattern, error_msg, optional=False):
        ERROR_STYLE = """
        QLineEdit {
                border: 1px solid #E53935;
                border-radius: 6px;
                padding: 6px;
            }
            """

        NORMAL_STYLE = """
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 6px;
        }
            """
        text = widget.text().strip()

        if optional and not text:
            widget.setStyleSheet(NORMAL_STYLE)
            widget.setToolTip("")
            return True

        if not re.fullmatch(pattern, text):
            widget.setStyleSheet(ERROR_STYLE)
            widget.setToolTip(error_msg)
            return False

        widget.setStyleSheet(NORMAL_STYLE)
        widget.setToolTip("")
        return True

    def validate_wage_live(self):
        ERROR_STYLE = """
        QLineEdit {
                border: 1px solid #E53935;
                border-radius: 6px;
                padding: 6px;
            }
            """

        NORMAL_STYLE = """
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 6px;
        }
            """
        text = self.wage_edit.text().strip()

        if not text:
            self.wage_edit.setStyleSheet(NORMAL_STYLE)
            self.wage_edit.setToolTip("")
            return True

        if not text.isdigit():
            self.wage_edit.setStyleSheet(ERROR_STYLE)
            self.wage_edit.setToolTip("Ο μισθός πρέπει να είναι αριθμός")
            return False

        self.wage_edit.setStyleSheet(NORMAL_STYLE)
        self.wage_edit.setToolTip("")
        return True


    def validate_staff_data(self,data):

        #Έλεγχος εγκυρότητας των δεδομένων πριν την εισαγωγή στη βάση.

        if not re.fullmatch(r"[Α-Ωα-ωA-Za-zΆ-Ώά-ώ\s'-]+", data["first_name"]):
            return "first_name", "Το όνομα πρέπει να περιέχει μόνο γράμματα."
        if not re.fullmatch(r"[Α-Ωα-ωA-Za-zΆ-Ώά-ώ\s'-]+", data["last_name"]):
            return "last_name", "Το επώνυμο πρέπει να περιέχει μόνο γράμματα."
        if data["pn"] and not re.fullmatch(r"\d{10}", data["pn"]):
           return "pn", "Το τηλέφωνο πρέπει να έχει 10 ψηφία."
        if data["wage"]:
            if not data["wage"].isdigit():
                return "wage", "Ο μισθός πρέπει να είναι αριθμός."
            data["wage"] = int(data["wage"])
        if data["email"] and not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", data["email"]):
            return "email", "Το email δεν είναι έγκυρο."
        return None, None
    

    def show_field_error(self, field_name, message):
        field_map = {
            "first_name": self.first_name_edit,
            "last_name": self.last_name_edit,
            "pn": self.pn_edit,
            "wage": self.wage_edit,
            "email": self.email_edit,
            "address": self.address_edit,   
        }
        field = field_map.get(field_name)
        if not field:
            return
        field.setStyleSheet(self.error_style)
        field.setToolTip(message)
        field.setFocus()
    
    def on_save_clicked(self):
        data = self.get_data()

        field, error = self.validate_staff_data(data)
        if error:
            self.show_field_error(field, error)
            QMessageBox.warning(self, "Σφάλμα", str(error))
            return

        self.accept()
               
     # ----------------- Διαχείριση εμφάνισης πεδίων ανά τύπο προσωπικού ----------------- 
     #           
     
    def on_staff_type_changed(self,index):
         
        staff_type = self.staff_type_combo.itemText(index)
        self.specialization_combo.clear()

        if staff_type == "Συντηρητής":
            self.specialization_combo.addItems(self.specializations["Συντηρητής"])
            self.specialization_combo.show()
            self.language_combo.hide()
        elif staff_type == "Ξεναγός":
            self.specialization_combo.hide()
            self.language_combo.show()
        
        elif staff_type == "Επιμελητής":
            self.specialization_combo.addItems(self.specializations["Επιμελητής"])
            self.specialization_combo.show()
            self.language_combo.hide()
           
        else:
            self.specialization_combo.hide()
            self.language_combo.hide()
            

     # ----------------- Λήψη δεδομένων από τη φόρμα -----------------

    def get_data(self):
        type_map = {"Συντηρητής": "conservator", "Ξεναγός": "guide", "Επιμελητής": "curator"}
        staff_type_text = self.staff_type_combo.currentText()
        staff_type = type_map.get(staff_type_text, None)
          
        # Επιλογή γλώσσας μόνο για ξεναγούς
        language = self.language_combo.currentText().strip() if staff_type == "guide" else None

        # Επιλογή ειδικότητας μόνο για συντηρητές και επιμελητές
        specialization = None
        if staff_type in ("conservator", "curator"):
            specialization = self.specialization_combo.currentText().strip()
        return {
            "first_name": self.first_name_edit.text().strip(),
            "last_name": self.last_name_edit.text().strip(),
            "pn": self.pn_edit.text().strip() or None,
            "wage": self.wage_edit.text().strip() or None,
            "email": self.email_edit.text().strip() or None,
            "address": self.address_edit.text().strip() or None,
            "specialization": specialization or None,
            "language": language,
            "staff_type": staff_type
        }

    def populate_fields(self):
    # Συμπλήρωση γενικών πεδίων
        self.first_name_edit.setText(str(self.staff_data.get("first_name") or ""))
        self.last_name_edit.setText(str(self.staff_data.get("last_name") or ""))
        self.pn_edit.setText(str(self.staff_data.get("pn") or ""))
        self.wage_edit.setText(str(self.staff_data.get("wage") or ""))
        self.email_edit.setText(str(self.staff_data.get("email") or ""))
        self.address_edit.setText(str(self.staff_data.get("address") or ""))

    # Μετατροπή τύπου προσωπικού σε ελληνικά
        type_map = {
        "conservator": "Συντηρητής",
        "guide": "Ξεναγός",
        "curator": "Επιμελητής"
        }
        staff_type_text = type_map.get(self.staff_data.get("staff_type"), "Συντηρητής")
        #self.staff_type_combo.setCurrentText(staff_type_text)

    # Εμφάνιση σωστών πεδίων ανά τύπο προσωπικού
    # **Καλούμε μόνο μετά τη ρύθμιση του combo**
        self.staff_type_combo.setCurrentText(staff_type_text)
        self.on_staff_type_changed(self.staff_type_combo.currentIndex())

    # Θέτουμε ειδικότητα ή γλώσσα
        if self.staff_data.get("specialization") and staff_type_text in ("Συντηρητής", "Επιμελητής"):
            self.specialization_combo.setCurrentText(self.staff_data["specialization"])
        if self.staff_data.get("language") and staff_type_text == "Ξεναγός":
            self.language_combo.setCurrentText(self.staff_data["language"])





class ArtistBrowserPopup(QFrame):
    """
    Modern popup (Qt.Popup) που εμφανίζει καλλιτέχνες σαν cards + detail panel.

    - Ανοίγει "κάτω από" ένα κουμπί (anchor widget)
    - Κλείνει αυτόματα όταν πατήσεις έξω (Qt.Popup συμπεριφορά)
    - Δίνει πίσω στον caller (MainWindow) τον επιλεγμένο καλλιτέχνη μέσω callback

    Χρήση:
        popup = ArtistBrowserPopup(parent=self, apply_callback=func)
        popup.open_below(anchor_widget)
    """

    def __init__(self, parent=None, apply_callback=None):
        super().__init__(parent)

        # Callback: συνάρτηση που θα καλέσουμε όταν ο χρήστης πατήσει "Φιλτράρισε τα έργα"
        # π.χ. στο main_window.py: να γράφει το όνομα στο search και να κάνει refresh το gallery.
        self.apply_callback = apply_callback

        # Cache δεδομένων (θα φορτωθούν 1 φορά όταν ανοίξει το popup)
        self._artists = []          # λίστα dict με καλλιτέχνες από DB
        self._works_count = {}      # dict: artist_id -> πόσα έργα έχει

        # ---------- Window flags / συμπεριφορά popup ----------
        # Qt.Popup: κλείνει όταν πατήσεις έξω
        # Frameless: χωρίς default "παράθυρο" και τίτλο
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)

        # Επιτρέπει rounded corners + shadow σε “floating” κάρτα (διαφανές background στο window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # ---------- Outer container (η "κάρτα") ----------
        # Δεν κάνουμε style στο ίδιο το window, αλλά σε ένα outer QFrame για καθαρό αποτέλεσμα.
        outer = QFrame()
        outer.setObjectName("outerCard")

        # QSS για "μοντέρνο" dark glass look (μπορείς να το αλλάξεις όπως θες)
        outer.setStyleSheet("""
        QFrame#outerCard {
            background-color: #111827;          /* ίδιο με menu */
            border: 1px solid #374151;          /* ίδιο με menu border */
            border-radius: 18px;
        }
        QLabel { color: #e5e7eb; }
        QLineEdit {
            background-color: #0f172a;
            border: 1px solid #1f2937;
            border-radius: 12px;
            padding: 8px 10px;
            color: #e5e7eb;
        }
        QListWidget { background: transparent; border: none; }
        QTextEdit {
            background-color: #0f172a;
            border: 1px solid #1f2937;
            border-radius: 14px;
            color: #e5e7eb;
            padding: 8px;
        }
        QPushButton {
            background-color: #2563eb;         /* ίδιο highlight με menu */
            border: none;
            border-radius: 12px;
            padding: 10px 12px;
            color: #f9fafb;
            font-weight: 700;
        }
        QPushButton:hover { background-color: #1d4ed8; }
        QPushButton:pressed { background-color: #1e40af; }
        """)


        # ---------- Shadow effect ----------
        # Δίνει “floating card” αίσθηση (μοντέρνο UI)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 12)
        outer.setGraphicsEffect(shadow)

        # ---------- Main layout (2 στήλες: αριστερά λίστα, δεξιά λεπτομέρειες) ----------
        main = QHBoxLayout(outer)
        main.setContentsMargins(14, 14, 14, 14)
        main.setSpacing(14)

        # ======================================================
        # LEFT: Title + Search + List
        # ======================================================
        left = QVBoxLayout()
        left.setSpacing(10)

        title = QLabel("Καλλιτέχνες")
        f = QFont()
        f.setPointSize(12)
        f.setBold(True)
        title.setFont(f)

        # Search input (φιλτράρει live)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Αναζήτηση καλλιτέχνη…")
        self.search.textChanged.connect(self._render_list)

        # List (εμφανίζει “cards” με name + αριθμό έργων)
        # List
        self.list = QListWidget()
        self.list.setSpacing(10)
        self.list.setMinimumWidth(360)

        # επιλογή -> ενημέρωση detail panel
        self.list.currentItemChanged.connect(self._on_current_changed)
        # πιο “dropdown/combobox” selection styling
        self.list.setStyleSheet("""
        QListWidget::item { border: none; padding: 0px; }
        QListWidget::item:selected { background: transparent; }   /* το κάνουμε εμείς */
        QListWidget::item:hover { background: transparent; }
        """)
        self.list.currentRowChanged.connect(self._apply_selection_styles)


        # Όταν αλλάζει επιλογή, ενημερώνουμε το detail panel
        self.list.currentItemChanged.connect(self._on_current_changed)

        left.addWidget(title)
        left.addWidget(self.search)
        left.addWidget(self.list, 1)

        # ======================================================
        # RIGHT: Details + Apply button
        # ======================================================
        right = QVBoxLayout()
        right.setSpacing(10)

        # Τίτλος επιλεγμένου καλλιτέχνη
        self.detail_name = QLabel("Επίλεξε καλλιτέχνη")
        f2 = QFont()
        f2.setPointSize(11)
        f2.setBold(True)
        self.detail_name.setFont(f2)

        # Meta πληροφορίες (εθνικότητα, ημερομηνίες, πόσα έργα)
        self.detail_meta = QLabel("")
        self.detail_meta.setStyleSheet("color: rgba(232,238,252,180);")

        # Πεδίο πληροφοριών/βιογραφικού (read-only)
        self.detail_info = QTextEdit()
        self.detail_info.setReadOnly(True)
        self.detail_info.setMinimumWidth(360)
        self.detail_info.setMinimumHeight(200)

        # Κουμπί εφαρμογής φίλτρου (θα καλέσει apply_callback)
        self.btn_apply = QPushButton("Φιλτράρισε τα έργα")
        # CRUD κουμπιά καλλιτέχνη
        crud = QHBoxLayout()
        crud.setSpacing(8)

        self.btn_add_artist = QPushButton("➕")
        self.btn_edit_artist = QPushButton("✏️")
        self.btn_delete_artist = QPushButton("🗑️")

        for b in (self.btn_add_artist, self.btn_edit_artist, self.btn_delete_artist):
            b.setFixedSize(40, 36)
            b.setCursor(Qt.PointingHandCursor)

        crud.addWidget(self.btn_add_artist)
        crud.addWidget(self.btn_edit_artist)
        crud.addWidget(self.btn_delete_artist)
        crud.addStretch()

        right.addLayout(crud)

        self.btn_apply.clicked.connect(self._apply_selected)

        right.addWidget(self.detail_name)
        right.addWidget(self.detail_meta)
        right.addWidget(self.detail_info, 1)
        right.addWidget(self.btn_apply)

        # Βάζουμε τις 2 στήλες στο main layout
        main.addLayout(left, 1)
        main.addLayout(right, 1)

        # ---------- Wrapper layout στο ίδιο το popup ----------
        # (για να έχουμε λίγο padding γύρω από το outerCard)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(outer)

        # ---------- Load data + initial render ----------
        self._load_data()
        self._render_list()
        
        self.btn_add_artist.clicked.connect(self._add_artist)
        self.btn_edit_artist.clicked.connect(self._edit_selected_artist)
        self.btn_delete_artist.clicked.connect(self._delete_selected_artist)


    # --------------------------------------------------------
    # Φορτώνει καλλιτέχνες + υπολογίζει πόσα έργα έχει ο καθένας
    # --------------------------------------------------------
    def _load_data(self):
        # Καλλιτέχνες από DB
        self._artists = get_all_artists()

        # Μετράμε έργα ανά artist_id (για badge "X έργα")
        counts = {}
        for w in get_all_works():
            aid = w.get("artist_id")
            if aid is None:
                continue
            counts[aid] = counts.get(aid, 0) + 1

        self._works_count = counts

    # --------------------------------------------------------
    # EPILOGI καλλιτέχνες + ΠΡΟΣΘΕΤΕΙ ΑΦΑΙΡΕΙ ΕΠΕΞΕΡΓΑΖΕΤΑΙ
    # --------------------------------------------------------

    def _get_current_artist(self):
        
        item = self.list.currentItem()
        if not item:
            return None
        return item.data(Qt.UserRole)


    def _add_artist(self):
        dlg = ArtistDialog(self)
        if dlg.exec() == QDialog.Accepted:
            fn, ln, bd, dd, nat, spec, info = dlg.get_data()
            add_artist(fn, ln, bd, dd, nat, spec, info)
            self._load_data()
            self._render_list()


    def _edit_selected_artist(self):
        a = self._get_current_artist()
        if not a:
            return

        dlg = ArtistDialog(self, artist=a)
        if dlg.exec() == QDialog.Accepted:
            fn, ln, bd, dd, nat, spec, info = dlg.get_data()
            update_artist(a["id"], fn, ln, bd, dd, nat, spec, info)
            self._load_data()
            self._render_list()


    def _delete_selected_artist(self):
        a = self._get_current_artist()
        if not a:
            return

        reply = QMessageBox.question(
            self,
            "Διαγραφή καλλιτέχνη",
            "Είσαι σίγουρος ότι θέλεις να διαγράψεις αυτόν τον καλλιτέχνη;",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        delete_artist(a["id"])
        self._load_data()
        self._render_list()


    # --------------------------------------------------------
    # Δημιουργεί "καθαρό" display name (first + last)
    # --------------------------------------------------------
    def _artist_display_name(self, a):
        first = (a.get("first_name") or "").strip()
        last = (a.get("last_name") or "").strip()
        name = (first + " " + last).strip()
        return name or "Άγνωστος"

    def _make_artist_item_widget(self, name: str, works_n: int) -> QFrame:
        """Φτιάχνει ένα “card” widget για κάθε καλλιτέχνη."""
        w = QFrame()
        w.setObjectName("artistCard")
        w.setStyleSheet("""
        QFrame#artistCard {
            background-color: transparent;
            border-radius: 14px;
            padding: 10px 12px;
        }
        QLabel#nameLbl {
            color: #e5e7eb;
            font-weight: 700;
            font-size: 10.5pt;
        }
        QLabel#metaLbl {
            color: rgba(229,231,235,170);
            font-size: 8.5pt;
        }
        """)

        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(2)

        name_lbl = QLabel(name)
        name_lbl.setObjectName("nameLbl")

        meta_lbl = QLabel(f"{works_n} έργα")
        meta_lbl.setObjectName("metaLbl")

        lay.addWidget(name_lbl)
        lay.addWidget(meta_lbl)
        return w


    def _apply_selection_styles(self):
        """Κάνει το selected item μπλε και τα γράμματα λευκά (σαν combobox)."""
        for i in range(self.list.count()):
            item = self.list.item(i)
            card = self.list.itemWidget(item)
            if not card:
                continue

            name_lbl = card.findChild(QLabel, "nameLbl")
            meta_lbl = card.findChild(QLabel, "metaLbl")

            if i == self.list.currentRow():
                # Selected
                card.setStyleSheet("""
                QFrame#artistCard {
                    background-color: #2563eb;
                    border-radius: 14px;
                    padding: 10px 12px;
                }
                QLabel#nameLbl { color: #f9fafb; font-weight: 800; font-size: 10.5pt; }
                QLabel#metaLbl { color: rgba(249,250,251,210); font-size: 8.5pt; }
                """)
            else:
                # Normal
                card.setStyleSheet("""
                QFrame#artistCard {
                    background-color: transparent;
                    border-radius: 14px;
                    padding: 10px 12px;
                }
                QLabel#nameLbl { color: #e5e7eb; font-weight: 700; font-size: 10.5pt; }
                QLabel#metaLbl { color: rgba(229,231,235,170); font-size: 8.5pt; }
                """)


    # --------------------------------------------------------
    # Render της λίστας ανάλογα με το search query
    # --------------------------------------------------------
    def _render_list(self):
        q = self.search.text().strip().lower()

        self.list.clear()

        # Φιλτράρουμε artists με βάση το query
        filtered = []
        for a in self._artists:
            name = self._artist_display_name(a)
            if q and q not in name.lower():
                continue
            filtered.append(a)

        # Προσθέτουμε items στη λίστα
        for a in filtered:
            name = self._artist_display_name(a)
            works_n = self._works_count.get(a.get("id"), 0)

            item = QListWidgetItem()
            item.setData(Qt.UserRole, a)

            # ύψος κάρτας
            item.setSizeHint(QSize(10, 62))

            self.list.addItem(item)

            # custom widget card
            card = self._make_artist_item_widget(name, works_n)
            self.list.setItemWidget(item, card)

        # Αν υπάρχει τουλάχιστον ένα στοιχείο, κάνουμε auto-select το πρώτο
        if self.list.count() > 0 and self.list.currentRow() < 0:
            self.list.setCurrentRow(0)
            self._apply_selection_styles()


    # --------------------------------------------------------
    # Όταν αλλάζει η επιλογή στη λίστα, ενημερώνουμε δεξιά panel
    # --------------------------------------------------------
    def _on_current_changed(self, current, previous):
        if not current:
            return

        a = current.data(Qt.UserRole)
        name = self._artist_display_name(a)

        birth = (a.get("birth_date") or "").strip()
        death = (a.get("death_date") or "").strip()
        nat = (a.get("nationality") or "").strip()
        works_n = self._works_count.get(a.get("id"), 0)

        # Φτιάχνουμε “meta line” με bullet separators
        meta_bits = []
        if nat:
            meta_bits.append(nat)
        if birth or death:
            meta_bits.append(f"{birth} - {death}".strip(" -"))
        meta_bits.append(f"{works_n} έργα")

        self.detail_name.setText(name)
        self.detail_meta.setText(" • ".join([x for x in meta_bits if x]))

        # Info/βιογραφικό (αν δεν υπάρχει, δείχνουμε "—")
        info = (a.get("info") or "").strip()
        self.detail_info.setPlainText(info if info else "—")

    # --------------------------------------------------------
    # Πατάει ο χρήστης "Φιλτράρισε τα έργα"
    # -> Καλούμε apply_callback(name) και κλείνουμε το popup
    # --------------------------------------------------------
    def _apply_selected(self):
        item = self.list.currentItem()
        if not item:
            return

        a = item.data(Qt.UserRole)
        name = self._artist_display_name(a)

        # Επιστρέφουμε την επιλογή στον caller (π.χ. MainWindow)
        if callable(self.apply_callback):
            self.apply_callback(name)

        # Κλείνουμε το popup
        self.close()

    # --------------------------------------------------------
    # Άνοιγμα popup ακριβώς κάτω από ένα κουμπί (anchor)
    # --------------------------------------------------------
    def open_below(self, anchor_widget):
        if not anchor_widget:
            self.show()
            return

        # Πρώτα δείχνουμε για να υπολογιστεί σωστά το sizeHint/geometry
        self.adjustSize()

        # Πλάτος/ύψος του popup
        popup_w = self.width()
        popup_h = self.height()

        # global θέση κάτω από το κουμπί
        below = anchor_widget.mapToGlobal(QPoint(0, anchor_widget.height() + 8))
        above = anchor_widget.mapToGlobal(QPoint(0, -popup_h - 8))

        # διαθέσιμη περιοχή οθόνης
        screen = QGuiApplication.screenAt(below) or QApplication.primaryScreen()
        g = screen.availableGeometry()

        # Default: κάτω
        x = below.x()
        y = below.y()

        # Αν δεν χωράει κάτω, άνοιξε πάνω
        if y + popup_h > g.bottom():
            y = above.y()

        # Clamp X μέσα στην οθόνη
        if x + popup_w > g.right():
            x = g.right() - popup_w
        if x < g.left():
            x = g.left()

        # Clamp Y μέσα στην οθόνη
        if y + popup_h > g.bottom():
            y = g.bottom() - popup_h
        if y < g.top():
            y = g.top()

        self.move(x, y)
        self.show()

        # αφού ανοίξει, ανανέωσε selection colors
        self._apply_selection_styles()

class AIExhibitionDialog(QDialog):
    def __init__(self, parent=None, proposal=None):
        super().__init__(parent)
        self.proposal_data = None
        self.setWindowTitle("🤖 Ο βοηθός ΑΙ")
        self.setMinimumWidth(500)
        self.setStyleSheet("background-color: #f8f9fa;")
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        title = QLabel("Προτεινόμενη Έκθεση")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #ced4da;
                padding: 10px;
                font-size: 11pt;
                color: #212529;
            }
        """)
        btns = QHBoxLayout()
        btns.addStretch()
        layout.addWidget(self.text)
        self.save_btn = QPushButton("✅ Δημιουργία Έκθεσης")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setFixedSize(160, 35)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                border-radius: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #005a9e; }
            QPushButton:pressed { background-color: #004070; }
        """)
        cancel_btn = QPushButton("❌ Άκυρο")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setFixedSize(160, 35)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #dee2e6;
                color: #212529;
                border-radius: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #ced4da; }
            QPushButton:pressed { background-color: #adb5bd; }
        """)
        btns.addWidget(self.save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        self.save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)


        if proposal is not None:
            self.set_proposal(proposal)
        else:
            self.set_loading(True)

    def set_loading(self, loading: bool):
        self.save_btn.setEnabled(not loading)
        if loading:
            self.text.setPlainText("⏳ Δημιουργώ πρόταση έκθεσης...")

    def set_proposal(self, proposal):
        # Αν έρθει dict από το AI: κράτα το για αποθήκευση
        if isinstance(proposal, dict):
            self.proposal_data = proposal

            title = (proposal.get("title") or "").strip()
            start_date = (proposal.get("start_date") or "").strip()
            end_date = (proposal.get("end_date") or "").strip()
            desc = (proposal.get("description") or "").strip()
            works = proposal.get("selected_works") or []

            lines = []
            lines.append(f"📌 Τίτλος: {title or '—'}")
            lines.append(f"🗓️ Ημερομηνίες: {start_date or '—'} → {end_date or '—'}")
            lines.append("")

            if desc:
                lines.append("📝 Περιγραφή:")
                lines.append(desc)
                lines.append("")

            lines.append(f"🖼️ Επιλεγμένα έργα: {len(works)}")
            for i, w in enumerate(works, start=1):
                # επιτρέπουμε είτε dict είτε σκέτο id (int/str), για να μην σκάει αν το AI επιστρέψει λάθος format
                if isinstance(w, dict):
                    wid = w.get("work_id") if "work_id" in w else w.get("id")
                    note = (w.get("note") or "").strip()
                else:
                    wid = w
                    note = ""
                lines.append(f"{i}. #{wid} — {note}" if note else f"{i}. #{wid}")

            self.text.setPlainText("\n".join(lines))

        else:
            self.proposal_data = None
            self.text.setPlainText(str(proposal))

        self.save_btn.setEnabled(True)

        




class ExhibitionWorksDialog(QDialog):
    """
    works: list από get_all_works() (dicts)
    preselected: list από get_exhibition_works(ex_id) ή από AI selected_works
                [{"work_id":..,"note":..,"order":..}, ...]
    """
    def __init__(self, parent=None, works=None, preselected=None, title_hint=""):
        super().__init__(parent)
        self.setWindowTitle("Επιλογή Έργων για την Έκθεση")

        self._works = works or []
        preselected = preselected or []

        # map work_id -> {note, order}
        self._pre = {int(x["work_id"]): x for x in preselected if "work_id" in x}

        layout = QVBoxLayout(self)

        info = QLabel("Τσέκαρε τα έργα που θα ανήκουν στην έκθεση και βάλε σειρά/σημείωση.")
        info.setWordWrap(True)
        layout.addWidget(info)

        if title_hint:
            layout.addWidget(QLabel(f"Έκθεση: {title_hint}"))

        self.tbl = QTableWidget(0, 6, self)
        self.tbl.setHorizontalHeaderLabels(["✓", "ID", "Τίτλος", "Καλλιτέχνης", "Order", "Note"])
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.tbl)

        self._build_rows()

        btns = QHBoxLayout()
        btns.addStretch()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Άκυρο")
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        ok_btn.clicked.connect(self._on_ok)
        cancel_btn.clicked.connect(self.reject)

    def _build_rows(self):
        self.tbl.setRowCount(len(self._works))

        for r, w in enumerate(self._works):
            wid = int(w["id"])
            title = w.get("title", "")
            artist = w.get("artist_name", "")
            pre = self._pre.get(wid)

            # checkbox
            chk = QTableWidgetItem("")
            chk.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            chk.setCheckState(Qt.Checked if pre else Qt.Unchecked)
            self.tbl.setItem(r, 0, chk)

            self.tbl.setItem(r, 1, QTableWidgetItem(str(wid)))
            self.tbl.setItem(r, 2, QTableWidgetItem(title))
            self.tbl.setItem(r, 3, QTableWidgetItem(artist))

            # order spin
            sp = QSpinBox(self.tbl)
            sp.setRange(0, 9999)
            sp.setValue(int(pre.get("order", r + 1)) if pre else 0)
            self.tbl.setCellWidget(r, 4, sp)

            # note edit
            le = QLineEdit(self.tbl)
            le.setText(pre.get("note", "") if pre else "")
            self.tbl.setCellWidget(r, 5, le)

    def _on_ok(self):
        items = self.get_selected_works()
        if not items:
            QMessageBox.warning(self, "Σφάλμα", "Διάλεξε τουλάχιστον 1 έργο.")
            return
        self.accept()

    def get_selected_works(self):
        out = []
        for r in range(self.tbl.rowCount()):
            chk = self.tbl.item(r, 0)
            if chk and chk.checkState() == Qt.Checked:
                wid = int(self.tbl.item(r, 1).text())
                sp = self.tbl.cellWidget(r, 4)
                le = self.tbl.cellWidget(r, 5)
                out.append({
                    "work_id": wid,
                    "order": int(sp.value()) if sp else 0,
                    "note": le.text().strip() if le else ""
                })

        # ταξινόμηση με βάση order
        out.sort(key=lambda x: (x.get("order", 0), x.get("work_id", 0)))
        return out
                
                                
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextBrowser, QSizePolicy
)

class ExhibitionDetailsDialog(QDialog):
    def __init__(self, parent=None, exhibition=None, works=None):
        super().__init__(parent)
        self.setWindowTitle("Λεπτομέρειες Έκθεσης")
        self.resize(900, 620)

        exhibition = exhibition or {}
        works = works or []

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # --- Header card ---
        card = QFrame()
        card.setObjectName("card")
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(16, 14, 16, 14)
        card_l.setSpacing(8)

        title = QLabel(exhibition.get("title", ""))
        title.setObjectName("title")
        title.setWordWrap(True)

        dates = QLabel(f'🗓️ {exhibition.get("start_date","")} → {exhibition.get("end_date","")}')
        dates.setObjectName("subtitle")

        meta = QLabel(f'🖼️ Έργα: {exhibition.get("num_works", 0)}')
        meta.setObjectName("subtitle")

        card_l.addWidget(title)
        row = QHBoxLayout()
        row.addWidget(dates)
        row.addStretch()
        row.addWidget(meta)
        card_l.addLayout(row)
        cur_name = exhibition.get("curator_name") or "—"
        reserved = exhibition.get("reserved_seats", 0) or 0
        max_seats = exhibition.get("max_seats")

        curator_lbl = QLabel(f"🧑‍🎨 Επιμελητής: {cur_name}")
        curator_lbl.setObjectName("subtitle")

        if max_seats:
            seats_txt = f"🎟️ Θέσεις: {reserved}/{max_seats}"
        else:
            seats_txt = f"🎟️ Κρατημένες: {reserved}"

        seats_lbl = QLabel(seats_txt)
        seats_lbl.setObjectName("subtitle")
        row2 = QHBoxLayout()
        row2.addWidget(curator_lbl)
        row2.addStretch()
        row2.addWidget(seats_lbl)
        card_l.addLayout(row2)



        root.addWidget(card)

        # --- Description (scrollable) ---
        desc = QTextBrowser()
        desc.setObjectName("desc")
        desc.setOpenExternalLinks(False)
        desc.setText(exhibition.get("description", "") or "")
        desc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        desc.setMinimumHeight(120)
        root.addWidget(desc)

        # --- Works table ---
        lbl = QLabel("Έργα της έκθεσης")
        lbl.setObjectName("section")
        root.addWidget(lbl)

        tbl = QTableWidget(0, 5)
        tbl.setObjectName("worksTable")
        tbl.setHorizontalHeaderLabels(["ID", "Τίτλος", "Καλλιτέχνης", "Order", "Note"])
        tbl.verticalHeader().setVisible(False)
        tbl.setWordWrap(True)
        tbl.setRowCount(len(works))

        for r, w in enumerate(works):
            tbl.setItem(r, 0, QTableWidgetItem(str(w.get("work_id",""))))
            tbl.setItem(r, 1, QTableWidgetItem(w.get("title","")))
            tbl.setItem(r, 2, QTableWidgetItem(w.get("artist_name","")))
            tbl.setItem(r, 3, QTableWidgetItem(str(w.get("order",0))))
            tbl.setItem(r, 4, QTableWidgetItem(w.get("note","")))

        hdr = tbl.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        tbl.resizeRowsToContents()
        root.addWidget(tbl, 1)

        # --- Buttons ---
        btns = QHBoxLayout()
        btns.addStretch()
        close_btn = QPushButton("Κλείσιμο")
        close_btn.clicked.connect(self.accept)
        btns.addWidget(close_btn)
        root.addLayout(btns)

        # --- Modern styling ---
        self.setStyleSheet("""
        QDialog { background: #ffffff; }
        #card {
            background: #f6f7fb;
            border: 1px solid #e6e8f0;
            border-radius: 16px;
        }
        #title { font-size: 18px; font-weight: 700; color: #111827; }
        #subtitle { font-size: 12px; color: #4b5563; }
        #section { font-size: 13px; font-weight: 700; color: #111827; margin-top: 4px; }
        #desc {
            background: #ffffff;
            border: 1px solid #e6e8f0;
            border-radius: 12px;
            padding: 8px;
            color: #111827;
        }
        #worksTable {
            border: 1px solid #e6e8f0;
            border-radius: 12px;
        }
        QHeaderView::section {
            background: #f3f4f6;
            padding: 8px;
            border: none;
            border-bottom: 1px solid #e6e8f0;
            font-weight: 700;
        }
        QTableWidget { gridline-color: #eef0f5; }
        QTableWidget::item { padding: 6px; }
        QPushButton {
            background: #111827;
            color: white;
            border: none;
            border-radius: 12px;
            padding: 8px 14px;
            font-weight: 600;
        }
        QPushButton:hover { background: #0b1220; }
        """)


from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDialogButtonBox, QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt



class ExhibitionWorksPickerDialog(QDialog):
    """
    Dialog για επιλογή έργων που θα ανήκουν σε μια έκθεση.
    Δείχνει όλα τα έργα, με checkbox + order + note.
    """
    def __init__(self, parent=None, all_works=None, selected_items=None):
        super().__init__(parent)
        self.setWindowTitle("Επιλογή έργων για την έκθεση")
        self.resize(900, 520)

        self.all_works = all_works or []
        # selected_items: [{"work_id":..,"note":..,"order":..}, ...]
        selected_items = selected_items or []
        self._selected_map = {int(it["work_id"]): it for it in selected_items}

        root = QVBoxLayout(self)

        # Top bar (search + count)
        top = QHBoxLayout()
        root.addLayout(top)

        top.addWidget(QLabel("Αναζήτηση:"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("τίτλος / καλλιτέχνης ...")
        top.addWidget(self.search, 1)

        self.lbl_count = QLabel("")
        top.addWidget(self.lbl_count)

        # Table
        self.tbl = QTableWidget(0, 7, self)
        self.tbl.setHorizontalHeaderLabels(["✓", "ID", "Τίτλος", "Καλλιτέχνης", "Έτος", "Order", "Σημείωση"])
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        root.addWidget(self.tbl, 1)

        # Buttons
        bb = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok, self)
        bb.button(QDialogButtonBox.Ok).setText("Αποθήκευση επιλογών")
        bb.button(QDialogButtonBox.Cancel).setText("Άκυρο")
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        root.addWidget(bb)

        self._build_rows()
        self.search.textChanged.connect(self._apply_filter)
        self._update_count()

    def _build_rows(self):
        self.tbl.setRowCount(len(self.all_works))

        for row, w in enumerate(self.all_works):
            work_id = int(w["id"])
            title = w.get("title", "")
            artist = w.get("artist_name", "")
            year = w.get("year", "")

            # checkbox
            chk = QCheckBox()
            chk.setTristate(False)
            self.tbl.setCellWidget(row, 0, chk)

            # static cells
            self.tbl.setItem(row, 1, QTableWidgetItem(str(work_id)))
            self.tbl.setItem(row, 2, QTableWidgetItem(title))
            self.tbl.setItem(row, 3, QTableWidgetItem(artist))
            self.tbl.setItem(row, 4, QTableWidgetItem(str(year) if year is not None else ""))

            # order spin
            sp = QSpinBox()
            sp.setRange(0, 9999)
            self.tbl.setCellWidget(row, 5, sp)

            # note editable item (QTableWidgetItem, κάνουμε flags editable μόνο όταν checked)
            note_item = QTableWidgetItem("")
            note_item.setFlags(note_item.flags() | Qt.ItemIsEditable)
            self.tbl.setItem(row, 6, note_item)

            # preload (edit mode)
            if work_id in self._selected_map:
                it = self._selected_map[work_id]
                chk.setChecked(True)
                sp.setValue(int(it.get("order", 0) or 0))
                note_item.setText(it.get("note", "") or "")
                self._enable_row(row, True)
            else:
                chk.setChecked(False)
                sp.setValue(0)
                note_item.setText("")
                self._enable_row(row, False)

            # connect checkbox
            chk.toggled.connect(lambda checked, r=row: self._on_toggle(r, checked))

    def _enable_row(self, row: int, enabled: bool):
        sp = self.tbl.cellWidget(row, 5)
        note_item = self.tbl.item(row, 6)

        sp.setEnabled(enabled)
        if enabled:
            note_item.setFlags(note_item.flags() | Qt.ItemIsEditable)
        else:
            note_item.setFlags(note_item.flags() & ~Qt.ItemIsEditable)

    def _on_toggle(self, row: int, checked: bool):
        work_id = int(self.tbl.item(row, 1).text())
        sp = self.tbl.cellWidget(row, 5)
        note_item = self.tbl.item(row, 6)

        self._enable_row(row, checked)

        if checked:
            # αν δεν έχει order, δώσε επόμενο διαθέσιμο
            if sp.value() == 0:
                sp.setValue(self._next_order_value())
        else:
            sp.setValue(0)
            note_item.setText("")

        self._update_count()

    def _next_order_value(self) -> int:
        max_order = 0
        for r in range(self.tbl.rowCount()):
            chk = self.tbl.cellWidget(r, 0)
            if chk and chk.isChecked():
                sp = self.tbl.cellWidget(r, 5)
                max_order = max(max_order, int(sp.value()))
        return max_order + 1

    def _apply_filter(self, text: str):
        q = (text or "").strip().lower()
        for r in range(self.tbl.rowCount()):
            title = (self.tbl.item(r, 2).text() or "").lower()
            artist = (self.tbl.item(r, 3).text() or "").lower()
            show = (q in title) or (q in artist) if q else True
            self.tbl.setRowHidden(r, not show)

    def _update_count(self):
        n = 0
        for r in range(self.tbl.rowCount()):
            chk = self.tbl.cellWidget(r, 0)
            if chk and chk.isChecked():
                n += 1
        self.lbl_count.setText(f"Επιλεγμένα: {n}")

    def get_selected_items(self):
        items = []
        for r in range(self.tbl.rowCount()):
            chk = self.tbl.cellWidget(r, 0)
            if not (chk and chk.isChecked()):
                continue
            work_id = int(self.tbl.item(r, 1).text())
            sp = self.tbl.cellWidget(r, 5)
            note = self.tbl.item(r, 6).text() if self.tbl.item(r, 6) else ""
            items.append({
                "work_id": work_id,
                "order": int(sp.value()) if sp else 0,
                "note": note or ""
            })

        # sort by order (0 goes last)
        items.sort(key=lambda x: (x["order"] == 0, x["order"], x["work_id"]))
        return items


class BorrowerDialog(QDialog):
    def __init__(self, parent=None, borrower_data=None):
        super().__init__(parent)
        self.setWindowTitle("Δανειστής")
        self.setMinimumWidth(420)
        self.borrower_data = borrower_data

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["", "Ιδιώτης", "Μουσείο", "Πινακοθήκη", "Ίδρυμα", "Άλλο"])

        self.country_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(90)

        form.addRow("Επωνυμία/Όνομα *", self.name_edit)
        form.addRow("Τύπος", self.type_combo)
        form.addRow("Χώρα", self.country_edit)
        form.addRow("Email", self.email_edit)
        form.addRow("Διεύθυνση", self.address_edit)
        form.addRow("Τηλέφωνο", self.phone_edit)
        form.addRow("Σημειώσεις", self.notes_edit)

        layout.addLayout(form)

        btns = QHBoxLayout()
        self.btn_ok = QPushButton("Αποθήκευση")
        self.btn_cancel = QPushButton("Άκυρο")
        btns.addStretch()
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)
        layout.addLayout(btns)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self._on_ok)

        if borrower_data:
            self.name_edit.setText(borrower_data.get("name",""))
            self.type_combo.setCurrentText(borrower_data.get("borrower_type",""))
            self.country_edit.setText(borrower_data.get("country",""))
            self.email_edit.setText(borrower_data.get("email",""))
            self.address_edit.setText(borrower_data.get("address",""))
            self.phone_edit.setText(borrower_data.get("phone",""))
            self.notes_edit.setPlainText(borrower_data.get("notes",""))

    def _on_ok(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Σφάλμα", "Η επωνυμία/όνομα είναι υποχρεωτική.")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "borrower_type": self.type_combo.currentText().strip(),
            "country": self.country_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "address": self.address_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "notes": self.notes_edit.toPlainText().strip(),
        }


class LoanDialog(QDialog):
    def __init__(self, parent=None, works=None, borrowers=None, loan_data=None, lock_work=False):
        super().__init__(parent)
        self.setWindowTitle("Δανεισμός")
        self.setMinimumWidth(520)

        self.works = works or []          # list of dict from get_all_works()
        self.borrowers = borrowers or []  # list of dict from get_all_borrowers()
        self.loan_data = loan_data or {}
        self.lock_work = lock_work

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.direction_combo = QComboBox()
        self.direction_combo.addItem("📤 Δανείζουμε (OUT)", "OUT")
        self.direction_combo.addItem("📥 Δανειζόμαστε (IN)", "IN")
        form.addRow("Τύπος:", self.direction_combo)
        # ✅ αν είναι edit, διάβασε direction από loan_data και προεπίλεξέ το
        if loan_data:
            dir_val = loan_data.get("direction", "OUT")
            idx = self.direction_combo.findData(dir_val)
            if idx >= 0:
                self.direction_combo.setCurrentIndex(idx)


        self.work_combo = QComboBox()
        self.work_combo.addItem("— Επιλογή έργου —", None)
        for w in self.works:
            self.work_combo.addItem(f"[{w['id']}] {w['title']}", w["id"])
        # ✅ Αν το dialog ανοίγει από WorkDialog (lock_work=True) και έχουμε 1 έργο,
        # προεπίλεξέ το αυτόματα.
        if self.lock_work and (not loan_data) and len(self.works) == 1:
            self.work_combo.setCurrentIndex(1)  #το πρώτο πραγματικό έργο (μετά το "— Επιλογή έργου —")


        self.borrower_combo = QComboBox()
        self.borrower_combo.addItem("— Επιλογή δανειστή —", None)
        for b in self.borrowers:
            self.borrower_combo.addItem(f"[{b['id']}] {b['name']}", b["id"])

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setDate(QDate.currentDate())

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setDate(QDate.currentDate().addDays(30))
        self.end_date.setSpecialValueText("")  # προαιρετικό

        self.notes = QTextEdit()
        self.notes.setFixedHeight(90)


        form.addRow("Έργο *", self.work_combo)
        form.addRow("Δανειστής *", self.borrower_combo)
        form.addRow("Ημ/νία έναρξης *", self.start_date)
        form.addRow("Ημ/νία λήξης", self.end_date)
        form.addRow("Σημειώσεις", self.notes)

        layout.addLayout(form)

        btns = QHBoxLayout()
        self.btn_ok = QPushButton("Αποθήκευση")
        self.btn_cancel = QPushButton("Άκυρο")
        btns.addStretch()
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)
        layout.addLayout(btns)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self._on_ok)

        # Prefill edit
        if loan_data:
            work_id = loan_data.get("work_id")
            borrower_id = loan_data.get("borrower_id")
            self._set_combo_by_data(self.work_combo, work_id)
            self._set_combo_by_data(self.borrower_combo, borrower_id)

            sd = loan_data.get("start_date") or ""
            ed = loan_data.get("end_date") or ""
            if sd:
                y,m,d = map(int, sd.split("-"))
                self.start_date.setDate(QDate(y,m,d))
            if ed:
                y,m,d = map(int, ed.split("-"))
                self.end_date.setDate(QDate(y,m,d))

            self.notes.setPlainText(loan_data.get("notes",""))

        if lock_work:
            self.work_combo.setEnabled(False)

    def _set_combo_by_data(self, combo: QComboBox, value):
        for i in range(combo.count()):
            if combo.itemData(i) == value:
                combo.setCurrentIndex(i)
                return

    def _on_ok(self):
        work_id = self.work_combo.currentData()
        borrower_id = self.borrower_combo.currentData()
        if not work_id:
            QMessageBox.warning(self, "Σφάλμα", "Επίλεξε έργο.")
            return
        if not borrower_id:
            QMessageBox.warning(self, "Σφάλμα", "Επίλεξε δανειστή.")
            return

        self.accept()

    def get_data(self):
        work_id = self.work_combo.currentData()
        direction = self.direction_combo.currentData()
        borrower_id = self.borrower_combo.currentData()
        sd = self.start_date.date().toString("yyyy-MM-dd")
        ed = self.end_date.date().toString("yyyy-MM-dd") if self.end_date.date().isValid() else ""
        return {
            "work_id": work_id,
            "borrower_id": borrower_id,
            "start_date": sd,
            "end_date": ed,
            "notes": self.notes.toPlainText().strip(),
            "direction": self.direction_combo.currentData() or "OUT",
        }


class BorrowersManagerDialog(QDialog):
    """
    Ένας απλός manager για Δανειστές (CRUD).
    Θα τον ανοίγουμε από το module Δανεισμών.
    """
    def __init__(self, parent=None, db_api=None):
        super().__init__(parent)
        self.setWindowTitle("Δανειστές")
        self.setMinimumSize(820, 420)

        # db_api: dict με functions (για να μην κάνουμε circular imports εδώ)
        self.db = db_api or {}

        layout = QVBoxLayout(self)

        # Top buttons
        top = QHBoxLayout()
        self.btn_add = QPushButton("➕ Νέος Δανειστής")
        self.btn_edit = QPushButton("✏️ Επεξεργασία")
        self.btn_delete = QPushButton("🗑️ Διαγραφή")
        top.addWidget(self.btn_add)
        top.addWidget(self.btn_edit)
        top.addWidget(self.btn_delete)
        top.addStretch()
        layout.addLayout(top)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Επωνυμία", "Τύπος", "Χώρα", "Email", "Τηλέφωνο"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # ✅ Συνδέσεις (αυτό σου λείπει τώρα)
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)

        # initial load
        self.reload()

    def reload(self):
        # προστασία: αν δεν πέρασες functions σωστά
        if "get_all_borrowers" not in self.db:
            QMessageBox.warning(self, "Σφάλμα", "Δεν πέρασε get_all_borrowers στο BorrowersManagerDialog.")
            return

        borrowers = self.db["get_all_borrowers"]()

        self.table.setRowCount(0)
        for b in borrowers:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(b.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(b.get("name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(b.get("borrower_type", "")))
            self.table.setItem(row, 3, QTableWidgetItem(b.get("country", "")))
            self.table.setItem(row, 4, QTableWidgetItem(b.get("email", "")))
            self.table.setItem(row, 5, QTableWidgetItem(b.get("phone", "")))

    def _selected_id(self):
        r = self.table.currentRow()
        if r < 0:
            return None
        try:
            return int(self.table.item(r, 0).text())
        except Exception:
            return None

    def _add(self):
        # BorrowerDialog πρέπει να υπάρχει στο dialogs.py
        dlg = BorrowerDialog(self)
        if dlg.exec() == QDialog.Accepted:
            if "add_borrower" not in self.db:
                QMessageBox.warning(self, "Σφάλμα", "Δεν πέρασε add_borrower στο BorrowersManagerDialog.")
                return
            self.db["add_borrower"](dlg.get_data())
            self.reload()

    def _edit(self):
        borrower_id = self._selected_id()
        if not borrower_id:
            QMessageBox.information(self, "Info", "Επίλεξε δανειστή.")
            return

        borrowers = self.db["get_all_borrowers"]()
        b = next((x for x in borrowers if x.get("id") == borrower_id), None)
        if not b:
            QMessageBox.warning(self, "Σφάλμα", "Δεν βρέθηκε ο δανειστής.")
            return

        dlg = BorrowerDialog(self, borrower_data=b)
        if dlg.exec() == QDialog.Accepted:
            if "update_borrower" not in self.db:
                QMessageBox.warning(self, "Σφάλμα", "Δεν πέρασε update_borrower στο BorrowersManagerDialog.")
                return
            self.db["update_borrower"](borrower_id, dlg.get_data())
            self.reload()

    def _delete(self):
        borrower_id = self._selected_id()
        if not borrower_id:
            QMessageBox.information(self, "Info", "Επίλεξε δανειστή.")
            return

        if QMessageBox.question(self, "Επιβεβαίωση", "Να διαγραφεί ο δανειστής;") != QMessageBox.Yes:
            return

        if "delete_borrower" not in self.db:
            QMessageBox.warning(self, "Σφάλμα", "Δεν πέρασε delete_borrower στο BorrowersManagerDialog.")
            return

        try:
            self.db["delete_borrower"](borrower_id)
            self.reload()
        except Exception as e:
            QMessageBox.warning(self, "Σφάλμα", str(e))
class MaintenanceDialog(QDialog):
        def __init__(self, parent=None, maint_id=None):
            super().__init__(parent)
            self.setWindowTitle("Ανάθεση Συντηρητή")
            self.setMinimumWidth(400)
            self.maint_id = maint_id

            layout = QVBoxLayout(self)
            self.form = QFormLayout()

        # Συντηρητής
            self.conservator_combo = QComboBox()
            self.form.addRow("Συντηρητής:", self.conservator_combo)

            layout.addLayout(self.form)

            # Κουμπιά
            btn_layout = QHBoxLayout()
            save_btn = QPushButton("Αποθήκευση")
            cancel_btn = QPushButton("Άκυρο")
            btn_layout.addStretch()
            btn_layout.addWidget(save_btn)
            btn_layout.addWidget(cancel_btn)
            layout.addLayout(btn_layout)

            save_btn.clicked.connect(self.accept)
            cancel_btn.clicked.connect(self.reject)

            # Φόρτωση συντηρητών
            self.load_conservators()

        def load_conservators(self):
            """Φόρτωση συντηρητών από βάση"""
            
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("""
            SELECT s.id, s.first_name, s.last_name, c.specialization
            FROM staff s
            JOIN conservators c ON s.id = c.staff_id
            ORDER BY c.specialization, s.last_name
        """)
            rows = cur.fetchall()
            conn.close()

            self.conservator_combo.clear()
            for staff_id, first, last, specialization in rows:
                display_text = f"{first} {last} ({specialization})"
                self.conservator_combo.addItem(display_text, staff_id)
        def get_selected_conservator(self):

            """Επιστρέφει το staff_id του επιλεγμένου συντηρητή"""
            return self.conservator_combo.currentData()

class TourSessionDialog(QDialog):
    """Dialog για Νέα / Επεξεργασία Ξενάγησης."""

    def __init__(self, parent=None, session=None, guides=None, exhibitions=None):
        super().__init__(parent)
        self.setWindowTitle("Νέα ξενάγηση" if session is None else "Επεξεργασία ξενάγησης")
        self.setMinimumWidth(420)

        self._guides = guides or []           # list of dicts (id, full_name, language, wage, ...)
        self._exhibitions = exhibitions or [] # list of dicts (id, title, ...)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.id_label = QLabel("")
        form.addRow("ID:", self.id_label)

        self.title_edit = QLineEdit()
        form.addRow("Τίτλος:", self.title_edit)

        self.start_dt_edit = QDateTimeEdit()
        self.start_dt_edit.setCalendarPopup(True)
        self.start_dt_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.start_dt_edit.setDateTime(QDateTime.currentDateTime())
        form.addRow("Έναρξη:", self.start_dt_edit)

        self.duration_combo = QComboBox()
        self.duration_combo.addItems(["60", "90", "120"])
        self.duration_combo.setEditable(True)  # να γράφει κιόλας αν θέλει
        form.addRow("Διάρκεια (λεπτά):", self.duration_combo)

        self.buffer_spin = QSpinBox()
        self.buffer_spin.setRange(0, 60)
        self.buffer_spin.setValue(15)
        form.addRow("Buffer (λεπτά):", self.buffer_spin)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["", "Ελληνικά", "English", "Français", "Deutsch", "Italiano", "Español"])
        form.addRow("Γλώσσα:", self.language_combo)

        self.guide_combo = QComboBox()
        self.guide_combo.addItem("— χωρίς ανάθεση —", None)
        for g in self._guides:
            # g: {id, first_name, last_name, language, ...}
            name = f"{g.get('first_name','')} {g.get('last_name','')}".strip()
            label = name or f"Guide #{g.get('id')}"
            lang = (g.get("language") or "").strip()
            if lang:
                label += f" ({lang})"
            self.guide_combo.addItem(label, g.get("id"))
        form.addRow("Ξεναγός:", self.guide_combo)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["", "Κλασική Διαδρομή", "Σύγχρονη Τέχνη", "Family tour", "School tour"])
        form.addRow("Τύπος:", self.type_combo)

        self.capacity_spin = QSpinBox()
        self.capacity_spin.setRange(0, 500)
        self.capacity_spin.setValue(20)
        form.addRow("Μέγ. άτομα:", self.capacity_spin)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["scheduled", "in-progress", "completed", "canceled"])
        form.addRow("Κατάσταση:", self.status_combo)

        self.exhibition_combo = QComboBox()
        self.exhibition_combo.addItem("— καμία —", None)
        for e in self._exhibitions:
            self.exhibition_combo.addItem(f"{e.get('title','')} (#{e.get('id')})", e.get("id"))
        form.addRow("Έκθεση (προαιρετικό):", self.exhibition_combo)

        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(90)
        form.addRow("Σημειώσεις:", self.notes_edit)

        self.cancel_reason_edit = QLineEdit()
        self.cancel_reason_edit.setPlaceholderText("Μόνο αν status = canceled")
        form.addRow("Λόγος ακύρωσης:", self.cancel_reason_edit)

        layout.addLayout(form)

        # buttons
        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Άκυρο")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

        # Fill data
        if session:
            self.id_label.setText(str(session.get("id", "")))
            self.title_edit.setText(session.get("title", ""))
            # start
            try:
                sdt = session.get("start_dt", "").replace("T", " ")
                self.start_dt_edit.setDateTime(QDateTime.fromString(sdt, "yyyy-MM-dd HH:mm"))
            except Exception:
                pass
            # duration: infer minutes from end-start
            try:
                sdt = session.get("start_dt", "").replace("T", " ")
                edt = session.get("end_dt", "").replace("T", " ")
                s_qdt = QDateTime.fromString(sdt, "yyyy-MM-dd HH:mm")
                e_qdt = QDateTime.fromString(edt, "yyyy-MM-dd HH:mm")
                mins = int(s_qdt.secsTo(e_qdt) / 60)
                if mins > 0:
                    self.duration_combo.setCurrentText(str(mins))
            except Exception:
                pass

            self.language_combo.setCurrentText(session.get("language", ""))
            # guide
            gid = session.get("guide_staff_id")
            if gid is not None:
                ix = self.guide_combo.findData(gid)
                if ix >= 0:
                    self.guide_combo.setCurrentIndex(ix)

            self.type_combo.setCurrentText(session.get("tour_type", ""))
            self.capacity_spin.setValue(int(session.get("capacity") or 0))
            self.status_combo.setCurrentText(session.get("status", "scheduled"))
            # exhibition
            exid = session.get("exhibition_id")
            if exid is not None:
                ix = self.exhibition_combo.findData(exid)
                if ix >= 0:
                    self.exhibition_combo.setCurrentIndex(ix)

            self.notes_edit.setPlainText(session.get("notes", ""))
            self.cancel_reason_edit.setText(session.get("cancellation_reason", ""))

    def get_data(self) -> dict:
        title = self.title_edit.text().strip() or "Ξενάγηση"
        start_dt = self.start_dt_edit.dateTime().toString("yyyy-MM-dd HH:mm")

        try:
            dur_min = int(self.duration_combo.currentText().strip())
        except Exception:
            dur_min = 60

        # end = start + duration
        end_dt = self.start_dt_edit.dateTime().addSecs(dur_min * 60).toString("yyyy-MM-dd HH:mm")

        return {
            "title": title,
            "start_dt": start_dt,
            "end_dt": end_dt,
            "language": self.language_combo.currentText().strip(),
            "guide_staff_id": self.guide_combo.currentData(),
            "tour_type": self.type_combo.currentText().strip(),
            "capacity": int(self.capacity_spin.value()),
            "status": self.status_combo.currentText().strip(),
            "exhibition_id": self.exhibition_combo.currentData(),
            "notes": self.notes_edit.toPlainText().strip(),
            "cancellation_reason": self.cancel_reason_edit.text().strip(),
        }


class TourBookingDialog(QDialog):
    """Dialog για Νέα / Επεξεργασία Κράτησης ξενάγησης."""

    def __init__(self, parent=None, booking=None, sessions=None):
        super().__init__(parent)
        self.setWindowTitle("Νέα κράτηση" if booking is None else "Επεξεργασία κράτησης")
        self.setMinimumWidth(420)

        self._sessions = sessions or []  # list of dicts from get_tour_sessions

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.id_label = QLabel("")
        form.addRow("ID:", self.id_label)

        self.session_combo = QComboBox()
        for s in self._sessions:
            label = f"#{s['id']} | {s.get('start_dt','')} | {s.get('title','')} | {s.get('language','')} | {s.get('guide_name','')}"
            self.session_combo.addItem(label, s["id"])
        form.addRow("Session:", self.session_combo)

        self.group_edit = QLineEdit()
        form.addRow("Όνομα ομάδας:", self.group_edit)

        self.phone_edit = QLineEdit()
        form.addRow("Τηλέφωνο:", self.phone_edit)

        self.email_edit = QLineEdit()
        form.addRow("Email:", self.email_edit)

        self.people_spin = QSpinBox()
        self.people_spin.setRange(1, 500)
        self.people_spin.setValue(2)
        form.addRow("Άτομα:", self.people_spin)

        self.lang_pref = QLineEdit()
        form.addRow("Προτίμηση γλώσσας:", self.lang_pref)

        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["unpaid", "paid", "comp"])
        form.addRow("Πληρωμή:", self.payment_combo)

        self.comments = QTextEdit()
        self.comments.setFixedHeight(90)
        form.addRow("Σχόλια:", self.comments)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Άκυρο")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

        if booking:
            self.id_label.setText(str(booking.get("id", "")))
            sid = booking.get("session_id")
            if sid is not None:
                ix = self.session_combo.findData(sid)
                if ix >= 0:
                    self.session_combo.setCurrentIndex(ix)

            self.group_edit.setText(booking.get("group_name", ""))
            self.phone_edit.setText(booking.get("phone", ""))
            self.email_edit.setText(booking.get("email", ""))
            self.people_spin.setValue(int(booking.get("people_count") or 1))
            self.lang_pref.setText(booking.get("language_pref", ""))
            self.payment_combo.setCurrentText(booking.get("payment_status", "unpaid"))
            self.comments.setPlainText(booking.get("comments", ""))

    def get_data(self) -> dict:
        return {
            "session_id": int(self.session_combo.currentData()),
            "group_name": self.group_edit.text().strip() or "Ομάδα",
            "phone": self.phone_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "people_count": int(self.people_spin.value()),
            "language_pref": self.lang_pref.text().strip(),
            "payment_status": self.payment_combo.currentText().strip(),
            "comments": self.comments.toPlainText().strip(),
        }


class TicketTypeDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Τύπος εισιτηρίου")
        self.data = data or {}

        lay = QVBoxLayout(self)

        self.ed_name = QLineEdit(self.data.get("name",""))
        self.ed_price = QDoubleSpinBox()
        self.ed_price.setMaximum(9999)
        self.ed_price.setDecimals(2)
        self.ed_price.setValue(float(self.data.get("price") or 0))

        self.chk_active = QCheckBox("Ενεργό")
        self.chk_active.setChecked(bool(int(self.data.get("active", 1))))

        self.chk_online = QCheckBox("Διαθέσιμο online")
        self.chk_online.setChecked(bool(int(self.data.get("online_enabled", 1))))

        self.chk_proof = QCheckBox("Χρειάζεται έλεγχος δικαιολογητικού")
        self.chk_proof.setChecked(bool(int(self.data.get("requires_proof", 0))))

        self.ed_notes = QTextEdit(self.data.get("notes",""))

        lay.addWidget(QLabel("Όνομα"))
        lay.addWidget(self.ed_name)
        lay.addWidget(QLabel("Τιμή"))
        lay.addWidget(self.ed_price)
        lay.addWidget(self.chk_active)
        lay.addWidget(self.chk_online)
        lay.addWidget(self.chk_proof)
        lay.addWidget(QLabel("Σημειώσεις"))
        lay.addWidget(self.ed_notes)

        btns = QHBoxLayout()
        b_ok = QPushButton("Αποθήκευση")
        b_cancel = QPushButton("Άκυρο")
        b_ok.clicked.connect(self.accept)
        b_cancel.clicked.connect(self.reject)
        btns.addStretch(1)
        btns.addWidget(b_ok)
        btns.addWidget(b_cancel)
        lay.addLayout(btns)

    def get_data(self):
        return {
            "name": self.ed_name.text().strip(),
            "price": float(self.ed_price.value()),
            "active": 1 if self.chk_active.isChecked() else 0,
            "online_enabled": 1 if self.chk_online.isChecked() else 0,
            "requires_proof": 1 if self.chk_proof.isChecked() else 0,
            "notes": self.ed_notes.toPlainText().strip(),
        }


class TicketSaleDialog(QDialog):
    """
    MVP: 1 γραμμή πώλησης (τύπος + qty) + ημερομηνία επίσκεψης + payment + optional session/exhibition + optional email
    """
    def __init__(self, parent=None, ticket_types=None, sessions=None, exhibitions=None):
        super().__init__(parent)
        self.setWindowTitle("Νέα Πώληση")
        self.ticket_types = ticket_types or []
        self.sessions = sessions or []
        self.exhibitions = exhibitions or []

        lay = QVBoxLayout(self)

        # customer/email + channel
        row0 = QHBoxLayout()
        self.cmb_channel = QComboBox()
        self.cmb_channel.addItems(["cashier", "online"])
        self.ed_email = QLineEdit()
        self.ed_email.setPlaceholderText("email (μόνο αν online)")
        row0.addWidget(QLabel("Κανάλι:"))
        row0.addWidget(self.cmb_channel)
        row0.addSpacing(10)
        row0.addWidget(QLabel("Email:"))
        row0.addWidget(self.ed_email)
        lay.addLayout(row0)

        # type + qty
        row1 = QHBoxLayout()
        self.cmb_type = QComboBox()
        for tt in self.ticket_types:
            self.cmb_type.addItem(f'{tt["name"]} — {tt["price"]:.2f}€', tt["id"])
        self.sp_qty = QSpinBox()
        self.sp_qty.setMinimum(1)
        self.sp_qty.setMaximum(999)
        row1.addWidget(QLabel("Τύπος:"))
        row1.addWidget(self.cmb_type, 1)
        row1.addSpacing(10)
        row1.addWidget(QLabel("Ποσότητα:"))
        row1.addWidget(self.sp_qty)
        lay.addLayout(row1)

        # visit date
        row2 = QHBoxLayout()
        self.dt_visit = QDateEdit()
        self.dt_visit.setCalendarPopup(True)
        self.dt_visit.setDate(QDate.currentDate())
        row2.addWidget(QLabel("Ημ/νία επίσκεψης:"))
        row2.addWidget(self.dt_visit)
        lay.addLayout(row2)

        # optional session/exhibition
        row3 = QHBoxLayout()
        self.cmb_session = QComboBox()
        self.cmb_session.addItem("(χωρίς ξενάγηση)", None)
        for s in self.sessions:
            self.cmb_session.addItem(f'{s["start_dt"]} • {s["title"]}', s["id"])

        self.cmb_ex = QComboBox()
        self.cmb_ex.addItem("(χωρίς έκθεση)", None)
        for e in self.exhibitions:
            self.cmb_ex.addItem(f'{e["start_date"]} • {e["title"]}', e["id"])
        # map exhibition -> (max_seats, reserved_seats) για να περιορίζουμε το qty
        self._ex_caps = {}
        for e in self.exhibitions:
            if e.get("id"):
                self._ex_caps[int(e["id"])] = (e.get("max_seats"), e.get("reserved_seats", 0))

        self.cmb_ex.currentIndexChanged.connect(self._update_qty_limit_from_exhibition)
        self._update_qty_limit_from_exhibition()

        row3.addWidget(QLabel("Ξενάγηση:"))
        row3.addWidget(self.cmb_session, 1)
        row3.addSpacing(10)
        row3.addWidget(QLabel("Έκθεση:"))
        row3.addWidget(self.cmb_ex, 1)
        lay.addLayout(row3)

        # payment
        row4 = QHBoxLayout()
        self.cmb_payment = QComboBox()
        self.cmb_payment.addItems(["cash", "card", "online"])
        row4.addWidget(QLabel("Πληρωμή:"))
        row4.addWidget(self.cmb_payment)
        lay.addLayout(row4)

        self.ed_notes = QTextEdit()
        self.ed_notes.setPlaceholderText("Σχόλια…")
        lay.addWidget(self.ed_notes)

        btns = QHBoxLayout()
        b_ok = QPushButton("Δημιουργία")
        b_cancel = QPushButton("Άκυρο")
        b_ok.clicked.connect(self.accept)
        b_cancel.clicked.connect(self.reject)
        btns.addStretch(1)
        btns.addWidget(b_ok)
        btns.addWidget(b_cancel)
        lay.addLayout(btns)

    def _update_qty_limit_from_exhibition(self):
        ex_id = self.cmb_ex.currentData()
        if not ex_id:
            self.sp_qty.setMaximum(999)
            return

        ex_id = int(ex_id)
        max_seats, reserved = self._ex_caps.get(ex_id, (None, 0))

        if not max_seats:
            self.sp_qty.setMaximum(999)
            return

        remaining = int(max_seats) - int(reserved or 0)
        self.sp_qty.setMaximum(max(1, remaining))

        if self.sp_qty.value() > self.sp_qty.maximum():
            self.sp_qty.setValue(self.sp_qty.maximum())

    def accept(self):
        ex_id = self.cmb_ex.currentData()
        if ex_id:
            ex_id = int(ex_id)
            max_seats, reserved = self._ex_caps.get(ex_id, (None, 0))
            if max_seats:
                remaining = int(max_seats) - int(reserved or 0)
                if remaining <= 0:
                    QMessageBox.warning(self, "Πλήρης έκθεση", "Δεν υπάρχουν διαθέσιμες θέσεις για αυτή την έκθεση.")
                    return
                if self.sp_qty.value() > remaining:
                    QMessageBox.warning(self, "Δεν γίνεται", f"Διαθέσιμες θέσεις: {remaining}.")
                    return

        super().accept()


    def get_payload(self):
        type_id = self.cmb_type.currentData()
        qty = int(self.sp_qty.value())
        visit_date = self.dt_visit.date().toString("yyyy-MM-dd")
        return {
            "order": {
                "channel": self.cmb_channel.currentText(),
                "customer_email": self.ed_email.text().strip() or None,
                "payment_method": self.cmb_payment.currentText(),
                "status": "paid",
            },
            "items": [{
                "ticket_type_id": int(type_id),
                "qty": qty,
                "visit_date": visit_date,
                "tour_session_id": self.cmb_session.currentData(),
                "exhibition_id": self.cmb_ex.currentData(),
            }],
            "notes": self.ed_notes.toPlainText().strip(),
        }


class OrderDetailsDialog(QDialog):
    def __init__(self, parent=None, details=None):
        super().__init__(parent)
        self.setWindowTitle("Λεπτομέρειες Παραγγελίας")
        details = details or {}
        lay = QVBoxLayout(self)

        o = details.get("order", {})
        lay.addWidget(QLabel(
            f'Order #{o.get("id","")} • {o.get("created_at","")} • {o.get("channel","")} • {o.get("status","")} • {o.get("total",0):.2f}€'
        ))

        # items
        lay.addWidget(QLabel("Items"))
        t1 = QTableWidget()
        t1.setColumnCount(6)
        t1.setHorizontalHeaderLabels(["Τύπος", "Qty", "Unit", "Total", "Visit", "Ξενάγηση"])
        t1.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        items = details.get("items", [])
        t1.setRowCount(len(items))
        for i, it in enumerate(items):
            t1.setItem(i, 0, QTableWidgetItem(it.get("type_name","")))
            t1.setItem(i, 1, QTableWidgetItem(str(it.get("qty",0))))
            t1.setItem(i, 2, QTableWidgetItem(f'{it.get("unit_price",0):.2f}'))
            t1.setItem(i, 3, QTableWidgetItem(f'{it.get("line_total",0):.2f}'))
            t1.setItem(i, 4, QTableWidgetItem(it.get("visit_date","")))
            t1.setItem(i, 5, QTableWidgetItem(it.get("tour_title","")))
        lay.addWidget(t1)

        # tickets
        lay.addWidget(QLabel("Tickets (QR codes)"))
        t2 = QTableWidget()
        t2.setColumnCount(5)
        t2.setHorizontalHeaderLabels(["Code", "Τύπος", "Ημ/νία", "Status", "Checked-in"])
        t2.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        tickets = details.get("tickets", [])
        t2.setRowCount(len(tickets))
        for i, tk in enumerate(tickets):
            t2.setItem(i, 0, QTableWidgetItem(tk.get("code","")))
            t2.setItem(i, 1, QTableWidgetItem(tk.get("type_name","")))
            t2.setItem(i, 2, QTableWidgetItem(tk.get("visit_date","")))
            t2.setItem(i, 3, QTableWidgetItem(tk.get("status","")))
            t2.setItem(i, 4, QTableWidgetItem(tk.get("checked_in_at","")))
        lay.addWidget(t2)

        b = QPushButton("Κλείσιμο")
        b.clicked.connect(self.accept)
        lay.addWidget(b)