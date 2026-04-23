# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ApplyAllMessageBox.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_applyAllMessageBoxDialog(object):
    def setupUi(self, applyAllMessageBoxDialog):
        if not applyAllMessageBoxDialog.objectName():
            applyAllMessageBoxDialog.setObjectName(u"applyAllMessageBoxDialog")
        applyAllMessageBoxDialog.resize(240, 269)
        applyAllMessageBoxDialog.setWindowTitle(u"Apply animations")
        applyAllMessageBoxDialog.setStyleSheet(u"")
        self.verticalLayoutWidget = QWidget(applyAllMessageBoxDialog)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(-1, 29, 241, 241))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.radioButton_1 = QRadioButton(self.verticalLayoutWidget)
        self.radioButton_1.setObjectName(u"radioButton_1")
        self.radioButton_1.setText(u"Source")
        self.radioButton_1.setChecked(True)

        self.verticalLayout.addWidget(self.radioButton_1)

        self.radioButton_2 = QRadioButton(self.verticalLayoutWidget)
        self.radioButton_2.setObjectName(u"radioButton_2")
        self.radioButton_2.setText(u"One after another")

        self.verticalLayout.addWidget(self.radioButton_2)

        self.radioButton_3 = QRadioButton(self.verticalLayoutWidget)
        self.radioButton_3.setObjectName(u"radioButton_3")
        self.radioButton_3.setText(u"Every 100")

        self.verticalLayout.addWidget(self.radioButton_3)

        self.buttonBox = QDialogButtonBox(self.verticalLayoutWidget)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)

        self.verticalLayout.addWidget(self.buttonBox)

        self.titleFrame = QFrame(applyAllMessageBoxDialog)
        self.titleFrame.setObjectName(u"titleFrame")
        self.titleFrame.setGeometry(QRect(-1, -1, 241, 31))
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.titleFrame.sizePolicy().hasHeightForWidth())
        self.titleFrame.setSizePolicy(sizePolicy)
        self.titleFrame.setFrameShape(QFrame.StyledPanel)
        self.titleFrame.setFrameShadow(QFrame.Raised)
        self.horizontalLayoutWidget = QWidget(self.titleFrame)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(-1, -1, 241, 31))
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(10, 0, 0, 0)
        self.titleLabel = QLabel(self.horizontalLayoutWidget)
        self.titleLabel.setObjectName(u"titleLabel")
        self.titleLabel.setText(u"How apply animation")

        self.horizontalLayout.addWidget(self.titleLabel)


        self.retranslateUi(applyAllMessageBoxDialog)
        self.buttonBox.accepted.connect(applyAllMessageBoxDialog.accept)
        self.buttonBox.rejected.connect(applyAllMessageBoxDialog.reject)
        self.radioButton_1.clicked.connect(applyAllMessageBoxDialog.onRadioOptionSource)
        self.radioButton_2.clicked.connect(applyAllMessageBoxDialog.onRadioOptionQueue)
        self.radioButton_3.clicked.connect(applyAllMessageBoxDialog.onRadioOptionEvery100)

        QMetaObject.connectSlotsByName(applyAllMessageBoxDialog)
    # setupUi

    def retranslateUi(self, applyAllMessageBoxDialog):
        pass
    # retranslateUi

