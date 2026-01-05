"""
Κύριο παράθυρο για τη διαχείριση:
- Εκθέσεων / Έργων / Καλλιτεχνών
- Συντήρησης
- Προσωπικού
- Δανεισμών
- Ξεναγήσεων
- Εισιτηρίων & αναφορών

"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date, timedelta

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from openai import OpenAI

from PySide6.QtCore import QDate, QEasingCurve, QEvent, QObject, QPoint, QPropertyAnimation, QSize, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap, QStandardItem, QStandardItemModel, QTextCharFormat
from PySide6.QtWidgets import QAbstractItemView, QButtonGroup, QCalendarWidget, QCheckBox, QComboBox, QDateEdit, QDialog, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListView, QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox, QPushButton, QSizePolicy, QStackedWidget, QTabWidget, QTableView, QTableWidget, QTableWidgetItem, QToolButton, QToolTip, QVBoxLayout, QWidget

from ui_interface import Ui_MainWindow
from ui_utils import html_preview
from dialogs import (AIExhibitionDialog, ArtistBrowserPopup, ArtistDialog, BorrowersManagerDialog, ExhibitionDetailsDialog, ExhibitionDialog, ExhibitionWorksPickerDialog, LoanDialog, LoginDialog, MaintenanceDialog, OrderDetailsDialog, StaffDialog, TicketSaleDialog, TicketTypeDialog, TourBookingDialog, TourSessionDialog, WorkDialog)
from db import (add_artist, add_borrower, add_exhibition, add_exhibition_returning_id, add_exhibition_works, add_loan, add_staff_member, add_ticket_type, add_tour_booking, add_tour_session, add_work, archive_work, check_in_ticket, create_ticket_order, del_pros, delete_artist, delete_borrower, delete_exhibition, delete_loan, delete_tour_booking, delete_tour_session, delete_work, get_all_artists, get_all_borrowers, get_all_exhibition_dates, get_all_exhibitions, get_all_halls, get_all_works, get_due_loans_for_calendar, get_exhibition_work_items, get_exhibition_works, get_exhibitions_count, get_exhibitions_count_this_month_upcoming, get_loan_by_id, get_loans, get_maintenance_for_calendar, get_maintenance_overview_stats, get_scan_log, get_staff, get_staff_by_id, get_staff_count, get_staff_overview_stats, get_ticket_order_details, get_ticket_orders, get_ticket_overview_stats, get_ticket_types, get_tour_bookings, get_tour_overview_stats, get_tour_sessions, get_upcoming_exhibitions, get_works_overview_stats, has_tour_conflict, mark_loan_returned, report_sales_by_session, report_sales_by_type, report_ticket_revenue_by_day, report_ticket_revenue_by_month, report_ticket_revenue_by_month_range, set_exhibition_works, set_order_status, set_ticket_type_active, undo_last_checkin, update_artist, update_borrower, update_exhibition, update_loan, update_staff_member, update_ticket_type, update_tour_booking, update_tour_session, update_work)



# Κοινό στυλ για κουμπιά που χρησιμοποιούνται σε διάφορα tabs
COMMON_BTN_STYLE = """
QPushButton {
    padding: 6px 14px;
    border-radius: 6px;
    background-color: #151d2a;
    color: #ffffff;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #1f2a3d;
}
"""
# DOts για calendar
class MultiMarkCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        """Εσωτερική βοηθητική μέθοδος."""
        super().__init__(parent)
        self.events_by_date = {}

        #σειρά εμφάνισης dots
        self.kind_order = ["exhibitions", "loans", "maintenance", "tours"]

        #ίδια colors που χρησιμοποιείς
        self.kind_colors = {
            "exhibitions": QColor("#f6c26b"),  # πορτοκαλί
            "loans": QColor("#ff6b6b"),        # κόκκινο
            "maintenance": QColor("#6fa8dc"),  # μπλε
            "tours": QColor("#7bd389"),        # πράσινο
        }

    def set_events(self, events_by_date: dict):
        """Εφαρμόζει φίλτρο/ρύθμιση και ανανεώνει το UI."""
        self.events_by_date = events_by_date or {}
        self.updateCells()

    def paintCell(self, painter, rect, date):
        """Μέθοδος βοηθητικής λειτουργίας."""
        super().paintCell(painter, rect, date)

        key = date.toString("yyyy-MM-dd")
        kinds = self.events_by_date.get(key)
        if not kinds:
            return

        present = [k for k in self.kind_order if k in kinds and kinds[k]]
        if not present:
            return

        # ✅ dots ΠΑΝΤΑ (ακόμα και για 1 κατηγορία)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)

        r = 4
        gap = 2
        total = min(4, len(present))
        w = total * (2 * r) + (total - 1) * gap

        x0 = rect.center().x() - w // 2
        y0 = rect.bottom() - (2 * r) - 2

        for i, k in enumerate(present[:4]):
            painter.setBrush(self.kind_colors.get(k, QColor("#999")))
            cx = x0 + i * ((2 * r) + gap)
            painter.drawEllipse(QPoint(cx + r, y0 + r), r, r)

        painter.restore()


class MainWindow(QMainWindow):

    def __init__(self, user, parent=None):
        """Εσωτερική βοηθητική μέθοδος."""
        super().__init__(parent)
        self.user = user

        # Φόρτωμα UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
       
        
         #calendarWidget_2 
        old_cal = self.ui.calendarWidget_2
        parent = old_cal.parentWidget()             
        geom = old_cal.geometry()
        size_policy = old_cal.sizePolicy()
        font = old_cal.font()

        new_cal = MultiMarkCalendar(parent)
        new_cal.setObjectName("calendarWidget_2")
        new_cal.setGeometry(geom)
        new_cal.setSizePolicy(size_policy)
        new_cal.setFont(font)

        # ρυθμίσεις
        new_cal.setGridVisible(old_cal.isGridVisible())
        new_cal.setVerticalHeaderFormat(old_cal.verticalHeaderFormat())
        new_cal.setHorizontalHeaderFormat(old_cal.horizontalHeaderFormat())

        old_cal.setParent(None)
        old_cal.deleteLater()

        self.ui.calendarWidget_2 = new_cal


        #view + eventFilter + selectionChanged    
        self.calendar_view = self.ui.calendarWidget_2.findChild(QTableView)
        if self.calendar_view:
            self.calendar_view.viewport().installEventFilter(self)

        self.ui.calendarWidget_2.selectionChanged.connect(self.on_calendar_date_selected)

        
        #Διατήρηση 2 στηλών (Στατιστικά / Ημερολόγιο)
        try:
            from PySide6.QtWidgets import QSizePolicy
            if hasattr(self.ui, "horizontalLayout_12") and self.ui.horizontalLayout_12:
                # 0: widget_4 (Στατιστικά), 1: widget_5 (Ημερολόγιο)
                self.ui.horizontalLayout_12.setStretch(0, 3)
                self.ui.horizontalLayout_12.setStretch(1, 2)
            if hasattr(self.ui, "widget_5") and self.ui.widget_5:
                #ώστε να μη εξαφανίζεται το ημερολόγιο όταν το chart ζητάει χώρο
                self.ui.widget_5.setMinimumWidth(520)
                self.ui.widget_5.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        except Exception:
            pass

        #hide το search στο header
        if hasattr(self.ui, "searchFrame"):
            self.ui.searchFrame.hide()


        


        self.ui.label_15.setText("ΗΜΕΡΟΛΟΓΙΟ")
        # Calendar toggles πάνω από το ημερολόγιο
        self.cb_cal_exhibitions = QCheckBox("Εκθέσεις")
        self.cb_cal_loans = QCheckBox("Επιστροφές")
        self.cb_cal_maintenance = QCheckBox("Συντήρηση")
        self.cb_cal_tours = QCheckBox("Ξεναγήσεις")

        for cb in (self.cb_cal_exhibitions, self.cb_cal_loans, self.cb_cal_maintenance, self.cb_cal_tours):
            cb.setChecked(True)
            cb.stateChanged.connect(self._on_calendar_filters_changed)

        self._update_calendar_filter_styles()

        # -------- Calendar & label κάτω από το ημερολόγιο --------
        self.refresh_calendar_events()
        # τα βάζουμε στο ίδιο header row ) δίπλα από το "ΗΜΕΡΟΛΟΓΙΟ"
        self.ui.horizontalLayout_14.addStretch(1)
        self.ui.horizontalLayout_14.addWidget(self.cb_cal_exhibitions)
        self.ui.horizontalLayout_14.addWidget(self.cb_cal_loans)
        self.ui.horizontalLayout_14.addWidget(self.cb_cal_maintenance)
        self.ui.horizontalLayout_14.addWidget(self.cb_cal_tours)


        self.calendarInfoLabel = QLabel(self.ui.widget_5)
        self.calendarInfoLabel.setGeometry(40, 270, 431, 40)
        self.calendarInfoLabel.setWordWrap(True)
        self.calendarInfoLabel.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.calendarInfoLabel.setMinimumHeight(90) 
        self.calendarInfoLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)

        self.calendarInfoLabel.setStyleSheet("font-size: 10pt; color: #151d2a; padding: 6px;")


        self.calendarInfoLabel.setText(
            "Δεν υπάρχει έκθεση για την επιλεγμένη ημερομηνία."
        )
        self.on_calendar_date_selected()

        #Tooltips με hover πάνω στο calendar
        self.ui.calendarWidget_2.setMouseTracking(True)
        cal_view = self.ui.calendarWidget_2.findChild(QTableView)
        if cal_view:
            cal_view.setMouseTracking(True)
            cal_view.viewport().setMouseTracking(True)
            cal_view.viewport().installEventFilter(self)
            self.calendar_view = cal_view
        else:
            self.calendar_view = None
        


        # -Dashboard counters 
        self.refresh_dashboard_counters()


        self.ui.label_6.setText(str(get_exhibitions_count_this_month_upcoming()))  # card "ΕΚΘΕΣΕΙΣ"

        # ]Chart: Ticket revenue]
        self.init_ticket_revenue_chart()
        self.apply_ticket_stats_filters()

        # -------- Δεξί profile: όνομα χρήστη + logout --------
        self.ui.label_18.setText(self.user["full_name"])
        self.ui.frame_13.setMinimumSize(0, 0)
        self.ui.pushButton_8.clicked.connect(self.logout)

        self.ui.verticalLayout_12.setContentsMargins(10, 20, 10, 20)
        self.ui.verticalLayout_12.setSpacing(6)
        self.ui.verticalLayout_12.setAlignment(Qt.AlignTop)
        self.ui.label_18.setWordWrap(True)
        self.ui.label_18.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.ui.label_18.setStyleSheet("font-size: 13px; font-weight: bold;")


        # 1) ΟΜΑΔΑ ΚΟΥΜΠΙΩΝ ΜΕΝΟΥ 

        self.menu_buttons = [
            self.ui.pushButton_2,  # ΑΡΧΙΚΗ
            self.ui.pushButton_3,  # ΕΡΓΑ
            self.ui.pushButton_4,  # ΕΚΘΕΣΕΙΣ
            self.ui.pushButton_5,  # ΣΥΝΤΗΡΗΣΗ
            self.ui.pushButton_6,  # ΠΡΟΣΩΠΙΚΟ
            self.ui.pushButton_7,  # ΤΟ ΠΡΟΦΙΛ ΜΟΥ
            self.ui.pushButton_8,  # ΑΠΟΣΥΝΔΕΣΗ
        ]
        #ΚΟΥΜΠΙ ΔΑΝΕΙΣΜΟΙ 
       
        self.btn_loans = QPushButton("ΔΑΝΕΙΣΜΟΙ", self.ui.frame_12)
        self.btn_loans.setFont(self.ui.pushButton_6.font())
        icon = QIcon()
        icon.addFile(":/blueIcons/icons/activity.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.btn_loans.setIcon(icon)
        self.btn_loans.setIconSize(QSize(27, 27))

        # προσθήκη στο layout του αριστερού μενού (κάτω από ΠΡΟΣΩΠΙΚΟ)
        self.ui.verticalLayout_9.addWidget(self.btn_loans)
        self.menu_buttons.insert(5, self.btn_loans)  
        
        #ΚΟΥΜΠΙ ΞΕΝΑΓΗΣΕΙΣ
        self.btn_tours = QPushButton("ΞΕΝΑΓΗΣΕΙΣ", self.ui.frame_12)
        self.btn_tours.setFont(self.ui.pushButton_6.font())
        icon2 = QIcon()
        icon2.addFile(":/blueIcons/icons/guide1.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.btn_tours.setIcon(icon2)
        self.btn_tours.setIconSize(QSize(27, 27))

        #ΚΟΥΜΠΙ TICKETS
        self.btn_tickets = QPushButton("ΕΙΣΙΤΗΡΙΑ", self.ui.frame_12)
        self.btn_tickets.setFont(self.ui.pushButton_6.font())
        icon3 = QIcon()
        icon3.addFile(":/blueIcons/icons/eye.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.btn_tickets.setIcon(icon3)
        self.btn_tickets.setIconSize(QSize(27, 27))

        # προσθήκη στο layout του αριστερού μενού (κάτω από ΔΑΝΕΙΣΜΟΙ)
        self.ui.verticalLayout_9.addWidget(self.btn_tours)

        # πρόσθεσέ το και στην exclusive ομάδα (πριν το profile/logout)
        self.menu_buttons.insert(6, self.btn_tours)


        # προσθήκη στο layout του αριστερού μενού tickets)
        self.ui.verticalLayout_9.addWidget(self.btn_tickets)
        self.menu_buttons.insert(6, self.btn_tickets)

        group = QButtonGroup(self)
        group.setExclusive(True)
        for btn in self.menu_buttons:
            btn.setCheckable(True)
            group.addButton(btn)
        self.ui.pushButton_2.setChecked(True)

       
        # 2) QStackedWidget ΜΕΣΑ στο mainBody (header πάνω)

        layout = self.ui.verticalLayout  # QVBoxLayout του mainBody

        layout.removeWidget(self.ui.cardsFrame)
        layout.removeWidget(self.ui.mainFrame)
        self.ui.cardsFrame.setParent(None)
        self.ui.mainFrame.setParent(None)

        self.stacked = QStackedWidget(self.ui.mainBody)

        # page 0: ΑΡΧΙΚΗ
        self.page_home = QWidget()
        page_home_layout = QVBoxLayout(self.page_home)
        page_home_layout.setContentsMargins(20,20, 20, 20)
        page_home_layout.setSpacing(26)
        page_home_layout.addWidget(self.ui.cardsFrame)
        page_home_layout.addWidget(self.ui.mainFrame)
        self.stacked.addWidget(self.page_home)  # index 0
        layout.addWidget(self.stacked)
                          
        def make_page(title: str) -> QWidget:
            """Μέθοδος βοηθητικής λειτουργίας."""
            w = QWidget()
            lay = QVBoxLayout(w)
            lbl = QLabel(title)
            lbl.setStyleSheet("font-size: 24px; font-weight: bold;")
            lay.addWidget(lbl)
            lay.addStretch()
            return w


        # page 1: ΕΡΓΑ – gallery
        self.page_erga = QWidget()
        erga_layout = QVBoxLayout(self.page_erga)
        erga_layout.setContentsMargins(10, 10, 10, 10)
        erga_layout.setSpacing(10)

        # επάνω μπάρα: αναζήτηση + φίλτρα (κατηγορία, καλλιτέχνης)
        # κουμπί "Φίλτρο" με menu για Κατηγορίες + Αίθουσες
        self.filter_button = QToolButton()
        self.filter_button.setText("Φίλτρο: Όλα τα έργα")
        self.filter_button.setPopupMode(QToolButton.InstantPopup)

        self.filter_button.setStyleSheet("""
        QToolButton {
            background-color: #151d2a;
            border-radius: 16px;
            border: 1px solid #394b63;
            color: #ffffff;
            padding: 4px 12px;
            font-weight: 500;
        }
        QToolButton::menu-indicator {
            image: none;
        }
        QToolButton:hover {
            background-color: #1f2a3d;
        }
        """)

        # menu φίλτρων
        self.filter_menu = QMenu(self)

        
        menu_style = """
        QMenu {
            background-color: #111827;      /* σκούρο indigo */
            border: 1px solid #374151;
            color: #e5e7eb;
        }
        QMenu::item {
            padding: 6px 18px;
            background-color: transparent;
        }
        QMenu::item:selected {
            background-color: #2563eb;      /* μπλε highlight */
            color: #f9fafb;
        }
        QMenu::separator {
            height: 1px;
            background: #1f2937;
            margin: 4px 10px;
        }
        """

        self.filter_menu.setStyleSheet(menu_style)


        # "Όλα τα έργα" 
        action_all = self.filter_menu.addAction("Όλα τα έργα")
        action_all.triggered.connect(
            lambda checked=False: self.reset_gallery_filters()
        )

        # -Υπομενού Κατηγορίες 
        cat_menu = self.filter_menu.addMenu("Κατηγορίες")
        act_cat_all = cat_menu.addAction("Όλες οι κατηγορίες")
        act_cat_all.triggered.connect(
            lambda checked=False: self.set_category_filter(None, None)
        )

        act_cat_paint = cat_menu.addAction("Πίνακες")
        act_cat_paint.triggered.connect(
            lambda checked=False: self.set_category_filter("Πίνακας", "Πίνακες")
        )

        act_cat_sculpt = cat_menu.addAction("Γλυπτά")
        act_cat_sculpt.triggered.connect(
            lambda checked=False: self.set_category_filter("Γλυπτό", "Γλυπτά")
        )

        # Υπομενού Αίθουσες
        hall_menu = self.filter_menu.addMenu("Αίθουσες")
        cat_menu.setStyleSheet(menu_style)
        hall_menu.setStyleSheet(menu_style)

        from db import get_all_halls
        for hall in get_all_halls():
            hall_id = hall["id"]
            hall_name = hall["name"]
            act_h = hall_menu.addAction(hall_name)
            act_h.triggered.connect(
                lambda checked=False, hid=hall_id, hname=hall_name:
                    self.set_hall_filter(hid, hname))

                
        # Υπομενού Δανεισμοί 
        loan_menu = self.filter_menu.addMenu("Δανεισμοί")
        loan_menu.setStyleSheet(menu_style)


        act_loan_borrowed = loan_menu.addAction("Μόνο δανεισμένα")
        act_loan_borrowed.triggered.connect(
            lambda checked=False: self.set_loan_filter("BORROWED", "Δανεισμένα")
        )

        act_loan_soon = loan_menu.addAction("Λήγουν σύντομα (7 ημέρες)")
        act_loan_soon.triggered.connect(
            lambda checked=False: self.set_loan_filter("SOON", "Λήγουν σύντομα (7 ημέρες)")
        )

        act_loan_overdue = loan_menu.addAction("Εκπρόθεσμα")
        act_loan_overdue.triggered.connect(
            lambda checked=False: self.set_loan_filter("OVERDUE", "Εκπρόθεσμα"))
        


        


        self.filter_button.setMenu(self.filter_menu)

        # τρέχον φίλτρο κατηγορίας + αίθουσας (μπορούν να συνδυαστούν)
        self.filter_category = None          # "Πίνακας", "Γλυπτό" ή None
        self.filter_category_label = None    
        self.filter_hall_id = None           # id αίθουσας ή None
        self.filter_hall_label = None        # π.χ. "Αίθουσα 1 – Αναγέννηση"

        # αρχικό κείμενο στο κουμπί φίλτρου
        self._update_filter_button_text()

        
        top_bar = QHBoxLayout()

        #search σαν του header (searchFrame + icon + lineEdit)]
        self.works_search_frame = QFrame()
        self.works_search_frame.setObjectName("searchFrame")  # για να πιάσει το ίδιο style
        self.works_search_frame.setMinimumSize(QSize(160, 0))
        self.works_search_frame.setFrameShape(QFrame.StyledPanel)
        self.works_search_frame.setFrameShadow(QFrame.Raised)

        search_layout = QHBoxLayout(self.works_search_frame)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)

        search_icon = QLabel(self.works_search_frame)
        search_icon.setMaximumSize(QSize(24, 16777215))
        search_icon.setPixmap(QPixmap(":/blueIcons/icons/search.svg"))
        search_layout.addWidget(search_icon)

        self.works_search_edit = QLineEdit(self.works_search_frame)
        self.works_search_edit.setPlaceholderText("Search")   # ή "Αναζήτηση έργων..."
        search_layout.addWidget(self.works_search_edit)


        top_bar.addWidget(self.works_search_frame)

        # κουμπί φίλτρου (QToolButton + menu)
        top_bar.addWidget(self.filter_button)



        # κουμπί "Καλλιτέχνες"
        self.btn_artists_popup = QPushButton("👩‍🎨 Καλλιτέχνες")
        self.btn_artists_popup.setCursor(Qt.PointingHandCursor)
        self.btn_artists_popup.setStyleSheet("""
        QPushButton {
            background-color: #0f172a;          /* ίδιο “dark” με combo */
            border-radius: 16px;
            border: 1px solid #1d4ed8;          /* ίδιο μπλε περίγραμμα */
            color: #e5e7eb;
            padding: 6px 14px;                   /* πιο κοντά στο combobox */
            font-weight: 600;
            min-height: 34px;                    /* ίδιο ύψος περίπου */
        }
        QPushButton:hover {
            background-color: #111827;           /* ίδιο hover */
        }
        QPushButton:pressed {
            background-color: #020617;           /* ίδιο “pressed” */
        }
        """)

        self.btn_artists_popup.clicked.connect(self.open_artists_popup)
        top_bar.addWidget(self.btn_artists_popup)

        top_bar.addStretch()




        top_bar.addStretch()

        erga_layout.addLayout(top_bar)





        # gallery list
        self.works_list = QListWidget()
        self.works_list.setViewMode(QListWidget.IconMode)
        self.works_list.setResizeMode(QListWidget.Adjust)
        self.works_list.setMovement(QListWidget.Static)
        self.works_list.setIconSize(QSize(220, 220))
        self.works_list.setGridSize(QSize(240, 280))
        self.works_list.setSpacing(16)
        self.works_list.setWordWrap(True)
        self.works_list.setSelectionMode(QListWidget.SingleSelection)

        erga_layout.addWidget(self.works_list)

        # κουμπί για νέο έργο (κάτω δεξιά)
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()

        self.btn_delete_work = QPushButton("🗑️ Διαγραφή έργου")
        self.btn_delete_work.setStyleSheet(COMMON_BTN_STYLE)
        bottom_bar.addWidget(self.btn_delete_work)

        self.btn_add_work = QPushButton("➕ Νέο έργο")
        self.btn_add_work.setStyleSheet(COMMON_BTN_STYLE)
        bottom_bar.addWidget(self.btn_add_work)

        erga_layout.addLayout(bottom_bar)
        self.stacked.addWidget(self.page_erga)  # index 1




        # page 2: ΕΚΘΕΣΕΙΣ με tabs
        self.page_ektheseis = QWidget()
        ek_layout = QVBoxLayout(self.page_ektheseis)
        ek_layout.setContentsMargins(10, 10, 10, 10)
        ek_layout.setSpacing(10)

        # γραμμή κουμπιών CRUD
        btn_bar = QHBoxLayout()
        self.btn_add_exhibition = QPushButton("➕ Νέα έκθεση")
        self.btn_edit_exhibition = QPushButton("✏️ Επεξεργασία")
        self.btn_delete_exhibition = QPushButton("🗑️ Διαγραφή")


        for b in (self.btn_add_exhibition, self.btn_edit_exhibition, self.btn_delete_exhibition):
            b.setStyleSheet(COMMON_BTN_STYLE)

        btn_bar.addWidget(self.btn_add_exhibition)
        btn_bar.addWidget(self.btn_edit_exhibition)
        btn_bar.addWidget(self.btn_delete_exhibition)
        
        # AI button μέσα στις Εκθέσεις
        self.btn_ai_exhibition = QPushButton("🤖 AI Πρόταση Έκθεσης")
        self.btn_ai_exhibition.setStyleSheet("""
    QPushButton {
        background-color: #0078D7;
        color: white;
        border-radius: 12px;
        font-weight: bold;
        font-size: 12pt;
    }
    QPushButton:hover { background-color: #005a9e; }
    QPushButton:pressed { background-color: #004070; }
""") 
        self.btn_ai_exhibition.clicked.connect(self.open_ai_exhibition_dialog)
        btn_bar.addWidget(self.btn_ai_exhibition)

        btn_bar.addStretch()

        

        ek_layout.addLayout(btn_bar)

        # Tabs
        self.exhibitions_tabs = QTabWidget()
        ek_layout.addWidget(self.exhibitions_tabs)

        # Tab 1: Επερχόμενες
        self.tab_upcoming = QWidget()
        up_layout = QVBoxLayout(self.tab_upcoming)
        self.table_upcoming = QTableWidget()
        self.table_upcoming = QTableWidget()
        self.table_upcoming.setColumnCount(8)
        self.table_upcoming.setHorizontalHeaderLabels(
            ["ID", "Τίτλος", "Ημερομηνία(Έναρξη - Λήξη)", "Επιμελητής", "Μέγ. Θέσεις", "Κρατημένες", "Αριθμός έργων", "Περιγραφή"]
        )

        self.table_upcoming.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_upcoming.setSelectionMode(QTableWidget.SingleSelection)
        self.table_upcoming.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_upcoming.horizontalHeader().setStretchLastSection(True)
        self.table_upcoming.verticalHeader().setVisible(False)
        up_layout.addWidget(self.table_upcoming)
        self.exhibitions_tabs.addTab(self.tab_upcoming, "Επερχόμενες")

        # Tab 2: Παλιές
        self.tab_past = QWidget()
        past_layout = QVBoxLayout(self.tab_past)
        self.table_past = QTableWidget()
        self.table_past = QTableWidget()
        self.table_past.setColumnCount(8)
        self.table_past.setHorizontalHeaderLabels(
            ["ID", "Τίτλος", "Ημερομηνία(Έναρξη - Λήξη)", "Επιμελητής", "Μέγ. Θέσεις", "Κρατημένες", "Αριθμός έργων", "Περιγραφή"]
        )

        self.table_past.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_past.setSelectionMode(QTableWidget.SingleSelection)
        self.table_past.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_past.horizontalHeader().setStretchLastSection(True)
        self.table_past.verticalHeader().setVisible(False)
        past_layout.addWidget(self.table_past)
        self.exhibitions_tabs.addTab(self.tab_past, "Παλιές")

        self.stacked.addWidget(self.page_ektheseis)  # index 2
        self.table_upcoming.itemDoubleClicked.connect(self.open_selected_exhibition_details)
        self.table_past.itemDoubleClicked.connect(self.open_selected_exhibition_details)


        # ------------------------------------------------------- PAGE 3 ΣΥΝΤΗΡΗΣΗ -----------------------------------------------------------------------------------
        self.page_syntirisi = QWidget()
        syntirisi_layout = QVBoxLayout(self.page_syntirisi)
        syntirisi_layout.setContentsMargins(10, 10, 10, 10)
        syntirisi_layout.setSpacing(10)

# Τίτλος
        title_label = QLabel("Σελίδα: ΣΥΝΤΗΡΗΣΗ")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        syntirisi_layout.addWidget(title_label)

#Φίλτρο Τύπου Συντήρησης 
        filter_layout = QHBoxLayout()

        filter_label = QLabel("Φίλτρο Συντήρησης:")
        self.maintenance_filter = QComboBox()
        self.maintenance_filter.addItems(["Όλα","Καθαρισμός καμβά / επιφάνειας", "Καθαρισμός γλυπτού / σταθεροποίηση"])

        self.maintenance_filter.setStyleSheet("""
        QComboBox {
            background-color: #151d2a;
            border-radius: 16px;
            border: 1px solid #394b63;
            color: #ffffff;
            padding: 4px 12px;
            font-weight: 500;
        }
        QComboBox:hover {
            background-color: #1f2a3d;
        }
        QComboBox::drop-down {
            border: 0px;
            width: 22px;
        }
        QComboBox::down-arrow {
            image: none;  
        }

        /* το dropdown list */
        QComboBox QAbstractItemView {
            background-color: #111827;
            border: 1px solid #374151;
            color: #e5e7eb;
            selection-background-color: #2563eb;
            selection-color: #f9fafb;
            outline: 0;
        }
        """)


        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.maintenance_filter)
        filter_layout.addStretch()

        syntirisi_layout.addLayout(filter_layout)

# Πίνακας Συντήρησης 
        self.syntirisi_table = QTableWidget()
        self.syntirisi_table.setColumnCount(6)
        self.syntirisi_table.setHorizontalHeaderLabels([
    "ID Συντήρησης",
    "Τίτλος Έργου",
    "Ημ/νία Προσθήκης",
    "Τύπος Συντήρησης",
    "Ημ/νία Έναρξης",
    "Συντηρητής"
])

        self.syntirisi_table.horizontalHeader().setStretchLastSection(True)
        self.syntirisi_table.verticalHeader().setVisible(False)
        self.syntirisi_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.syntirisi_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.syntirisi_table.setSelectionMode(QTableWidget.SingleSelection)

        syntirisi_layout.addWidget(self.syntirisi_table)

        self.stacked.addWidget(self.page_syntirisi)
        self.load_works_maintenance()
        self.maintenance_filter.currentIndexChanged.connect(self.load_works_maintenance)

          

        # page 4: ΠΡΟΣΩΠΙΚΟ
        self.page_prosopiko = QWidget()
        self.layout_pros = QVBoxLayout(self.page_prosopiko)
        self.layout_pros.setContentsMargins(10, 10, 10, 10)
        self.layout_pros.setSpacing(10)
        self.stacked.addWidget(self.page_prosopiko)
     # Φόρτωσε τα μέλη προσωπικού
        self.load_staff()


        # page 5: ΔΑΝΕΙΣΜΟΙ
        self.page_loans = QWidget()
        self.layout_loans = QVBoxLayout(self.page_loans)
        self.layout_loans.setContentsMargins(10, 10, 10, 10)
        self.layout_loans.setSpacing(10)
        self.stacked.addWidget(self.page_loans)  # index 5

        self.load_loans_page()

        # page 6: ΞΕΝΑΓΗΣΕΙΣ
        self.page_tours = QWidget()
        self.tours_layout = QVBoxLayout(self.page_tours)
        self.tours_layout.setContentsMargins(10, 10, 10, 10)
        self.tours_layout.setSpacing(10)
        self.stacked.addWidget(self.page_tours)  # index 6

        self.setup_tours_page()
        self.refresh_tours_page()

        # page 7: tickets
        self.page_tickets = QWidget()
        self.tickets_layout = QVBoxLayout(self.page_tickets)
        self.tickets_layout.setContentsMargins(10, 10, 10, 10)
        self.tickets_layout.setSpacing(10)
        self.stacked.addWidget(self.page_tickets)  # index 7

        self.setup_tickets_page()
        self.refresh_tickets_page()



        # Φόρτωση εκθέσεων στα tabs
        self.load_exhibitions_tables()

        # Φόρτωση gallery

        
        self.load_works_gallery()

        self.works_search_edit.textChanged.connect(self.load_works_gallery)
        self.works_list.itemDoubleClicked.connect(self.open_work_from_item)
        self.btn_add_work.clicked.connect(self.add_work_dialog)

        self.btn_delete_work.clicked.connect(self.delete_selected_work)


        # Συνδέσεις CRUD
        self.btn_add_exhibition.clicked.connect(self.add_exhibition_dialog)
        self.btn_edit_exhibition.clicked.connect(self.edit_selected_exhibition)
        self.btn_delete_exhibition.clicked.connect(self.delete_selected_exhibition)

        # Συνδέσεις menu κουμπιών → σελίδες
        self.ui.pushButton_2.clicked.connect(lambda: self.stacked.setCurrentIndex(0))
        self.ui.pushButton_3.clicked.connect(lambda: self.stacked.setCurrentIndex(1))
        self.ui.pushButton_4.clicked.connect(lambda: self.stacked.setCurrentIndex(2))
        self.ui.pushButton_5.clicked.connect(lambda: self.stacked.setCurrentIndex(3))
        self.ui.pushButton_6.clicked.connect(lambda: self.stacked.setCurrentIndex(4))
        self.btn_loans.clicked.connect(lambda: self.stacked.setCurrentIndex(5))
        self.btn_tours.clicked.connect(lambda: self.stacked.setCurrentIndex(6))
        self.btn_tickets.clicked.connect(lambda: self.stacked.setCurrentIndex(7))


        # 3) SLIDERS: αριστερό menu & δεξί profile

        self.left_menu_expanded_width = 200
        self.left_menu_collapsed_width = 60
        self.left_menu_open = True
        self.ui.leftMenu.setMaximumWidth(self.left_menu_expanded_width)
        self.ui.menuBtn.clicked.connect(self.toggle_left_menu)

        self.profile_expanded_width = 200
        self.profile_collapsed_width = 0
        self.profile_open = False
        self.ui.Profile.setMaximumWidth(self.profile_collapsed_width)
        self.ui.Profile.setMinimumWidth(0)
        self.ui.frame_13.setMinimumWidth(0)
        self.ui.accountBtn.clicked.connect(self.toggle_profile_menu)


        # 4) Notifications (καμπανάκι)

        self.ui.pushButton.clicked.connect(self.show_notifications_popup)


    # SLIDER ΑΡΙΣΤΕΡΟΥ ΜΕΝΟΥ

    def toggle_left_menu(self):
        """Εναλλάσσει (expand/collapse) το αριστερό μενού με animation."""
        current_width = self.ui.leftMenu.width()

        if self.left_menu_open:
            start_width = current_width
            end_width = self.left_menu_collapsed_width
            self.left_menu_open = False
            self.ui.label_17.hide()
        else:
            start_width = current_width
            end_width = self.left_menu_expanded_width
            self.left_menu_open = True
            self.ui.label_17.show()

        anim = QPropertyAnimation(self.ui.leftMenu, b"maximumWidth")
        anim.setDuration(250)
        anim.setStartValue(start_width)
        anim.setEndValue(end_width)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.start()
        self._left_menu_anim = anim  # κρατάμε ref


    # SLIDER ΔΕΞΙΟΥ PROFILE PANEL

    def toggle_profile_menu(self):
        """Εναλλάσσει (open/close) το δεξί profile panel με animation."""
        current_width = self.ui.Profile.width()

        if self.profile_open:
            start_width = current_width
            end_width = self.profile_collapsed_width
            self.profile_open = False
            self.ui.pushButton_7.hide()
            self.ui.pushButton_8.hide()
        else:
            start_width = current_width
            end_width = self.profile_expanded_width
            self.profile_open = True
            self.ui.pushButton_7.hide()
            self.ui.pushButton_8.show()

        anim = QPropertyAnimation(self.ui.Profile, b"maximumWidth")
        anim.setDuration(250)
        anim.setStartValue(start_width)
        anim.setEndValue(end_width)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.start()
        self._profile_anim = anim


    def refresh_dashboard_counters(self):
        # ΣΥΝΤΗΡΗΣΗ (ανοιχτές συντηρήσεις)
        """Ανανέωση των counters/στατιστικών στο dashboard."""
        mstats = get_maintenance_overview_stats()
        self.ui.label_12.setText(str(mstats["open"]))

        # ΠΡΟΣΩΠΙΚΟ
        s = get_staff_overview_stats()
        self.ui.label_9.setText(str(s["total"]))   # label_9 = μεγάλο νούμερο στο card ΠΡΟΣΩΠΙΚΟ
        self.ui.label_staff_sub.setText(
    f"Ξεναγοί: {s['guides']} | Συντηρητές: {s['conservators']} | Επιμελητές: {s['curators']}"
)


        # ΕΡΓΑ
        stats = get_works_overview_stats()
        self.ui.label.setText(str(stats["total_active"]))  # το "ΕΡΓΑ" counter είναι το label:contentReference[oaicite:5]{index=5}
        self.ui.label_works_sub.setText(
    f"ΔΙΚΑ ΜΑΣ (ΕΝΤΟΣ): {stats['owned_active']} | ΔΙΚΑ ΜΑΣ (ΣΥΝΟΛΟ): {stats.get('owned_total_active', 0)} | IN: {stats['borrowed_in_active']} | OUT: {stats['loaned_out_active']}"
)



    # DASHBOARD CHART: Ticket revenue (Στατιστικά)

    def init_ticket_revenue_chart(self):
        """Φτιάχνει το matplotlib chart + φίλτρα μέσα στο card 'ΣΤΑΤΙΣΤΙΚΑ'.

        Επιλογές:
        - Ανά ημέρα
        - Ανά μήνα
        - Ανά τύπο εισιτηρίου
        - Custom date range
        """
        try:
            # Υπάρχει placeholder graphicsView στο UI — το κρύβουμε.
            if hasattr(self.ui, "graphicsView") and self.ui.graphicsView:
                self.ui.graphicsView.hide()

            # container είναι το frame_6 μέσα στο widget_4 (ΣΤΑΤΙΣΤΙΚΑ)
            container = getattr(self.ui, "frame_6", None)
            if container is None:
                return

            # Layout (αν δεν υπάρχει)
            lay = container.layout()
            if lay is None:
                lay = QVBoxLayout(container)
                lay.setContentsMargins(10, 10, 10, 10)
                lay.setSpacing(8)

            # -------- Controls (mode + date range) --------
            controls = QWidget(container)
            ctrl = QHBoxLayout(controls)
            ctrl.setContentsMargins(0, 0, 0, 0)
            ctrl.setSpacing(8)

            lbl_mode = QLabel("Προβολή:")
            self.ticketStatsMode = QComboBox()
            self.ticketStatsMode.addItems(["Ανά ημέρα", "Ανά μήνα", "Ανά τύπο εισιτηρίου"])

            lbl_from = QLabel("Από:")
            self.ticketStatsFrom = QDateEdit()
            self.ticketStatsFrom.setCalendarPopup(True)
            self.ticketStatsFrom.setDisplayFormat("dd/MM/yyyy")

            lbl_to = QLabel("Έως:")
            self.ticketStatsTo = QDateEdit()
            self.ticketStatsTo.setCalendarPopup(True)
            self.ticketStatsTo.setDisplayFormat("dd/MM/yyyy")

            # Default range: τελευταίες 30 ημέρες
            d_from, d_to = self._ticket_stats_default_range_qdates()
            self.ticketStatsFrom.setDate(d_from)
            self.ticketStatsTo.setDate(d_to)


            ctrl.addWidget(lbl_mode)
            ctrl.addWidget(self.ticketStatsMode, 0)
            ctrl.addSpacing(10)
            ctrl.addWidget(lbl_from)
            ctrl.addWidget(self.ticketStatsFrom, 0)
            ctrl.addWidget(lbl_to)
            ctrl.addWidget(self.ticketStatsTo, 0)
            ctrl.addStretch(1)
            lay.addWidget(controls)

            # -------- Matplotlib Figure + Canvas --------
            self._ticket_rev_fig = Figure(figsize=(5.4, 2.6), tight_layout=True)
            self._ticket_rev_ax = self._ticket_rev_fig.add_subplot(111)
            self._ticket_rev_canvas = FigureCanvas(self._ticket_rev_fig)
            lay.addWidget(self._ticket_rev_canvas, 1)

            # Μην αφήνουμε το canvas να "καταπίνει" όλο το διαθέσιμο χώρο
            try:
                from PySide6.QtWidgets import QSizePolicy
                self._ticket_rev_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                self._ticket_rev_canvas.setMinimumSize(0, 0)
                self._ticket_rev_canvas.setMaximumHeight(280)
            except Exception:
                pass

            # Debounce refresh όταν αλλάζουν φίλτρα
            self._ticket_stats_refresh_timer = QTimer(self)
            self._ticket_stats_refresh_timer.setSingleShot(True)
            self._ticket_stats_refresh_timer.timeout.connect(self.apply_ticket_stats_filters)

          
            self.ticketStatsMode.currentIndexChanged.connect(lambda *_: self._ticket_stats_refresh_timer.start(150))
            self.ticketStatsFrom.dateChanged.connect(lambda *_: self._ticket_stats_refresh_timer.start(150))
            self.ticketStatsTo.dateChanged.connect(lambda *_: self._ticket_stats_refresh_timer.start(150))

        except Exception:
            # αν κάτι πάει στραβά, να μη “σπάει” το app
            return

    def _ticket_stats_default_range_qdates(self):
        """Default: τελευταίες 30 ημέρες (QDate, QDate)."""
        d_to = QDate.currentDate()
        d_from = d_to.addDays(-29)
        return d_from, d_to

    def apply_ticket_stats_filters(self):
        """Διαβάζει τα φίλτρα από το UI και κάνει refresh στο γράφημα."""
        if not hasattr(self, "_ticket_rev_ax") or not hasattr(self, "_ticket_rev_canvas"):
            return
        if not hasattr(self, "ticketStatsMode") or not hasattr(self, "ticketStatsFrom") or not hasattr(self, "ticketStatsTo"):
            return

        mode = self.ticketStatsMode.currentText().strip()
        q_from = self.ticketStatsFrom.date()
        q_to = self.ticketStatsTo.date()

        # Αν ο χρήστης τα βάλει ανάποδα, τα διορθώνουμε σιωπηλά
        if q_from > q_to:
            q_from, q_to = q_to, q_from
            self.ticketStatsFrom.setDate(q_from)
            self.ticketStatsTo.setDate(q_to)

        date_from = q_from.toString("yyyy-MM-dd")
        date_to = q_to.toString("yyyy-MM-dd")

        self.refresh_ticket_stats_chart(mode=mode, date_from=date_from, date_to=date_to)

    def refresh_ticket_stats_chart(self, mode: str, date_from: str, date_to: str):
        """Κάνει refresh το chart βάσει mode + date range."""
        ax = self._ticket_rev_ax
        ax.clear()

        labels = []
        values = []
        title = "Έσοδα από εισιτήρια"

        try:
            if mode == "Ανά τύπο εισιτηρίου":
                data = report_sales_by_type(date_from, date_to) or []
                labels = [d.get("type", "") for d in data]
                values = [float(d.get("revenue") or 0) for d in data]
                title = "Έσοδα ανά τύπο εισιτηρίου"
            elif mode == "Ανά μήνα":
                data = report_ticket_revenue_by_month_range(date_from, date_to) or []
                labels = [d.get("month", "") for d in data]
                values = [float(d.get("revenue") or 0) for d in data]
                title = "Έσοδα ανά μήνα"
            else:  # default: Ανά ημέρα
                data = report_ticket_revenue_by_day(date_from, date_to) or []
                labels = [d.get("day", "") for d in data]
                values = [float(d.get("revenue") or 0) for d in data]
                title = "Έσοδα ανά ημέρα"
        except Exception:
            labels = []
            values = []

        if not labels:
            ax.text(0.5, 0.5, "Δεν υπάρχουν δεδομένα.", ha="center", va="center", transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
            self._ticket_rev_canvas.draw()
            return

        if sum(values) <= 0:
            ax.text(0.5, 0.5, "Δεν υπάρχουν πωλήσεις εισιτηρίων.", ha="center", va="center", transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
            self._ticket_rev_canvas.draw()
            return

        x = list(range(len(labels)))

        # Αν έχουμε πολλές ημέρες, προτιμάμε γραμμή αντί για πολλά bars
        draw_line = (mode == "Ανά ημέρα" and len(labels) > 45)

        if draw_line:
            ax.plot(x, values)
        else:
            ax.bar(x, values)

        ax.set_title(f"{title} ({date_from} → {date_to})")
        ax.set_ylabel("Euro €")

        # Ρύθμιση xticks:
        # - Στην προβολή "Ανά ημέρα" δείχνουμε labels ΜΟΝΟ στις ημέρες που έχουν πωλήσεις,
        #   αλλά κρατάμε την απόσταση των ημερών ίδια (οι ενδιάμεσες ημέρες υπάρχουν στο x, απλώς δεν έχουν label).
        # - Στις άλλες προβολές, περιορίζουμε τα labels για να μην "μπουκώσει" ο άξονας.
        if mode == "Ανά ημέρα":
            sale_idx = [i for i, v in enumerate(values) if (v or 0) > 0]
            if not sale_idx:
                sale_idx = list(range(len(labels)))

            # Αν είναι πολλά, κρατάμε ένα υποσύνολο από τα sale days για αναγνωσιμότητα
            max_labels = 20
            if len(sale_idx) > max_labels:
                step = (len(sale_idx) + max_labels - 1) // max_labels  # ceil division
                tick_idx = sale_idx[::step]
            else:
                tick_idx = sale_idx

            ax.set_xticks(tick_idx)
            ax.set_xticklabels([labels[i] for i in tick_idx], rotation=35, ha="right", fontsize=8)
        else:
            max_labels = 12
            step = max(1, len(labels) // max_labels)
            tick_idx = list(range(0, len(labels), step))
            ax.set_xticks(tick_idx)
            ax.set_xticklabels([labels[i] for i in tick_idx], rotation=35, ha="right", fontsize=8)

        ax.grid(axis="y", alpha=0.25)
        self._ticket_rev_canvas.draw()

    # NOTIFICATIONS POPUP

    def show_notifications_popup(self):
        # Ειδοποιήσεις: όλα τα είδη γεγονότων για τις επόμενες 7 ημέρες
        """Εμφανίζει popup ειδοποιήσεων για γεγονότα των επόμενων ημερών."""
        from datetime import datetime, date, timedelta

        window_days = 7  # σήμερα + επόμενες 6 = 7 ημέρες
        today = date.today()
        window_end = today + timedelta(days=window_days - 1)

        def _parse_iso_date(s: str):
            """Εσωτερική βοηθητική μέθοδος."""
            try:
                return date.fromisoformat((s or "").strip())
            except Exception:
                return None

        def _nice_date(iso: str) -> str:
            """Εσωτερική βοηθητική μέθοδος."""
            q = self._qdate_from_iso((iso or "").strip())
            return q.toString("dd/MM/yyyy") if q else (iso or "").strip()

        def _in_window(d: date) -> bool:
            """Εσωτερική βοηθητική μέθοδος."""
            return (d is not None) and (today <= d <= window_end)

        items = []  # [{"sort_dt": datetime, "title": str, "meta": [str,...]}]

        # --- Εκθέσεις (start μέσα στο παράθυρο) ---
        try:
            exhibitions = get_upcoming_exhibitions(days_ahead=window_days + 2, limit=200) or []
        except Exception:
            exhibitions = []

        for ev in exhibitions:
            s_iso = (ev.get("start_date") or "").strip()
            e_iso = (ev.get("end_date") or "").strip() or s_iso
            s_d = _parse_iso_date(s_iso)
            if not _in_window(s_d):
                continue

            start_nice = _nice_date(s_iso)
            end_nice = _nice_date(e_iso)
            if end_nice == start_nice:
                period_text = f"Ημερομηνία: {start_nice}"
            else:
                period_text = f"Περίοδος: {start_nice} – {end_nice}"

            items.append({
                "sort_dt": datetime.combine(s_d, datetime.min.time()),
                "title": f"🖼️ Έκθεση: {ev.get('title','')}",
                "meta": [
                    period_text,
                    f"Έργα: {ev.get('num_works', 0)}",
                ],
            })

        # --- Επιστροφές δανεισμών (due μέσα στο παράθυρο) ---
        try:
            loans = get_due_loans_for_calendar() or []
        except Exception:
            loans = []

        for x in loans:
            due_iso = (x.get("due_date") or "").strip()
            d = _parse_iso_date(due_iso)
            if not _in_window(d):
                continue

            borrower = (x.get("borrower_name") or "").strip()
            direction = (x.get("direction") or "OUT").upper()
            meta = f"Έργο: {x.get('work_title','')} · {direction}"
            if borrower:
                meta += f" · {borrower}"

            items.append({
                "sort_dt": datetime.combine(d, datetime.min.time()),
                "title": "🔁 Επιστροφή δανεισμού",
                "meta": [
                    f"Ημερομηνία: {_nice_date(due_iso)}",
                    meta,
                ],
            })

        # --- Συντήρηση (range που τέμνει το παράθυρο) ---
        try:
            maints = get_maintenance_for_calendar() or []
        except Exception:
            maints = []

        for m in maints:
            s_iso = (m.get("start") or "").strip()
            if not s_iso:
                continue
            e_iso = (m.get("end") or "").strip() or s_iso

            s_d = _parse_iso_date(s_iso)
            e_d = _parse_iso_date(e_iso) or s_d
            if not s_d or not e_d:
                continue

            # overlap με [today, window_end]
            if s_d > window_end or e_d < today:
                continue

            start_nice = _nice_date(s_iso)
            end_nice = _nice_date(e_iso)
            period_text = (
                f"Περίοδος: {start_nice} – {end_nice}" if end_nice != start_nice else f"Ημερομηνία: {start_nice}"
            )

            cons = (m.get("conservator_name") or "").strip()
            work_title = (m.get("work_title") or "").strip()
            mtype = (m.get("type") or "").strip()

            meta_lines = [period_text]
            if work_title or mtype:
                meta_lines.append(f"Έργο: {work_title} · {mtype}".strip(" ·"))
            if cons:
                meta_lines.append(f"Συντηρητής: {cons}")

            # sort με βάση την πρώτη ημέρα που “φαίνεται” στο παράθυρο
            sort_d = s_d if s_d >= today else today
            items.append({
                "sort_dt": datetime.combine(sort_d, datetime.min.time()),
                "title": "🛠️ Συντήρηση",
                "meta": meta_lines,
            })

        # --- Ξεναγήσεις (start_dt μέσα στο παράθυρο) ---
        try:
            sessions = get_tour_sessions("all") or []
        except Exception:
            sessions = []

        for s in sessions:
            status = (s.get("status") or "").strip().lower()
            if status in ("canceled", "cancelled", "completed"):
                continue

            start_dt = (s.get("start_dt") or "").strip()
            if not start_dt:
                continue

            try:
                dt = datetime.fromisoformat(start_dt)
            except Exception:
                try:
                    dt = datetime.strptime(start_dt, "%Y-%m-%d %H:%M")
                except Exception:
                    continue

            if not _in_window(dt.date()):
                continue

            end_dt = (s.get("end_dt") or "").strip()
            end_txt = ""
            if end_dt:
                try:
                    edt = datetime.fromisoformat(end_dt)
                    end_txt = edt.strftime("%H:%M")
                except Exception:
                    try:
                        edt = datetime.strptime(end_dt, "%Y-%m-%d %H:%M")
                        end_txt = edt.strftime("%H:%M")
                    except Exception:
                        end_txt = ""

            when = dt.strftime("%d/%m/%Y %H:%M")
            if end_txt:
                when += f" – {end_txt}"

            tour_type = (s.get("tour_type") or "Ξενάγηση").strip()
            lang = (s.get("language") or "").strip()
            guide = (s.get("guide_name") or "").strip()
            extra = " · ".join([p for p in [lang, guide] if p])

            meta_lines = [f"Ώρα: {when}"]
            if extra:
                meta_lines.append(extra)

            ex_title = (s.get("exhibition_title") or "").strip()
            if ex_title:
                meta_lines.append(f"Έκθεση: {ex_title}")

            items.append({
                "sort_dt": dt,
                "title": f"🧭 {tour_type}",
                "meta": meta_lines,
            })

        # sort + limit
        items.sort(key=lambda x: x["sort_dt"])
        items = items[:15]

        # ---------- UI ----------
        dlg = QDialog(self)
        dlg.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        dlg.setAttribute(Qt.WA_TranslucentBackground, False)
        dlg.setStyleSheet(
            """
        QDialog {
            background-color: #ffffff;
            border-radius: 12px;
            border: 1px solid #d0d7e2;
        }
        QLabel#notifTitle {
            font-size: 11pt;
            font-weight: 600;
            color: #151d2a;
        }
        QLabel#notifItemTitle {
            font-size: 9pt;
            font-weight: 500;
            color: #151d2a;
        }
        QLabel#notifItemMeta {
            font-size: 8pt;
            color: #7a7f8a;
        }
        """
        )

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        title = QLabel("Ειδοποιήσεις (επόμενες 7 ημέρες)")
        title.setObjectName("notifTitle")
        layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        if not items:
            info = QLabel("Δεν υπάρχουν γεγονότα στις επόμενες 7 ημέρες.")
            info.setObjectName("notifItemMeta")
            layout.addWidget(info)
        else:
            for it in items:
                item_frame = QFrame()
                item_layout = QVBoxLayout(item_frame)
                item_layout.setContentsMargins(0, 4, 0, 4)
                item_layout.setSpacing(0)

                lbl_title = QLabel(it["title"])
                lbl_title.setObjectName("notifItemTitle")
                item_layout.addWidget(lbl_title)

                for line_txt in it.get("meta", [])[:3]:
                    lbl_meta = QLabel(line_txt)
                    lbl_meta.setObjectName("notifItemMeta")
                    item_layout.addWidget(lbl_meta)

                layout.addWidget(item_frame)

        layout.addStretch()

        btn = self.ui.pushButton
        global_pos = btn.mapToGlobal(btn.rect().bottomRight())

        dlg.adjustSize()
        popup_width = dlg.width()
        x = global_pos.x() - popup_width + btn.width()
        y = global_pos.y() + 8

        dlg.move(x, y)
        dlg.exec()


    # ---------------------------------------------------------
    # CALENDAR HIGHLIGHT + INFO
    # ---------------------------------------------------------
    def _update_calendar_filter_styles(self):
        """Εσωτερική βοηθητική μέθοδος."""
        mapping = {
            self.cb_cal_exhibitions: "#f6c26b",  # πορτοκαλί
            self.cb_cal_loans: "#ff6b6b",        # κόκκινο
            self.cb_cal_maintenance: "#6fa8dc",  # μπλε
            self.cb_cal_tours: "#7bd389",        # πράσινο
        }
        for cb, color in mapping.items():
            if cb.isChecked():
                cb.setStyleSheet(
                    f"""
                    QCheckBox {{
                        color: {color};
                        font-weight: 700;
                    }}
                    QCheckBox::indicator:checked {{
                        background-color: {color};
                        border: 1px solid {color};
                    }}
                    """
                )
            else:
                cb.setStyleSheet(
                    """
                    QCheckBox { color: #6b7280; font-weight: 500; }
                    QCheckBox::indicator:unchecked { background: #fff; border: 1px solid #9ca3af; }
                    """
                )

    def _on_calendar_filters_changed(self, *args):
        """Εσωτερική βοηθητική μέθοδος."""
        self._update_calendar_filter_styles()
        self.refresh_calendar_events()

    def _add_calendar_event(self, date_str: str, kind: str, text: str):
        # kind: "exhibitions" | "loans" | "maintenance" | "tours"
        """Εσωτερική βοηθητική μέθοδος."""
        self.calendar_events_by_date.setdefault(date_str, {}).setdefault(kind, []).append(text)

    def _qdate_from_iso(self, iso: str) -> QDate | None:
        """Εσωτερική βοηθητική μέθοδος."""
        try:
            y, m, d = map(int, iso.split("-"))
            return QDate(y, m, d)
        except Exception:
            return None

    def refresh_calendar_events(self):
        """
        Χρωματίζει ημερολόγιο με βάση toggles:
        - Εκθέσεις (πορτοκαλί)
        - Επιστροφές δανεισμών (κόκκινο)
        - Συντήρηση (μπλε, range start→end)
        - Ξεναγήσεις (πράσινο)
        """
        self.calendar_events_by_date = {}

        # 1) καθάρισμα formats
        self.ui.calendarWidget_2.setDateTextFormat(QDate(), QTextCharFormat())

        # 2) μάζεμα events ανά toggle
        if self.cb_cal_exhibitions.isChecked():
            for date_str, title in get_all_exhibition_dates():
                if date_str:
                    self._add_calendar_event(date_str, "exhibitions", title)

        if self.cb_cal_loans.isChecked():
            for x in get_due_loans_for_calendar():
                due = (x.get("due_date") or "").strip()
                if not due:
                    continue
                borrower = (x.get("borrower_name") or "").strip()
                direction = (x.get("direction") or "OUT").upper()
                label = f'{x.get("work_title","")} · {direction}'
                if borrower:
                    label += f' · {borrower}'
                self._add_calendar_event(due, "loans", label)

        if self.cb_cal_maintenance.isChecked():
            for m in get_maintenance_for_calendar():
                start = (m.get("start") or "").strip()
                if not start:
                    continue
                end = (m.get("end") or "").strip() or start

                # range highlight: start → end (inclusive)
                qs = self._qdate_from_iso(start)
                qe = self._qdate_from_iso(end)
                if not qs or not qe:
                    continue

                # περιγραφή για tooltip/info
                cons = (m.get("conservator_name") or "").strip()
                label = f'{m.get("work_title","")} · {m.get("type","")}'
                if cons:
                    label += f' · {cons}'

                d = qs
                while d <= qe:
                    key = d.toString("yyyy-MM-dd")
                    self._add_calendar_event(key, "maintenance", label)
                    d = d.addDays(1)

        if self.cb_cal_tours.isChecked():
            # πάρε όλες τις ξεναγήσεις
            sessions = get_tour_sessions("all")
            for s in sessions:
                start_dt = (s.get("start_dt") or "").strip()
                if not start_dt:
                    continue
                date_str = start_dt.split(" ")[0]  # YYYY-MM-DD
                status = (s.get("status") or "").strip()
                # αν θες, κρύβεις canceled:
                if status.lower() == "canceled":
                    continue
                label = f'{s.get("tour_type","")} · {s.get("language","")} · {s.get("guide_name","")}'
                self._add_calendar_event(date_str, "tours", label)


            #δώσε τα events στο custom calendar για να ζωγραφίσει dots
            if hasattr(self.ui.calendarWidget_2, "set_events"):
                self.ui.calendarWidget_2.set_events(self.calendar_events_by_date)

        
            

    def on_calendar_date_selected(self):
        """Ενημερώνει το label πληροφοριών όταν αλλάζει η επιλεγμένη ημερομηνία."""
        selected_date = self.ui.calendarWidget_2.selectedDate()
        date_str = selected_date.toString("yyyy-MM-dd")

        info = self.calendar_events_by_date.get(date_str)
        if not info:
            self.calendarInfoLabel.setText(f"📅 {date_str}: Δεν υπάρχουν γεγονότα.")
            return

        parts = [f"📅 {date_str}:"]
        if "exhibitions" in info:
            parts.append("• Εκθέσεις: " + " | ".join(info["exhibitions"]))
        if "loans" in info:
            parts.append("• Επιστροφές: " + " | ".join(info["loans"]))
        if "maintenance" in info:
            parts.append("• Συντήρηση: " + " | ".join(info["maintenance"]))
        if "tours" in info:
            parts.append("• Ξεναγήσεις: " + " | ".join(info["tours"]))

        self.calendarInfoLabel.setText("\n".join(parts))


    def eventFilter(self, obj, event):
        # Hover πάνω στο calendar για tooltips
        """Μέθοδος βοηθητικής λειτουργίας."""
        if hasattr(self, "calendar_view") and self.calendar_view is not None:
            if obj is self.calendar_view.viewport() and event.type() == QEvent.MouseMove:
                index = self.calendar_view.indexAt(event.pos())
                if index.isValid():
                    day = index.data()
                    if not isinstance(day, int):
                        QToolTip.hideText()
                        return False

                    row = index.row()
                    month = self.ui.calendarWidget_2.monthShown()
                    year = self.ui.calendarWidget_2.yearShown()

                    # previous / next month
                    if row == 0 and day > 20:
                        month -= 1
                        if month == 0:
                            month = 12
                            year -= 1
                    elif row >= 4 and day <= 14:
                        month += 1
                        if month == 13:
                            month = 1
                            year += 1

                    hovered_date = QDate(year, month, day)
                    key = hovered_date.toString("yyyy-MM-dd")

                    info = getattr(self, "calendar_events_by_date", {}).get(key)

                    if info:
                        lines = [f"{hovered_date.toString('dd/MM/yyyy')}"]

                        if "loans" in info:
                            lines.append("Επιστροφές:")
                            lines += [f"• {t}" for t in info["loans"][:4]]
                            if len(info["loans"]) > 4:
                                lines.append(f"… (+{len(info['loans'])-4})")

                        if "maintenance" in info:
                            lines.append("Συντήρηση:")
                            lines += [f"• {t}" for t in info["maintenance"][:3]]
                            if len(info["maintenance"]) > 3:
                                lines.append(f"… (+{len(info['maintenance'])-3})")

                        if "tours" in info:
                            lines.append("Ξεναγήσεις:")
                            lines += [f"• {t}" for t in info["tours"][:3]]
                            if len(info["tours"]) > 3:
                                lines.append(f"… (+{len(info['tours'])-3})")

                        if "exhibitions" in info:
                            lines.append("Εκθέσεις:")
                            lines += [f"• {t}" for t in info["exhibitions"][:3]]
                            if len(info["exhibitions"]) > 3:
                                lines.append(f"… (+{len(info['exhibitions'])-3})")

                        text = "\n".join(lines)
                        global_pos = self.calendar_view.viewport().mapToGlobal(event.pos())
                        QToolTip.showText(global_pos, text)
                    else:
                        QToolTip.hideText()

                else:
                    QToolTip.hideText()
                return False

        return super().eventFilter(obj, event)


    def open_artists_popup(self):
        # callback που θα εφαρμόσει φίλτρο στα έργα
        """Ανοίγει dialog/popup για την αντίστοιχη λειτουργία."""
        def apply_artist(name: str):
            # Γράφει στο search των έργων και κάνει refresh το gallery
            """Μέθοδος βοηθητικής λειτουργίας."""
            self.works_search_edit.setText(name)
            self.load_works_gallery()

        popup = ArtistBrowserPopup(parent=self, apply_callback=apply_artist)
        popup.open_below(self.btn_artists_popup)


    def open_selected_exhibition_details(self):
        """Ανοίγει dialog/popup για την αντίστοιχη λειτουργία."""
        ex_id, _ = self.get_selected_exhibition()
        if ex_id is None:
            return

        ex_list = get_all_exhibitions()
        ex = next((e for e in ex_list if e["id"] == ex_id), None)
        if not ex:
            return

        works = get_exhibition_works(ex_id)
        dlg = ExhibitionDetailsDialog(self, exhibition=ex, works=works)
        dlg.exec()


    def open_ai_exhibition_dialog(self):
        """Ανοίγει dialog/popup για την αντίστοιχη λειτουργία."""
        self._ai_dlg = AIExhibitionDialog(self, proposal=None)
        self._ai_dlg.set_loading(True)
        self._ai_cancelled = False

        self._ai_thread = QThread(self._ai_dlg)  # cleanup μαζί με το dialog
        self._ai_worker = AIProposalWorker(self.generate_ai_exhibition_mock)
        self._ai_worker.moveToThread(self._ai_thread)

        # Αν κλείσει/ακυρώσει, μη γίνει UI update μετά
        def _cancel():
            """Εσωτερική βοηθητική μέθοδος."""
            self._ai_cancelled = True
            self._ai_thread.quit()

        self._ai_dlg.rejected.connect(_cancel)
        self._ai_dlg.finished.connect(_cancel)

        self._ai_thread.started.connect(self._ai_worker.run)

        # ΣΗΜΑΝΤΙΚΟ: συνδέουμε σε QObject slots (όχι lambda / inner function)
        self._ai_worker.finished.connect(self._ai_finished)
        self._ai_worker.failed.connect(self._ai_failed)

        self._ai_worker.finished.connect(self._ai_worker.deleteLater)
        self._ai_thread.finished.connect(self._ai_thread.deleteLater)

        self._ai_thread.start()

        if self._ai_dlg.exec():
            data = getattr(self._ai_dlg, "proposal_data", None)
            # Fallback: αν δεν έχει dict, προσπάθησε να κάνεις parse από το textbox
            if not isinstance(data, dict):
                try:
                    import json
                    raw = self._ai_dlg.text.toPlainText().strip()
                    raw = raw[raw.find("{"): raw.rfind("}") + 1]  # κόβει τυχόν extra κείμενο
                    data = json.loads(raw)
                    self._ai_dlg.proposal_data = data  # αποθήκευσέ το για σιγουριά
                except Exception:
                    data = None   
            if not isinstance(data, dict):
                
                QMessageBox.warning(self, "Έκθεση", "Δεν υπάρχει έγκυρη πρόταση για αποθήκευση.")
                return

            selected = data.get("selected_works", []) or []
            ex_id = add_exhibition_returning_id(
                title=data.get("title", "Νέα Έκθεση"),
                start_date=data.get("start_date", ""),
                end_date=data.get("end_date", ""),
                num_works=len(selected),
                description=data.get("description", ""),
            )
            add_exhibition_works(ex_id, selected)

            if hasattr(self, "load_exhibitions_tables"):
                self.load_exhibitions_tables()

            QMessageBox.information(self, "Έκθεση", f"Αποθηκεύτηκε η έκθεση (ID: {ex_id}).")


    
    def generate_ai_exhibition_mock(self) -> dict:
        """Ζητά από το OpenAI μια πρόταση έκθεσης και επιστρέφει dict.

        Προϋπόθεση: το OPENAI_API_KEY να υπάρχει στο περιβάλλον.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Λείπει το OPENAI_API_KEY στο περιβάλλον.")

        client = OpenAI(api_key=api_key)

        works = get_all_works()
        if not works:
            raise RuntimeError("Δεν υπάρχουν έργα για να προταθεί έκθεση.")

        # Όριο για ταχύτητα/κόστος.
        works = works[:80]
        works_lines = "\n".join(
            f'{w["id"]}: {w["title"]} — {w.get("artist_name","")} ({w.get("year") or "?"})'
            for w in works
        )

        today = date.today()
        prompt = f"""
ΣΗΜΕΡΑ ΕΙΝΑΙ: {today.isoformat()}.
Είσαι επιμελητής μουσείου. Με βάση τη λίστα έργων, πρότεινε 1 νέα έκθεση.

ΕΠΙΣΤΡΕΨΕ ΜΟΝΟ ΕΓΚΥΡΟ JSON (χωρίς markdown, χωρίς σχόλια, χωρίς extra κείμενο) με αυτό ακριβώς το σχήμα:
{{
  "title": "string",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "description": "string",
  "selected_works": [1,2,3]
}}

Κανόνες:
- start_date: από {today.isoformat()} έως {(today + timedelta(days=30)).isoformat()}
- end_date: 5–30 μέρες μετά το start_date
- selected_works: 10 έως 25 έργα, ΜΟΝΟ από τα IDs που δίνω.

ΛΙΣΤΑ ΕΡΓΩΝ:
{works_lines}
""".strip()

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Είσαι επιμελητής τέχνης. Απάντησε στα ελληνικά."},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=1500,
        )

        content = (response.choices[0].message.content or "").strip()
        if not content:
            raise RuntimeError("Κενή απάντηση από το AI.")

        # Αν βάλει extra κείμενο, κράτα μόνο το JSON ανάμεσα σε { ... }.
        if "{" in content and "}" in content:
            content = content[content.find("{") : content.rfind("}") + 1]

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Μη έγκυρο JSON από το AI: {e}") from e

        #ημερομηνιών ώστε να μην πέφτει σε παλιά/ανάποδα ranges.
        try:
            sd = date.fromisoformat(str(data.get("start_date", "")).strip())
            ed = date.fromisoformat(str(data.get("end_date", "")).strip())
        except Exception:
            sd = today + timedelta(days=7)
            ed = sd + timedelta(days=14)

        if sd < today:
            sd = today + timedelta(days=7)
        if ed <= sd:
            ed = sd + timedelta(days=14)

        days = (ed - sd).days
        if days < 5:
            ed = sd + timedelta(days=5)
        elif days > 30:
            ed = sd + timedelta(days=30)

        data["start_date"] = sd.isoformat()
        data["end_date"] = ed.isoformat()

        return data


    @Slot(object)
    def _ai_finished(self, data):
        """Slot: ενημερώνει το AI dialog όταν ολοκληρωθεί η παραγωγή πρότασης."""
        if getattr(self, "_ai_cancelled", False):
            return

        proposal = data
        #Ο worker μπορεί να επιστρέψει dict ή JSON string ή list με work_ids (ανάλογα με το prompt/format).
        if isinstance(proposal, str):
            try:
                proposal = json.loads(proposal)
            except Exception:
                proposal = {"raw_text": proposal}

        if isinstance(proposal, list):
            proposal = {"selected_works": proposal}

        if not isinstance(proposal, dict):
            proposal = {"raw": proposal}

        works = proposal.get("selected_works")
        if isinstance(works, list):
            normalized = []
            for w in works:
                if isinstance(w, dict):
                    normalized.append(w)
                else:
                    normalized.append({"work_id": w})
            proposal["selected_works"] = normalized

        self._ai_dlg.set_proposal(proposal)
        self._ai_dlg.set_loading(False)
        self._ai_thread.quit()
    @Slot(str)
    def _ai_failed(self, msg):
        """Slot: εμφανίζει σφάλμα στο AI dialog όταν αποτύχει η παραγωγή πρότασης."""
        if getattr(self, "_ai_cancelled", False):
            return
        self._ai_dlg.set_proposal({
            "title": "",
            "start_date": "",
            "end_date": "",
            "description": "❌ Σφάλμα: " + msg,
            "selected_works": []
        })
        self._ai_dlg.set_loading(False)
        self._ai_thread.quit()

            
            

    # EXHIBITIONS TABS (Επερχόμενες / Παλιές)

    def load_exhibitions_tables(self):
        """Φορτώνει/ανανεώνει δεδομένα στο αντίστοιχο UI στοιχείο."""
        exhibitions = get_all_exhibitions()
        today = date.today()

        upcoming = []
        past = []

        for ex in exhibitions:
            # ημερομηνία έναρξης (fallback αν κάτι πάει στραβά)
            try:
                start_date = date.fromisoformat(ex["start_date"])
            except Exception:
                start_date = today

            # αν έχουμε λήξη, την χρησιμοποιούμε για σύγκριση
            end_str = ex.get("end_date")
            if end_str:
                try:
                    end_date = date.fromisoformat(end_str)
                except Exception:
                    end_date = start_date
            else:
                end_date = start_date

            # ΚΡΙΤΗΡΙΟ:
            #   αν end_date >= today  -> Επερχόμενη
            #   αν end_date <  today  -> Παλιά
            if end_date >= today:
                upcoming.append(ex)
            else:
                past.append(ex)


        self.exhibition_ids_upcoming = [e["id"] for e in upcoming]
        self.exhibition_ids_past = [e["id"] for e in past]

        def format_period(start_str, end_str):
            # format έναρξης
            """Μέθοδος βοηθητικής λειτουργίας."""
            try:
                y1, m1, d1 = map(int, start_str.split("-"))
                q1 = QDate(y1, m1, d1)
                start_nice = q1.toString("dd/MM/yyyy")
            except Exception:
                start_nice = start_str

            # αν δεν έχει end_date, θεωρούμε ίδια μέρα
            if not end_str:
                return start_nice

            try:
                y2, m2, d2 = map(int, end_str.split("-"))
                q2 = QDate(y2, m2, d2)
                end_nice = q2.toString("dd/MM/yyyy")
            except Exception:
                end_nice = end_str

            if end_nice == start_nice:
                return start_nice
            return f"{start_nice} - {end_nice}"

        # UPCOMING
        # UPCOMING
        self.table_upcoming.setRowCount(len(upcoming))
        for row, ex in enumerate(upcoming):
            period = format_period(ex["start_date"], ex["end_date"])
            num_works_str = str(ex["num_works"])
            desc_plain = html_preview(ex["description"])

            curator = ex.get("curator_name") or "—"
            max_seats = ex.get("max_seats")
            reserved = ex.get("reserved_seats", 0) or 0

            max_seats_txt = "—" if not max_seats else str(max_seats)
            reserved_txt = f"{reserved}/{max_seats}" if max_seats else str(reserved)

            self.table_upcoming.setItem(row, 0, QTableWidgetItem(str(ex["id"])))
            self.table_upcoming.setItem(row, 1, QTableWidgetItem(ex["title"]))
            self.table_upcoming.setItem(row, 2, QTableWidgetItem(period))
            self.table_upcoming.setItem(row, 3, QTableWidgetItem(curator))
            self.table_upcoming.setItem(row, 4, QTableWidgetItem(max_seats_txt))
            self.table_upcoming.setItem(row, 5, QTableWidgetItem(reserved_txt))
            self.table_upcoming.setItem(row, 6, QTableWidgetItem(num_works_str))
            self.table_upcoming.setItem(row, 7, QTableWidgetItem(desc_plain))

        self.table_upcoming.resizeColumnsToContents()

        # PAST

        self.table_past.setRowCount(len(past))
        for row, ex in enumerate(past):
            period = format_period(ex["start_date"], ex["end_date"])
            num_works_str = str(ex["num_works"])
            desc_plain = html_preview(ex["description"])

            curator = ex.get("curator_name") or "—"
            max_seats = ex.get("max_seats")
            reserved = ex.get("reserved_seats", 0) or 0

            max_seats_txt = "—" if not max_seats else str(max_seats)
            reserved_txt = f"{reserved}/{max_seats}" if max_seats else str(reserved)

            self.table_past.setItem(row, 0, QTableWidgetItem(str(ex["id"])))
            self.table_past.setItem(row, 1, QTableWidgetItem(ex["title"]))
            self.table_past.setItem(row, 2, QTableWidgetItem(period))
            self.table_past.setItem(row, 3, QTableWidgetItem(curator))
            self.table_past.setItem(row, 4, QTableWidgetItem(max_seats_txt))
            self.table_past.setItem(row, 5, QTableWidgetItem(reserved_txt))
            self.table_past.setItem(row, 6, QTableWidgetItem(num_works_str))
            self.table_past.setItem(row, 7, QTableWidgetItem(desc_plain))


        self.table_past.resizeColumnsToContents()

    def get_selected_exhibition(self):
        """Επιστρέφει (ex_id, από ποιο tab) ή (None, None)."""
        current_tab = self.exhibitions_tabs.currentWidget()
        if current_tab is self.tab_upcoming:
            table = self.table_upcoming
            ids = getattr(self, "exhibition_ids_upcoming", [])
        else:
            table = self.table_past
            ids = getattr(self, "exhibition_ids_past", [])

        sel = table.selectionModel().selectedRows()
        if not sel:
            return None, None

        row = sel[0].row()
        if row < 0 or row >= len(ids):
            return None, None

        return ids[row], current_tab

    def add_exhibition_dialog(self):
        """UI handler για δημιουργία νέας εγγραφής."""
        dlg = ExhibitionDialog(self, exhibition=None)
        if dlg.exec() != QDialog.Accepted:
            return

        title, start_str, end_str, _num_works_ignored, desc, curator_id, max_seats = dlg.get_data()
        items = getattr(dlg, "selected_works", []) or []

        if not title.strip():
            QMessageBox.warning(self, "Σφάλμα", "Ο τίτλος είναι υποχρεωτικός.")
            return
        if not items:
            QMessageBox.warning(self, "Σφάλμα", "Πρέπει να επιλέξεις τουλάχιστον 1 έργο.")
            return

        ex_id = add_exhibition_returning_id(title, start_str, end_str, len(items), desc, curator_id, max_seats)
        set_exhibition_works(ex_id, items)

        self.refresh_exhibitions_data()





    def edit_selected_exhibition(self):
        """UI handler για επεξεργασία/ενημέρωση επιλεγμένης εγγραφής."""
        ex_id, _ = self.get_selected_exhibition()
        if ex_id is None:
            QMessageBox.information(self, "Πληροφορία", "Επέλεξε πρώτα μια έκθεση.")
            return

        exhibitions = get_all_exhibitions()
        ex = next((e for e in exhibitions if e["id"] == ex_id), None)
        if not ex:
            QMessageBox.warning(self, "Σφάλμα", "Δεν βρέθηκε η έκθεση.")
            return

        dlg = ExhibitionDialog(self, exhibition=ex)
        if dlg.exec() != QDialog.Accepted:
            return

        title, start_str, end_str, _num_works_ignored, desc, curator_id, max_seats = dlg.get_data()
        items = getattr(dlg, "selected_works", []) or []

        if not title.strip():
            QMessageBox.warning(self, "Σφάλμα", "Ο τίτλος είναι υποχρεωτικός.")
            return
        if not items:
            QMessageBox.warning(self, "Σφάλμα", "Η έκθεση πρέπει να έχει τουλάχιστον 1 έργο.")
            return

        update_exhibition(ex_id, title, start_str, end_str, len(items), desc, curator_id, max_seats)
        set_exhibition_works(ex_id, items)

        self.refresh_exhibitions_data()




    def delete_selected_exhibition(self):
        """UI handler για διαγραφή επιλεγμένης εγγραφής."""
        ex_id, _ = self.get_selected_exhibition()
        if ex_id is None:
            QMessageBox.information(self, "Πληροφορία", "Επέλεξε πρώτα μια έκθεση.")
            return

        reply = QMessageBox.question(
            self,
            "Διαγραφή",
            "Είσαι σίγουρος ότι θέλεις να διαγράψεις αυτή την έκθεση;",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            delete_exhibition(ex_id)
            self.refresh_exhibitions_data()

    def refresh_exhibitions_data(self):
        """Ανανέωση tabs, calendar, notifications και card counter."""
        self.load_exhibitions_tables()
        self.refresh_calendar_events()
        self.ui.label_6.setText(str(get_exhibitions_count_this_month_upcoming()))


    # ΕΡΓΑ – TABLES & CRUD

    
    def _update_filter_button_text(self):
        """Ενημερώνει το κείμενο στο κουμπί φίλτρου ανάλογα με τα ενεργά φίλτρα."""
        parts = []
        if self.filter_category_label:
            parts.append(self.filter_category_label)
        if self.filter_hall_label:
            parts.append(self.filter_hall_label)
        if getattr(self, "filter_loan_label", None):
            parts.append(self.filter_loan_label)


        if not parts:
            text = "Φίλτρο: Όλα τα έργα"
        else:
            text = "Φίλτρο: " + " · ".join(parts)

        self.filter_button.setText(text)

    def set_category_filter(self, category_value, label_text):
        """category_value: 'Πίνακας', 'Γλυπτό' ή None (για όλες)."""
        self.filter_category = category_value
        self.filter_category_label = label_text
        self._update_filter_button_text()
        self.load_works_gallery()

    def set_hall_filter(self, hall_id, hall_label):
        """hall_id: id αίθουσας ή None (για όλες)."""
        self.filter_hall_id = hall_id
        self.filter_hall_label = hall_label
        self._update_filter_button_text()
        self.load_works_gallery()

    def set_loan_filter(self, loan_filter_value, label_text):
        """
        loan_filter_value: None | 'BORROWED' | 'SOON' | 'OVERDUE'
        """
        self.filter_loan = loan_filter_value
        self.filter_loan_label = label_text

        # ✅ Τα δανεισμένα τα βγάζουμε "εκτός αίθουσας" (hall_id=None),
        # οπότε αν υπάρχει φίλτρο αίθουσας θα τα κρύβει. Καθαρίζουμε την αίθουσα.
        if loan_filter_value in ("BORROWED", "SOON", "OVERDUE"):
            self.filter_hall_id = None
            self.filter_hall_label = None

            # (προαιρετικό) αν θες να καθαρίζει και την κατηγορία:
            # self.filter_category = None
            # self.filter_category_label = None

        self._update_filter_button_text()
        self.load_works_gallery()



    def reset_gallery_filters(self):
        """Καθαρισμός όλων των φίλτρων (κατηγορία + αίθουσα)."""
        self.filter_category = None
        self.filter_category_label = None
        self.filter_hall_id = None
        self.filter_hall_label = None
        self.filter_loan = None
        self.filter_loan_label = None

        self._update_filter_button_text()
        self.load_works_gallery()




 
    def load_works_gallery(self):

        """Φορτώνει όλα τα έργα στο QListWidget της gallery."""
        all_works = get_all_works()  # πρέπει να επιστρέφει και artist_* + hall_name
        text = self.works_search_edit.text().strip().lower()
        
        # τρέχον φίλτρο κατηγορίας / αίθουσας (από το κουμπί)
        cat_filter = getattr(self, "filter_category", None)
        hall_filter_id = getattr(self, "filter_hall_id", None)
        loan_filter = getattr(self, "filter_loan", None)




        self.works_list.clear()
        self.work_ids = []

        for w in all_works:
            # φίλτρο αναζήτησης (τίτλος + καλλιτέχνης)
            hay = f"{w['title']} {w.get('artist_name', '')}".lower()
            if text and text not in hay:
                continue

            # φίλτρο κατηγορίας (π.χ. μόνο Πίνακες / μόνο Γλυπτά)
            if cat_filter is not None:
                work_cat = (w.get("category") or "").strip()
                if work_cat != cat_filter:
                    continue

            # φίλτρο αίθουσας (π.χ. μόνο Αίθουσα 1)
            if hall_filter_id is not None:
                if w.get("hall_id") != hall_filter_id:
                    continue


            item = QListWidgetItem()

            # ✅ ΠΑΝΤΑ πρώτα ορίζουμε loan fields, πριν τα χρησιμοποιήσουμε
            active_loan_id = w.get("active_loan_id")
            loan_end = (w.get("loan_end_date") or w.get("end_date") or "").strip()
            loan_direction = (w.get("loan_direction") or "OUT").upper()   # "IN" / "OUT"
            is_external = int(w.get("is_external") or 0)

            # --- 1η γραμμή: Τίτλος έργου (με emoji IN/OUT αν υπάρχει ενεργός δανεισμός) ---
            base_title = w["title"]

            if active_loan_id:
                if loan_direction == "IN":
                    line1 = f"📥 {base_title}"
                else:
                    line1 = f"📤 {base_title}"
            else:
                # προαιρετικό: αν είναι external χωρίς ενεργό loan
                if is_external:
                    line1 = f"🌍 {base_title}"
                else:
                    line1 = base_title



            # --- 2η γραμμή: Καλλιτέχνης – Ειδικότητα – Αίθουσα ---

            # πλήρες όνομα καλλιτέχνη
            first = (w.get("artist_first_name") or "").strip()
            last = (w.get("artist_last_name") or "").strip()
            full_name = f"{first} {last}".strip() or w.get("artist_name") or "Άγνωστος καλλιτέχνης"

            spec = (w.get("artist_specialty") or "").strip()
            hall_name = (w.get("hall_name") or "").strip()

            line2 = full_name
            if spec:
                line2 += f" – {spec}"
            if hall_name:
                line2 += f" – {hall_name}"


            # φίλτρο δανεισμού
            active_loan_id = w.get("active_loan_id")
            loan_end = (w.get("loan_end_date") or w.get("end_date") or "").strip()
            loan_direction = (w.get("loan_direction") or "OUT").upper()  # "IN" / "OUT"
            is_external = int(w.get("is_external") or 0)


            loan_status = None  # None | "BORROWED" | "SOON" | "OVERDUE"
            if active_loan_id:
                loan_status = "BORROWED"
                if loan_end:
                    try:
                        y, m, d = map(int, loan_end.split("-"))
                        end_dt = date(y, m, d)
                        today = date.today()
                        if end_dt < today:
                            loan_status = "OVERDUE"
                        elif end_dt <= (today + timedelta(days=7)):
                            loan_status = "SOON"
                    except Exception:
                        pass

            # --- Loan filter (αν το έχεις ενεργό) ---
            loan_filter = getattr(self, "filter_loan", None)
            if loan_filter == "BORROWED" and not active_loan_id:
                continue
            if loan_filter == "OVERDUE" and loan_status != "OVERDUE":
                continue
            if loan_filter == "SOON" and loan_status != "SOON":
                continue

            # --- Badge text (μόνο αν είναι δανεισμένο) ---
            badge = ""
            if active_loan_id:
                borrower = (w.get("borrower_name") or "").strip()
                end_date = (w.get("loan_end_date") or "").strip()

                # ✅ βάση direction
                base_txt = "📥 ΔΑΝΕΙΖΟΜΑΣΤΕ (IN)" if loan_direction == "IN" else "📤 ΔΑΝΕΙΖΟΥΜΕ (OUT)"

                if loan_status == "OVERDUE":
                    status_txt = f"⚠️ {base_txt} (ΕΚΠΡΟΘΕΣΜΟ)"
                elif loan_status == "SOON":
                    status_txt = f"⏳ {base_txt} (ΛΗΓΕΙ ΣΥΝΤΟΜΑ)"
                else:
                    status_txt = base_txt

                extra = ""
                if end_date:
                    extra += f" έως {end_date}"
                if borrower:
                    extra += f" · {borrower}"

                badge = f"\n{status_txt}{extra}"
            else:
                badge = ""


            item.setText(f"{line1}\n{line2}{badge}")


            # --- Εικόνα ---
            pixmap = QPixmap()
            image_path = w.get("image_path")
            if image_path:
                pixmap.load(image_path)
            if pixmap.isNull():
                pixmap = QPixmap(220, 220)
                pixmap.fill(QColor("#333333"))

            item.setIcon(QIcon(pixmap))

            # αποθήκευση id έργου στο item
            item.setData(Qt.UserRole, w["id"])

            # προσθήκη στη λίστα
            self.works_list.addItem(item)
            self.work_ids.append(w["id"])

            self.refresh_dashboard_counters()






    def set_gallery_filter(self, mode, value, label_text):
        """
        mode: "all" | "category" | "hall"
        value: None ή string κατηγορίας ή int hall_id
        """
        self.gallery_filter_mode = mode
        self.gallery_filter_value = value
        self.filter_button.setText(label_text)
        self.load_works_gallery()




    def open_work_from_item(self, item):
        """Ανοίγει dialog/popup για την αντίστοιχη λειτουργία."""
        work_id = item.data(Qt.UserRole)
        if work_id is None:
            return

        works = get_all_works()
        w = next((x for x in works if x["id"] == work_id), None)
        if w is None:
            QMessageBox.warning(self, "Σφάλμα", "Δεν βρέθηκε το έργο.")
            return

        dlg = WorkDialog(self, work=w)
        dlg.exec()  # ✅ δεν μας νοιάζει Accepted πλέον

        # ✅ ΠΑΝΤΑ refresh μετά το κλείσιμο
        self.load_works_gallery()
        self.load_works_maintenance()
        if hasattr(self, "reload_loans_table"):
            self.reload_loans_table()






    def add_work_dialog(self):
        """UI handler για δημιουργία νέας εγγραφής."""
        dlg = WorkDialog(self)
        dlg.exec()
        self.load_works_gallery()
        self.load_works_maintenance()







    def delete_selected_work(self):
        """UI handler για διαγραφή επιλεγμένης εγγραφής."""
        item = self.works_list.currentItem()
        if not item:
            QMessageBox.information(self, "Πληροφορία", "Επέλεξε πρώτα ένα έργο.")
            return

        work_id = item.data(Qt.UserRole)
        if work_id is None:
            QMessageBox.warning(self, "Σφάλμα", "Δεν βρέθηκε το ID του έργου.")
            return

        reply = QMessageBox.question(
            self,
            "Διαγραφή έργου",
            "Είσαι σίγουρος ότι θέλεις να διαγράψεις αυτό το έργο;",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        delete_work(work_id)
        self.load_works_gallery()
        self.load_works_maintenance()

        # ---------------- ΚΑΛΛΙΤΕΧΝΕΣ – CRUD από την σελίδα "Έργα" ----------------



    def add_artist_dialog(self):
        """UI handler για δημιουργία νέας εγγραφής."""
        dlg = ArtistDialog(self)
        if dlg.exec() == QDialog.Accepted:
            fn, ln, bd, dd, nat, spec, info = dlg.get_data()
            add_artist(fn, ln, bd, dd, nat, spec, info)
            self.refresh_artist_filter(keep_selection=False)
            self.load_works_gallery()


    def edit_selected_artist(self):
        """UI handler για επεξεργασία/ενημέρωση επιλεγμένης εγγραφής."""
        artist_id = self._get_selected_artist_id()
        if artist_id is None:
            QMessageBox.information(self, "Πληροφορία",
                                    "Επέλεξε πρώτα έναν καλλιτέχνη από τη λίστα.")
            return

        artists = get_all_artists()
        artist = next((a for a in artists if a["id"] == artist_id), None)
        if artist is None:
            QMessageBox.warning(self, "Σφάλμα", "Δεν βρέθηκε ο καλλιτέχνης.")
            return

        dlg = ArtistDialog(self, artist=artist)
        if dlg.exec() == QDialog.Accepted:
            fn, ln, bd, dd, nat, spec, info = dlg.get_data()
            update_artist(artist_id, fn, ln, bd, dd, nat, spec, info)
            self.refresh_artist_filter()
            self.load_works_gallery()

    def delete_selected_artist(self):
        """UI handler για διαγραφή επιλεγμένης εγγραφής."""
        artist_id = self._get_selected_artist_id()
        if artist_id is None:
            QMessageBox.information(self, "Πληροφορία",
                                    "Επέλεξε πρώτα έναν καλλιτέχνη από τη λίστα.")
            return

        reply = QMessageBox.question(
            self,
            "Διαγραφή καλλιτέχνη",
            "Είσαι σίγουρος ότι θέλεις να διαγράψεις αυτόν τον καλλιτέχνη;",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            delete_artist(artist_id)
        except Exception:
            QMessageBox.warning(
                self,
                "Σφάλμα",
                "Δεν ήταν δυνατή η διαγραφή (ίσως υπάρχουν έργα που ανήκουν σε αυτόν τον καλλιτέχνη).",
            )
            return

        self.refresh_artist_filter()
        self.load_works_gallery()

    def load_loans_page(self):
        # Top bar: search + status filter + buttons
        """Φορτώνει/ανανεώνει δεδομένα στο αντίστοιχο UI στοιχείο."""
        top = QHBoxLayout()

        self.loans_search = QLineEdit()
        self.loans_search.setPlaceholderText("Αναζήτηση δανεισμού (έργο / δανειστής / ημερομηνία)...")
        self.loans_search.setFixedHeight(40)
        self.loans_search.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 12pt;
            }
        """)
        

        self.loans_filter = QComboBox()
        self.loans_filter.addItems(["Όλα", "Ενεργά", "Λήγουν σύντομα", "Εκπρόθεσμα", "Ολοκληρωμένα"])
        self.loans_filter.setFixedHeight(36)
        self.loans_filter.setView(QListView())

        # ίδιο look με το φίλτρο των Έργων 
        self.loans_filter.setStyleSheet("""
        QComboBox {
            background-color: #151d2a;
            border-radius: 16px;
            border: 1px solid #394b63;
            color: #ffffff;
            padding: 4px 12px;
            font-weight: 500;
        }
        QComboBox:hover {
            background-color: #1f2a3d;
        }
        QComboBox::drop-down {
            border: 0px;
            width: 22px;
        }
        QComboBox::down-arrow {
            image: none;  /* αν θες, εδώ μπορείς να βάλεις svg */
        }

        /* το dropdown list */
        QComboBox QAbstractItemView {
            background-color: #111827;
            border: 1px solid #374151;
            color: #e5e7eb;
            selection-background-color: #2563eb;
            selection-color: #f9fafb;
            outline: 0;
        }
        """)
        
        self.loans_dir_filter = QComboBox()
        self.loans_dir_filter.addItems(["Όλοι οι τύποι", "Δανείζουμε (OUT)", "Δανειζόμαστε (IN)"])
        self.loans_dir_filter.setFixedHeight(36)
        self.loans_dir_filter.setStyleSheet(self.loans_filter.styleSheet())
        top.addWidget(self.loans_dir_filter)


        self.btn_new_loan = QPushButton("➕ Νέος Δανεισμός")
        self.btn_new_loan.setStyleSheet(COMMON_BTN_STYLE)

        self.btn_manage_borrowers = QPushButton("🏛️ Δανειστές")
        self.btn_manage_borrowers.setStyleSheet(COMMON_BTN_STYLE)

        top.addWidget(self.loans_search, 1)
        top.addWidget(self.loans_filter)
        top.addWidget(self.btn_manage_borrowers)
        top.addWidget(self.btn_new_loan)
        self.layout_loans.addLayout(top)

        # Table
        self.table_loans = QTableWidget()
        self.table_loans.setColumnCount(9)
        self.table_loans.setHorizontalHeaderLabels([
            "ID","Τύπος", "Έργο", "Δανειστής", "Έναρξη", "Λήξη", "Επιστροφή", "Κατάσταση", "Σχόλια"
        ])


        self.table_loans.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_loans.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_loans.horizontalHeader().setStretchLastSection(True)
        self.layout_loans.addWidget(self.table_loans)

        # Action buttons
        actions = QHBoxLayout()
        self.btn_edit_loan = QPushButton("✏️ Επεξεργασία")
        self.btn_return_loan = QPushButton("↩️ Επιστροφή")
        self.btn_delete_loan = QPushButton("🗑️ Διαγραφή")

        for b in (self.btn_edit_loan, self.btn_return_loan, self.btn_delete_loan):
            b.setStyleSheet(COMMON_BTN_STYLE)

        actions.addWidget(self.btn_edit_loan)
        actions.addWidget(self.btn_return_loan)
        actions.addWidget(self.btn_delete_loan)
        actions.addStretch()
        self.layout_loans.addLayout(actions)

        # Signals
        self.loans_search.textChanged.connect(self.reload_loans_table)
        self.loans_filter.currentTextChanged.connect(self.reload_loans_table)
        self.btn_new_loan.clicked.connect(self.add_loan_dialog)
        self.btn_edit_loan.clicked.connect(self.edit_selected_loan)
        self.btn_return_loan.clicked.connect(self.return_selected_loan)
        self.btn_delete_loan.clicked.connect(self.delete_selected_loan)
        self.btn_manage_borrowers.clicked.connect(self.open_borrowers_manager)
        self.loans_dir_filter.currentTextChanged.connect(self.reload_loans_table)

        self.reload_loans_table()

    def reload_loans_table(self):
        """Μέθοδος βοηθητικής λειτουργίας."""
        dir_choice = self.loans_dir_filter.currentText()
        direction = None
        if "OUT" in dir_choice:
            direction = "OUT"
        elif "IN" in dir_choice:
            direction = "IN"

        data = get_loans(
            search_text=self.loans_search.text(),
            status=self.loans_filter.currentText(),
            direction=direction
        )

        self.table_loans.setRowCount(0)

        for loan in data:
            row = self.table_loans.rowCount()
            self.table_loans.insertRow(row)

            dir_txt = loan.get("direction", "OUT")  # OUT/IN από DB
            dir_label = "📤 Δίνουμε" if dir_txt == "OUT" else "📥 Παίρνουμε"

            self.table_loans.setItem(row, 0, QTableWidgetItem(str(loan["id"])))
            self.table_loans.setItem(row, 1, QTableWidgetItem(dir_label))  # ✅ νέα στήλη
            self.table_loans.setItem(row, 2, QTableWidgetItem(f"[{loan['work_id']}] {loan['work_title']}"))
            self.table_loans.setItem(row, 3, QTableWidgetItem(loan.get("borrower_name", "")))
            self.table_loans.setItem(row, 4, QTableWidgetItem(loan.get("start_date", "")))
            self.table_loans.setItem(row, 5, QTableWidgetItem(loan.get("end_date", "")))
            self.table_loans.setItem(row, 6, QTableWidgetItem(loan.get("return_date", "")))
            self.table_loans.setItem(row, 7, QTableWidgetItem(loan.get("status", "")))
            self.table_loans.setItem(row, 8, QTableWidgetItem(loan.get("notes", "")))


    def _selected_loan_id(self):
        """Εσωτερική βοηθητική μέθοδος."""
        r = self.table_loans.currentRow()
        if r < 0:
            return None
        try:
            return int(self.table_loans.item(r, 0).text())
        except Exception:
            return None

    def add_loan_dialog(self):
        """UI handler για δημιουργία νέας εγγραφής."""
        works = get_all_works()
        borrowers = get_all_borrowers()

        dlg = LoanDialog(self, works=works, borrowers=borrowers)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.get_data()

            try:
                add_loan(
                    work_id=d["work_id"],
                    borrower_id=d["borrower_id"],
                    start_date=d["start_date"],
                    end_date=d["end_date"] or None,
                    notes=d["notes"],direction=d.get("direction", "OUT")

                )
                self.reload_loans_table()
                self.load_works_gallery()  # για να ενημερωθεί το gallery αν θες “δανεισμένα”
            except Exception as e:
                QMessageBox.warning(self, "Σφάλμα", str(e))

    def edit_selected_loan(self):
        """UI handler για επεξεργασία/ενημέρωση επιλεγμένης εγγραφής."""
        loan_id = self._selected_loan_id()
        if not loan_id:
            QMessageBox.information(self, "Info", "Επίλεξε δανεισμό.")
            return

        loan = get_loan_by_id(loan_id)
        if not loan:
            return

        works = get_all_works()
        borrowers = get_all_borrowers()

        dlg = LoanDialog(self, works=works, borrowers=borrowers, loan_data=loan, lock_work=True)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.get_data()


            try:
                update_loan(
                    loan_id=loan_id,
                    borrower_id=d["borrower_id"],
                    start_date=d["start_date"],
                    end_date=d["end_date"] or None,
                    notes=d["notes"],direction=d.get("direction", "OUT")
                )
                self.reload_loans_table()
                self.refresh_calendar_events()
                self.load_works_gallery()

            except Exception as e:
                QMessageBox.warning(self, "Σφάλμα", str(e))

    def return_selected_loan(self):
        """Μέθοδος βοηθητικής λειτουργίας."""
        loan_id = self._selected_loan_id()
        if not loan_id:
            QMessageBox.information(self, "Info", "Επίλεξε δανεισμό.")
            return

        if QMessageBox.question(self, "Επιβεβαίωση", "Καταχώρηση επιστροφής;") != QMessageBox.Yes:
            return

        try:
            loan = get_loan_by_id(loan_id)
            if not loan:
                QMessageBox.warning(self, "Σφάλμα", "Δεν βρέθηκε ο δανεισμός.")
                return

            # 1) πρώτα κλείνουμε τον δανεισμό
            mark_loan_returned(loan_id)

            # 2) αν είναι IN (δανειζόμαστε) → διαγράφουμε το έργο
            if (loan.get("direction") == "IN"):
                work_id = loan.get("work_id")
                if work_id:
                    archive_work(work_id)

            # refresh UI
            self.reload_loans_table()
            self.refresh_calendar_events()
            self.load_works_gallery()
            self.load_works_maintenance()

        except Exception as e:
            QMessageBox.warning(self, "Σφάλμα", str(e))


    def delete_selected_loan(self):
        """UI handler για διαγραφή επιλεγμένης εγγραφής."""
        loan_id = self._selected_loan_id()
        if not loan_id:
            QMessageBox.information(self, "Info", "Επίλεξε δανεισμό.")
            return

        if QMessageBox.question(self, "Επιβεβαίωση", "Να διαγραφεί ο δανεισμός;") != QMessageBox.Yes:
            return

        try:
            delete_loan(loan_id)
            self.reload_loans_table()
            self.refresh_calendar_events()
            self.load_works_gallery()
        except Exception as e:
            QMessageBox.warning(self, "Σφάλμα", str(e))

    def open_borrowers_manager(self):
        """Ανοίγει dialog/popup για την αντίστοιχη λειτουργία."""
        dlg = BorrowersManagerDialog(self, db_api={
            "get_all_borrowers": get_all_borrowers,
            "add_borrower": add_borrower,
            "update_borrower": update_borrower,
            "delete_borrower": delete_borrower,
        })
        dlg.exec()

    def _get_guides_list(self) -> list[dict]:

        """Εσωτερική βοηθητική μέθοδος."""
        staff = get_staff()
        return [s for s in staff if (s.get("staff_type") or "").lower() == "guide"]


    def setup_tours_page(self):
        # ---------- Overview cards ----------
        """Μέθοδος βοηθητικής λειτουργίας."""
        top = QFrame(self.page_tours)
        top.setStyleSheet("QFrame { background: transparent; }")
        top_lay = QHBoxLayout(top)
        top_lay.setContentsMargins(0, 0, 0, 0)
        top_lay.setSpacing(10)

        def make_card(title: str) -> tuple[QFrame, QLabel]:
            """Μέθοδος βοηθητικής λειτουργίας."""
            card = QFrame(top)
            card.setStyleSheet(
                """
                QFrame {
                    background-color: #0f1625;
                    border: 1px solid #1f2a3d;
                    border-radius: 10px;
                }
                QLabel { color: white; }
                """
            )
            lay = QVBoxLayout(card)
            lay.setContentsMargins(12, 10, 12, 10)

            lbl_title = QLabel(title)
            lbl_title.setStyleSheet("""
                QLabel {
                    border: none;
                    background: transparent;
                    color: #ffffff;
                    font-size: 14px;
                    font-weight: 600;
                }
            """)

            lbl_value = QLabel("0")
            lbl_value.setStyleSheet("""
                QLabel {
                    border: none;
                    background: transparent;
                    color: #ffffff;
                    font-size: 26px;
                    font-weight: 800;
                }
            """)
            lbl_title.setFrameShape(QFrame.NoFrame)
            lbl_value.setFrameShape(QFrame.NoFrame)



            lay.addWidget(lbl_title)
            lay.addWidget(lbl_value)
            return card, lbl_value

        c1, self.lbl_tours_today = make_card("Σήμερα: Ξεναγήσεις")
        c2, self.lbl_tours_next7 = make_card("Επόμενες 7 ημέρες")
        c3, self.lbl_tours_available = make_card("Διαθέσιμοι ξεναγοί (σήμερα)")
        c4, self.lbl_tours_canceled = make_card("Ακυρώσεις (30 ημέρες)")

        top_lay.addWidget(c1)
        top_lay.addWidget(c2)
        top_lay.addWidget(c3)
        top_lay.addWidget(c4)

        # ---------- Tabs ----------
        self.tabs_tours = QTabWidget(self.page_tours)
        self.tabs_tours.setStyleSheet(
            """
            QTabWidget::pane { border: 1px solid #1f2a3d; border-radius: 10px; }
            QTabBar::tab {
                background: #0f1625;
                color: #a7b4c7;
                padding: 8px 14px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
            }
            QTabBar::tab:selected { color: white; background: #151d2a; }
            """
        )

        # --- Tab 1: Sessions ---
        self.tab_sessions = QWidget()
        v1 = QVBoxLayout(self.tab_sessions)
        v1.setContentsMargins(10, 10, 10, 10)
        v1.setSpacing(10)

        # Filters + CRUD row
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.cmb_sessions_filter = QComboBox()
        self.cmb_sessions_filter.addItems(
            ["Όλα", "Σήμερα", "Εβδομάδα", "Ακυρωμένες", "Με διαθέσιμες θέσεις"]
        )
        self.cmb_sessions_filter.currentIndexChanged.connect(self.set_sessions_filter)
        self.cmb_sessions_filter.setFixedHeight(36)
        self.cmb_sessions_filter.setView(QListView())

        #look φίλτρο 
        self.cmb_sessions_filter.setStyleSheet("""
        QComboBox {
            background-color: #151d2a;
            border-radius: 16px;
            border: 1px solid #394b63;
            color: #ffffff;
            padding: 4px 12px;
            font-weight: 500;
        }
        QComboBox:hover {
            background-color: #1f2a3d;
        }
        QComboBox::drop-down {
            border: 0px;
            width: 22px;
        }
        QComboBox::down-arrow {
            image: none;  /* αν θες, εδώ μπορείς να βάλεις svg */
        }

        /* το dropdown list */
        QComboBox QAbstractItemView {
            background-color: #111827;
            border: 1px solid #374151;
            color: #e5e7eb;
            selection-background-color: #2563eb;
            selection-color: #f9fafb;
            outline: 0;
        }
        """)


        
        self.btn_add_session = QPushButton("Νέα Ξενάγηση")
        self.btn_add_session.setStyleSheet(COMMON_BTN_STYLE)
        self.btn_edit_session = QPushButton("Επεξεργασία")
        self.btn_edit_session.setStyleSheet(COMMON_BTN_STYLE)
        self.btn_delete_session = QPushButton("Διαγραφή")
        self.btn_delete_session.setStyleSheet(COMMON_BTN_STYLE)

        self.btn_add_session.clicked.connect(self.add_tour_session_ui)
        self.btn_edit_session.clicked.connect(self.edit_tour_session_ui)
        self.btn_delete_session.clicked.connect(self.delete_tour_session_ui)

        row1.addWidget(QLabel("Φίλτρο:"))
        
        row1.addWidget(self.cmb_sessions_filter)
        row1.addStretch(1)
        row1.addWidget(self.btn_add_session)
        row1.addWidget(self.btn_edit_session)
        row1.addWidget(self.btn_delete_session)

        v1.addLayout(row1)

        self.table_sessions = QTableWidget()
        self.table_sessions.setColumnCount(9)
        self.table_sessions.setHorizontalHeaderLabels(
            [
                "Ημ/νία & ώρα",
                "Γλώσσα",
                "Ξεναγός",
                "Τύπος",
                "Μέγ. άτομα",
                "Κρατήσεις",
                "Κατάσταση",
                "Έκθεση",
                "Σημειώσεις",
            ]
        )
        
        hdr = self.table_sessions.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Interactive)   # επιτρέπει widths
        hdr.setStretchLastSection(True)

        # 1η στήλη (Ημ/νία & ώρα) 
        self.table_sessions.setColumnWidth(0, 110)

        self.table_sessions.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_sessions.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_sessions.setAlternatingRowColors(True)

        v1.addWidget(self.table_sessions)

        #Tab 2: Guides
        self.tab_guides = QWidget()
        v2 = QVBoxLayout(self.tab_guides)
        v2.setContentsMargins(10, 10, 10, 10)
        v2.setSpacing(10)

        self.table_guides = QTableWidget()
        self.table_guides.setColumnCount(5)
        self.table_guides.setHorizontalHeaderLabels(
            ["Ονοματεπώνυμο", "Γλώσσα", "Ρόλος/Επίπεδο", "Τηλέφωνο", "Email"]
        )
        self.table_guides.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_guides.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_guides.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_guides.setAlternatingRowColors(True)

        v2.addWidget(self.table_guides)

        #Tab 3: Bookings 
        self.tab_bookings = QWidget()
        v3 = QVBoxLayout(self.tab_bookings)
        v3.setContentsMargins(10, 10, 10, 10)
        v3.setSpacing(10)

        row3 = QHBoxLayout()
        row3.setSpacing(8)

        self.btn_add_booking = QPushButton("Νέα Κράτηση")
        self.btn_add_booking.setStyleSheet(COMMON_BTN_STYLE)
        self.btn_edit_booking = QPushButton("Επεξεργασία")
        self.btn_edit_booking.setStyleSheet(COMMON_BTN_STYLE)
        self.btn_delete_booking = QPushButton("Διαγραφή")
        self.btn_delete_booking.setStyleSheet(COMMON_BTN_STYLE)

        self.btn_add_booking.clicked.connect(self.add_booking_ui)
        self.btn_edit_booking.clicked.connect(self.edit_booking_ui)
        self.btn_delete_booking.clicked.connect(self.delete_booking_ui)

        row3.addStretch(1)
        row3.addWidget(self.btn_add_booking)
        row3.addWidget(self.btn_edit_booking)
        row3.addWidget(self.btn_delete_booking)

        v3.addLayout(row3)

        self.table_bookings = QTableWidget()
        self.table_bookings.setColumnCount(8)
        self.table_bookings.setHorizontalHeaderLabels(
            [
                "Ομάδα",
                "Τηλέφωνο",
                "Email",
                "Άτομα",
                "Προτίμηση γλώσσας",
                "Session",
                "Πληρωμή",
                "Σχόλια",
            ]
        )
        self.table_bookings.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_bookings.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_bookings.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_bookings.setAlternatingRowColors(True)

        v3.addWidget(self.table_bookings)

        # Add tabs
        self.tabs_tours.addTab(self.tab_sessions, "Ξεναγήσεις")
        self.tabs_tours.addTab(self.tab_guides, "Ξεναγοί")
        self.tabs_tours.addTab(self.tab_bookings, "Κρατήσεις")

        # Final layout on page
        self.tours_layout.addWidget(top)
        self.tours_layout.addWidget(self.tabs_tours)

        # Default filter
        self._sessions_filter_mode = "all"

    def refresh_tours_page(self):
        """Κάνει refresh των δεδομένων/πινάκων/labels της τρέχουσας ενότητας."""
        self.refresh_tours_overview()
        self.load_tour_sessions_table()
        self.load_guides_table()
        self.load_bookings_table()

    def refresh_tours_overview(self):
        """Κάνει refresh των δεδομένων/πινάκων/labels της τρέχουσας ενότητας."""
        stats = get_tour_overview_stats()
        self.lbl_tours_today.setText(str(stats.get("today_sessions", 0)))
        self.lbl_tours_next7.setText(str(stats.get("next7_sessions", 0)))
        self.lbl_tours_available.setText(str(stats.get("available_guides", 0)))
        self.lbl_tours_canceled.setText(str(stats.get("canceled_30d", 0)))

    def set_sessions_filter(self, idx: int):
        """Εφαρμόζει φίλτρο/ρύθμιση και ανανεώνει το UI."""
        if idx == 0:
            self._sessions_filter_mode = "all"
        elif idx == 1:
            self._sessions_filter_mode = "today"
        elif idx == 2:
            self._sessions_filter_mode = "week"
        elif idx == 3:
            self._sessions_filter_mode = "canceled"
        elif idx == 4:
            self._sessions_filter_mode = "available"
        else:
            self._sessions_filter_mode = "all"

        self.load_tour_sessions_table()

    def load_tour_sessions_table(self):
        """Φορτώνει/ανανεώνει δεδομένα στο αντίστοιχο UI στοιχείο."""
        sessions = get_tour_sessions(self._sessions_filter_mode)

        self.table_sessions.setRowCount(len(sessions))
        for row, s in enumerate(sessions):
            dt_txt = f'{s["start_dt"]}\n→ {s["end_dt"]}'

            items = [
                QTableWidgetItem(dt_txt),
                QTableWidgetItem(s.get("language", "")),
                QTableWidgetItem(s.get("guide_name", "")),
                QTableWidgetItem(s.get("tour_type", "")),
                QTableWidgetItem(str(s.get("capacity", 0))),
                QTableWidgetItem(str(s.get("booked_people", 0))),
                QTableWidgetItem(s.get("status", "")),
                QTableWidgetItem(s.get("exhibition_title", "")),
                QTableWidgetItem(s.get("notes", "")),
            ]
            for col, it in enumerate(items):
                self.table_sessions.setItem(row, col, it)

            # κρατάμε το id στο πρώτο κελί
            self.table_sessions.item(row, 0).setData(Qt.UserRole, s["id"])

    def _get_selected_id(self, table: QTableWidget) -> int | None:
        """Εσωτερική βοηθητική μέθοδος."""
        rows = table.selectionModel().selectedRows()
        if not rows:
            return None
        r = rows[0].row()
        item = table.item(r, 0)
        if not item:
            return None
        return item.data(Qt.UserRole)

    def add_tour_session_ui(self):
        """UI handler για δημιουργία νέας εγγραφής."""
        guides = self._get_guides_list()
        exhibitions = get_all_exhibitions()

        dlg = TourSessionDialog(self, session=None, guides=guides, exhibitions=exhibitions)
        if dlg.exec() != QDialog.Accepted:
            return

        data = dlg.get_data()

        # conflict detection
        guide_id = data.get("guide_staff_id")
        if guide_id:
            if has_tour_conflict(int(guide_id), data["start_dt"], data["end_dt"], None):
                QMessageBox.warning(
                    self,
                    "Conflict",
                    "Ο ξεναγός έχει ήδη άλλη ξενάγηση που επικαλύπτεται χρονικά.",
                )
                return

        add_tour_session(data)
        self.refresh_tours_page()
        self.refresh_calendar_events()



    def edit_tour_session_ui(self):
        """UI handler για επεξεργασία/ενημέρωση επιλεγμένης εγγραφής."""
        session_id = self._get_selected_id(self.table_sessions)
        if not session_id:
            QMessageBox.information(self, "Επιλογή", "Διάλεξε μια ξενάγηση από τον πίνακα.")
            return

        sessions = get_tour_sessions("all")
        session = next((x for x in sessions if x["id"] == session_id), None)
        if not session:
            QMessageBox.warning(self, "Σφάλμα", "Δεν βρέθηκε η ξενάγηση.")
            return

        guides = self._get_guides_list()
        exhibitions = get_all_exhibitions()

        dlg = TourSessionDialog(self, session=session, guides=guides, exhibitions=exhibitions)
        if dlg.exec() != QDialog.Accepted:
            return

        data = dlg.get_data()
        guide_id = data.get("guide_staff_id")
        if guide_id:
            if has_tour_conflict(int(guide_id), data["start_dt"], data["end_dt"], session_id):
                QMessageBox.warning(
                    self,
                    "Conflict",
                    "Ο ξεναγός έχει ήδη άλλη ξενάγηση που επικαλύπτεται χρονικά.",
                )
                return

        update_tour_session(session_id, data)

        if (data.get("status") or "").strip().lower() == "canceled":
            from PySide6.QtWidgets import QMessageBox
            from db import cancel_tour_session_and_refund

            ans = QMessageBox.question(
                self,
                "Refund όλων;",
                "Η ξενάγηση έγινε canceled.\nΘες να γίνουν refund όλα τα σχετικά εισιτήρια και οι κρατήσεις;",
                QMessageBox.Yes | QMessageBox.No
            )
            if ans == QMessageBox.Yes:
                stats = cancel_tour_session_and_refund(session_id, data.get("cancellation_reason", ""))
                QMessageBox.information(
                    self,
                    "Ολοκληρώθηκε",
                    f"Refunded:\nΚρατήσεις: {stats['bookings']}\nOrders: {stats['orders']}\nTickets: {stats['tickets']}"
                )


        self.refresh_tours_page()
        self.refresh_calendar_events()

        if hasattr(self, "refresh_tickets_page"):
            self.refresh_tickets_page()




    def delete_tour_session_ui(self):
        """UI handler για διαγραφή επιλεγμένης εγγραφής."""
        session_id = self._get_selected_id(self.table_sessions)
        if not session_id:
            QMessageBox.information(self, "Επιλογή", "Διάλεξε μια ξενάγηση από τον πίνακα.")
            return

        res = QMessageBox.question(self, "Διαγραφή", "Σίγουρα θες να διαγράψεις τη ξενάγηση;")
        if res != QMessageBox.Yes:
            return

        delete_tour_session(session_id)
        self.refresh_tours_page()
        self.refresh_calendar_events()


    def load_guides_table(self):
        """Φορτώνει/ανανεώνει δεδομένα στο αντίστοιχο UI στοιχείο."""
        guides = self._get_guides_list()

        self.table_guides.setRowCount(len(guides))
        for row, g in enumerate(guides):
            name = f'{g.get("first_name","")} {g.get("last_name","")}'.strip()

            #Ρόλος/Επίπεδο: δεν έχεις ξεχωριστό πεδίο, οπότε δείχνουμε staff_type
            role_txt = (g.get("staff_type") or "").strip()

            items = [
                QTableWidgetItem(name),
                QTableWidgetItem(g.get("language", "")),
                QTableWidgetItem(role_txt),
                QTableWidgetItem(g.get("pn", "")),       # τηλέφωνο
                QTableWidgetItem(g.get("email", "")),
            ]
            for col, it in enumerate(items):
                self.table_guides.setItem(row, col, it)

            self.table_guides.item(row, 0).setData(Qt.UserRole, g.get("id"))

    def load_bookings_table(self):
        """Φορτώνει/ανανεώνει δεδομένα στο αντίστοιχο UI στοιχείο."""
        bookings = get_tour_bookings(None)

        self.table_bookings.setRowCount(len(bookings))
        for row, b in enumerate(bookings):
            session_txt = f'{b.get("session_start_dt","")} • {b.get("session_title","")}'.strip()

            # status ΜΕΣΑ στο loop
            status_txt = b.get("status", "active")

            # να φαίνεται στο UI χωρίς extra στήλη
            comments_txt = b.get("comments", "")
            if status_txt == "canceled":
                comments_txt = (comments_txt + " | CANCELED").strip(" |")

            items = [
                QTableWidgetItem(b.get("group_name", "")),
                QTableWidgetItem(b.get("phone", "")),
                QTableWidgetItem(b.get("email", "")),
                QTableWidgetItem(str(b.get("people_count", 0))),
                QTableWidgetItem(b.get("language_pref", "")),
                QTableWidgetItem(session_txt),
                QTableWidgetItem(b.get("payment_status", "")),
                QTableWidgetItem(comments_txt),
            ]

            for col, it in enumerate(items):
                self.table_bookings.setItem(row, col, it)

            self.table_bookings.item(row, 0).setData(Qt.UserRole, b["id"])


    def add_booking_ui(self):
        """UI handler για δημιουργία νέας εγγραφής."""
        sessions = get_tour_sessions("all")
        if not sessions:
            QMessageBox.information(self, "Info", "Πρώτα φτιάξε μια ξενάγηση (session).")
            return

        dlg = TourBookingDialog(self, booking=None, sessions=sessions)
        if dlg.exec() != QDialog.Accepted:
            return

        data = dlg.get_data()
        add_tour_booking(data)
        self.refresh_tours_page()
        self.refresh_calendar_events()


    def edit_booking_ui(self):
        """UI handler για επεξεργασία/ενημέρωση επιλεγμένης εγγραφής."""
        booking_id = self._get_selected_id(self.table_bookings)
        if not booking_id:
            QMessageBox.information(self, "Επιλογή", "Διάλεξε μια κράτηση από τον πίνακα.")
            return

        bookings = get_tour_bookings(None)
        booking = next((x for x in bookings if x["id"] == booking_id), None)
        if not booking:
            QMessageBox.warning(self, "Σφάλμα", "Δεν βρέθηκε η κράτηση.")
            return

        sessions = get_tour_sessions("all")
        dlg = TourBookingDialog(self, booking=booking, sessions=sessions)
        if dlg.exec() != QDialog.Accepted:
            return

        data = dlg.get_data()
        update_tour_booking(booking_id, data)
        self.refresh_tours_page()
        self.refresh_calendar_events()


    def delete_booking_ui(self):
        """UI handler για διαγραφή επιλεγμένης εγγραφής."""
        booking_id = self._get_selected_id(self.table_bookings)
        if not booking_id:
            QMessageBox.information(self, "Επιλογή", "Διάλεξε μια κράτηση από τον πίνακα.")
            return

        res = QMessageBox.question(self, "Διαγραφή", "Σίγουρα θες να διαγράψεις τη κράτηση;")
        if res != QMessageBox.Yes:
            return

        delete_tour_booking(booking_id)
        self.refresh_tours_page()
        self.refresh_calendar_events()



    #TICKETS PAGE (index 7)


    def setup_tickets_page(self):
        # Overview cards 
        """Μέθοδος βοηθητικής λειτουργίας."""
        top = QFrame(self.page_tickets)
        top.setStyleSheet("QFrame { background: transparent; }")
        top_lay = QHBoxLayout(top)
        top_lay.setContentsMargins(0, 0, 0, 0)
        top_lay.setSpacing(10)

        def make_card(title: str):
            """Μέθοδος βοηθητικής λειτουργίας."""
            card = QFrame(top)
            card.setStyleSheet("""
                QFrame {
                    background-color: #0f1625;
                    border: none;
                    border-radius: 10px;
                }
            """)
            lay = QVBoxLayout(card)
            lay.setContentsMargins(12, 10, 12, 10)

            lbl_title = QLabel(title)
            lbl_title.setStyleSheet("""
                QLabel { border:none; background:transparent; color:#ffffff; font-size:14px; font-weight:600; }
            """)
            lbl_value = QLabel("0")
            lbl_value.setStyleSheet("""
                QLabel { border:none; background:transparent; color:#ffffff; font-size:26px; font-weight:800; }
            """)

            lay.addWidget(lbl_title)
            lay.addWidget(lbl_value)
            return card, lbl_value

        c1, self.lbl_tk_today_sales = make_card("Σήμερα: Πωλήσεις (εισιτήρια)")
        c2, self.lbl_tk_today_checkins = make_card("Check-ins σήμερα")
        c3, self.lbl_tk_today_revenue = make_card("Σήμερα: Έσοδα")
        c4, self.lbl_tk_week_revenue = make_card("Εβδομάδα: Έσοδα")

        top_lay.addWidget(c1)
        top_lay.addWidget(c2)
        top_lay.addWidget(c3)
        top_lay.addWidget(c4)

        # Tabs 
        self.tabs_tickets = QTabWidget(self.page_tickets)

        # tAB 1: Orders 
        self.tab_orders = QWidget()
        v1 = QVBoxLayout(self.tab_orders)
        v1.setContentsMargins(10, 10, 10, 10)
        v1.setSpacing(10)

        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.cmb_orders_filter = QComboBox()
        self.cmb_orders_filter.addItems(["Όλα", "Σήμερα", "Εβδομάδα"])
        self.cmb_orders_filter.currentIndexChanged.connect(self.set_orders_filter)

        # ίδιο στυλ με tours filter (pill)
        try:
            self.cmb_orders_filter.setFixedHeight(36)
            self.cmb_orders_filter.setView(QListView())
        except Exception:
            pass

        self.cmb_orders_filter.setStyleSheet("""
        QComboBox {
            background-color: #151d2a;
            border-radius: 16px;
            border: 1px solid #394b63;
            color: #ffffff;
            padding: 4px 12px;
            font-weight: 500;
        }
        QComboBox:hover { background-color: #1f2a3d; }
        QComboBox::drop-down { border: 0px; width: 22px; }
        QComboBox::down-arrow { image: none; }
        QComboBox QAbstractItemView {
            background-color: #111827;
            border: 1px solid #374151;
            color: #e5e7eb;
            selection-background-color: #2563eb;
            selection-color: #f9fafb;
            outline: 0;
        }
        """)

        self.btn_new_sale = QPushButton("Νέα Πώληση")
        self.btn_new_sale.setStyleSheet(COMMON_BTN_STYLE)
        self.btn_order_details = QPushButton("Λεπτομέρειες")
        self.btn_order_details.setStyleSheet(COMMON_BTN_STYLE)
        self.btn_refund = QPushButton("Refund / Ακύρωση")
        self.btn_refund.setStyleSheet(COMMON_BTN_STYLE)

        self.btn_new_sale.clicked.connect(self.new_sale_ui)
        self.btn_order_details.clicked.connect(self.open_order_details_ui)
        self.btn_refund.clicked.connect(self.refund_order_ui)

        row1.addWidget(QLabel("Φίλτρο:"))
        row1.addWidget(self.cmb_orders_filter)
        row1.addStretch(1)
        row1.addWidget(self.btn_new_sale)
        row1.addWidget(self.btn_order_details)
        row1.addWidget(self.btn_refund)

        v1.addLayout(row1)

        self.table_orders = QTableWidget()
        self.table_orders.setColumnCount(7)
        self.table_orders.setHorizontalHeaderLabels([
            "Ώρα", "Κανάλι", "Email", "Σύνολο", "Πληρωμή", "Status", "Ταμίας"
        ])
        self.table_orders.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_orders.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_orders.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_orders.setAlternatingRowColors(True)

        v1.addWidget(self.table_orders)

        #TAB 2: Check-in
        self.tab_checkin = QWidget()
        v2 = QVBoxLayout(self.tab_checkin)
        v2.setContentsMargins(10, 10, 10, 10)
        v2.setSpacing(10)

        row2 = QHBoxLayout()
        row2.setSpacing(8)

        self.ed_scan = QLineEdit()
        self.ed_scan.setPlaceholderText("Σκάναρε QR / γράψε κωδικό και πάτα Enter…")
        self.ed_scan.returnPressed.connect(self.checkin_submit_ui)

        self.chk_enforce_date = QCheckBox("Έλεγχος ημερομηνίας (μόνο για σήμερα)")
        self.chk_enforce_date.setChecked(True)

        self.btn_scan = QPushButton("Check-in")
        self.btn_scan.setStyleSheet(COMMON_BTN_STYLE)
        self.btn_scan.clicked.connect(self.checkin_submit_ui)

        self.btn_undo = QPushButton("Undo last check-in")
        self.btn_undo.setStyleSheet(COMMON_BTN_STYLE)
        self.btn_undo.clicked.connect(self.undo_last_checkin_ui)

        row2.addWidget(self.ed_scan, 1)
        row2.addWidget(self.btn_scan)
        row2.addWidget(self.btn_undo)

        v2.addLayout(row2)
        v2.addWidget(self.chk_enforce_date)

        self.lbl_scan_result = QLabel("")
        self.lbl_scan_result.setStyleSheet("color: white; font-size: 16px; font-weight: 700;")
        self.lbl_scan_info = QLabel("")
        self.lbl_scan_info.setStyleSheet("color: #cbd5e1; font-size: 13px;")
        v2.addWidget(self.lbl_scan_result)
        v2.addWidget(self.lbl_scan_info)

        v2.addWidget(QLabel("Τελευταία scans"))

        self.table_scanlog = QTableWidget()
        self.table_scanlog.setColumnCount(4)
        self.table_scanlog.setHorizontalHeaderLabels(["Ώρα", "Code", "Result", "Notes"])
        self.table_scanlog.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_scanlog.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_scanlog.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_scanlog.setAlternatingRowColors(True)
        v2.addWidget(self.table_scanlog)

        # --- TAB 3: Ticket Types ---
        self.tab_types = QWidget()
        v3 = QVBoxLayout(self.tab_types)
        v3.setContentsMargins(10, 10, 10, 10)
        v3.setSpacing(10)

        row3 = QHBoxLayout()
        row3.setSpacing(8)

        self.btn_add_type = QPushButton("Νέος Τύπος")
        self.btn_add_type.setStyleSheet(COMMON_BTN_STYLE)
        self.btn_edit_type = QPushButton("Επεξεργασία")
        self.btn_edit_type.setStyleSheet(COMMON_BTN_STYLE)
        self.btn_toggle_type = QPushButton("Enable/Disable")
        self.btn_toggle_type.setStyleSheet(COMMON_BTN_STYLE)

        self.btn_add_type.clicked.connect(self.add_ticket_type_ui)
        self.btn_edit_type.clicked.connect(self.edit_ticket_type_ui)
        self.btn_toggle_type.clicked.connect(self.toggle_ticket_type_ui)

        row3.addStretch(1)
        row3.addWidget(self.btn_add_type)
        row3.addWidget(self.btn_edit_type)
        row3.addWidget(self.btn_toggle_type)
        v3.addLayout(row3)

        self.table_types = QTableWidget()
        self.table_types.setColumnCount(6)
        self.table_types.setHorizontalHeaderLabels([
            "Όνομα", "Τιμή", "Ενεργό", "Online", "Proof", "Σημειώσεις"
        ])
        self.table_types.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_types.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_types.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_types.setAlternatingRowColors(True)
        v3.addWidget(self.table_types)

        # --- TAB 4: Reports ---
        self.tab_reports = QWidget()
        v4 = QVBoxLayout(self.tab_reports)
        v4.setContentsMargins(10, 10, 10, 10)
        v4.setSpacing(10)

        row4 = QHBoxLayout()
        row4.setSpacing(8)

        self.dt_rep_from = QDateEdit()
        self.dt_rep_from.setCalendarPopup(True)
        self.dt_rep_to = QDateEdit()
        self.dt_rep_to.setCalendarPopup(True)

        # default last 7 days
        self.dt_rep_to.setDate(QDate.currentDate())
        self.dt_rep_from.setDate(QDate.currentDate().addDays(-6))

        self.btn_rep_refresh = QPushButton("Ανανέωση")
        self.btn_rep_refresh.setStyleSheet(COMMON_BTN_STYLE)
        self.btn_rep_refresh.clicked.connect(self.load_reports)

        row4.addWidget(QLabel("Από:"))
        row4.addWidget(self.dt_rep_from)
        row4.addWidget(QLabel("Έως:"))
        row4.addWidget(self.dt_rep_to)
        row4.addStretch(1)
        row4.addWidget(self.btn_rep_refresh)

        v4.addLayout(row4)

        v4.addWidget(QLabel("Πωλήσεις ανά τύπο"))
        self.table_rep_type = QTableWidget()
        self.table_rep_type.setColumnCount(3)
        self.table_rep_type.setHorizontalHeaderLabels(["Τύπος", "Qty", "Έσοδα"])
        self.table_rep_type.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_rep_type.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_rep_type.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_rep_type.setAlternatingRowColors(True)
        v4.addWidget(self.table_rep_type)

        v4.addWidget(QLabel("Tickets ανά ξενάγηση"))
        self.table_rep_session = QTableWidget()
        self.table_rep_session.setColumnCount(3)
        self.table_rep_session.setHorizontalHeaderLabels(["Ξενάγηση", "Tickets", "Revenue (est)"])
        self.table_rep_session.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_rep_session.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_rep_session.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_rep_session.setAlternatingRowColors(True)
        v4.addWidget(self.table_rep_session)

        # add tabs
        self.tabs_tickets.addTab(self.tab_orders, "Πωλήσεις / Orders")
        self.tabs_tickets.addTab(self.tab_checkin, "Check-in (QR)")
        self.tabs_tickets.addTab(self.tab_types, "Τύποι εισιτηρίων")
        self.tabs_tickets.addTab(self.tab_reports, "Reports")

        self.tickets_layout.addWidget(top)
        self.tickets_layout.addWidget(self.tabs_tickets)

        self._orders_filter_mode = "all"

    def refresh_tickets_page(self):
        """Κάνει refresh των δεδομένων/πινάκων/labels της τρέχουσας ενότητας."""
        self.refresh_tickets_overview()
        self.load_orders_table()
        self.load_scan_log_table()
        self.load_ticket_types_table()
        self.load_reports()

    def refresh_tickets_overview(self):
        """Κάνει refresh των δεδομένων/πινάκων/labels της τρέχουσας ενότητας."""
        stats = get_ticket_overview_stats()
        self.lbl_tk_today_sales.setText(str(stats.get("today_tickets", 0)))
        self.lbl_tk_today_checkins.setText(str(stats.get("today_checkins", 0)))
        self.lbl_tk_today_revenue.setText(f'{stats.get("today_revenue", 0):.2f}Euro €')
        self.lbl_tk_week_revenue.setText(f'{stats.get("week_revenue", 0):.2f}Euro €')

    # Orders 
    def set_orders_filter(self, idx: int):
        """Εφαρμόζει φίλτρο/ρύθμιση και ανανεώνει το UI."""
        if idx == 0:
            self._orders_filter_mode = "all"
        elif idx == 1:
            self._orders_filter_mode = "today"
        elif idx == 2:
            self._orders_filter_mode = "week"
        else:
            self._orders_filter_mode = "all"
        self.load_orders_table()

    def load_orders_table(self):
        """Φορτώνει/ανανεώνει δεδομένα στο αντίστοιχο UI στοιχείο."""
        orders = get_ticket_orders(self._orders_filter_mode)

        self.table_orders.setRowCount(len(orders))
        for row, o in enumerate(orders):
            items = [
                QTableWidgetItem(o.get("created_at", "")),
                QTableWidgetItem(o.get("channel", "")),
                QTableWidgetItem(o.get("customer_email", "")),
                QTableWidgetItem(f'{float(o.get("total", 0) or 0):.2f}Euro €'),
                QTableWidgetItem(o.get("payment_method", "")),
                QTableWidgetItem(o.get("status", "")),
                QTableWidgetItem(o.get("cashier_name", "")),
            ]
            for col, it in enumerate(items):
                self.table_orders.setItem(row, col, it)

            self.table_orders.item(row, 0).setData(Qt.UserRole, o["id"])

    def new_sale_ui(self):
        # active ticket types
        """Μέθοδος βοηθητικής λειτουργίας."""
        types = get_ticket_types(include_inactive=False)

        # sessions & exhibitions (δέσιμο)
        from db import get_tour_sessions_for_ticket_sales
        sessions = get_tour_sessions_for_ticket_sales(only_with_seats=True)

        exhibitions = get_all_exhibitions()

        dlg = TicketSaleDialog(self, ticket_types=types, sessions=sessions, exhibitions=exhibitions)
        if dlg.exec() != QDialog.Accepted:
            return

        payload = dlg.get_payload()

        # cashier staff id (αν υπάρχει)
        cashier_id = getattr(self, "current_user_id", None) or getattr(self, "user_id", None)
        
        payload["order"]["cashier_staff_id"] = cashier_id

        # δημιουργία order + tickets
        try:
            order_id = create_ticket_order(payload["order"], payload["items"])
        except ValueError as e:
            QMessageBox.warning(self, "Δεν γίνεται η πώληση", str(e))
            return

        QMessageBox.information(self, "OK", f"Δημιουργήθηκε Order #{order_id}")
        # refresh Tours UI (sessions/κρατήσεις/cards) μετά από πώληση με session
        if hasattr(self, "load_tour_sessions_table"):
            self.load_tour_sessions_table()

        if hasattr(self, "load_bookings_table"):
            self.load_bookings_table()

        if hasattr(self, "refresh_tours_overview"):
            self.refresh_tours_overview()
            


        self.refresh_tickets_page()
        self.apply_ticket_stats_filters()
        # refresh Εκθέσεις (κρατημένες θέσεις από tickets)
        if hasattr(self, "load_exhibitions_tables"):
            self.load_exhibitions_tables()


    def _selected_order_id(self):
        """Εσωτερική βοηθητική μέθοδος."""
        return self._get_selected_id(self.table_orders)

    def open_order_details_ui(self):
        """Ανοίγει dialog/popup για την αντίστοιχη λειτουργία."""
        order_id = self._selected_order_id()
        if not order_id:
            QMessageBox.information(self, "Επιλογή", "Διάλεξε ένα order από τον πίνακα.")
            return

        details = get_ticket_order_details(order_id)
        dlg = OrderDetailsDialog(self, details=details)
        dlg.exec()

    def refund_order_ui(self):
        """Μέθοδος βοηθητικής λειτουργίας."""
        order_id = self._selected_order_id()
        if not order_id:
            QMessageBox.information(self, "Επιλογή", "Διάλεξε ένα order από τον πίνακα.")
            return

        res = QMessageBox.question(
            self,
            "Refund / Ακύρωση",
            "Θες να κάνεις Refund/Ακύρωση; Θα ακυρωθούν όλα τα tickets του order.",
        )
        if res != QMessageBox.Yes:
            return

        # απλό κάνουμε status='refunded'
        set_order_status(order_id, "refunded", refund_reason="Refund από admin")
        if hasattr(self, "refresh_tours_ui"):
            self.refresh_tours_ui()
        else:
            if hasattr(self, "load_bookings_table"):
                self.load_bookings_table()
            if hasattr(self, "load_tour_sessions_table"):
                self.load_tour_sessions_table()
            if hasattr(self, "refresh_tours_overview"):
                self.refresh_tours_overview()

        self.refresh_tickets_page()
        self.apply_ticket_stats_filters()
        # refresh Εκθέσεις (κρατημένες θέσεις από tickets)
        if hasattr(self, "load_exhibitions_tables"):
            self.load_exhibitions_tables()


    #  Check-in
    def checkin_submit_ui(self):
        """Μέθοδος βοηθητικής λειτουργίας."""
        code = self.ed_scan.text().strip()
        if not code:
            return

        staff_id = getattr(self, "current_user_id", None) or getattr(self, "user_id", None)
        enforce = self.chk_enforce_date.isChecked()

        result = check_in_ticket(code, staff_id=staff_id, enforce_date=enforce)

        r = result.get("result", "")
        msg = result.get("message", "")

        # simple color feedback
        if r == "VALID":
            self.lbl_scan_result.setText("VALID ✅")
            self.lbl_scan_result.setStyleSheet("color: #22c55e; font-size: 18px; font-weight: 800;")
        elif r == "USED":
            self.lbl_scan_result.setText("ALREADY USED")
            self.lbl_scan_result.setStyleSheet("color: #f59e0b; font-size: 18px; font-weight: 800;")
        else:
            self.lbl_scan_result.setText(r)
            self.lbl_scan_result.setStyleSheet("color: #ef4444; font-size: 18px; font-weight: 800;")

        info = ""
        tk = result.get("ticket")
        if tk:
            info = f'{tk.get("type_name","")} • {tk.get("visit_date","")}'
            if tk.get("tour_title"):
                info += f' • Ξενάγηση: {tk.get("tour_title")} ({tk.get("tour_start_dt","")})'
            if tk.get("exhibition_title"):
                info += f' • Έκθεση: {tk.get("exhibition_title")}'
        else:
            info = msg

        self.lbl_scan_info.setText(info)

        self.ed_scan.clear()
        self.load_scan_log_table()
        self.refresh_tickets_overview()

    def undo_last_checkin_ui(self):
        """Μέθοδος βοηθητικής λειτουργίας."""
        ok = undo_last_checkin()
        if ok:
            QMessageBox.information(self, "OK", "Έγινε undo στο τελευταίο VALID check-in.")
        else:
            QMessageBox.information(self, "Info", "Δεν βρέθηκε VALID check-in για undo.")
        self.load_scan_log_table()
        self.refresh_tickets_overview()

    def load_scan_log_table(self):
        """Φορτώνει/ανανεώνει δεδομένα στο αντίστοιχο UI στοιχείο."""
        logs = get_scan_log(25)
        self.table_scanlog.setRowCount(len(logs))
        for row, l in enumerate(logs):
            items = [
                QTableWidgetItem(l.get("scanned_at","")),
                QTableWidgetItem(l.get("code","")),
                QTableWidgetItem(l.get("result","")),
                QTableWidgetItem(l.get("notes","")),
            ]
            for col, it in enumerate(items):
                self.table_scanlog.setItem(row, col, it)

    # ---------- Ticket Types ----------
    def load_ticket_types_table(self):
        """Φορτώνει/ανανεώνει δεδομένα στο αντίστοιχο UI στοιχείο."""
        types = get_ticket_types(include_inactive=True)

        self.table_types.setRowCount(len(types))
        for row, t in enumerate(types):
            items = [
                QTableWidgetItem(t.get("name","")),
                QTableWidgetItem(f'{float(t.get("price",0) or 0):.2f}Euro €'),
                QTableWidgetItem("Ναι" if int(t.get("active",0)) == 1 else "Όχι"),
                QTableWidgetItem("Ναι" if int(t.get("online_enabled",0)) == 1 else "Όχι"),
                QTableWidgetItem("Ναι" if int(t.get("requires_proof",0)) == 1 else "Όχι"),
                QTableWidgetItem(t.get("notes","")),
            ]
            for col, it in enumerate(items):
                self.table_types.setItem(row, col, it)

            self.table_types.item(row, 0).setData(Qt.UserRole, t["id"])
            self.table_types.item(row, 0).setData(Qt.UserRole + 1, int(t.get("active", 1)))

    def _selected_type_id(self):
        """Εσωτερική βοηθητική μέθοδος."""
        return self._get_selected_id(self.table_types)

    def add_ticket_type_ui(self):
        """UI handler για δημιουργία νέας εγγραφής."""
        dlg = TicketTypeDialog(self, data=None)
        if dlg.exec() != QDialog.Accepted:
            return
        data = dlg.get_data()
        if not data["name"]:
            QMessageBox.warning(self, "Σφάλμα", "Το όνομα είναι υποχρεωτικό.")
            return
        add_ticket_type(data)
        self.load_ticket_types_table()

    def edit_ticket_type_ui(self):
        """UI handler για επεξεργασία/ενημέρωση επιλεγμένης εγγραφής."""
        type_id = self._selected_type_id()
        if not type_id:
            QMessageBox.information(self, "Επιλογή", "Διάλεξε έναν τύπο εισιτηρίου.")
            return

        # παίρνουμε τα δεδομένα από DB
        types = get_ticket_types(include_inactive=True)
        cur = next((x for x in types if x["id"] == type_id), None)
        if not cur:
            QMessageBox.warning(self, "Σφάλμα", "Δεν βρέθηκε ο τύπος.")
            return

        dlg = TicketTypeDialog(self, data=cur)
        if dlg.exec() != QDialog.Accepted:
            return
        data = dlg.get_data()
        update_ticket_type(type_id, data)
        self.load_ticket_types_table()

    def toggle_ticket_type_ui(self):
        """Μέθοδος βοηθητικής λειτουργίας."""
        type_id = self._selected_type_id()
        if not type_id:
            QMessageBox.information(self, "Επιλογή", "Διάλεξε έναν τύπο εισιτητηρίου.")
            return

        # active από stored data
        rows = self.table_types.selectionModel().selectedRows()
        r = rows[0].row()
        active = int(self.table_types.item(r, 0).data(Qt.UserRole + 1) or 1)

        new_active = 0 if active == 1 else 1
        set_ticket_type_active(type_id, new_active)
        self.load_ticket_types_table()

    # ---------- Reports ----------
    def load_reports(self):
        """Φορτώνει/ανανεώνει δεδομένα στο αντίστοιχο UI στοιχείο."""
        d_from = self.dt_rep_from.date().toString("yyyy-MM-dd")
        d_to = self.dt_rep_to.date().toString("yyyy-MM-dd")

        by_type = report_sales_by_type(d_from, d_to)
        self.table_rep_type.setRowCount(len(by_type))
        for i, r in enumerate(by_type):
            self.table_rep_type.setItem(i, 0, QTableWidgetItem(r.get("type","")))
            self.table_rep_type.setItem(i, 1, QTableWidgetItem(str(r.get("qty",0))))
            self.table_rep_type.setItem(i, 2, QTableWidgetItem(f'{float(r.get("revenue",0) or 0):.2f}Euro €'))

        by_session = report_sales_by_session(d_from, d_to)
        self.table_rep_session.setRowCount(len(by_session))
        for i, r in enumerate(by_session):
            self.table_rep_session.setItem(i, 0, QTableWidgetItem(r.get("session","")))
            self.table_rep_session.setItem(i, 1, QTableWidgetItem(str(r.get("tickets",0))))
            self.table_rep_session.setItem(i, 2, QTableWidgetItem(f'{float(r.get("revenue_est",0) or 0):.2f}Euro €'))




        # STAFF – TABLES & CRUD

    def load_staff(self):
            
            # Παίρνουμε όλα τα στοιχεία των εργαζομένων από τη βάση
            """Φορτώνει/ανανεώνει δεδομένα στο αντίστοιχο UI στοιχείο."""
            all_staff = get_staff() 
            # Δημιουργία layout για προσωπικό αν δεν υπάρχει ήδη
            if not hasattr(self, "layout_pros"):

                self.layout_pros = QVBoxLayout(self.page_prosopiko)

                # Search bar
            if not hasattr(self, "search_edit"):
                search_layout = QHBoxLayout()
                self.search_edit = QLineEdit()
                self.search_edit.setPlaceholderText("Αναζήτηση εργαζομένου...")
                self.search_edit.setFixedHeight(40)
                self.search_edit.setStyleSheet("""
                    QLineEdit {
                            padding: 8px 12px;
                            border-radius: 18px;
                            border-radius: 18px;
                            border: 1px solid #ccc;
                            font-size: 13px;
                            }
                     QLineEdit::placeholder {
                                               color: #999999;
                                                }
                     QLineEdit:focus {
                                                border: 1px solid #2196F3;
                                                
                                               }
                      """)
                search_icon = QAction(QIcon("search_icon.png"), "", self.search_edit)
                self.search_edit.addAction(search_icon, QLineEdit.LeadingPosition)
                search_layout.addWidget(self.search_edit)



                if not hasattr(self, "filter_combo"):
                    self.filter_combo = QComboBox()
                    self.filter_combo.addItems(["Όλα", "Ξεναγός", "Συντηρητής", "Επιμελητής"])
                    self.filter_combo.setFixedHeight(30)
                    self.filter_combo.setView(QListView())
                    self.filter_combo.setStyleSheet("""
        QComboBox {
            background-color: #151d2a;
            border-radius: 16px;
            border: 1px solid #394b63;
            color: #ffffff;
            padding: 4px 12px;
            font-weight: 500;
        }
        QComboBox:hover {
            background-color: #1f2a3d;
        }
        QComboBox::drop-down {
            border: 0px;
            width: 22px;
        }
        QComboBox::down-arrow {
            image: none;  
        }

        /* το dropdown list */
        QComboBox QAbstractItemView {
            background-color: #111827;
            border: 1px solid #374151;
            color: #e5e7eb;
            selection-background-color: #2563eb;
            selection-color: #f9fafb;
            outline: 0;
        }
        """)
                
                model = QStandardItemModel()
                color_map = {
                    "Όλα": "#ffffff",
                    "Ξεναγός": "#E3F2FD",
                    "Επιμελητής": "#FFF3E0",
                    "Συντηρητής": "#E0FFE2"
                }
                for name, color in color_map.items():
                    item = QStandardItem(name)
                    item.setBackground(QColor(color))
                    item.setForeground(QColor("#000000"))
                    model.appendRow(item)
                self.filter_combo.setModel(model)
                search_layout.addWidget(self.filter_combo)
                search_layout.addStretch()
                self.layout_pros.addLayout(search_layout)


                self.search_edit.textChanged.connect(self.filter_staff)
                self.filter_combo.currentIndexChanged.connect(self.filter_staff)


                # ----------------- Πίνακας προσωπικού -----------------
            if not hasattr(self, "table_staff"):
                self.table_staff = QTableWidget()
                self.table_staff.setColumnCount(10)
                self.table_staff.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
                self.table_staff.setColumnHidden(0, True)
                self.table_staff.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

                self.table_staff.setStyleSheet("""
                QTableWidget {
                            background-color: #ffffff;
                            border: 1px solid #ddd;
                            border-radius: 10px;
                            gridline-color: transparent;
                            font-size: 13px;
                            }

                QTableWidget::item {
                            padding: 8px;
                            }

                QTableWidget::item:selected {
                            background-color: #E3F2FD;
                            color: #000;
                            }

                QHeaderView::section {
                            background-color: #F5F5F5;
                            padding: 8px;
                            border: none;
                            font-weight: bold;
                            font-size: 13px;
                            }

                QTableWidget::item:hover {
                            background-color: #F0F8FF;
                            }
                """)
                self.table_staff.setAlternatingRowColors(True)
                self.table_staff.setStyleSheet(
                    self.table_staff.styleSheet() + "QTableWidget { alternate-background-color: #FAFAFA; }"
                )      
                self.table_staff.setHorizontalHeaderLabels(["ID", "Όνομα", "Επίθετο", "Τηλέφωνο", "Μισθός", "Email", "Διεύθυνση", "Ειδικότητα", "Γλώσσα","Τύπος Προσωπικού"])
                self.table_staff.setEditTriggers(QTableWidget.NoEditTriggers)
                self.table_staff.setSelectionBehavior(QTableWidget.SelectRows)
                self.table_staff.setSelectionMode(QTableWidget.SingleSelection)
                self.table_staff.verticalHeader().setVisible(False)
                self.table_staff.horizontalHeader().setStretchLastSection(True)
                self.layout_pros.addWidget(self.table_staff)
    
                # ----------------- Κουμπιά για διαχείριση προσωπικού -----------------

                btn_layout = QHBoxLayout()
                self.btn_add_staff = QPushButton("➕ Νέο μέλος")
                self.btn_edit_staff = QPushButton("✏️ Επεξεργασία")
                self.btn_delete_staff = QPushButton("🗑️ Διαγραφή")
                for b in (self.btn_add_staff, self.btn_edit_staff, self.btn_delete_staff):
                    b.setStyleSheet(COMMON_BTN_STYLE)
                    btn_layout.addWidget(b)
                btn_layout.addStretch()
                self.layout_pros.addLayout(btn_layout)
                # ----------------- Συνδέσεις κουμπιών -----------------

                self.btn_add_staff.clicked.connect(self.add_staff_dialog)
                self.btn_delete_staff.clicked.connect(self.delete_selected_staff)
                self.btn_edit_staff.clicked.connect(self.edit_selected_staff)     

            # ----------------- Φόρτωση δεδομένων στον πίνακα -----------------

            self.table_staff.setRowCount(len(all_staff))
            type_map_display={"conservator":"Συντηρητής","guide":"Ξεναγός","curator":"Επιμελητής"}
            for row, s in enumerate(all_staff):
                    # Γέμισμα των κελιων με τα δεδομένα του κάθε εργαζόμενου 
                                      
                    self.table_staff.setItem(row, 0, QTableWidgetItem(str(s["id"])))
                    self.table_staff.setItem(row, 1, QTableWidgetItem(s["first_name"]))
                    self.table_staff.setItem(row, 2, QTableWidgetItem(s["last_name"]))
                    self.table_staff.setItem(row, 3, QTableWidgetItem(s.get("pn","")))
                    wage_item = "" if s.get("wage") is None else str(s.get("wage"))
                    self.table_staff.setItem(row, 4, QTableWidgetItem(wage_item))             
                    self.table_staff.setItem(row, 5, QTableWidgetItem(s.get("email","")))
                    self.table_staff.setItem(row, 6, QTableWidgetItem(s.get("address","")))
                    self.table_staff.setItem(row, 7, QTableWidgetItem(s.get("specialization","")))
                    self.table_staff.setItem(row, 8, QTableWidgetItem(s.get("language","")))

                    # Μετατροπή τύπου προσωπικού από αγγλικά σε ελληνικά
                    staff_type_eng = s.get("staff_type", "")
                    staff_type_gr = type_map_display.get(staff_type_eng, "")
                    type_item = QTableWidgetItem(staff_type_gr)
                    type_item.setTextAlignment(Qt.AlignCenter)
                    if staff_type_eng == "guide":
                        type_item.setBackground(QColor("#E3F2FD"))
                    elif staff_type_eng == "conservator":
                        type_item.setBackground(QColor("#E8F5E9"))
                    elif staff_type_eng == "curator":
                        type_item.setBackground(QColor("#FFF3E0"))
                                                                        
                    self.table_staff.setItem(row, 9, type_item)             
            self.table_staff.resizeColumnsToContents()
    def filter_staff(self, text):
            #Φιλτράρει τις γραμμές του πίνακα ανάλογα με το κείμενο στο search bar.

        """Μέθοδος βοηθητικής λειτουργίας."""
        text = self.search_edit.text().lower().strip()
        search_words = text.split() 
        selected_type = self.filter_combo.currentText()
        for row in range(self.table_staff.rowCount()):
            row_text = " ".join([
                self.table_staff.item(row, col).text() for col in range(self.table_staff.columnCount()) if self.table_staff.item(row, col)
            ]).lower()
            match_text = all(word in row_text for word in search_words)
            staff_type_item = self.table_staff.item(row, 9)
            if selected_type == "Όλα":
                match_type = True
            else:
                match_type=staff_type_item.text()==selected_type
                    
            self.table_staff.setRowHidden(row, not (match_text and match_type))

    
    
    # ----------------- Διαχείριση κουμπιού "Προσθήκη Προσωπικού" -----------------

    def add_staff_dialog(self):
        """UI handler για δημιουργία νέας εγγραφής."""
        dlg = StaffDialog(self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            field,error = dlg.validate_staff_data(data)
            if error:
                dlg.show_field_error(field, error)
                QMessageBox.warning(self, "Σφάλμα", error)
                return
            add_staff_member(**data)
            self.load_staff()

    # ----------------- Διαγραφή επιλεγμένου μέλους -----------------
    
    def delete_selected_staff(self):
        """UI handler για διαγραφή επιλεγμένης εγγραφής."""
        sel = self.table_staff.selectionModel().selectedRows()
        if not sel:
            QMessageBox.information(self, "Πληροφορία", "Επέλεξε πρώτα ένα μέλος.")
            return

        row = sel[0].row()
        staff_id = int(self.table_staff.item(row, 0).text())

        reply = QMessageBox.question(
            self,
            "Διαγραφή",
            "Είσαι σίγουρος ότι θέλεις να διαγράψεις αυτό το μέλος;",
            QMessageBox.Yes | QMessageBox.No,
            )
        if reply == QMessageBox.Yes:
            del_pros(staff_id)
            self.load_staff()

     # ----------------- Επεξεργασια επιλεγμένου μέλους -----------------       
    def edit_selected_staff(self):
        """UI handler για επεξεργασία/ενημέρωση επιλεγμένης εγγραφής."""
        sel = self.table_staff.selectionModel().selectedRows()
        if not sel:
            QMessageBox.information(self, "Πληροφορία", "Επέλεξε πρώτα ένα μέλος.")
            return

        row = sel[0].row()
        staff_id = int(self.table_staff.item(row, 0).text())

        staff_data = {
            "id": staff_id,
            "first_name": self.table_staff.item(row, 1).text(),
            "last_name": self.table_staff.item(row, 2).text(),
            "pn": self.table_staff.item(row, 3).text(),
            "wage": self.table_staff.item(row, 4).text(),
            "email": self.table_staff.item(row, 5).text(),
            "address": self.table_staff.item(row, 6).text(),
            "specialization": self.table_staff.item(row, 7).text() if self.table_staff.item(row, 7) else None,
            "language": self.table_staff.item(row, 8).text() if self.table_staff.item(row, 8) else None,
            "staff_type": self.table_staff.item(row, 9).text(),
        }

        dlg = StaffDialog(self, staff_data)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            error_field, error_msg = dlg.validate_staff_data(data)
            if error_msg:
                dlg.show_field_error(error_field, error_msg)
                QMessageBox.warning(self, "Σφάλμα", str(error_msg))
                return

            update_staff_member(
                staff_id,
                data["first_name"],
                data["last_name"],
                data["pn"],
                data["wage"],
                data["email"],
                data["address"],
                data["specialization"],
                data["language"],
                data["staff_type"]
            )
            self.load_staff()




    # ---------------------------------------------------------
    # LOGOUT
    # ---------------------------------------------------------
    def logout(self):
        """Μέθοδος βοηθητικής λειτουργίας."""
        self.close()
        login = LoginDialog()
        if login.exec() == QDialog.Accepted:
            new_window = MainWindow(login.user)
            new_window.show()

    def load_works_maintenance(self):
        """Φορτώνει/ανανεώνει δεδομένα στο αντίστοιχο UI στοιχείο."""
        from db import DB_NAME
        import sqlite3

    # Καθαρισμός πίνακα
        self.syntirisi_table.setRowCount(0)
        selected_filter = self.maintenance_filter.currentText()


    # Ορισμός στηλών
        self.syntirisi_table.setColumnCount(6)
        self.syntirisi_table.setHorizontalHeaderLabels(
        ["ID Συντήρησης", "Τίτλος Έργου", "Ημ/νία Προσθήκης",
         "Τύπος Συντήρησης", "Ημ/νία Έναρξης", "Επιλογή Συντηρητή"]
    )

    # Σύνδεση με βάση
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        if selected_filter == "Όλα":
            cur.execute("""
                SELECT m.id, w.title, w.date_added, m.type, m.start,
                       m.conservator_id, s.first_name, s.last_name
                FROM maintenance m
                JOIN works w ON m.work_id = w.id
                LEFT JOIN staff s ON m.conservator_id = s.id
                WHERE m.end IS NULL
                ORDER BY m.start ASC
            """)

        else:
            cur.execute("""
            SELECT m.id, w.title, w.date_added, m.type, m.start,
                   m.conservator_id, s.first_name, s.last_name
            FROM maintenance m
            JOIN works w ON m.work_id = w.id
            LEFT JOIN staff s ON m.conservator_id = s.id
            WHERE m.end IS NULL AND m.type = ?
            ORDER BY m.start ASC
        """, (selected_filter,))
           

            
        works = cur.fetchall()
        conn.close()

        for row_idx, work in enumerate(works):
             
            maint_id = work[0]
            title = work[1]
            date_added = work[2]
            maint_type = work[3]
            start_date = work[4]
            conservator_id = work[5] if len(work) > 5 else None
            first_name = work[6] if len(work) > 6 else None
            last_name = work[7] if len(work) > 7 else None
            self.syntirisi_table.insertRow(row_idx)
            self.syntirisi_table.setItem(row_idx, 0, QTableWidgetItem(str(maint_id)))
            self.syntirisi_table.setItem(row_idx, 1, QTableWidgetItem(title))
            self.syntirisi_table.setItem(row_idx, 2, QTableWidgetItem(str(date_added)))
            self.syntirisi_table.setItem(row_idx, 3, QTableWidgetItem(maint_type))
            self.syntirisi_table.setItem(row_idx, 4, QTableWidgetItem(str(start_date)))
            

        # Drop-down “Ανάθεση Συντηρητή”
            assign_combo = QComboBox()
            assign_combo.setStyleSheet("""
        QComboBox {
            background-color: #151d2a;
            border-radius: 16px;
            border: 1px solid #394b63;
            color: #ffffff;
            padding: 4px 12px;
            font-weight: 500;
        }
        QComboBox:hover {
            background-color: #1f2a3d;
        }
        QComboBox::drop-down {
            border: 0px;
            width: 22px;
        }
        QComboBox::down-arrow {
            image: none;  
        }

        /* το dropdown list */
        QComboBox QAbstractItemView {
            background-color: #111827;
            border: 1px solid #374151;
            color: #e5e7eb;
            selection-background-color: #2563eb;
            selection-color: #f9fafb;
            outline: 0;
        }
        """)


            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("""
            SELECT s.id, s.first_name, s.last_name, c.specialization
            FROM staff s
            JOIN conservators c ON s.id = c.staff_id
            ORDER BY c.specialization, s.last_name
        """)
            for staff_id, first, last, spec in cur.fetchall():
                display_text = f"{first} {last} ({spec})"
                assign_combo.addItem(display_text, staff_id)
            conn.close()

        # Ορισμός τρέχοντος συντηρητή στο combo
            if conservator_id:
                index = assign_combo.findData(conservator_id)
                if index != -1:
                    assign_combo.setCurrentIndex(index)

        # Σύνδεση αλλαγής με ενημέρωση βάσης
            assign_combo.currentIndexChanged.connect(
                lambda idx, wid=maint_id, combo=assign_combo: self.update_maintenance_conservator(
                    wid, combo.currentData()
                )
            )

            self.syntirisi_table.setCellWidget(row_idx, 5, assign_combo)

    def open_assign_dialog(self, maint_id):
        """Ανοίγει dialog/popup για την αντίστοιχη λειτουργία."""
        dlg = MaintenanceDialog(self,maint_id)
        if dlg.exec() == QDialog.Accepted:
            # Παίρνουμε τον επιλεγμένο συντηρητή
            conservator_id = dlg.get_selected_conservator()
        # Ενημέρωση της βάσης
            self.update_maintenance_conservator(maint_id, conservator_id)
        # Επαναφόρτωση πίνακα
            self.load_works_maintenance()


   ##


    def assign_maintenance(self, work_id, work_title):
        """Μέθοδος βοηθητικής λειτουργίας."""
        dlg= MaintenanceDialog(self, work_id, work_title)
        if dlg.exec() == QDialog.Accepted:
            conservator_id = dlg.get_selected_conservator()
            maint_type = dlg.maint_type_combo.currentText()
            self.add_maintenance_record(work_id, conservator_id, maint_type)
    def update_maintenance_conservator(self, maint_id, conservator_id):
        """UI handler για επεξεργασία/ενημέρωση επιλεγμένης εγγραφής."""
        import sqlite3
        from db import DB_NAME
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("UPDATE maintenance SET conservator_id=? WHERE id=?", (conservator_id, maint_id))
        conn.commit()
        conn.close()
    # Επαναφόρτωση πίνακα
    
    

class AIProposalWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, fn):
        """Εσωτερική βοηθητική μέθοδος."""
        super().__init__()
        self.fn = fn

    @Slot()
    def run(self):
        """Μέθοδος βοηθητικής λειτουργίας."""
        try:
            text = self.fn()
            self.finished.emit(text)
        except Exception as e:
            self.failed.emit(str(e))


