# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'relate_to_my_doc.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_relate_to_my_doc_dialog(object):
    def setupUi(self, relate_to_my_doc_dialog):
        relate_to_my_doc_dialog.setObjectName("relate_to_my_doc_dialog")
        relate_to_my_doc_dialog.resize(585, 469)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(relate_to_my_doc_dialog.sizePolicy().hasHeightForWidth())
        relate_to_my_doc_dialog.setSizePolicy(sizePolicy)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(relate_to_my_doc_dialog)
        self.verticalLayout_2.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tabWidget = QtWidgets.QTabWidget(relate_to_my_doc_dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.tabWidget.setObjectName("tabWidget")
        self.text_tab = QtWidgets.QWidget()
        self.text_tab.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.text_tab.setObjectName("text_tab")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.text_tab)
        self.verticalLayout.setContentsMargins(12, 12, 12, 12)
        self.verticalLayout.setSpacing(12)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_text = QtWidgets.QVBoxLayout()
        self.verticalLayout_text.setObjectName("verticalLayout_text")
        self.horizontalLayout_filt = QtWidgets.QHBoxLayout()
        self.horizontalLayout_filt.setObjectName("horizontalLayout_filt")
        self.label_3 = QtWidgets.QLabel(self.text_tab)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_filt.addWidget(self.label_3)
        self.fav_filter_checkbox = QtWidgets.QCheckBox(self.text_tab)
        self.fav_filter_checkbox.setObjectName("fav_filter_checkbox")
        self.horizontalLayout_filt.addWidget(self.fav_filter_checkbox)
        self.unfav_filter_checkbox = QtWidgets.QCheckBox(self.text_tab)
        self.unfav_filter_checkbox.setObjectName("unfav_filter_checkbox")
        self.horizontalLayout_filt.addWidget(self.unfav_filter_checkbox)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_filt.addItem(spacerItem)
        self.verticalLayout_text.addLayout(self.horizontalLayout_filt)
        self.horizontalLayout_navigate = QtWidgets.QHBoxLayout()
        self.horizontalLayout_navigate.setObjectName("horizontalLayout_navigate")
        self.prev_doc_button = QtWidgets.QPushButton(self.text_tab)
        self.prev_doc_button.setAutoDefault(False)
        self.prev_doc_button.setObjectName("prev_doc_button")
        self.horizontalLayout_navigate.addWidget(self.prev_doc_button)
        self.next_doc_button = QtWidgets.QPushButton(self.text_tab)
        self.next_doc_button.setDefault(True)
        self.next_doc_button.setObjectName("next_doc_button")
        self.horizontalLayout_navigate.addWidget(self.next_doc_button)
        self.label_2 = QtWidgets.QLabel(self.text_tab)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_navigate.addWidget(self.label_2)
        self.mark_fav_doc_button = QtWidgets.QPushButton(self.text_tab)
        self.mark_fav_doc_button.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/res/res/grey_heart.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.mark_fav_doc_button.setIcon(icon)
        self.mark_fav_doc_button.setCheckable(False)
        self.mark_fav_doc_button.setFlat(True)
        self.mark_fav_doc_button.setObjectName("mark_fav_doc_button")
        self.horizontalLayout_navigate.addWidget(self.mark_fav_doc_button)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_navigate.addItem(spacerItem1)
        self.del_doc_button = QtWidgets.QPushButton(self.text_tab)
        self.del_doc_button.setAutoDefault(False)
        self.del_doc_button.setObjectName("del_doc_button")
        self.horizontalLayout_navigate.addWidget(self.del_doc_button)
        self.verticalLayout_text.addLayout(self.horizontalLayout_navigate)
        self.verticalLayout.addLayout(self.verticalLayout_text)
        self.qweb_progress_bar = QtWidgets.QProgressBar(self.text_tab)
        self.qweb_progress_bar.setProperty("value", 0)
        self.qweb_progress_bar.setObjectName("qweb_progress_bar")
        self.verticalLayout.addWidget(self.qweb_progress_bar)
        self.tabWidget.addTab(self.text_tab, "")
        self.pic_tab = QtWidgets.QWidget()
        self.pic_tab.setBaseSize(QtCore.QSize(0, 7))
        self.pic_tab.setObjectName("pic_tab")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.pic_tab)
        self.verticalLayout_4.setContentsMargins(12, 12, 12, 12)
        self.verticalLayout_4.setSpacing(12)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.prev_pic_button = QtWidgets.QPushButton(self.pic_tab)
        self.prev_pic_button.setObjectName("prev_pic_button")
        self.horizontalLayout.addWidget(self.prev_pic_button)
        self.next_pic_button = QtWidgets.QPushButton(self.pic_tab)
        self.next_pic_button.setObjectName("next_pic_button")
        self.horizontalLayout.addWidget(self.next_pic_button)
        self.verticalLayout_4.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_5 = QtWidgets.QLabel(self.pic_tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_2.addWidget(self.label_5)
        self.pic_link_label = QtWidgets.QLabel(self.pic_tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pic_link_label.sizePolicy().hasHeightForWidth())
        self.pic_link_label.setSizePolicy(sizePolicy)
        self.pic_link_label.setText("")
        self.pic_link_label.setObjectName("pic_link_label")
        self.horizontalLayout_2.addWidget(self.pic_link_label)
        self.verticalLayout_4.addLayout(self.horizontalLayout_2)
        self.pic_label = QtWidgets.QLabel(self.pic_tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pic_label.sizePolicy().hasHeightForWidth())
        self.pic_label.setSizePolicy(sizePolicy)
        self.pic_label.setText("")
        self.pic_label.setAlignment(QtCore.Qt.AlignCenter)
        self.pic_label.setObjectName("pic_label")
        self.verticalLayout_4.addWidget(self.pic_label)
        self.tabWidget.addTab(self.pic_tab, "")
        self.media_tab = QtWidgets.QWidget()
        self.media_tab.setObjectName("media_tab")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.media_tab)
        self.verticalLayout_3.setContentsMargins(12, 12, 12, 12)
        self.verticalLayout_3.setSpacing(12)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label = QtWidgets.QLabel(self.media_tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.horizontalLayout_3.addWidget(self.label)
        self.media_link_label = QtWidgets.QLabel(self.media_tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.media_link_label.sizePolicy().hasHeightForWidth())
        self.media_link_label.setSizePolicy(sizePolicy)
        self.media_link_label.setObjectName("media_link_label")
        self.horizontalLayout_3.addWidget(self.media_link_label)
        self.verticalLayout_3.addLayout(self.horizontalLayout_3)
        self.mplayer_widget_container = QtWidgets.QLabel(self.media_tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mplayer_widget_container.sizePolicy().hasHeightForWidth())
        self.mplayer_widget_container.setSizePolicy(sizePolicy)
        self.mplayer_widget_container.setText("")
        self.mplayer_widget_container.setScaledContents(True)
        self.mplayer_widget_container.setObjectName("mplayer_widget_container")
        self.verticalLayout_3.addWidget(self.mplayer_widget_container)
        self.media_text_listWidget = QtWidgets.QListWidget(self.media_tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.media_text_listWidget.sizePolicy().hasHeightForWidth())
        self.media_text_listWidget.setSizePolicy(sizePolicy)
        self.media_text_listWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.media_text_listWidget.setObjectName("media_text_listWidget")
        self.verticalLayout_3.addWidget(self.media_text_listWidget)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.prev_media_button = QtWidgets.QPushButton(self.media_tab)
        self.prev_media_button.setAutoDefault(False)
        self.prev_media_button.setObjectName("prev_media_button")
        self.horizontalLayout_4.addWidget(self.prev_media_button)
        self.play_again_button = QtWidgets.QPushButton(self.media_tab)
        self.play_again_button.setObjectName("play_again_button")
        self.horizontalLayout_4.addWidget(self.play_again_button)
        self.next_media_button = QtWidgets.QPushButton(self.media_tab)
        self.next_media_button.setObjectName("next_media_button")
        self.horizontalLayout_4.addWidget(self.next_media_button)
        self.label_6 = QtWidgets.QLabel(self.media_tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)
        self.label_6.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_4.addWidget(self.label_6)
        self.mark_fav_media_button = QtWidgets.QPushButton(self.media_tab)
        self.mark_fav_media_button.setText("")
        self.mark_fav_media_button.setIcon(icon)
        self.mark_fav_media_button.setFlat(True)
        self.mark_fav_media_button.setObjectName("mark_fav_media_button")
        self.horizontalLayout_4.addWidget(self.mark_fav_media_button)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem2)
        self.unreg_media_button = QtWidgets.QPushButton(self.media_tab)
        self.unreg_media_button.setObjectName("unreg_media_button")
        self.horizontalLayout_4.addWidget(self.unreg_media_button)
        self.verticalLayout_3.addLayout(self.horizontalLayout_4)
        self.tabWidget.addTab(self.media_tab, "")
        self.verticalLayout_2.addWidget(self.tabWidget)

        self.retranslateUi(relate_to_my_doc_dialog)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(relate_to_my_doc_dialog)

    def retranslateUi(self, relate_to_my_doc_dialog):
        _translate = QtCore.QCoreApplication.translate
        relate_to_my_doc_dialog.setWindowTitle(_translate("relate_to_my_doc_dialog", "Relate to My Doc"))
        self.label_3.setText(_translate("relate_to_my_doc_dialog", "Showing Up Filter:"))
        self.fav_filter_checkbox.setText(_translate("relate_to_my_doc_dialog", "Favorite"))
        self.unfav_filter_checkbox.setText(_translate("relate_to_my_doc_dialog", "Others"))
        self.prev_doc_button.setText(_translate("relate_to_my_doc_dialog", "Previous"))
        self.next_doc_button.setText(_translate("relate_to_my_doc_dialog", "Next"))
        self.label_2.setText(_translate("relate_to_my_doc_dialog", "  Mark Link Favorite:"))
        self.del_doc_button.setText(_translate("relate_to_my_doc_dialog", "Delete Doc"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.text_tab), _translate("relate_to_my_doc_dialog", "Text"))
        self.prev_pic_button.setText(_translate("relate_to_my_doc_dialog", "Previous"))
        self.next_pic_button.setText(_translate("relate_to_my_doc_dialog", "Next"))
        self.label_5.setText(_translate("relate_to_my_doc_dialog", "Path:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.pic_tab), _translate("relate_to_my_doc_dialog", "Picture"))
        self.label.setText(_translate("relate_to_my_doc_dialog", "Path: "))
        self.media_link_label.setText(_translate("relate_to_my_doc_dialog", "TextLabel"))
        self.prev_media_button.setText(_translate("relate_to_my_doc_dialog", "Previous"))
        self.play_again_button.setText(_translate("relate_to_my_doc_dialog", "Play Again"))
        self.next_media_button.setText(_translate("relate_to_my_doc_dialog", "Next"))
        self.label_6.setText(_translate("relate_to_my_doc_dialog", "Mark Media Favorite: "))
        self.unreg_media_button.setText(_translate("relate_to_my_doc_dialog", "Unload Media"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.media_tab), _translate("relate_to_my_doc_dialog", "Multimedia"))

from . import myRes_rc