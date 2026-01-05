# main.py
import sys

from PySide6.QtWidgets import QApplication, QDialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from db import init_db
from dialogs import LoginDialog
from main_window import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)

    init_db()

    login = LoginDialog()
    if login.exec() == QDialog.Accepted:
        window = MainWindow(login.user)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)
