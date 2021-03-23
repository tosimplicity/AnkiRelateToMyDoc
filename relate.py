import time
import datetime
import sqlite3
import json
import logging
import os
import os.path
import re
from functools import partial

from aqt import mw
from PyQt5.Qt import *
from PyQt5.Qt import QDialog, QIcon, QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView

from .utils import get_path, show_text, html_to_text
from .ui_relate_to_my_doc import Ui_relate_to_my_doc_dialog
from . import mplayer_extended

MEDIA_FADE_TIME = 2
MEDIA_BLOCK_TIME = 10


class RelateToMyDocDialog(QDialog, Ui_relate_to_my_doc_dialog):

    def __init__(self, parent):

        super().__init__(parent)
        self.setupUi(self)
        self.setGeometry(mw.x() + mw.frameGeometry().width(),
                         mw.y() + mw.frameGeometry().height() - self.geometry().height(),
                         self.geometry().width(),
                         self.geometry().height())
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.currentChanged.connect(self.on_tab_change)

        self.qweb_progress_bar.hide()
        self.browser = QWebEngineView()
        self.browser.loadProgress.connect(self.qweb_progress_bar.setValue)
        self.browser.loadProgress.connect(lambda x: self.qweb_progress_bar.hide() if x == 100 else None)
        self.qweb_progress_bar.show()
        self.browser.setHtml("")
        self.verticalLayout_text.addWidget(self.browser)
        self.fav_filter_checkbox.setChecked(True)
        self.unfav_filter_checkbox.setChecked(True)
        # slots
        self.browser.loadFinished.connect(self.on_html_loaded)
        self.prev_doc_button.clicked.connect(self.show_previous_doc)
        self.next_doc_button.clicked.connect(self.show_next_doc)
        self.mark_fav_doc_button.clicked.connect(self.mark_fav_doc)
        self.del_doc_button.clicked.connect(self.delete_doc)
        self.fav_filter_checkbox.stateChanged.connect(self.on_fav_filter_checkbox)
        self.unfav_filter_checkbox.stateChanged.connect(self.on_unfav_filter_checkbox)

        self.pic_tab_image = None
        self.pic_label.setScaledContents(False)

        def pic_label_resizeEvent(event):
            if self.pic_tab_image and isinstance(self.pic_tab_image, QPixmap):
                scaled_image = self.pic_tab_image.scaled(self.pic_label.width() - 2,
                                                         self.pic_label.height() - 2,
                                                         aspectRatioMode=Qt.KeepAspectRatio,
                                                         transformMode=Qt.FastTransformation)
                self.pic_label.setPixmap(scaled_image)
            elif self.pic_tab_image:
                self.pic_tab_image.setScaledSize(self.pic_tab_image.scaledSize().scaled(self.pic_label.width() - 2,
                                                                                        self.pic_label.height() - 2,
                                                                                        Qt.KeepAspectRatio))
        self.pic_label.resizeEvent = pic_label_resizeEvent
        self.prev_pic_button.clicked.connect(self.show_previous_pic)
        self.next_pic_button.clicked.connect(self.show_next_pic)

        self.media_link_label.setText("")
        self.mplayer_widget_container.setStyleSheet("background-color: black;")
        self.prev_media_button.clicked.connect(self.show_previous_media)
        self.play_again_button.clicked.connect(self.play_media_again)
        self.next_media_button.clicked.connect(self.show_next_media)
        self.mark_fav_media_button.clicked.connect(self.mark_fav_media)
        self.unreg_media_button.clicked.connect(self.unreg_media)

        self.card = None
        self.card_id = None
        self.doc_tab_on_card_id = None
        self.pic_tab_on_card_id = None
        self.media_tab_on_card_id = None

        self.target_model_id_list = []
        conn = sqlite3.connect(get_path("user_files", "doc.db"))
        for row in conn.execute('select var_value from var_store where var_name = "target_model_id_list"'):
            self.target_model_id_list += json.loads(row[0])
        conn.close()

        with open(get_path("ir_verb_dict"), "r") as f:
            self.ir_verb_dict = json.load(f)
        with open(get_path("bypass_list"), "r") as f:
            self.bypass_list = json.load(f)

    def on_tab_change(self, cur_tab_index):

        self.tabWidget.setCurrentIndex(cur_tab_index)
        if cur_tab_index != 2:
            mplayer_extended.stop()
        if not self.card:
            pass
        elif cur_tab_index == 0 and self.doc_tab_on_card_id != self.card_id:
            self.show_doc_up_for_new_card()
        elif cur_tab_index == 1 and self.index_showing_pic == -1:
            self.index_showing_pic = 0
            self.show_pic_up_for_new_card()
        elif cur_tab_index == 2 and self.cur_index_media_rowid_list == -1:
            self.cur_index_media_rowid_list = 0
            self.show_media_up_for_new_card()

    def closeEvent(self, event):
        mplayer_extended.stop()
        event.accept()
        # if self.tabWidget.currentIndex() == 0:
        #     event.accept()
        # else:
        #     event.ignore()

    def refresh_new_card(self):

        if not self.prep_new_card():
            return
        self.prep_pic_up_for_new_card()
        self.index_showing_pic = -1
        self.prep_media_up_for_new_card()
        self.cur_index_media_rowid_list = -1
        self.show()

        if self.tabWidget.currentIndex() == 0:
            self.show_doc_up_for_new_card()
        elif self.tabWidget.currentIndex() == 1:
            self.index_showing_pic = 0
            self.show_pic_up_for_new_card()
        elif self.tabWidget.currentIndex() == 2:
            self.cur_index_media_rowid_list = 0
            self.show_media_up_for_new_card()

    def prep_new_card(self):

        # check note type
        card = mw.reviewer.card
        card_id = card.id
        model_id = mw.reviewer.card.note().mid
        if model_id not in self.target_model_id_list:
            return False
        original_words = card.note().fields[0]
        # remove words text after "|"
        # get card words
        if "|" in original_words:
            words_core = original_words[:original_words.find("|")].strip()
        else:
            words_core = original_words.strip()
        # get rid of html codes
        words_core = re.sub(r"\[.*?\]", "", words_core)  # remove media content
        words_core = re.sub(r"&nbsp;", "", words_core)  # remove html space
        words_core = re.sub(r"<.*?>", "", words_core)  # remove format mark
        words_core = re.sub(r"{{.*?::(.*?)}}", r"\1", words_core)  # remove cloze mark
        words_core = re.sub(r"\s+", r" ", words_core)  # replace multiple whitespaces to one space
        # handle words alternatives (ir, +ing, +s/es, +ed)
        if " " in words_core:
            words_core_first = original_words[:original_words.find(" ")]
            words_core_trailing = original_words[original_words.find(" "):].strip()
        else:
            words_core_first = words_core
            words_core_trailing = ""
        if words_core_trailing:
            words_core = words_core_first + " " + words_core_trailing
        words_vars = [words_core, ]
        if words_core_first.lower() in self.ir_verb_dict:
            for ir_verb_var in self.ir_verb_dict[words_core_first.lower()]:
                words_vars.append((ir_verb_var + " " + words_core_trailing).strip())
        if words_core_first.lower().endswith("e"):
            words_vars.append((words_core_first[:-1] + "ing" + " " + words_core_trailing).strip())
            words_vars.append((words_core_first + "s" + " " + words_core_trailing).strip())
            words_vars.append((words_core_first[:-1] + "d" + " " + words_core_trailing).strip())
        else:
            words_vars.append((words_core_first + "ing" + " " + words_core_trailing).strip())
            words_vars.append((words_core_first + "s" + " " + words_core_trailing).strip())
            words_vars.append((words_core_first + "es" + " " + words_core_trailing).strip())
            words_vars.append((words_core_first + "d" + " " + words_core_trailing).strip())
            words_vars.append((words_core_first + "ed" + " " + words_core_trailing).strip())
        # check bypass words
        if not words_core or words_core.lower() in self.bypass_list or '"' in words_core:
            return False

        self.card = card
        self.card_id = card_id
        self.original_words = original_words
        self.words_core = words_core
        self.words_vars = words_vars
        return True


    #
    # work on the doc tab
    #

    def show_doc_up_for_new_card(self):

        self.fav_doc_id_queue = []
        self.unfav_doc_id_queue = []
        self.dig_depth_doc_id = 0
        self.cur_doc_id = 0
        self.found_all_docs = False
        self.browser_show_temp_text = False
        # like siblings_doc_id [prev, next], 0 as prev represents start. 0 as next represents end.
        # when none, cur_doc_id is used to tell the current position
        # used for fav / unfav marking
        self.siblings_doc_id = None
        self.words_var_by_doc_id = {}
        # work out fav list
        conn = sqlite3.connect(get_path("user_files", "doc.db"),
                               detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        for row in conn.execute("select words_var, doc_id "
                                + "from words where words = ? order by doc_id desc", (self.words_core,)):
            if row[0]:
                self.words_var_by_doc_id[row[1]] = row[0]
            else:
                self.words_var_by_doc_id[row[1]] = self.words_core
            self.fav_doc_id_queue.append(row[1])
        conn.execute("update words set last_visit_date = current_timestamp where words = ?", (self.words_core,))
        conn.commit()
        conn.close()
        # render page
        if not self.fav_filter_checkbox.isChecked() and not self.unfav_filter_checkbox.isChecked():
            self.fav_filter_checkbox.setChecked(True) and self.unfav_filter_checkbox.setChecked(True)

        self.show_next_doc()
        self.doc_tab_on_card_id = self.card_id

    def render_page_as_filtered(self, only_notice=""):

        def disable_all_ui(reverse=False):
            # if reverse in true, that is enable all
            self.prev_doc_button.setEnabled(reverse)
            self.next_doc_button.setEnabled(reverse)
            self.mark_fav_doc_button.setEnabled(reverse)
            self.del_doc_button.setEnabled(reverse)
            self.fav_filter_checkbox.setEnabled(reverse)
            self.unfav_filter_checkbox.setEnabled(reverse)
            return
        # only to show to a notice
        if only_notice:
            self.qweb_progress_bar.show()
            self.browser.setHtml(only_notice)
            self.browser_show_temp_text = True
            self.show()
            return

        # case 1 doc id present
        disable_all_ui(reverse=False)
        if self.cur_doc_id:
            conn = sqlite3.connect(get_path("user_files", "doc.db"))
            cur = conn.cursor()
            row = cur.execute("select descr, link from doc where doc_id = ?", (self.cur_doc_id,)).fetchone()
            desc = row[0]
            link = row[1]
            conn.close()
        # case 2 need to find new doc
        elif not self.found_all_docs and self.unfav_filter_checkbox.isChecked():
            sql_script = ('select doc.doc_id, descr, link, words.words from doc left join words '
                          + 'on doc.doc_id = words.doc_id and words.words = ? '
                          + 'where (descr like "%'
                          + '%" or descr like "%'.join(self.words_vars) + '%") '
                          + 'and words.words is null '
                          + ('' if not self.dig_depth_doc_id else 'and doc.doc_id < %s ' % str(self.dig_depth_doc_id))
                          + 'order by doc.doc_id desc limit 10')
            # descr like "%abc%" or descr like "%abd%"
            # need to get a valid result in 10 outcomes otherwise the words are too weird
            found_flag = False
            word_chars = "abcdefghijklmnopqrstuvwxyz"
            conn = sqlite3.connect(get_path("user_files", "doc.db"))
            for row in conn.execute(sql_script, (self.words_core,)):
                if self.dig_depth_doc_id > row[0] or not self.dig_depth_doc_id:
                    self.dig_depth_doc_id = row[0]
                desc = row[1]
                desc_plain = html_to_text(desc)
                # desc_plain = desc
                for words_var in self.words_vars:
                    if words_var.lower() in desc_plain.lower():
                        split_desc = desc_plain.lower().strip().split(words_var.lower())
                        if len(split_desc) <= 1:
                            continue
                        else:
                            for i_split_desc in range(len(split_desc) - 1):
                                if len(split_desc[i_split_desc]) == 0 \
                                        or split_desc[i_split_desc][-1] not in word_chars:
                                    self.cur_doc_id = row[0]
                                    link = row[2]
                                    self.unfav_doc_id_queue.append(self.cur_doc_id)
                                    if self.cur_doc_id not in self.words_var_by_doc_id:
                                        self.words_var_by_doc_id[self.cur_doc_id] = words_var
                                    found_flag = True
                                    break
                            if found_flag:
                                break
                if found_flag:
                    break
            conn.close()
            if not found_flag:
                self.found_all_docs = True
                self.render_page_as_filtered("Can not find any more new document.")
                disable_all_ui(reverse=True)
                return
        else:
            self.render_page_as_filtered("Showed all docs.")
            disable_all_ui(reverse=True)
            return
        disable_all_ui(reverse=True)
        html_to_set = desc
        link_to_set = '<p><p><a href="%s">%s</a>' % (link, link)
        if "</body>" in html_to_set:
            html_to_set = html_to_set.replace("</body>", link_to_set + "</body>")
        else:
            html_to_set = html_to_set + link_to_set
        self.qweb_progress_bar.show()
        self.browser.setHtml(html_to_set)
        self.browser.findText(self.words_var_by_doc_id[self.cur_doc_id])
        self.browser_show_temp_text = False

        # set up button status
        add_up_doc_id_list = []
        if self.fav_filter_checkbox.isChecked():
            add_up_doc_id_list += self.fav_doc_id_queue
        if self.unfav_filter_checkbox.isChecked():
            add_up_doc_id_list += self.unfav_doc_id_queue
        if not self.cur_doc_id or self.cur_doc_id not in add_up_doc_id_list:
            self.prev_doc_button.setEnabled(True)
            self.next_doc_button.setEnabled(True)
        else:
            if add_up_doc_id_list.index(self.cur_doc_id) == 0:
                self.prev_doc_button.setEnabled(False)
            else:
                self.prev_doc_button.setEnabled(True)
            if add_up_doc_id_list.index(self.cur_doc_id) == len(add_up_doc_id_list) and self.found_all_docs:
                self.next_doc_button.setEnabled(False)
            else:
                self.next_doc_button.setEnabled(True)
        # set up favorite button
        icon = QIcon()
        if self.cur_doc_id in self.fav_doc_id_queue:
            icon.addPixmap(QPixmap(":/res/res/red_heart.png"), QIcon.Normal, QIcon.On)
        else:
            icon.addPixmap(QPixmap(":/res/res/grey_heart.png"), QIcon.Normal, QIcon.On)
        self.mark_fav_doc_button.setIcon(icon)
        self.show()

    def on_html_loaded(self, ok):
        try:
            self.browser.findText(self.words_var_by_doc_id[self.cur_doc_id])
        except Exception:
            pass

    def on_filter_change(self, filter_name="favorite"):
        if filter_name not in ("favorite", "others"):
            return
        if not self.fav_filter_checkbox.isChecked() and not self.unfav_filter_checkbox.isChecked():
            show_text("Can not check off both favorite and others filtes.")
            if filter_name == "favorite":
                self.fav_filter_checkbox.setChecked(True)
            else:
                self.unfav_filter_checkbox.setChecked(True)
            return
        if not self.doc_tab_on_card_id:
            return
        if not self.cur_doc_id:
            return
        if self.siblings_doc_id:
            return
        if self.browser_show_temp_text:
            self.show_next_doc()
            return
        if filter_name == "favorite" \
           and self.cur_doc_id in self.fav_doc_id_queue \
           and not self.fav_filter_checkbox.isChecked():
                self.show_next_doc()
        if filter_name == "others" \
           and self.cur_doc_id in self.unfav_doc_id_queue \
           and not self.unfav_filter_checkbox.isChecked():
                if self.fav_doc_id_queue:
                    self.cur_doc_id = self.fav_doc_id_queue[-1]
                else:
                    self.cur_doc_id= ""
                self.render_page_as_filtered()
        # set up button status
        add_up_doc_id_list = []
        if self.fav_filter_checkbox.isChecked():
            add_up_doc_id_list += self.fav_doc_id_queue
        if self.unfav_filter_checkbox.isChecked():
            add_up_doc_id_list += self.unfav_doc_id_queue
        if not self.cur_doc_id or self.cur_doc_id not in add_up_doc_id_list:
            self.prev_doc_button.setEnabled(True)
            self.next_doc_button.setEnabled(True)
        else:
            if add_up_doc_id_list.index(self.cur_doc_id) == 0:
                self.prev_doc_button.setEnabled(False)
            else:
                self.prev_doc_button.setEnabled(True)
            if add_up_doc_id_list.index(self.cur_doc_id) == len(add_up_doc_id_list) and self.found_all_docs:
                self.next_doc_button.setEnabled(False)
            else:
                self.next_doc_button.setEnabled(True)


    def on_fav_filter_checkbox(self, state):
        self.on_filter_change("favorite")

    def on_unfav_filter_checkbox(self, state):
        self.on_filter_change("others")

    def show_previous_doc(self):
        if not self.doc_tab_on_card_id:
            return
        add_up_doc_id_list = []
        if self.fav_filter_checkbox.isChecked():
            add_up_doc_id_list += self.fav_doc_id_queue
        if self.unfav_filter_checkbox.isChecked():
            add_up_doc_id_list += self.unfav_doc_id_queue
        # #cur item in temp status due to mark/unmark action
        if self.siblings_doc_id and self.siblings_doc_id[0]:
            self.cur_doc_id = self.siblings_doc_id[0]
            self.siblings_doc_id = None
            if self.cur_doc_id in add_up_doc_id_list:
                self.render_page_as_filtered()
                return
        elif self.siblings_doc_id and not self.siblings_doc_id[0]:
            self.siblings_doc_id = None
            self.cur_doc_id = 0
        if not add_up_doc_id_list:
            self.show_next_doc()
        elif not self.cur_doc_id:
            self.cur_doc_id = add_up_doc_id_list[-1]
            self.render_page_as_filtered()
        elif self.cur_doc_id in add_up_doc_id_list and add_up_doc_id_list.index(self.cur_doc_id) != 0:
            self.cur_doc_id = add_up_doc_id_list[add_up_doc_id_list.index(self.cur_doc_id) - 1]
            self.render_page_as_filtered()
        else:
            self.render_page_as_filtered("Can not find more previous doc.")

    def show_next_doc(self):
        if not self.doc_tab_on_card_id:
            return
        add_up_doc_id_list = []
        if self.fav_filter_checkbox.isChecked():
            add_up_doc_id_list += self.fav_doc_id_queue
        if self.unfav_filter_checkbox.isChecked():
            add_up_doc_id_list += self.unfav_doc_id_queue
        # cur item in temp status due to mark/unmark action
        if self.siblings_doc_id and self.siblings_doc_id[1]:
            self.cur_doc_id = self.siblings_doc_id[1]
            self.siblings_doc_id = None
            if self.cur_doc_id in add_up_doc_id_list:
                self.render_page_as_filtered()
                return
        elif self.siblings_doc_id and not self.siblings_doc_id[1]:
            self.cur_doc_id = 0
            self.siblings_doc_id = None
        # check again available items
        if not self.cur_doc_id:
            if add_up_doc_id_list:
                self.cur_doc_id = add_up_doc_id_list[0]
            self.render_page_as_filtered()
        else:
            if self.cur_doc_id in add_up_doc_id_list \
               and add_up_doc_id_list.index(self.cur_doc_id) != len(add_up_doc_id_list) - 1:
                self.cur_doc_id = add_up_doc_id_list[add_up_doc_id_list.index(self.cur_doc_id) + 1]
            else:
                if add_up_doc_id_list and self.cur_doc_id not in add_up_doc_id_list:
                    self.cur_doc_id = add_up_doc_id_list[0]
                else:
                    self.cur_doc_id = 0
            self.render_page_as_filtered()


    def mark_fav_doc(self):
        if not self.doc_tab_on_card_id:
            return
        doc_id_marked = self.cur_doc_id
        if not self.cur_doc_id:
            return
        if self.cur_doc_id not in self.words_var_by_doc_id:
            self.show_up_for_new_card()
            return
        if self.cur_doc_id in self.fav_doc_id_queue:
            conn = sqlite3.connect(get_path("user_files", "doc.db"))
            conn.execute("delete from words where words = ? and doc_id = ?", (self.words_core, self.cur_doc_id))
            conn.commit()
            conn.close()
            self.unfav_doc_id_queue.append(doc_id_marked)
            self.siblings_doc_id = [self.fav_doc_id_queue.index(doc_id_marked), 0]
            if self.fav_doc_id_queue.index(doc_id_marked) == len(self.fav_doc_id_queue) - 1:
                self.siblings_doc_id[1] = self.unfav_doc_id_queue[0]
            else:
                self.siblings_doc_id[1] = self.fav_doc_id_queue[self.fav_doc_id_queue.index(doc_id_marked) + 1]
            self.fav_doc_id_queue.remove(doc_id_marked)
        else:
            conn = sqlite3.connect(get_path("user_files", "doc.db"))
            conn.execute("insert or replace into words "
                         + "(words, words_var, doc_id, last_visit_date) values "
                         + "(?, ?, ?, current_timestamp)",
                         (self.words_core, self.words_var_by_doc_id[self.cur_doc_id], self.cur_doc_id))
            conn.commit()
            conn.close()
            self.fav_doc_id_queue.append(doc_id_marked)
            if self.unfav_doc_id_queue.index(doc_id_marked) == len(self.unfav_doc_id_queue):
                self.siblings_doc_id = [0, 0]
            else:
                self.siblings_doc_id = [0, len(self.unfav_doc_id_queue) - 1]
            if self.unfav_doc_id_queue.index(doc_id_marked) != 0:
                self.siblings_doc_id[0] = self.unfav_doc_id_queue.index(doc_id_marked) - 1
            else:
                self.siblings_doc_id[0] = self.fav_doc_id_queue[-1]
            self.unfav_doc_id_queue.remove(doc_id_marked)
        # set up favorite button
        icon = QIcon()
        if self.cur_doc_id in self.fav_doc_id_queue:
            icon.addPixmap(QPixmap(":/res/res/red_heart.png"), QIcon.Normal, QIcon.On)
        else:
            icon.addPixmap(QPixmap(":/res/res/grey_heart.png"), QIcon.Normal, QIcon.On)
        self.mark_fav_doc_button.setIcon(icon)
        self.show()


    def delete_doc(self):
        if not self.doc_tab_on_card_id:
            return
        doc_id_to_delete = self.cur_doc_id
        self.show_previous_doc()
        if self.cur_doc_id == doc_id_to_delete:
            self.show_next_doc()
        conn = sqlite3.connect(get_path("user_files", "doc.db"))
        conn.execute("delete from words where doc_id = ?", (doc_id_to_delete,))
        conn.execute("delete from doc where doc_id = ?", (doc_id_to_delete,))
        conn.commit()
        conn.close()
        if self.cur_doc_id == doc_id_to_delete:
            self.cur_doc_id = 0
            self.show_next_doc()

    #
    # work on the pic tab
    #

    def prep_pic_up_for_new_card(self):
        # self.index_showing_pic = 0
        # generate picture pool
        # only done once at the fist visit to the tab
        if self.pic_tab_on_card_id is None:
            config = mw.addonManager.getConfig(__name__)
            pic_dir_list = config["directory_list_for_pics_to_relate"]
            self.pic_pool = {}
            for pic_dir in pic_dir_list:
                if not os.path.isdir(pic_dir):
                    continue
                config = mw.addonManager.getConfig(__name__)
                if "filter_show_local_file_path_not_start_with" in config \
                        and config["filter_show_local_file_path_not_start_with"]["is_active"]:
                    flag_filter_fit = False
                    for each_filter in config["filter_show_local_file_path_not_start_with"]["filter"]:
                        if os.path.normpath(pic_dir).replace("\\", "/").lower().startswith(os.path.normpath(each_filter).replace("\\", "/").lower()):
                            flag_filter_fit = True
                            break
                    if flag_filter_fit:
                        break
                pics = []
                for filename in os.listdir(pic_dir):
                    if os.path.isfile(os.path.join(pic_dir, filename)) \
                       and (filename.endswith(".png") or filename.endswith(".jpg") or filename.endswith(".gif")):
                            pics.append(filename)
                if pics:
                    self.pic_pool[pic_dir] = pics

        self.related_pic_list = []
        for pic_dir in self.pic_pool.keys():
            for filename in self.pic_pool[pic_dir]:
                for words_var in self.words_vars:
                    if words_var in filename:
                        self.related_pic_list.append(os.path.join(pic_dir, filename))
                        continue
        if not self.related_pic_list:
            self.pic_link_label.setText("")
            self.pic_label.clear()

        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.pic_tab),
            "Picture(" + str(len(self.related_pic_list)) + ")")
        self.pic_tab_on_card_id = self.card_id

    def show_pic_up_for_new_card(self):
        if self.pic_tab_on_card_id != self.card_id:
            self.prep_pic_up_for_new_card()
        self.show_pic()

    def show_pic(self):

        if self.index_showing_pic >= len(self.related_pic_list) \
           or not os.path.exists(self.related_pic_list[self.index_showing_pic]):
                return
        self.pic_link_label.setText(os.path.normpath(self.related_pic_list[self.index_showing_pic]))
        self.pic_label.clear()
        if not self.related_pic_list[self.index_showing_pic].lower().endswith(".gif"):
            self.pic_tab_image = QPixmap(self.related_pic_list[self.index_showing_pic])
            scaled_image = self.pic_tab_image.scaled(self.pic_label.width() - 2,
                                                     self.pic_label.height() - 2,
                                                     aspectRatioMode=Qt.KeepAspectRatio,
                                                     transformMode=Qt.FastTransformation)
            self.pic_label.setPixmap(scaled_image)
        else:
            self.pic_tab_image = QMovie(self.related_pic_list[self.index_showing_pic], QByteArray(), self)
            self.pic_tab_image.setCacheMode(QMovie.CacheAll)
            self.pic_tab_image.setSpeed(100)
            self.pic_tab_image.setScaledSize(self.pic_tab_image.scaledSize().scaled(self.pic_label.width() - 2,
                                                                                    self.pic_label.height() - 2,
                                                                                    Qt.KeepAspectRatio))
            self.pic_label.setMovie(self.pic_tab_image)
            self.pic_tab_image.start()
        if self.index_showing_pic == 0:
            self.prev_pic_button.setEnabled(False)
        else:
            self.prev_pic_button.setEnabled(True)
        if self.index_showing_pic >= len(self.related_pic_list) - 1:
            self.next_pic_button.setEnabled(False)
        else:
            self.next_pic_button.setEnabled(True)

        total = str(len(self.related_pic_list))
        cur = str(self.index_showing_pic + 1) if total != "0" else "0"
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.pic_tab),
            "Picture(" + cur + "/" + total + ")")
        self.show()

    def show_previous_pic(self):

        if not self.pic_tab_on_card_id:
            return
        if self.index_showing_pic != 0:
            self.index_showing_pic -= 1
            self.show_pic()

    def show_next_pic(self):
        if not self.pic_tab_on_card_id:
            return
        if self.index_showing_pic != len(self.related_pic_list) - 1:
            self.index_showing_pic += 1
            self.show_pic()

    #
    # work on the media tab
    #

    def prep_media_up_for_new_card(self):
        # generate media pool
        # only done once at the fist visit to the tab
        sql_script = ('select rowid, media_path_no_ext from subs '
                      + 'where sub_text like "%'
                      + '%" or sub_text like "%'.join(self.words_vars) + '%" '
                      + 'order by is_fav desc, media_path_no_ext asc')
        conn = sqlite3.connect(get_path("user_files", "doc.db"))
        self.media_rowid_list = []
        config = mw.addonManager.getConfig(__name__)
        try:
            if config["filter_show_local_file_path_not_start_with"]["is_active"]:
                flag_filters = config["filter_show_local_file_path_not_start_with"]["filter"]
            else:
                flag_filters = None
        except KeyError:
            flag_filters = None
        for row in conn.execute(sql_script):
            config = mw.addonManager.getConfig(__name__)
            if flag_filters:
                flag_filter_fit = False
                for each_filter in flag_filters:
                    if os.path.normpath(row[1]).replace("\\", "/").lower().startswith(os.path.normpath(each_filter).replace("\\", "/").lower()):
                        flag_filter_fit = True
                        break
                if flag_filter_fit:
                    continue
            self.media_rowid_list.append(row[0])
        conn.close()
        # self.cur_index_media_rowid_list = 0
        # cur_sub [media_path_no_ext, media_ext, sub_text, is_fav]
        self.cur_sub = []
        # cur_sub_details [[start, end, line content], next, next, ...]
        self.cur_sub_details = []
        # words_in_sub_pointers point to indexes in cur_sub_details
        self.words_in_sub_pointers = []
        self.index_words_in_sub_pointers = 0
        self.media_play_para = []
        if not self.media_rowid_list:
            self.prev_media_button.setEnabled(False)
            self.next_media_button.setEnabled(False)

        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.media_tab),
            "Multimedia(" + str(len(self.media_rowid_list)) + ")")
        self.media_tab_on_card_id = self.card_id

    def show_media_up_for_new_card(self):
        if self.media_tab_on_card_id != self.card_id:
            self.prep_media_up_for_new_card()
        self.show_media()

    def show_media(self):

        if self.cur_index_media_rowid_list < 0 \
                or self.cur_index_media_rowid_list >= len(self.media_rowid_list):
            return "error"
        if not self.cur_sub:
            conn = sqlite3.connect(get_path("user_files", "doc.db"))
            for row in conn.execute("select media_path_no_ext, media_ext, sub_text, is_fav from subs where rowid = ?",
                                    (self.media_rowid_list[self.cur_index_media_rowid_list],)):
                self.cur_sub = [x for x in row]
                break
            if not os.path.isfile(self.cur_sub[0] + self.cur_sub[1]):
                # no. we don't won't want to delete that
                # conn.execute("delete from subs where rowid = ?",
                #              (self.media_rowid_list[self.cur_index_media_rowid_list],))
                # conn.commit()
                # conn.close()
                # file not existing
                self.media_rowid_list.pop(self.cur_index_media_rowid_list)
                if self.cur_index_media_rowid_list >= len(self.media_rowid_list):
                    self.cur_index_media_rowid_list = max(len(self.media_rowid_list) - 1, 0)
                    return "sub-prev"
                else:
                    return "sub-next"
            conn.close()
            re_sub_block = re.compile(r"<<<start=(\d+),end=(\d+)\|\|(.*?)>>>", re.DOTALL)
            sub_blocks = re_sub_block.findall(self.cur_sub[2])
            self.cur_sub_details = []
            self.words_in_sub_pointers = []
            self.index_words_in_sub_pointers = 0
            for i in range(len(sub_blocks)):
                self.cur_sub_details.append([int(sub_blocks[i][0]), int(sub_blocks[i][1]), sub_blocks[i][2]])
                for target_words in self.words_vars:
                    if target_words.lower() in sub_blocks[i][2].lower():
                        self.words_in_sub_pointers.append(i)
                        break
            if not self.words_in_sub_pointers:
                # invalid record for current words
                self.media_rowid_list.pop(self.cur_index_media_rowid_list)
                if self.cur_index_media_rowid_list >= len(self.media_rowid_list):
                    self.cur_index_media_rowid_list = max(len(self.media_rowid_list) - 1, 0)
                    self.cur_sub = []
                    return "sub-prev"
                else:
                    self.cur_sub = []
                    return "sub-next"
        if self.index_words_in_sub_pointers < 0 or self.index_words_in_sub_pointers >= len(self.words_in_sub_pointers):
            return "error"

        # work on the start second and context - before
        pointer = self.words_in_sub_pointers[self.index_words_in_sub_pointers]
        if pointer < 0 or pointer >= len(self.cur_sub_details):
            return "error"
        if pointer == 0:
            start = self.cur_sub_details[pointer][0]
            line_before_text = ""
            start = 0 if start < MEDIA_FADE_TIME else start - MEDIA_FADE_TIME
        else:
            line_before_start = self.cur_sub_details[pointer-1][0]
            start = self.cur_sub_details[pointer][0]
            start = line_before_start if line_before_start > start - MEDIA_BLOCK_TIME else start - MEDIA_FADE_TIME
            if start < 0:
                start = 0
            line_before_text = self.cur_sub_details[pointer-1][2]
        # current line
        line_text = self.cur_sub_details[pointer][2]
        # work on the end second and context - after
        if pointer == len(self.cur_sub_details) - 1:
            end = self.cur_sub_details[pointer][1]
            line_after_text = ""
        else:
            end = self.cur_sub_details[pointer][1]
            if end != 0:
                end = end + MEDIA_FADE_TIME \
                    if self.cur_sub_details[pointer + 1][1] > end + MEDIA_BLOCK_TIME \
                    else self.cur_sub_details[pointer + 1][1]
            else:
                end = self.cur_sub_details[pointer][0]
                if self.cur_sub_details[pointer + 1][0] > end + 2 * MEDIA_BLOCK_TIME:
                    end = end + 2 * MEDIA_BLOCK_TIME
                elif pointer + 2 < len(self.cur_sub_details):
                    if self.cur_sub_details[pointer + 2][0] < end + 2 * MEDIA_BLOCK_TIME:
                        end = self.cur_sub_details[pointer + 2][0]
                    else:
                        end = max(end + 2 * MEDIA_BLOCK_TIME, self.cur_sub_details[pointer + 1][0])
                else:
                    end = max(end + 2 * MEDIA_BLOCK_TIME, self.cur_sub_details[pointer + 1][0])
            line_after_text = self.cur_sub_details[pointer + 1][2]
        # get start time string
        _ = int(start)
        _,  second = _ // 60, _ % 60
        hour, minute = _ // 60, _ % 60
        start_str = '%d:%02d:%02d ' % (hour, minute, second)
        self.media_link_label.setText(start_str + os.path.normpath(self.cur_sub[0] + self.cur_sub[1]))
        self.media_text_listWidget.clear()
        self.media_text_listWidget.addItem(line_before_text)
        self.media_text_listWidget.addItem(line_text)
        self.media_text_listWidget.addItem(line_after_text)
        if self.cur_index_media_rowid_list == 0 and self.index_words_in_sub_pointers == 0:
            self.prev_media_button.setEnabled(False)
        else:
            self.prev_media_button.setEnabled(True)
        if self.cur_index_media_rowid_list == len(self.media_rowid_list) - 1 \
                and self.index_words_in_sub_pointers == len(self.words_in_sub_pointers) - 1:
            self.next_media_button.setEnabled(False)
        else:
            self.next_media_button.setEnabled(True)
        if not self.media_rowid_list:
            self.prev_media_button.setEnabled(False)
            self.next_media_button.setEnabled(False)
        icon = QIcon()
        if self.cur_sub[3]:
            icon.addPixmap(QPixmap(":/res/res/red_heart.png"), QIcon.Normal, QIcon.On)
        else:
            icon.addPixmap(QPixmap(":/res/res/grey_heart.png"), QIcon.Normal, QIcon.On)
        self.mark_fav_media_button.setIcon(icon)
        self.media_play_para = [self.cur_sub[0] + self.cur_sub[1], start, end]
        mplayer_extended.stop()
        mplayer_extended.setup(int(self.mplayer_widget_container.winId()))
        # logger = logging.getLogger(__name__)
        # logger.info(
        #     'mplayer_widget_container wid '
        #     + str(int(self.mplayer_widget_container.winId())))
        mplayer_extended.play(self.media_play_para[0], self.media_play_para[1], self.media_play_para[2])

        total = str(len(self.media_rowid_list))
        cur = str(self.cur_index_media_rowid_list + 1) if total != "0" else "0"
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.media_tab),
            "Multimedia(" + cur + "/" + total + ")")
        self.show()
        return "ok"

    def show_previous_media(self):
        if not self.media_tab_on_card_id:
            return
        if not self.media_rowid_list:
            return
        if self.cur_index_media_rowid_list == 0 and self.index_words_in_sub_pointers == 0:
            self.prev_media_button.setEnabled(False)
            return
        if self.index_words_in_sub_pointers != 0:
            self.index_words_in_sub_pointers -= 1
            self.show_media()
            return
        elif self.cur_index_media_rowid_list != 0:
            self.cur_index_media_rowid_list -= 1
            self.cur_sub = []
            self.show_media()

    def show_next_media(self):
        if not self.media_tab_on_card_id:
            return
        if not self.media_rowid_list:
            return
        if self.cur_index_media_rowid_list == len(self.media_rowid_list) - 1 \
                and self.index_words_in_sub_pointers == len(self.words_in_sub_pointers) - 1:
            self.next_media_button.setEnabled(False)
            return
        if self.index_words_in_sub_pointers != len(self.words_in_sub_pointers) - 1:
            self.index_words_in_sub_pointers += 1
            self.show_media()
            return
        elif self.cur_index_media_rowid_list != len(self.media_rowid_list) - 1:
            self.cur_index_media_rowid_list += 1
            self.cur_sub = []
            result = self.show_media()
            while result == "sub-next":
                result = self.show_media()

    def play_media_again(self):

        if not self.media_tab_on_card_id:
            return
        if not self.media_rowid_list:
            return
        if not self.media_play_para:
            return
        mplayer_extended.stop()
        mplayer_extended.setup(int(self.mplayer_widget_container.winId()))
        # logger = logging.getLogger(__name__)
        # logger.info(
        #     'mplayer_widget_container wid '
        #     + str(int(self.mplayer_widget_container.winId())))
        mplayer_extended.play(self.media_play_para[0], self.media_play_para[1], self.media_play_para[2])

    def mark_fav_media(self):

        if not self.media_tab_on_card_id:
            return
        if not self.media_rowid_list:
            return
        if not self.cur_sub:
            return
        rowid = self.media_rowid_list[self.cur_index_media_rowid_list]
        if self.cur_sub[3]:
            conn = sqlite3.connect(get_path("user_files", "doc.db"))
            conn.execute("update subs set is_fav = ? where rowid = ?", (False, rowid))
            conn.commit()
            conn.close()
            self.cur_sub[3] = False
        else:
            conn = sqlite3.connect(get_path("user_files", "doc.db"))
            conn.execute("update subs set is_fav = ? where rowid = ?", (True, rowid))
            conn.commit()
            conn.close()
            self.cur_sub[3] = True
        icon = QIcon()
        if self.cur_sub[3]:
            icon.addPixmap(QPixmap(":/res/res/red_heart.png"), QIcon.Normal, QIcon.On)
        else:
            icon.addPixmap(QPixmap(":/res/res/grey_heart.png"), QIcon.Normal, QIcon.On)
        self.mark_fav_media_button.setIcon(icon)

    def unreg_media(self):

        if not self.media_tab_on_card_id:
            return
        if not self.media_rowid_list:
            return
        if not self.cur_sub:
            return
        rowid_to_delete = self.media_rowid_list[self.cur_index_media_rowid_list]
        conn = sqlite3.connect(get_path("user_files", "doc.db"))
        conn.execute("delete from subs where rowid = ?", (rowid_to_delete, ))
        conn.commit()
        conn.close()
        self.prep_media_up_for_new_card()
        self.cur_index_media_rowid_list = 0
        self.show_media_up_for_new_card()
