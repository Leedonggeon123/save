# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'signup.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1280, 800)
        Form.setStyleSheet(u"QWidget{background:white;} QLabel#title_label{color:#0b3d63;font-size:72px;font-weight:800;} QLineEdit{background:#eeeeee;border:0;border-radius:7px;padding:13px 18px;font-size:19px;min-height:38px;} QPushButton{background:#2379aa;color:white;border:0;border-radius:7px;padding:12px 14px;font-size:14px;min-width:130px;} QPushButton#signup_button{font-size:24px;min-height:60px;}")
        self.main_layout = QVBoxLayout(Form)
        self.main_layout.setSpacing(9)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(320, 0, 320, 20)
        self.title_label = QLabel(Form)
        self.title_label.setObjectName(u"title_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.title_label.sizePolicy().hasHeightForWidth())
        self.title_label.setSizePolicy(sizePolicy)
        self.title_label.setMinimumSize(QSize(0, 100))
        self.title_label.setMaximumSize(QSize(16777215, 100))
        self.title_label.setAlignment(Qt.AlignCenter)

        self.main_layout.addWidget(self.title_label)

        self.name_input = QLineEdit(Form)
        self.name_input.setObjectName(u"name_input")

        self.main_layout.addWidget(self.name_input)

        self.phone_input = QLineEdit(Form)
        self.phone_input.setObjectName(u"phone_input")
        self.main_layout.addWidget(self.phone_input)

        self.email_layout = QHBoxLayout()
        self.email_layout.setObjectName(u"email_layout")
        self.email_input = QLineEdit(Form)
        self.email_input.setObjectName(u"email_input")

        self.email_layout.addWidget(self.email_input)

        self.check_email_button = QPushButton(Form)
        self.check_email_button.setObjectName(u"check_email_button")

        self.email_layout.addWidget(self.check_email_button)


        self.main_layout.addLayout(self.email_layout)

        self.code_layout = QHBoxLayout()
        self.code_layout.setObjectName(u"code_layout")
        self.code_input = QLineEdit(Form)
        self.code_input.setObjectName(u"code_input")

        self.code_layout.addWidget(self.code_input)

        self.send_code_button = QPushButton(Form)
        self.send_code_button.setObjectName(u"send_code_button")

        self.code_layout.addWidget(self.send_code_button)

        self.verify_code_button = QPushButton(Form)
        self.verify_code_button.setObjectName(u"verify_code_button")

        self.code_layout.addWidget(self.verify_code_button)


        self.main_layout.addLayout(self.code_layout)

        self.timer_label = QLabel(Form)
        self.timer_label.setObjectName(u"timer_label")
        sizePolicy.setHeightForWidth(self.timer_label.sizePolicy().hasHeightForWidth())
        self.timer_label.setSizePolicy(sizePolicy)
        self.timer_label.setMinimumSize(QSize(0, 24))
        self.timer_label.setMaximumSize(QSize(16777215, 24))

        self.main_layout.addWidget(self.timer_label)

        self.password_input = QLineEdit(Form)
        self.password_input.setObjectName(u"password_input")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.main_layout.addWidget(self.password_input)

        self.password_confirm_input = QLineEdit(Form)
        self.password_confirm_input.setObjectName(u"password_confirm_input")
        self.password_confirm_input.setEchoMode(QLineEdit.Password)

        self.main_layout.addWidget(self.password_confirm_input)

        self.signup_button = QPushButton(Form)
        self.signup_button.setObjectName(u"signup_button")

        self.main_layout.addWidget(self.signup_button)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"JEWEL Cloud - \ud68c\uc6d0\uac00\uc785", None))
        self.title_label.setText(QCoreApplication.translate("Form", u"JEWEL Cloud", None))
        self.name_input.setPlaceholderText(QCoreApplication.translate("Form", u"\uc774\ub984", None))
        self.phone_input.setPlaceholderText(QCoreApplication.translate("Form", u"전화번호 (010-1234-5678)", None))
        self.email_input.setPlaceholderText(QCoreApplication.translate("Form", u"\uad6c\uae00 \uc774\uba54\uc77c", None))
        self.check_email_button.setText(QCoreApplication.translate("Form", u"\uc544\uc774\ub514 \uc911\ubcf5", None))
        self.code_input.setPlaceholderText(QCoreApplication.translate("Form", u"\uc778\uc99d\ubc88\ud638", None))
        self.send_code_button.setText(QCoreApplication.translate("Form", u"\uc778\uc99d\ubc88\ud638 \ubc1c\uc1a1", None))
        self.verify_code_button.setText(QCoreApplication.translate("Form", u"\uc778\uc99d\ubc88\ud638 \ud655\uc778", None))
        self.timer_label.setStyleSheet(QCoreApplication.translate("Form", u"color:#777777;margin-left:18px;", None))
        self.timer_label.setText(QCoreApplication.translate("Form", u"\uc778\uc99d\ubc88\ud638\ub97c \ubc1c\uc1a1\ud558\uba74 \uc720\ud6a8\uc2dc\uac04\uc774 \ud45c\uc2dc\ub429\ub2c8\ub2e4.", None))
        self.password_input.setPlaceholderText(QCoreApplication.translate("Form", u"\ube44\ubc00\ubc88\ud638", None))
        self.password_confirm_input.setPlaceholderText(QCoreApplication.translate("Form", u"\ube44\ubc00\ubc88\ud638 \ud655\uc778", None))
        self.signup_button.setText(QCoreApplication.translate("Form", u"\ud68c\uc6d0\uac00\uc785", None))
    # retranslateUi

