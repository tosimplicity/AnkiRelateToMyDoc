# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'set_pic_dir.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_set_pic_dir_dialog(object):
    def setupUi(self, set_pic_dir_dialog):
        set_pic_dir_dialog.setObjectName("set_pic_dir_dialog")
        set_pic_dir_dialog.resize(329, 448)
        set_pic_dir_dialog.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(set_pic_dir_dialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.action_buttons = QtWidgets.QHBoxLayout()
        self.action_buttons.setSpacing(6)
        self.action_buttons.setObjectName("action_buttons")
        self.add_dir_button = QtWidgets.QPushButton(set_pic_dir_dialog)
        self.add_dir_button.setEnabled(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/res/res/add.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.add_dir_button.setIcon(icon)
        self.add_dir_button.setObjectName("add_dir_button")
        self.action_buttons.addWidget(self.add_dir_button)
        self.remove_dir_button = QtWidgets.QPushButton(set_pic_dir_dialog)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/res/res/remove.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.remove_dir_button.setIcon(icon1)
        self.remove_dir_button.setCheckable(False)
        self.remove_dir_button.setObjectName("remove_dir_button")
        self.action_buttons.addWidget(self.remove_dir_button)
        self.verticalLayout_2.addLayout(self.action_buttons)
        self.dir_list_widget = QtWidgets.QListWidget(set_pic_dir_dialog)
        self.dir_list_widget.setProperty("isWrapping", False)
        self.dir_list_widget.setWordWrap(False)
        self.dir_list_widget.setObjectName("dir_list_widget")
        self.verticalLayout_2.addWidget(self.dir_list_widget)

        self.retranslateUi(set_pic_dir_dialog)
        QtCore.QMetaObject.connectSlotsByName(set_pic_dir_dialog)

    def retranslateUi(self, set_pic_dir_dialog):
        _translate = QtCore.QCoreApplication.translate
        set_pic_dir_dialog.setWindowTitle(_translate("set_pic_dir_dialog", "Load from Feed"))
        self.add_dir_button.setText(_translate("set_pic_dir_dialog", "Add Directory"))
        self.remove_dir_button.setText(_translate("set_pic_dir_dialog", "Remove Directory"))

from . import myRes_rc
