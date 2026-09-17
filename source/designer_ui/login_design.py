# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'login.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_LoginPage(object):
    def setupUi(self, LoginPage):
        if not LoginPage.objectName():
            LoginPage.setObjectName(u"LoginPage")
        LoginPage.resize(1280, 800)
        LoginPage.setStyleSheet(u"QWidget#LoginPage{background:#ffffff;} QFrame#top_bar{background:#ffffff;} QLabel#title_label{color:#0b3d63;font-size:72px;font-weight:800;} QLineEdit{background:#eeeeee;color:#858585;border:0;border-radius:7px;padding:13px 20px;font-size:22px;min-height:38px;} QPushButton{border:0;} QPushButton#login_button{background:#2379aa;color:white;border-radius:7px;font-size:30px;min-height:92px;} QPushButton#find_password_button,QPushButton#signup_button{background:transparent;color:#858585;font-size:22px;min-width:120px;}")
        self.outer_layout = QVBoxLayout(LoginPage)
        self.outer_layout.setSpacing(0)
        self.outer_layout.setObjectName(u"outer_layout")
        self.outer_layout.setContentsMargins(0, 0, 0, 0)
        self.top_bar = QFrame(LoginPage)
        self.top_bar.setObjectName(u"top_bar")
        self.top_bar.setMinimumSize(QSize(0, 40))
        self.top_bar.setMaximumSize(QSize(16777215, 40))
        self.top_bar.setFrameShape(QFrame.NoFrame)

        self.outer_layout.addWidget(self.top_bar)

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(0)
        self.content_layout.setObjectName(u"content_layout")
        self.content_layout.setContentsMargins(322, 88, 322, 100)
        self.title_label = QLabel(LoginPage)
        self.title_label.setObjectName(u"title_label")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.content_layout.addWidget(self.title_label)

        self.title_spacer = QSpacerItem(20, 64, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.content_layout.addItem(self.title_spacer)

        self.email_input = QLineEdit(LoginPage)
        self.email_input.setObjectName(u"email_input")
        self.email_input.setMinimumSize(QSize(0, 64))

        self.content_layout.addWidget(self.email_input)

        self.email_spacer = QSpacerItem(20, 44, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.content_layout.addItem(self.email_spacer)

        self.password_input = QLineEdit(LoginPage)
        self.password_input.setObjectName(u"password_input")
        self.password_input.setMinimumSize(QSize(0, 64))
        self.password_input.setEchoMode(QLineEdit.Password)

        self.content_layout.addWidget(self.password_input)

        self.password_spacer = QSpacerItem(20, 72, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.content_layout.addItem(self.password_spacer)

        self.login_button = QPushButton(LoginPage)
        self.login_button.setObjectName(u"login_button")

        self.content_layout.addWidget(self.login_button)

        self.button_spacer = QSpacerItem(20, 38, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.content_layout.addItem(self.button_spacer)

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setObjectName(u"bottom_layout")
        self.find_password_button = QPushButton(LoginPage)
        self.find_password_button.setObjectName(u"find_password_button")

        self.bottom_layout.addWidget(self.find_password_button)

        self.link_spacer = QSpacerItem(300, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.bottom_layout.addItem(self.link_spacer)

        self.signup_button = QPushButton(LoginPage)
        self.signup_button.setObjectName(u"signup_button")

        self.bottom_layout.addWidget(self.signup_button)


        self.content_layout.addLayout(self.bottom_layout)


        self.outer_layout.addLayout(self.content_layout)


        self.retranslateUi(LoginPage)

        QMetaObject.connectSlotsByName(LoginPage)
    # setupUi

    def retranslateUi(self, LoginPage):
        LoginPage.setWindowTitle(QCoreApplication.translate("LoginPage", u"JEWEL Cloud - \ub85c\uadf8\uc778", None))
        self.title_label.setText(QCoreApplication.translate("LoginPage", u"JEWEL Cloud", None))
        self.email_input.setPlaceholderText(QCoreApplication.translate("LoginPage", u"\uc544\uc774\ub514", None))
        self.password_input.setPlaceholderText(QCoreApplication.translate("LoginPage", u"\ube44\ubc00\ubc88\ud638", None))
        self.login_button.setText(QCoreApplication.translate("LoginPage", u"\ub85c\uadf8\uc778", None))
        self.find_password_button.setText(QCoreApplication.translate("LoginPage", u"\ube44\ubc00\ubc88\ud638 \ucc3e\uae30", None))
        self.signup_button.setText(QCoreApplication.translate("LoginPage", u"\ud68c\uc6d0\uac00\uc785", None))
    # retranslateUi

