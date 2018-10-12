# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'note_type_setting.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_note_type_setting_dialog(object):
    def setupUi(self, note_type_setting_dialog):
        note_type_setting_dialog.setObjectName("note_type_setting_dialog")
        note_type_setting_dialog.resize(422, 457)
        note_type_setting_dialog.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(note_type_setting_dialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(note_type_setting_dialog)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.all_note_type_listWidget = QtWidgets.QListWidget(note_type_setting_dialog)
        self.all_note_type_listWidget.setObjectName("all_note_type_listWidget")
        self.verticalLayout.addWidget(self.all_note_type_listWidget)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.add_note_type_button = QtWidgets.QPushButton(note_type_setting_dialog)
        self.add_note_type_button.setObjectName("add_note_type_button")
        self.horizontalLayout_2.addWidget(self.add_note_type_button)
        self.remove_note_type_button = QtWidgets.QPushButton(note_type_setting_dialog)
        self.remove_note_type_button.setObjectName("remove_note_type_button")
        self.horizontalLayout_2.addWidget(self.remove_note_type_button)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.label_2 = QtWidgets.QLabel(note_type_setting_dialog)
        self.label_2.setWordWrap(True)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.target_note_type_listWidget = QtWidgets.QListWidget(note_type_setting_dialog)
        self.target_note_type_listWidget.setObjectName("target_note_type_listWidget")
        self.verticalLayout.addWidget(self.target_note_type_listWidget)
        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.retranslateUi(note_type_setting_dialog)
        QtCore.QMetaObject.connectSlotsByName(note_type_setting_dialog)

    def retranslateUi(self, note_type_setting_dialog):
        _translate = QtCore.QCoreApplication.translate
        note_type_setting_dialog.setWindowTitle(_translate("note_type_setting_dialog", "Set Note Type to Relate"))
        self.label.setText(_translate("note_type_setting_dialog", "Note Type List"))
        self.add_note_type_button.setText(_translate("note_type_setting_dialog", "↓Add Note Type Selected Above"))
        self.remove_note_type_button.setText(_translate("note_type_setting_dialog", "↑Remove Note Type Selected Below"))
        self.label_2.setText(_translate("note_type_setting_dialog", "Card with note type listed below will activate add-on to show ralated doc. Add/Remove note type included."))

from . import myRes_rc
