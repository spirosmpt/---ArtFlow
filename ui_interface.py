# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'interfaceqlVOil.ui'
##
## Created by: Qt User Interface Compiler version 5.14.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QMetaObject, QObject, QPoint,
    QRect, QSize, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QLinearGradient, QPalette, QPainter, QPixmap,
    QRadialGradient)
from PySide6.QtWidgets import *

import resources_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1157, 566)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setStyleSheet(u"*{\n"
"	color: #000;\n"
"border: none;\n"
"}\n"
"\n"
"\n"
"#centralwidget{\n"
"	background-color: #ffffff;\n"
"}\n"
"\n"
"#leftMenu{\n"
"	background-color: #151d2a;\n"
"}\n"
"\n"
"QLineEdit{\n"
"	background-color: transparent;\n"
"}\n"
"\n"
"#searchFrame{\n"
"	border-radius: 10px;\n"
"    border: 2px solid #151d2a;\n"
"}\n"
"\n"
"#appHeader{\n"
"	color: #151d2a;\n"
"}\n"
"\n"
"#card1, #card2, #card3, #card4{\n"
"	background-color: #fefeff;\n"
"    border-radius: 18px;\n"
"	border: 2px;\n"
"}\n"
"\n"
"#widget_4, #widget_5, #Profile{\n"
"	background-color: #fefeff;\n"
"    border-radius: 18px;\n"
"}\n"
"\n"
"#headerFrame{\n"
"	background-color: #fefeff;\n"
"}\n"
"\n"
"#pushButton_2{\n"
"}\n"
"\n"
"QPushButton{\n"
"    padding: 5px;\n"
"    text-align: left;\n"
"    color: #ffffff;\n"
"    background-color: transparent;\n"
"    border-radius: 3px;\n"
"}\n"
"\n"
"QPushButton:checked{\n"
"    background-color: #fefeff;\n"
"    color: #151d2a;\n"
"}\n"
"#pushButton_7, #pushButton_8{\n"
"    background-color: #fefeff;\n"
"    color: #151d2a;\n"
"    border-radius: 8px;\n"
"    padding: 6px 10px;\n"
"}\n"
"#pushButton_7:hover, #pushButton_8:hover{\n"
"    background-color: #e3e7ff;\n"
"}\n"
"#pushButton_7:pressed, #pushButton_8:pressed{\n"
"    border: 2px solid #151d2a;\n"
"    background-color: #ffffff;\n"
"    color: #151d2a;\n"
"}\n"
)
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.leftMenu = QWidget(self.centralwidget)
        self.leftMenu.setObjectName(u"leftMenu")
        self.verticalLayout_7 = QVBoxLayout(self.leftMenu)
        self.verticalLayout_7.setSpacing(0)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(12, 0, 9, 0)
        self.frame_9 = QFrame(self.leftMenu)
        self.frame_9.setObjectName(u"frame_9")
        self.frame_9.setFrameShape(QFrame.StyledPanel)
        self.frame_9.setFrameShadow(QFrame.Raised)
        self.verticalLayout_8 = QVBoxLayout(self.frame_9)
        self.verticalLayout_8.setSpacing(0)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.frame_10 = QFrame(self.frame_9)
        self.frame_10.setObjectName(u"frame_10")
        self.frame_10.setFrameShape(QFrame.StyledPanel)
        self.frame_10.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_15 = QHBoxLayout(self.frame_10)
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.label_17 = QLabel(self.frame_10)
        self.label_17.setObjectName(u"label_17")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(QFont.Weight.Bold)
        font.setKerning(True)
        self.label_17.setFont(font)
        self.label_17.setAutoFillBackground(False)
        self.label_17.setScaledContents(False)
        self.label_17.setWordWrap(False)

        self.horizontalLayout_15.addWidget(self.label_17, 0, Qt.AlignTop)


        self.verticalLayout_8.addWidget(self.frame_10, 0, Qt.AlignTop)

        self.frame_11 = QFrame(self.frame_9)
        self.frame_11.setObjectName(u"frame_11")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_11.sizePolicy().hasHeightForWidth())
        self.frame_11.setSizePolicy(sizePolicy)
        self.frame_11.setFrameShape(QFrame.StyledPanel)
        self.frame_11.setFrameShadow(QFrame.Raised)
        self.verticalLayout_10 = QVBoxLayout(self.frame_11)
        self.verticalLayout_10.setSpacing(0)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.frame_12 = QFrame(self.frame_11)
        self.frame_12.setObjectName(u"frame_12")
        self.frame_12.setFrameShape(QFrame.StyledPanel)
        self.frame_12.setFrameShadow(QFrame.Raised)
        self.verticalLayout_9 = QVBoxLayout(self.frame_12)
        self.verticalLayout_9.setSpacing(20)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 11)
        self.pushButton_2 = QPushButton(self.frame_12)
        self.pushButton_2.setObjectName(u"pushButton_2")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.pushButton_2.sizePolicy().hasHeightForWidth())
        self.pushButton_2.setSizePolicy(sizePolicy1)
        self.pushButton_2.setMinimumSize(QSize(0, 0))
        self.pushButton_2.setMaximumSize(QSize(16777213, 16777215))
        font1 = QFont()
        font1.setBold(True)
        font1.setWeight(QFont.Weight.Bold)
        self.pushButton_2.setFont(font1)
        self.pushButton_2.setAutoFillBackground(False)
        icon = QIcon()
        icon.addFile(u":/blueIcons/icons/home.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_2.setIcon(icon)
        self.pushButton_2.setIconSize(QSize(27, 27))
        self.pushButton_2.setCheckable(False)

        self.verticalLayout_9.addWidget(self.pushButton_2)

        self.pushButton_3 = QPushButton(self.frame_12)
        self.pushButton_3.setObjectName(u"pushButton_3")
        self.pushButton_3.setFont(font1)
        self.pushButton_3.setAutoFillBackground(False)
        icon1 = QIcon()
        icon1.addFile(u":/blueIcons/icons/photograph-art-svgrepo-com (1).svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_3.setIcon(icon1)
        self.pushButton_3.setIconSize(QSize(27, 27))

        self.verticalLayout_9.addWidget(self.pushButton_3)

        self.pushButton_4 = QPushButton(self.frame_12)
        self.pushButton_4.setObjectName(u"pushButton_4")
        self.pushButton_4.setFont(font1)
        self.pushButton_4.setAutoFillBackground(False)
        icon2 = QIcon()
        icon2.addFile(u":/blueIcons/icons/event (1).svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_4.setIcon(icon2)
        self.pushButton_4.setIconSize(QSize(27, 27))

        self.verticalLayout_9.addWidget(self.pushButton_4)

        self.pushButton_5 = QPushButton(self.frame_12)
        self.pushButton_5.setObjectName(u"pushButton_5")
        self.pushButton_5.setFont(font1)
        self.pushButton_5.setAutoFillBackground(False)
        icon3 = QIcon()
        icon3.addFile(u":/blueIcons/icons/tools (1).svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_5.setIcon(icon3)
        self.pushButton_5.setIconSize(QSize(27, 27))

        self.verticalLayout_9.addWidget(self.pushButton_5)

        self.pushButton_6 = QPushButton(self.frame_12)
        self.pushButton_6.setObjectName(u"pushButton_6")
        self.pushButton_6.setFont(font1)
        self.pushButton_6.setAutoFillBackground(False)
        icon4 = QIcon()
        icon4.addFile(u":/blueIcons/icons/recruitment (1) (2).svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_6.setIcon(icon4)
        self.pushButton_6.setIconSize(QSize(27, 27))

        self.verticalLayout_9.addWidget(self.pushButton_6)


        self.verticalLayout_10.addWidget(self.frame_12, 0, Qt.AlignTop)


        self.verticalLayout_8.addWidget(self.frame_11)


        self.verticalLayout_7.addWidget(self.frame_9)


        self.horizontalLayout.addWidget(self.leftMenu)

        self.mainBody = QWidget(self.centralwidget)
        self.mainBody.setObjectName(u"mainBody")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.mainBody.sizePolicy().hasHeightForWidth())
        self.mainBody.setSizePolicy(sizePolicy2)
        self.verticalLayout = QVBoxLayout(self.mainBody)
        self.verticalLayout.setSpacing(26)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.headerFrame = QWidget(self.mainBody)
        self.headerFrame.setObjectName(u"headerFrame")
        self.horizontalLayout_2 = QHBoxLayout(self.headerFrame)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.widget = QWidget(self.headerFrame)
        self.widget.setObjectName(u"widget")
        self.horizontalLayout_3 = QHBoxLayout(self.widget)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.menuBtn = QPushButton(self.widget)
        self.menuBtn.setObjectName(u"menuBtn")
        icon5 = QIcon()
        icon5.addFile(u":/blueIcons/icons/menu.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.menuBtn.setIcon(icon5)
        self.menuBtn.setIconSize(QSize(25, 25))

        self.horizontalLayout_3.addWidget(self.menuBtn)

        self.appHeader = QLabel(self.widget)
        self.appHeader.setObjectName(u"appHeader")
        font2 = QFont()
        font2.setPointSize(13)
        font2.setBold(True)
        font2.setItalic(False)
        font2.setUnderline(False)
        font2.setWeight(QFont.Weight.Bold)
        font2.setStrikeOut(False)
        font2.setKerning(True)
        self.appHeader.setFont(font2)

        self.horizontalLayout_3.addWidget(self.appHeader)


        self.horizontalLayout_2.addWidget(self.widget, 0, Qt.AlignLeft|Qt.AlignTop)

        self.widget_2 = QWidget(self.headerFrame)
        self.widget_2.setObjectName(u"widget_2")
        self.horizontalLayout_4 = QHBoxLayout(self.widget_2)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.searchFrame = QFrame(self.widget_2)
        self.searchFrame.setObjectName(u"searchFrame")
        self.searchFrame.setMinimumSize(QSize(160, 0))
        self.searchFrame.setFrameShape(QFrame.StyledPanel)
        self.searchFrame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.searchFrame)
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.label_2 = QLabel(self.searchFrame)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMaximumSize(QSize(24, 16777215))
        self.label_2.setAutoFillBackground(False)
        self.label_2.setPixmap(QPixmap(u":/blueIcons/icons/search.svg"))
        self.label_2.setScaledContents(False)
        self.label_2.setWordWrap(False)
        self.label_2.setOpenExternalLinks(False)

        self.horizontalLayout_5.addWidget(self.label_2)

        self.lineEdit = QLineEdit(self.searchFrame)
        self.lineEdit.setObjectName(u"lineEdit")

        self.horizontalLayout_5.addWidget(self.lineEdit)


        self.horizontalLayout_4.addWidget(self.searchFrame, 0, Qt.AlignTop)


        self.horizontalLayout_2.addWidget(self.widget_2, 0, Qt.AlignHCenter)

        self.widget_3 = QWidget(self.headerFrame)
        self.widget_3.setObjectName(u"widget_3")
        self.horizontalLayout_6 = QHBoxLayout(self.widget_3)
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.pushButton = QPushButton(self.widget_3)
        self.pushButton.setObjectName(u"pushButton")
        sizePolicy3 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy3)
        icon6 = QIcon()
        icon6.addFile(u":/blueIcons/icons/bell (1).svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton.setIcon(icon6)
        self.pushButton.setIconSize(QSize(30, 30))

        self.horizontalLayout_6.addWidget(self.pushButton)

        self.accountBtn = QPushButton(self.widget_3)
        self.accountBtn.setObjectName(u"accountBtn")
        icon7 = QIcon()
        icon7.addFile(u":/blueIcons/icons/user.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.accountBtn.setIcon(icon7)
        self.accountBtn.setIconSize(QSize(35, 35))

        self.horizontalLayout_6.addWidget(self.accountBtn)


        self.horizontalLayout_2.addWidget(self.widget_3, 0, Qt.AlignRight|Qt.AlignTop)


        self.verticalLayout.addWidget(self.headerFrame)

        self.cardsFrame = QWidget(self.mainBody)
        self.cardsFrame.setObjectName(u"cardsFrame")
        self.horizontalLayout_7 = QHBoxLayout(self.cardsFrame)
        self.horizontalLayout_7.setSpacing(20)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(10, 10, 10, 10)
        self.card1 = QFrame(self.cardsFrame)
        self.card1.setObjectName(u"card1")
        self.card1.setFrameShape(QFrame.StyledPanel)
        self.card1.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.card1)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.frame = QFrame(self.card1)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_8 = QHBoxLayout(self.frame)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")
        font3 = QFont()
        font3.setPointSize(14)
        font3.setBold(True)
        font3.setWeight(QFont.Weight.Bold)
        self.label.setFont(font3)

        self.horizontalLayout_8.addWidget(self.label)

        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMinimumSize(QSize(0, 0))
        self.label_3.setLineWidth(1)
        self.label_3.setPixmap(QPixmap(u":/blueIcons/icons/photograph-art-svgrepo-com (1).svg"))
        self.label_3.setScaledContents(False)
        self.label_3.setMargin(1)
        self.label_3.setIndent(0)
###
        self.horizontalLayout_8.addWidget(self.label_3, 0, Qt.AlignLeft)


        self.verticalLayout_2.addWidget(self.frame)

        self.label_4 = QLabel(self.card1)
        self.label_4.setObjectName(u"label_4")
        font4 = QFont()
        font4.setPointSize(8)
        font4.setBold(True)
        font4.setWeight(QFont.Weight.Bold)
        self.label_4.setFont(font4)

        self.verticalLayout_2.addWidget(self.label_4, 0, Qt.AlignTop)

        self.label_works_sub = QLabel(self.card1)
        self.label_works_sub.setObjectName(u"label_works_sub")
        font_sub = QFont()
        font_sub.setPointSize(7)
        font_sub.setBold(False)
        font_sub.setWeight(QFont.Weight.Normal)
        self.label_works_sub.setFont(font_sub)
        self.label_works_sub.setWordWrap(True)
        self.label_works_sub.setStyleSheet("color: #6b7280;")  # διακριτικό γκρι
        self.verticalLayout_2.addWidget(self.label_works_sub, 0, Qt.AlignTop)


        self.horizontalLayout_7.addWidget(self.card1)

        self.card2 = QFrame(self.cardsFrame)
        self.card2.setObjectName(u"card2")
        self.card2.setFrameShape(QFrame.StyledPanel)
        self.card2.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.card2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.frame_2 = QFrame(self.card2)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_9 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.label_6 = QLabel(self.frame_2)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setFont(font3)

        self.horizontalLayout_9.addWidget(self.label_6)

        self.label_7 = QLabel(self.frame_2)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setMinimumSize(QSize(0, 0))
        self.label_7.setPixmap(QPixmap(u":/blueIcons/icons/event (1).svg"))

        self.horizontalLayout_9.addWidget(self.label_7)


        self.verticalLayout_3.addWidget(self.frame_2)

        self.label_5 = QLabel(self.card2)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font4)

        self.verticalLayout_3.addWidget(self.label_5, 0, Qt.AlignTop)


        self.horizontalLayout_7.addWidget(self.card2)

        self.card4 = QFrame(self.cardsFrame)
        self.card4.setObjectName(u"card4")
        self.card4.setFrameShape(QFrame.StyledPanel)
        self.card4.setFrameShadow(QFrame.Raised)
        self.verticalLayout_5 = QVBoxLayout(self.card4)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.frame_4 = QFrame(self.card4)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.StyledPanel)
        self.frame_4.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_11 = QHBoxLayout(self.frame_4)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.label_12 = QLabel(self.frame_4)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setFont(font3)

        self.horizontalLayout_11.addWidget(self.label_12)

        self.label_13 = QLabel(self.frame_4)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setMinimumSize(QSize(0, 0))
        self.label_13.setPixmap(QPixmap(u":/blueIcons/icons/tools (1).svg"))

        self.horizontalLayout_11.addWidget(self.label_13)


        self.verticalLayout_5.addWidget(self.frame_4)

        self.label_11 = QLabel(self.card4)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setFont(font4)

        self.verticalLayout_5.addWidget(self.label_11, 0, Qt.AlignTop)


        self.horizontalLayout_7.addWidget(self.card4)

        self.card3 = QFrame(self.cardsFrame)
        self.card3.setObjectName(u"card3")
        self.card3.setFrameShape(QFrame.StyledPanel)
        self.card3.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.card3)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.frame_3 = QFrame(self.card3)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_10 = QHBoxLayout(self.frame_3)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.label_9 = QLabel(self.frame_3)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setFont(font3)

        self.horizontalLayout_10.addWidget(self.label_9)

        self.label_10 = QLabel(self.frame_3)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setMinimumSize(QSize(0, 0))
        self.label_10.setPixmap(QPixmap(u":/blueIcons/icons/recruitment (1) (2).svg"))

        self.horizontalLayout_10.addWidget(self.label_10)


        self.verticalLayout_4.addWidget(self.frame_3)

        self.label_8 = QLabel(self.card3)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setFont(font4)

        self.verticalLayout_4.addWidget(self.label_8, 0, Qt.AlignTop)
        self.label_staff_sub = QLabel(self.card3)
        self.label_staff_sub.setObjectName(u"label_staff_sub")
        font_sub = QFont()
        font_sub.setPointSize(7)
        self.label_staff_sub.setFont(font_sub)
        self.label_staff_sub.setWordWrap(True)
        self.label_staff_sub.setStyleSheet("color: #6b7280;")
        self.verticalLayout_4.addWidget(self.label_staff_sub, 0, Qt.AlignTop)



        self.horizontalLayout_7.addWidget(self.card3)


        self.verticalLayout.addWidget(self.cardsFrame)

        self.mainFrame = QWidget(self.mainBody)
        self.mainFrame.setObjectName(u"mainFrame")
        sizePolicy.setHeightForWidth(self.mainFrame.sizePolicy().hasHeightForWidth())
        self.mainFrame.setSizePolicy(sizePolicy)
        self.horizontalLayout_12 = QHBoxLayout(self.mainFrame)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.widget_4 = QWidget(self.mainFrame)
        self.widget_4.setObjectName(u"widget_4")
        self.verticalLayout_6 = QVBoxLayout(self.widget_4)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.frame_5 = QFrame(self.widget_4)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.StyledPanel)
        self.frame_5.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_13 = QHBoxLayout(self.frame_5)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.label_14 = QLabel(self.frame_5)
        self.label_14.setObjectName(u"label_14")
        font5 = QFont()
        font5.setPointSize(9)
        font5.setBold(True)
        font5.setWeight(QFont.Weight.Bold)
        self.label_14.setFont(font5)
        self.label_14.setAutoFillBackground(False)
        self.label_14.setScaledContents(False)

        self.horizontalLayout_13.addWidget(self.label_14, 0, Qt.AlignLeft)


        self.verticalLayout_6.addWidget(self.frame_5, 0, Qt.AlignTop)

        self.frame_6 = QFrame(self.widget_4)
        self.frame_6.setObjectName(u"frame_6")
        self.frame_6.setFrameShape(QFrame.StyledPanel)
        self.frame_6.setFrameShadow(QFrame.Raised)
        self.graphicsView = QGraphicsView(self.frame_6)
        self.graphicsView.setObjectName(u"graphicsView")
        self.graphicsView.setGeometry(QRect(45, 1, 391, 231))

        self.verticalLayout_6.addWidget(self.frame_6)

        self.verticalSpacer = QSpacerItem(20, 69, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer)


        self.horizontalLayout_12.addWidget(self.widget_4)

        self.widget_5 = QWidget(self.mainFrame)
        self.widget_5.setObjectName(u"widget_5")
        self.frame_7 = QFrame(self.widget_5)
        self.frame_7.setObjectName(u"frame_7")
        self.frame_7.setGeometry(QRect(0, 10, 487, 36))
        self.frame_7.setFrameShape(QFrame.StyledPanel)
        self.frame_7.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_14 = QHBoxLayout(self.frame_7)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.label_15 = QLabel(self.frame_7)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setFont(font5)
        self.label_15.setAutoFillBackground(False)
        self.label_15.setScaledContents(False)

        self.horizontalLayout_14.addWidget(self.label_15, 0, Qt.AlignLeft)

        self.frame_8 = QFrame(self.widget_5)
        self.frame_8.setObjectName(u"frame_8")
        self.frame_8.setGeometry(QRect(0, 54, 487, 221))
        self.frame_8.setFrameShape(QFrame.StyledPanel)
        self.frame_8.setFrameShadow(QFrame.Raised)
        self.calendarWidget_2 = QCalendarWidget(self.frame_8)
        self.calendarWidget_2.setObjectName(u"calendarWidget_2")
        self.calendarWidget_2.setGeometry(QRect(40, 10, 431, 211))
        sizePolicy2.setHeightForWidth(self.calendarWidget_2.sizePolicy().hasHeightForWidth())
        self.calendarWidget_2.setSizePolicy(sizePolicy2)
        self.calendarWidget_2.setMinimumSize(QSize(0, 0))
        font6 = QFont()
        font6.setBold(False)
        font6.setItalic(False)
        font6.setUnderline(False)
        font6.setWeight(QFont.Weight.Normal)
        self.calendarWidget_2.setFont(font6)
        self.calendarWidget_2.setMouseTracking(False)
        self.calendarWidget_2.setAutoFillBackground(False)
        self.calendarWidget_2.setGridVisible(False)
        self.calendarWidget_2.setNavigationBarVisible(True)
        self.calendarWidget_2.setDateEditEnabled(True)

        self.horizontalLayout_12.addWidget(self.widget_5)


        self.verticalLayout.addWidget(self.mainFrame)


        self.horizontalLayout.addWidget(self.mainBody)

        self.Profile = QWidget(self.centralwidget)
        self.Profile.setObjectName(u"Profile")
        self.Profile.setMinimumSize(QSize(100, 0))
        self.verticalLayout_11 = QVBoxLayout(self.Profile)
        self.verticalLayout_11.setSpacing(0)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.verticalLayout_11.setContentsMargins(0, 0, 0, -1)
        self.frame_13 = QFrame(self.Profile)
        self.frame_13.setObjectName(u"frame_13")
        self.frame_13.setMinimumSize(QSize(125, 557))
        self.frame_13.setLayoutDirection(Qt.LeftToRight)
        self.frame_13.setFrameShape(QFrame.StyledPanel)
        self.frame_13.setFrameShadow(QFrame.Raised)
        self.frame_13.setLineWidth(1)
        self.verticalLayout_12 = QVBoxLayout(self.frame_13)
        self.verticalLayout_12.setSpacing(0)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.verticalLayout_12.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout_12.setContentsMargins(-1, -1, 9, 480)
        self.label_18 = QLabel(self.frame_13)
        self.label_18.setObjectName(u"label_18")
        font7 = QFont()
        font7.setPointSize(10)
        font7.setBold(True)
        font7.setWeight(QFont.Weight.Bold)
        self.label_18.setFont(font7)
        self.label_18.setAlignment(Qt.AlignCenter)

        self.verticalLayout_12.addWidget(self.label_18, 0, Qt.AlignTop)

        self.pushButton_7 = QPushButton(self.frame_13)
        self.pushButton_7.setObjectName(u"pushButton_7")
        self.pushButton_7.hide()
        
        icon8 = QIcon()
        icon8.addFile(u":/blueIcons/icons/users.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_7.setIcon(icon8)

        self.verticalLayout_12.addWidget(self.pushButton_7)

        self.pushButton_8 = QPushButton(self.frame_13)
        self.pushButton_8.setObjectName(u"pushButton_8")
        icon9 = QIcon()
        icon9.addFile(u":/blueIcons/icons/log-out.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_8.setIcon(icon9)
        self.pushButton_8.setIconSize(QSize(16, 16))

        self.verticalLayout_12.addWidget(self.pushButton_8, 0, Qt.AlignTop)


        self.verticalLayout_11.addWidget(self.frame_13)


        self.horizontalLayout.addWidget(self.Profile, 0, Qt.AlignTop)

                # ========= SHADOWS ΣΕ CARDS & WIDGETS =========
        self._addShadow(self.card1)
        self._addShadow(self.card2)
        self._addShadow(self.card3)
        self._addShadow(self.card4)

        # κάτω widgets (στατιστικά + ημερολόγιο)
        self._addShadow(self.widget_4)
        self._addShadow(self.widget_5)

        # προαιρετικά και στο δεξί profile panel
        self._addShadow(self.Profile, blur=25, yOffset=4, alpha=50)
        # ==============================================


        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label_17.setText(QCoreApplication.translate(
            "MainWindow",
            u"<html><head/><body><p><span style=\" color:#ffffff;\">ArtFlow</span></p></body></html>",
            None
        ))

        self.pushButton_2.setText(QCoreApplication.translate("MainWindow", u"\u0391\u03a1\u03a7\u0399\u039a\u0397", None))
        self.pushButton_3.setText(QCoreApplication.translate("MainWindow", u"\u0395\u03a1\u0393\u0391", None))
        self.pushButton_4.setText(QCoreApplication.translate("MainWindow", u"\u0395\u039a\u0398\u0395\u03a3\u0395\u0399\u03a3", None))
        self.pushButton_5.setText(QCoreApplication.translate("MainWindow", u"\u03a3\u03a5\u039d\u03a4\u0397\u03a1\u0397\u03a3\u0397", None))
        self.pushButton_6.setText(QCoreApplication.translate("MainWindow", u"\u03a0\u03a1\u039f\u03a3\u03a9\u03a0\u0399\u039a\u039f", None))
        self.menuBtn.setText("")
        self.appHeader.setText(QCoreApplication.translate("MainWindow", u"Menu", None))
        self.label_2.setText("")
        self.lineEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Search", None))
        self.pushButton.setText("")
        self.accountBtn.setText("")
        self.label.setText(QCoreApplication.translate("MainWindow", u"50", None))
        self.label_3.setText("")
        self.label_4.setText(QCoreApplication.translate("MainWindow", u" \u0395\u03a1\u0393\u0391", None))
        self.label_works_sub.setText(QCoreApplication.translate("MainWindow", u"", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"50", None))
        self.label_7.setText("")
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"\u0395\u039a\u0398\u0395\u03a3\u0395\u0399\u03a3", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"50", None))
        self.label_13.setText("")
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"\u03a3\u03a5\u039d\u03a4\u0397\u03a1\u0397\u03a3\u0397", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"50", None))
        self.label_10.setText("")
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"\u03a0\u03a1\u039f\u03a3\u03a9\u03a0\u0399\u039a\u039f", None))
        self.label_staff_sub.setText(QCoreApplication.translate("MainWindow", u"", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"\u03a3\u03a4\u0391\u03a4\u0399\u03a3\u03a4\u0399\u039a\u0391", None))
        self.label_15.setText(QCoreApplication.translate("MainWindow", u"\u0397\u039c\u0395\u03a1\u039f\u039b\u039f\u0393\u0399\u039f", None))
        self.label_18.setText(QCoreApplication.translate("MainWindow", u"\u039f\u039d\u039f\u039c\u0391", None))
        self.pushButton_7.setText(QCoreApplication.translate("MainWindow", u"\u03a4\u039f \u03a0\u03a1\u039f\u03a6\u0399\u039b \u039c\u039f\u03a5", None))
        self.pushButton_8.setText(QCoreApplication.translate("MainWindow", u"\u0391\u03a0\u039f\u03a3\u03a5\u039d\u0394\u0395\u03a3\u0397", None))
    # retranslateUi
    def _addShadow(self, widget, blur=30, xOffset=0, yOffset=3, alpha=60):
        """Βάζει drop shadow σε ένα widget."""
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur)
        shadow.setOffset(xOffset, yOffset)
        c = QColor(0, 0, 0)
        c.setAlpha(alpha)
        shadow.setColor(c)
        widget.setGraphicsEffect(shadow)

