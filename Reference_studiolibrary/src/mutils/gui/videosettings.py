# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'videosettings.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_settings_preview(object):
    def setupUi(self, settings_preview):
        if not settings_preview.objectName():
            settings_preview.setObjectName(u"settings_preview")
        settings_preview.resize(222, 258)
        settings_preview.setMinimumSize(QSize(500, 500))
        settings_preview.setWindowFilePath(u"")
        self.centralwidget = QWidget(settings_preview)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.sizeComboBox = QComboBox(self.frame)
        self.sizeComboBox.addItem("")
        self.sizeComboBox.addItem("")
        self.sizeComboBox.addItem("")
        self.sizeComboBox.setObjectName(u"sizeComboBox")
        self.sizeComboBox.setCurrentText(u"500 x 500")

        self.verticalLayout_2.addWidget(self.sizeComboBox)

        self.line_2 = QFrame(self.frame)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_2)

        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMaximumSize(QSize(16777215, 30))
        self.label_3.setText(u"Image")

        self.verticalLayout_2.addWidget(self.label_3)

        self.radioButtonJpg = QRadioButton(self.frame)
        self.radioButtonJpg.setObjectName(u"radioButtonJpg")
        self.radioButtonJpg.setMaximumSize(QSize(16777215, 20))
        self.radioButtonJpg.setText(u".jpg")
        self.radioButtonJpg.setChecked(True)

        self.verticalLayout_2.addWidget(self.radioButtonJpg)

        self.radioButtonPng = QRadioButton(self.frame)
        self.radioButtonPng.setObjectName(u"radioButtonPng")
        self.radioButtonPng.setMaximumSize(QSize(16777215, 20))
        self.radioButtonPng.setText(u".png")
        self.radioButtonPng.setChecked(False)

        self.verticalLayout_2.addWidget(self.radioButtonPng)

        self.line = QFrame(self.frame)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line)

        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMaximumSize(QSize(16777215, 30))
        self.label_2.setText(u"Video")
        self.label_2.setTextFormat(Qt.AutoText)

        self.verticalLayout_2.addWidget(self.label_2)

        self.checkBoxMp4 = QCheckBox(self.frame)
        self.checkBoxMp4.setObjectName(u"checkBoxMp4")
        self.checkBoxMp4.setText(u" convert .mp4")
        self.checkBoxMp4.setChecked(True)

        self.verticalLayout_2.addWidget(self.checkBoxMp4)


        self.verticalLayout.addWidget(self.frame)

        settings_preview.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(settings_preview)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 222, 21))
        settings_preview.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(settings_preview)
        self.statusbar.setObjectName(u"statusbar")
        settings_preview.setStatusBar(self.statusbar)

        self.retranslateUi(settings_preview)
        self.checkBoxMp4.stateChanged.connect(settings_preview.onVideoFormatChange)
        self.radioButtonJpg.clicked.connect(settings_preview.onImageFormatJpg)
        self.radioButtonPng.clicked.connect(settings_preview.onImageFormatPng)
        self.sizeComboBox.currentIndexChanged.connect(settings_preview.onSizeChange)

        QMetaObject.connectSlotsByName(settings_preview)
    # setupUi

    def retranslateUi(self, settings_preview):
        settings_preview.setWindowTitle(QCoreApplication.translate("settings_preview", u"settings preview", None))
        self.sizeComboBox.setItemText(0, QCoreApplication.translate("settings_preview", u"500 x 500", None))
        self.sizeComboBox.setItemText(1, QCoreApplication.translate("settings_preview", u"800 x 800", None))
        self.sizeComboBox.setItemText(2, QCoreApplication.translate("settings_preview", u"1000 x 1000", None))

    # retranslateUi

