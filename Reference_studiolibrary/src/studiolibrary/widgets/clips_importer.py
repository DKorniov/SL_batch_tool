# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'clips_importer.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(924, 300)
        Dialog.setMinimumSize(QSize(400, 300))
        Dialog.setAcceptDrops(True)
        Dialog.setWindowTitle(u"Import Animation Clips")
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 12, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.clipsLayout = QVBoxLayout()
        self.clipsLayout.setObjectName(u"clipsLayout")
        self.clipsTitleLabel = QLabel(Dialog)
        self.clipsTitleLabel.setObjectName(u"clipsTitleLabel")
        self.clipsTitleLabel.setText(u"Anim Clips Folder")

        self.clipsLayout.addWidget(self.clipsTitleLabel)

        self.line = QFrame(Dialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.clipsLayout.addWidget(self.line)

        self.addClipsButton = QPushButton(Dialog)
        self.addClipsButton.setObjectName(u"addClipsButton")
        self.addClipsButton.setText(u"Add clips folder")

        self.clipsLayout.addWidget(self.addClipsButton)

        self.removeClipsButton = QPushButton(Dialog)
        self.removeClipsButton.setObjectName(u"removeClipsButton")
        self.removeClipsButton.setText(u"Remove clips folder")

        self.clipsLayout.addWidget(self.removeClipsButton)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.clipsLayout.addItem(self.verticalSpacer)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.clipsLayout.addItem(self.horizontalSpacer)


        self.horizontalLayout.addLayout(self.clipsLayout)

        self.charSetsLayout = QVBoxLayout()
        self.charSetsLayout.setObjectName(u"charSetsLayout")
        self.charsetTitleLabel = QLabel(Dialog)
        self.charsetTitleLabel.setObjectName(u"charsetTitleLabel")
        self.charsetTitleLabel.setText(u"Charset")

        self.charSetsLayout.addWidget(self.charsetTitleLabel)

        self.line_2 = QFrame(Dialog)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.charSetsLayout.addWidget(self.line_2)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.charSetsLayout.addItem(self.horizontalSpacer_2)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.charSetsLayout.addItem(self.verticalSpacer_2)


        self.horizontalLayout.addLayout(self.charSetsLayout)

        self.cameraLayout = QVBoxLayout()
        self.cameraLayout.setObjectName(u"cameraLayout")
        self.cameraTitleLabel = QLabel(Dialog)
        self.cameraTitleLabel.setObjectName(u"cameraTitleLabel")

        self.cameraLayout.addWidget(self.cameraTitleLabel)

        self.line_3 = QFrame(Dialog)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.cameraLayout.addWidget(self.line_3)

        self.cameraHorizontalLayout = QHBoxLayout()
        self.cameraHorizontalLayout.setObjectName(u"cameraHorizontalLayout")
        self.cameraTitleLabel_2 = QLabel(Dialog)
        self.cameraTitleLabel_2.setObjectName(u"cameraTitleLabel_2")
        self.cameraTitleLabel_2.setMaximumSize(QSize(50, 16777215))
        self.cameraTitleLabel_2.setText(u"Camera:")
        self.cameraTitleLabel_2.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.cameraHorizontalLayout.addWidget(self.cameraTitleLabel_2)

        self.cameraComboBox = QComboBox(Dialog)
        self.cameraComboBox.setObjectName(u"cameraComboBox")
        self.cameraComboBox.setCurrentText(u"")

        self.cameraHorizontalLayout.addWidget(self.cameraComboBox)


        self.cameraLayout.addLayout(self.cameraHorizontalLayout)

        self.outputFolderHorizontalLayout = QHBoxLayout()
        self.outputFolderHorizontalLayout.setObjectName(u"outputFolderHorizontalLayout")
        self.outputFolderTitleLabel = QLabel(Dialog)
        self.outputFolderTitleLabel.setObjectName(u"outputFolderTitleLabel")
        self.outputFolderTitleLabel.setMaximumSize(QSize(70, 16777215))
        self.outputFolderTitleLabel.setText(u"Output folder:")
        self.outputFolderTitleLabel.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.outputFolderHorizontalLayout.addWidget(self.outputFolderTitleLabel)

        self.outputFolderLineEdit = QLineEdit(Dialog)
        self.outputFolderLineEdit.setObjectName(u"outputFolderLineEdit")

        self.outputFolderHorizontalLayout.addWidget(self.outputFolderLineEdit)

        self.outputFolderButton = QPushButton(Dialog)
        self.outputFolderButton.setObjectName(u"outputFolderButton")
        self.outputFolderButton.setMaximumSize(QSize(25, 20))
        self.outputFolderButton.setText(u"...")

        self.outputFolderHorizontalLayout.addWidget(self.outputFolderButton)


        self.cameraLayout.addLayout(self.outputFolderHorizontalLayout)

        self.startImportButton = QPushButton(Dialog)
        self.startImportButton.setObjectName(u"startImportButton")
        self.startImportButton.setMaximumSize(QSize(16777215, 25))
        self.startImportButton.setText(u"Start")

        self.cameraLayout.addWidget(self.startImportButton)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.cameraLayout.addItem(self.horizontalSpacer_3)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.cameraLayout.addItem(self.verticalSpacer_3)


        self.horizontalLayout.addLayout(self.cameraLayout)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.importProgressBar = QProgressBar(Dialog)
        self.importProgressBar.setObjectName(u"importProgressBar")
        self.importProgressBar.setValue(0)

        self.horizontalLayout_2.addWidget(self.importProgressBar)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.retranslateUi(Dialog)
        self.addClipsButton.clicked.connect(Dialog.onAddClipsFolderButton)
        self.outputFolderButton.clicked.connect(Dialog.onSetOuputFolder)
        self.startImportButton.clicked.connect(Dialog.onStartButton)
        self.cameraComboBox.currentIndexChanged.connect(Dialog.onCameraIndexChange)
        self.removeClipsButton.clicked.connect(Dialog.onRemoveClipsFolderButton)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        self.cameraTitleLabel.setText(QCoreApplication.translate("Dialog", u"Studio Library Settings", None))
        pass
    # retranslateUi

