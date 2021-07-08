import time
import datetime
import sqlite3
import json
import os
import os.path
import re
import logging
import urllib
from operator import itemgetter

from . import feedparser
from aqt import mw
from PyQt5.Qt import *
from PyQt5.Qt import QDialog, QVBoxLayout, QPushButton
from PyQt5.Qt import QLineEdit, QTextEdit, QDialogButtonBox, QColor, QMessageBox, QFileDialog
from PyQt5.Qt import QInputDialog, Qt, QListWidgetItem
from PyQt5.QtWebEngineWidgets import QWebEngineView

from .utils import get_path, show_text, get_file_data
from .relate import RelateToMyDocDialog
from .ui_load_feed import Ui_load_feed_dialog
from .ui_note_type_setting import Ui_note_type_setting_dialog
from .ui_set_pic_dir import Ui_set_pic_dir_dialog
from .ui_view_doc import Ui_view_doc_dialog
from . import mplayer_extended


def relate_to_my_doc(card=None):
    if hasattr(mw.addon_RTMD.load_feed_dialog, "hard_work") and mw.addon_RTMD.load_feed_dialog.hard_work:
        if not mw.addon_RTMD.silent_for_new_card:
            show_text("Wait for load-feed-dialog to complete its job first.")
            mw.addon_RTMD.silent_for_new_card = True
        return
    if mw.addon_RTMD.loading_media_subs:
        if not mw.addon_RTMD.silent_for_new_card:
            show_text("Wait for loading media subs to be completed its job first.")
            mw.addon_RTMD.silent_for_new_card = True
        return
    mw.addon_RTMD.silent_for_new_card = False
    if not mw.addon_RTMD.relate_to_my_doc_dialog:
        mw.addon_RTMD.relate_to_my_doc_dialog = RelateToMyDocDialog(mw)
    mw.addon_RTMD.relate_to_my_doc_dialog.refresh_new_card(card)


def stop_media_playing():
    mplayer_extended.stop()
    try:
        mw.addon_RTMD.relate_to_my_doc_dialog.stop_media_playing()
    except Exception:
        pass


class LoadFeedDialog(QDialog, Ui_load_feed_dialog):

    def __init__(self, parent):

        super().__init__(parent)
        self.setupUi(self)
        self.load_feed_button.setText('Load All Feeds')
        self.remove_feed_content_button = QPushButton('Clear Feed Content')
        icon1 = QIcon()
        icon1.addPixmap(QPixmap(":/res/res/remove.png"), QIcon.Normal, QIcon.On)
        self.remove_feed_content_button.setIcon(icon1)
        self.action_buttons.insertWidget(2, self.remove_feed_content_button)
        self.progressBar.hide()

        self.manual_input_button.clicked.connect(self.manual_input)
        self.load_text_button.clicked.connect(self.load_from_text_file)
        self.add_feed_button.clicked.connect(self.add_feed)
        self.remove_feed_button.clicked.connect(self.remove_feed)
        self.remove_feed_content_button.clicked.connect(self.remove_feed_content)
        self.load_feed_button.clicked.connect(self.load_from_feed)
        self.abort_button.clicked.connect(self.abort_actions)
        self.clean_aged_button.clicked.connect(self.clean_aged_data)

        # init feed list
        self.feed_id_list = []
        self.feed_address_list = []
        conn = sqlite3.connect(get_path("user_files", "doc.db"),
                               detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        for row in conn.execute("select feed_id, address from feed order by feed_id desc"):
            self.feed_id_list.append(row[0])
            self.feed_address_list.append(row[1])
            self.feed_list_ui.addItem(row[1])

        self.need_abort = False
        self.hard_work = []

    def manual_input(self):

        self.status_label.setText("")
        edit_dialog = QDialog(self)
        verticalLayout = QVBoxLayout(edit_dialog)
        title_input = QLineEdit('title here', edit_dialog)
        editor = QTextEdit(edit_dialog)
        verticalLayout.addWidget(title_input)
        verticalLayout.addWidget(editor)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.manual_input_text = ""
        self.manual_input_title = ""

        def editor_accepted():
            if editor.toPlainText():
                self.manual_input_text = editor.toHtml()
                self.manual_input_title = title_input.text().strip()
            edit_dialog.close()

        def editor_rejected(): edit_dialog.close()
        buttonBox.accepted.connect(editor_accepted)
        buttonBox.rejected.connect(editor_rejected)
        verticalLayout.addWidget(buttonBox)
        edit_dialog.exec_()
        if self.manual_input_text:
            existing_doc_id_list_part = []  # existing feed id between now and mark
            conn = sqlite3.connect(get_path("user_files", "doc.db"),
                                   detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
            cur = conn.cursor()
            cur.execute("select feed_id from doc where feed_id between ? and ?",
                        (int(time.time()*1000), int(time.time()*1000)+10000))
            while True:
                doc_id = int(time.time()*1000)
                if doc_id not in existing_doc_id_list_part:
                    break
            cur.execute("""insert into doc
                            (doc_id, title, descr, doc_type)
                            values (?, ?, ?, 'mi')""",
                        (doc_id, self.manual_input_title, self.manual_input_text))
            conn.commit()
            conn.close()
            self.manual_input_text = ""
        self.status_label.setText("Manual Load Completed")

    def load_from_text_file(self):

        import_dir = mw.pm.profile.get("importDirectory", "")
        myfilter = "TXT/HTML (*.txt *.html);;All Files (*.*)"
        open_file_dialog = QFileDialog()
        open_file_dialog.setFileMode(QFileDialog.ExistingFiles)
        self.load_text_file_paths = open_file_dialog.getOpenFileNames(self,
                                                                      "Select Files to Import",
                                                                      import_dir,
                                                                      myfilter)[0]
        if not self.load_text_file_paths:
            return
        # disable buttons
        self.manual_input_button.setEnabled(False)
        self.load_text_button.setEnabled(False)
        self.clean_aged_button.setEnabled(False)
        self.add_feed_button.setEnabled(False)
        self.remove_feed_button.setEnabled(False)
        self.load_feed_button.setEnabled(False)
        if "load_from_text_file" not in self.hard_work:
            self.hard_work.append("load_from_text_file")
        self.existing_doc_id_list_part = []

        # thread to get feed data
        class LoadTextThreadSignals(QObject):
            exit_signal = pyqtSignal(str)

        class LoadTextThread(QRunnable):

            def __init__(self, parent, file_path):
                super(LoadTextThread, self).__init__()
                self.parent = parent
                self.file_path = file_path
                self.signals = LoadTextThreadSignals()

            def run(self):

                if self.parent.need_abort:
                    self.signals.exit_signal.emit("")
                    return

                desc = ""
                is_ok, desc = get_file_data(self.file_path)
                if not is_ok:
                    self.signals.exit_signal.emit("Need UTF-8 Encoding: %s" % self.file_path)
                    return
                if desc:
                    link_to_set = '<p><p><a href="%s">%s</a>' % (self.file_path, self.file_path)
                    if "</body>" in desc:
                        desc = desc.replace("</body>", link_to_set + "</body>")
                    else:
                        desc = desc + link_to_set
                    title = os.path.basename(self.file_path)
                    conn = sqlite3.connect(get_path("user_files", "doc.db"),
                                           detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
                    cur = conn.cursor()
                    cur.execute("select feed_id from doc where feed_id between ? and ?",
                                (int(time.time()*1000), int(time.time()*1000)+10000))
                    while True:
                        doc_id = int(time.time()*1000)
                        if doc_id not in self.parent.existing_doc_id_list_part:
                            break
                    self.parent.existing_doc_id_list_part.append(doc_id)
                    cur.execute("""insert into doc
                                (doc_id, link, title, descr, doc_type)
                                values (?, ?, ?, ?, 'tf')""",
                                (doc_id, self.file_path, title, desc))
                    conn.commit()
                    conn.close()
                    self.signals.exit_signal.emit("")

        def load_exit_msg_slot(signal_error_msg):
            self.load_text_completed_thread_count += 1
            if signal_error_msg:
                self.load_text_file_error_message += signal_error_msg + "<p>"
            self.status_label.setText("Completed files %s / %s"
                                      % (self.load_text_completed_thread_count,
                                         len(self.load_text_file_paths)))
            if self.load_text_completed_thread_count == len(self.load_text_file_paths):
                if self.hard_work:
                    self.hard_work.remove("load_from_text_file")
                if not self.need_abort:
                    self.status_label.setText("Completed loading.")
                if not self.hard_work and self.need_abort:
                    self.need_abort = False
                if self.load_text_file_error_message:
                    QMessageBox(QMessageBox.Warning, "Warning", self.load_text_file_error_message).exec()
                    self.load_text_file_error_message = ""
                # enable buttons
                self.manual_input_button.setEnabled(True)
                self.load_text_button.setEnabled(True)
                self.clean_aged_button.setEnabled(True)
                self.add_feed_button.setEnabled(True)
                self.remove_feed_button.setEnabled(True)
                self.load_feed_button.setEnabled(True)

        self.load_text_completed_thread_count = 0
        self.load_text_file_error_message = ""
        for file_path in self.load_text_file_paths:
            load_thread = LoadTextThread(self, file_path)
            load_thread.signals.exit_signal.connect(load_exit_msg_slot)
            thread_pool = QThreadPool.globalInstance()
            thread_pool.start(load_thread)

    def add_feed(self):

        for i in range(len(self.feed_address_list)):
            self.feed_list_ui.item(i).setData(Qt.BackgroundRole, None)
        new_feed_str, ok = QInputDialog.getText(self, "Add Feed", "Input your feed address below:")
        if ok and new_feed_str.strip():
            while True:
                feed_id = int(time.time()*1000)
                if feed_id not in self.feed_id_list:
                    break
            self.feed_id_list.insert(0, feed_id)
            self.feed_address_list.insert(0, new_feed_str.strip())
            conn = sqlite3.connect(get_path("user_files", "doc.db"),
                                   detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
            conn.execute("insert into feed (feed_id, address) values (?, ?)", (feed_id, new_feed_str.strip()))
            conn.commit()
            conn.close()
            self.feed_list_ui.insertItem(0, new_feed_str.strip())

    def remove_feed(self):

        for i in range(len(self.feed_address_list)):
            self.feed_list_ui.item(i).setData(Qt.BackgroundRole, None)
        for item in self.feed_list_ui.selectedItems():
            row_item = self.feed_list_ui.row(item)
            feed_id = self.feed_id_list[row_item]
            feed_address = self.feed_address_list[row_item]
            if feed_address != self.feed_list_ui.item(row_item).text():
                QMessageBox(QMessageBox.Warning,
                            "Warning",
                            "Inconsist data, restart the load feed dialog before removal"
                            ).exec()
                return
            conn = sqlite3.connect(get_path("user_files", "doc.db"),
                                   detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
            conn.execute("delete from feed where feed_id = ?", (feed_id,))
            conn.commit()
            conn.close()
            self.feed_id_list.pop(row_item)
            self.feed_address_list.pop(row_item)
            self.status_label.setText(str(row_item))
            self.feed_list_ui.takeItem(self.feed_list_ui.row(item))

    def remove_feed_content(self):
        for i in range(len(self.feed_address_list)):
            self.feed_list_ui.item(i).setData(Qt.BackgroundRole, None)
        for item in self.feed_list_ui.selectedItems():
            row_item = self.feed_list_ui.row(item)
            feed_id = self.feed_id_list[row_item]
            feed_address = self.feed_address_list[row_item]
            if feed_address != self.feed_list_ui.item(row_item).text():
                QMessageBox(QMessageBox.Warning,
                            "Warning",
                            "Inconsist data, restart the load feed dialog before removal"
                            ).exec()
                return
            conn = sqlite3.connect(get_path("user_files", "doc.db"),
                                   detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
            # clear favorites
            conn.execute(
                "delete from words where doc_id in "
                + "(select doc_id from doc where feed_id = ?)",
                (feed_id,))
            # clear docs
            conn.execute("delete from doc where feed_id = ?", (feed_id,))
            conn.commit()
            conn.close()

    def load_from_feed(self):
        """get feed data and store in doc db"""

        if not self.feed_address_list:
            return
        # disable buttons
        self.manual_input_button.setEnabled(False)
        self.load_text_button.setEnabled(False)
        self.clean_aged_button.setEnabled(False)
        self.add_feed_button.setEnabled(False)
        self.remove_feed_button.setEnabled(False)
        self.load_feed_button.setEnabled(False)
        if "load_from_feed" not in self.hard_work:
            self.hard_work.append("load_from_feed")
        self.existing_doc_id_list_part = []

        # thread to get feed data
        class LoadFeedThreadSignals(QObject):
            error_message = pyqtSignal(str)

        class LoadFeedThread(QRunnable):

            def __init__(self, parent, item_no):
                super(LoadFeedThread, self).__init__()
                self.parent = parent
                self.item_no = item_no
                self.signals = LoadFeedThreadSignals()

            def run(self):

                # check if to abort #1
                if self.parent.need_abort:
                    self.signals.error_message.emit("")
                    return
                feed_id = self.parent.feed_id_list[self.item_no]
                address = self.parent.feed_address_list[self.item_no]

                # remove any background color
                self.parent.feed_list_ui.item(self.item_no).setData(Qt.BackgroundRole, None)
                conn = sqlite3.connect(get_path("user_files", "doc.db"))
                cur = conn.cursor()
                cur.execute("select fetch_mod_date from feed where feed_id = ?", (feed_id,))
                fetch_mod_date = cur.fetchone()[0]
                if isinstance(fetch_mod_date, str):
                    try:
                        fetch_mod_date = datetime.datetime.fromisoformat()
                    except Exception:
                        fetch_mod_date = None
                conn.close()

                if not fetch_mod_date:
                    fetch_mod_date = datetime.datetime.now() - datetime.timedelta(days=1)
                agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
                modified = fetch_mod_date.utctimetuple()
                short_weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                since = '%s, %02d %s %04d %02d:%02d:%02d GMT' % (short_weekdays[modified[6]], modified[2], months[modified[1] - 1], modified[0], modified[3], modified[4], modified[5])
                #print('since', since)
                accept = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
                headers = {}
                headers = {'A-IM': 'feed'}
                headers['User-Agent'] = agent
                headers['If-Modified-Since'] = since
                headers['accept'] = accept
                # headers['Accept-encoding'] = 'gzip, deflate'
                try:
                    page = urllib.request.Request(address, headers=headers)
                    html = urllib.request.urlopen(page, timeout=10).read().decode("utf-8")
                    if self.parent.need_abort:
                        self.signals.error_message.emit("")
                        return
                    feed = feedparser.parse(html)
                except Exception:
                    self.parent.feed_list_ui.item(self.item_no).setBackground(QColor("red"))
                    error_message = "Failed to get from %s\n" % address
                    self.signals.error_message.emit(error_message)
                    return
                # if fetch_mod_text:
                #     feed = feedparser.parse(address, modified=fetch_mod_text)
                # else:
                #     feed = feedparser.parse(address)
                # check if to abort #2

                # get data at feed level
                fetch_mod_text = getattr(feed, "modified", "")
                fetch_mod_date = getattr(feed, "modified_parsed", time.localtime())
                fetch_mod_date = datetime.datetime.fromtimestamp(time.mktime(fetch_mod_date))

                conn = sqlite3.connect(get_path("user_files", "doc.db"),
                                       detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
                cur = conn.cursor()
                cur.execute("select feed_id from doc where feed_id between ? and ?",
                            (int(time.time()*1000), int(time.time()*1000)+10000))
                for row in cur.fetchall():
                    if row[0] not in self.parent.existing_doc_id_list_part:
                        self.parent.existing_doc_id_list_part.append(row[0])
                data_entries = []
                create_date = datetime.datetime.now()
                feed_id_using_name = ""
                feed_current_entry_id_list = []
                for entry in feed.entries:
                    data_entry = {}
                    data_entry["link"] = getattr(entry, "link", "").strip()
                    # feed_id_using_name if "id" not the right word, try to find the right one
                    # if can not find any, set it as "id"
                    if not feed_id_using_name:
                        data_entry["feed_entry_id"] = getattr(entry, "id", "")
                        if data_entry["feed_entry_id"]:
                            feed_id_using_name = "id"
                        else:
                            for key in entry.keys():
                                if key and "id" in key.lower() and isinstance(entry[key], str) and entry[key]:
                                    feed_id_using_name = key
                                    break
                            if not feed_id_using_name and data_entry["link"]:
                                feed_id_using_name = "link"
                            if not feed_id_using_name:
                                feed_id_using_name = "id"
                    data_entry["feed_entry_id"] = getattr(entry, feed_id_using_name, "").strip()
                    if data_entry["feed_entry_id"] and data_entry["feed_entry_id"] in feed_current_entry_id_list:
                        continue
                    elif data_entry["feed_entry_id"]:
                        feed_current_entry_id_list.append(data_entry["feed_entry_id"])
                    data_entry["title"] = getattr(entry, "title", "").strip()
                    summary = getattr(entry, "description", "").strip()
                    content = getattr(entry, "content", [{"value":""}])[0]["value"].strip()
                    desc = summary if len(summary) >= len(content) else content
                    data_entry["desc"] = data_entry["title"] + "<p>" + desc if data_entry["title"] else desc
                    data_entry["feed_updated"] = getattr(entry, "updated", "")
                    entry_existing = False
                    if data_entry["feed_entry_id"]:
                        if cur.execute("select feed_entry_id from doc where feed_id = ? and feed_entry_id = ?",
                                       (feed_id, data_entry["feed_entry_id"])).fetchone():
                            entry_existing = True
                    if data_entry["desc"] and not entry_existing:
                        while True:
                            doc_id = int(time.time()*1000)
                            if doc_id not in self.parent.existing_doc_id_list_part:
                                break
                        data_entry["doc_id"] = doc_id
                        data_entries.append([data_entry["doc_id"],
                                            feed_id,
                                            data_entry["feed_entry_id"],
                                            data_entry["link"],
                                            data_entry["title"],
                                            data_entry["desc"],
                                            data_entry["feed_updated"],
                                            create_date])
                        self.parent.existing_doc_id_list_part.append(doc_id)
                if not data_entries:
                    self.signals.error_message.emit("")
                    return

                # write to db
                if fetch_mod_text:
                    cur.execute("update feed set fetch_mod_text = ?, fetch_mod_date = ? where feed_id = ?",
                                (fetch_mod_text, fetch_mod_date, feed_id))
                else:
                    cur.execute("update feed set fetch_mod_date = ? where feed_id = ?",
                                (fetch_mod_date, feed_id))
                cur.executemany("""insert into doc
                                (doc_id, feed_id, feed_entry_id, link, title, descr, feed_updated, create_date)
                                values (?, ?, ?, ?, ?, ?, ?, ?)""", data_entries)
                conn.commit()
                conn.close()
                self.signals.error_message.emit("")
                return

        def load_error_msg_slot(signal_error_msg):
            self.load_feed_completed_thread_count += 1
            if signal_error_msg:
                self.load_feed_error_message += signal_error_msg + "\n"
            self.status_label.setText("Completed feed %s / %s"
                                      % (self.load_feed_completed_thread_count,
                                         len(self.feed_address_list)))
            if self.load_feed_completed_thread_count == len(self.feed_address_list):
                if self.hard_work:
                    self.hard_work.remove("load_from_feed")
                if not self.need_abort:
                    self.status_label.setText("Completed loading.")
                if not self.hard_work and self.need_abort:
                    self.need_abort = False
                if self.load_feed_error_message:
                    QMessageBox(QMessageBox.Warning, "Warning", self.load_feed_error_message).exec()
                    self.load_feed_error_message = ""
                # enable buttons
                self.manual_input_button.setEnabled(True)
                self.load_text_button.setEnabled(True)
                self.clean_aged_button.setEnabled(True)
                self.add_feed_button.setEnabled(True)
                self.remove_feed_button.setEnabled(True)
                self.load_feed_button.setEnabled(True)

        self.load_feed_completed_thread_count = 0
        self.load_feed_error_message = ''
        feed_list_len = len(self.feed_address_list)
        for i in range(feed_list_len):
            load_thread = LoadFeedThread(self, i)
            load_thread.signals.error_message.connect(load_error_msg_slot)
            thread_pool = QThreadPool.globalInstance()
            thread_pool.start(load_thread)

    def abort_actions(self):
        if not self.hard_work:
            self.need_abort = True

    def clean_aged_data(self):
        config = mw.addonManager.getConfig(__name__)
        doc_aged_def = int(config["clean_normal_docs_over_n_days"])
        doc_aged_fav_def = int(config["clean_favorite_docs_over_n_days"])
        # if doc_aged_def < 100 or doc_aged_fav_def < 100:
        #     show_text("Days threshold to clean data should be above 100.")
        #     return
        now = datetime.datetime.now()
        aged_date_normal = now - datetime.timedelta(days=doc_aged_def)
        aged_date_fav = now - datetime.timedelta(days=doc_aged_fav_def)
        conn = sqlite3.connect(get_path("user_files", "doc.db"),
                               detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.execute("""delete from doc where
                        doc_id in (select doc.doc_id from doc left join words
                                   on doc.doc_id = words.doc_id
                                   where words.doc_id is null and create_date < ?)""", (aged_date_normal,))
        conn.execute("""delete from doc where
                        doc_id in (select doc.doc_id from doc join words
                                   where doc.doc_id = words.doc_id and last_visit_date < ?)""", (aged_date_fav,))
        conn.execute("delete from words where doc_id not in (select doc.doc_id from doc)")
        conn.commit()
        conn.close()
        show_text("Cleaned aged data.")

    def closeEvent(self, event):
        if not self.hard_work:
            event.accept()
        else:
            event.ignore()


def load_feed():

    if not mw.addon_RTMD.load_feed_dialog:
        mw.addon_RTMD.load_feed_dialog = LoadFeedDialog(mw)
    mw.addon_RTMD.load_feed_dialog.show()


class SetNoteTypeToRelateDialog(QDialog, Ui_note_type_setting_dialog):

    def __init__(self, parent):

        super().__init__(parent)
        self.setupUi(self)

        self.mw = mw
        self.col = mw.col
        self.model_manager = self.col.models
        self.all_model_id_list = []
        self.models = self.col.models.all()
        self.models.sort(key=itemgetter("name"))
        self.all_note_type_listWidget.clear()
        for m in self.models:
            item = QListWidgetItem("%s" % m['name'])
            self.all_model_id_list.append(m['id'])
            self.all_note_type_listWidget.addItem(item)
        self.all_note_type_listWidget.setCurrentRow(0)

        self.target_model_id_list = []
        conn = sqlite3.connect(get_path("user_files", "doc.db"))
        for row in conn.execute('select var_value from var_store where var_name = "target_model_id_list"'):
            self.target_model_id_list += json.loads(row[0])
        conn.close()
        self.refresh_target_note_type_listWidget()

        self.add_note_type_button.clicked.connect(self.add_note_type)
        self.remove_note_type_button.clicked.connect(self.remove_note_type)

    def refresh_target_note_type_listWidget(self, select_model_id=""):

        row_to_select = 0
        self.target_note_type_listWidget.clear()
        if self.target_model_id_list:
            self.target_model_id_list.sort()
            for model_id in self.target_model_id_list:
                if model_id not in self.all_model_id_list:
                    self.target_model_id_list.remove(model_id)
            for model_id in self.target_model_id_list:
                item = QListWidgetItem("%s" % self.model_manager.get(model_id)["name"])
                self.target_note_type_listWidget.addItem(item)
                if model_id == select_model_id:
                    row_to_select = self.target_model_id_list.index(model_id)
        self.target_note_type_listWidget.setCurrentRow(row_to_select)

    def add_note_type(self):

        row_select = self.all_note_type_listWidget.currentRow()
        model_id_to_add = self.all_model_id_list[row_select]
        if model_id_to_add in self.target_model_id_list:
            for model_id in self.target_model_id_list:
                if model_id == model_id_to_add:
                    row_to_select = self.target_model_id_list.index(model_id)
                    self.target_note_type_listWidget.setCurrentRow(row_to_select)
            return
        self.target_model_id_list.append(model_id_to_add)
        self.target_model_id_list.sort()
        conn = sqlite3.connect(get_path("user_files", "doc.db"))
        conn.execute('update var_store set var_value = ? where var_name = "target_model_id_list"',
                     (json.dumps(self.target_model_id_list),))
        conn.commit()
        conn.close()
        self.refresh_target_note_type_listWidget(model_id_to_add)

    def remove_note_type(self):

        row_select = self.target_note_type_listWidget.currentRow()
        if row_select not in range(len(self.target_model_id_list)):
            return
        model_id_to_remove = self.target_model_id_list[row_select]
        self.target_model_id_list.remove(model_id_to_remove)
        self.target_model_id_list.sort()
        conn = sqlite3.connect(get_path("user_files", "doc.db"))
        conn.execute('update var_store set var_value = ? where var_name = "target_model_id_list"',
                     (json.dumps(self.target_model_id_list),))
        conn.commit()
        conn.close()
        self.refresh_target_note_type_listWidget()


def set_note_type_to_relate():

    if not mw.addon_RTMD.note_type_setting_dialog:
        mw.addon_RTMD.note_type_setting_dialog = SetNoteTypeToRelateDialog(mw)
    mw.addon_RTMD.note_type_setting_dialog.show()

class ViewDocDialog(QDialog, Ui_view_doc_dialog):

    def __init__(self, parent):

        super().__init__(parent)
        self.setupUi(self)
        self.browser = QWebEngineView()
        self.browser.loadProgress.connect(self.progressBar.setValue)
        self.browser.loadProgress.connect(lambda x: self.progressBar.hide() if x == 100 else None)
        self.progressBar.show()
        self.browser.setHtml("")
        self.desc_view_Layout.addWidget(self.browser)
        self.setGeometry(mw.x(),
                         mw.y() + mw.frameGeometry().height() - self.geometry().height(),
                         self.geometry().width(),
                         self.geometry().height())
        self.cur_page_no_edit.setFixedWidth(36)
        self.cur_page_no_edit.setAlignment(Qt.AlignRight)
        self.cur_page_no_edit.setText("")

        self.prev_button.clicked.connect(self.show_previous)
        self.next_button.clicked.connect(self.show_next)
        self.del_doc_button.clicked.connect(self.delete_doc)
        self.cur_page_no_edit.editingFinished.connect(self.turn_to_doc)

        self.cur_doc_id = 0
        self.show_next()

    def refresh_static_fields_dialog(self, total_count, title, link, desc, feed_updated):

        # data def [total count, title, link, desc, feed_updated]
        link_text = link
        if link:
            if link_text.startswith(r"http://"):
                link_text = link_text[7:]
            if link_text.startswith(r"https://"):
                link_text = link_text[8:]
            if len(link_text) > 36:
                link_text = link_text[:36] + "..."
        else:
            link_text = "No Link"
        self.count_label.setText("/ %d" % total_count)
        self.title_label.setText(title)
        self.link_label.setText('<a href="%s">%s</a>' % (link, link_text))
        self.feed_updated_label.setText(feed_updated)
        self.progressBar.show()
        self.browser.setHtml(desc)

    def show_previous(self):
        conn = sqlite3.connect(get_path("user_files", "doc.db"))
        cur = conn.cursor()
        if not self.cur_doc_id:
            row = cur.execute("select doc_id, title, link, descr, feed_updated from doc order by doc_id desc limit 1").fetchone()
        else:
            row = cur.execute("select doc_id, title, link, descr, feed_updated from doc where doc_id > ? order by doc_id asc limit 1",
                              (self.cur_doc_id,)).fetchone()
        if not row:
            show_text("No previous doc existing.")
            conn.close()
            return
        doc_id = row[0]
        title = row[1]
        link = row[2]
        desc = row[3]
        feed_updated = row[4]
        self.cur_doc_id = doc_id
        total_count = cur.execute("select count(doc_id) from doc").fetchone()[0]
        cur_count = cur.execute("select count(doc_id) from doc where doc_id >= ?", [doc_id]).fetchone()[0]
        conn.close()
        validator = QIntValidator(1, total_count)
        self.cur_page_no_edit.setValidator(validator)
        self.cur_page_no_edit.setText(str(cur_count))
        self.refresh_static_fields_dialog(total_count, title, link, desc, feed_updated)
        self.show()


    def show_next(self):
        conn = sqlite3.connect(get_path("user_files", "doc.db"))
        cur = conn.cursor()
        if not self.cur_doc_id:
            row = cur.execute("select doc_id, title, link, descr, feed_updated from doc order by doc_id desc limit 1").fetchone()
        else:
            row = cur.execute("select doc_id, title, link, descr, feed_updated from doc where doc_id < ? order by doc_id desc limit 1",
                              (self.cur_doc_id,)).fetchone()
        if not row:
            show_text("No next doc existing.")
            conn.close()
            return
        doc_id = row[0]
        title = row[1]
        link = row[2]
        desc = row[3]
        feed_updated = row[4]
        self.cur_doc_id = doc_id
        total_count = cur.execute("select count(doc_id) from doc").fetchone()[0]
        cur_count = cur.execute("select count(doc_id) from doc where doc_id >= ?", [doc_id]).fetchone()[0]
        conn.close()
        validator = QIntValidator(1, total_count)
        self.cur_page_no_edit.setValidator(validator)
        self.cur_page_no_edit.setText(str(cur_count))
        self.refresh_static_fields_dialog(total_count, title, link, desc, feed_updated)
        self.show()

    def turn_to_doc(self):
        turn_to_no = int(self.cur_page_no_edit.text())
        conn = sqlite3.connect(get_path("user_files", "doc.db"))
        cur = conn.cursor()
        total_count = cur.execute("select count(doc_id) from doc").fetchone()[0]
        row = cur.execute("select doc_id, title, link, descr, feed_updated from doc order by doc_id desc limit 1 offset ?",
                              (turn_to_no - 1,)).fetchone()
        if not row:
            show_text("Can not find doc.")
            conn.close()
            return
        doc_id = row[0]
        title = row[1]
        link = row[2]
        desc = row[3]
        feed_updated = row[4]
        self.cur_doc_id = doc_id
        total_count = cur.execute("select count(doc_id) from doc").fetchone()[0]
        conn.close()
        validator = QIntValidator(1, total_count)
        self.cur_page_no_edit.setValidator(validator)
        self.refresh_static_fields_dialog(total_count, title, link, desc, feed_updated)
        self.show()

    def delete_doc(self):
        if not self.cur_doc_id:
            return
        doc_id_to_delete = self.cur_doc_id
        self.browser.setHtml("")
        conn = sqlite3.connect(get_path("user_files", "doc.db"))
        conn.execute("delete from words where doc_id = ?", (doc_id_to_delete,))
        conn.execute("delete from doc where doc_id = ?", (doc_id_to_delete,))
        row = conn.execute("select doc_id from doc order by doc_id desc limit 1").fetchone()
        if not row:
            return
        if doc_id_to_delete != row[0]:
            self.show_previous()
        else:
            self.show_next()
        conn.commit()
        conn.close()
        if self.cur_doc_id == doc_id_to_delete:
            self.cur_doc_id = 0
            self.show_next()

def view_doc():
    if not mw.addon_RTMD.view_doc_dialog:
        mw.addon_RTMD.view_doc_dialog = ViewDocDialog(mw)
    mw.addon_RTMD.view_doc_dialog.show()

class SetPicDirDialog(QDialog, Ui_set_pic_dir_dialog):

    def __init__(self, parent):

        super().__init__(parent)
        self.setupUi(self)

        self.add_dir_button.clicked.connect(self.add_dir)
        self.remove_dir_button.clicked.connect(self.remove_dir)

        config = mw.addonManager.getConfig(__name__)
        pic_dir_list = config["directory_list_for_pics_to_relate"]
        missing_dir_list = []
        self.added_dir_list = []
        for pic_dir in pic_dir_list:
            if pic_dir in self.added_dir_list:
                continue
            if not os.path.isdir(pic_dir):
                missing_dir_list.append(pic_dir)
                continue
            self.added_dir_list.append(pic_dir)
            item = QListWidgetItem(pic_dir)
            self.dir_list_widget.addItem(item)
        # remove missing directory
        if missing_dir_list:
            for pic_dir in missing_dir_list:
                pic_dir_list.remove(pic_dir)
            config["directory_list_for_pics_to_relate"] = pic_dir_list
            mw.addonManager.writeConfig(__name__, config)

    def add_dir(self):
        import_dir = mw.pm.profile.get("importDirectory", "")
        pic_dir = QFileDialog.getExistingDirectory(self, "Add Directory",
                                                   import_dir,
                                                   QFileDialog.ShowDirsOnly
                                                   | QFileDialog.DontResolveSymlinks)
        if not pic_dir:
            return
        if pic_dir in self.added_dir_list:
            show_text("The directory already exists.")
            return
        self.added_dir_list.append(pic_dir)
        config = mw.addonManager.getConfig(__name__)
        config["directory_list_for_pics_to_relate"] = self.added_dir_list
        mw.addonManager.writeConfig(__name__, config)
        item = QListWidgetItem(pic_dir)
        self.dir_list_widget.addItem(item)

    def remove_dir(self):
        dirs_to_remove = []
        for item in self.dir_list_widget.selectedItems():
            row_item = self.dir_list_widget.row(item)
            dirs_to_remove.append(self.added_dir_list[row_item])
            self.dir_list_widget.takeItem(row_item)
        for pic_dir in dirs_to_remove:
            self.added_dir_list.remove(pic_dir)
        config = mw.addonManager.getConfig(__name__)
        config["directory_list_for_pics_to_relate"] = self.added_dir_list
        mw.addonManager.writeConfig(__name__, config)

def set_pic_dir():
    if not mw.addon_RTMD.set_pic_dir_dialog:
        mw.addon_RTMD.set_pic_dir_dialog = SetPicDirDialog(mw)
    mw.addon_RTMD.set_pic_dir_dialog.show()

def load_media_subs():

    import_dir = mw.pm.profile.get("importDirectory", "")
    myfilter = "Subtitles (*.lrc *.srt);;All Files (*.*)"
    open_file_dialog = QFileDialog()
    open_file_dialog.setFileMode(QFileDialog.ExistingFiles)
    load_media_subs_paths = open_file_dialog.getOpenFileNames(mw,
                                                              "Select Sub to Import",
                                                              import_dir,
                                                              myfilter)[0]
    if not load_media_subs_paths:
        return
    mw.addon_RTMD.loading_media_subs = True

    # thread to get feed data
    class LoadSubsThreadSignals(QObject):

        error_message = pyqtSignal(str)

    class LoadSubsThread(QRunnable):

        def __init__(self, parent, sub_path):
            super(LoadSubsThread, self).__init__()
            self.parent = parent
            self.sub_path = sub_path
            self.signals = LoadSubsThreadSignals()

        def run(self):

            if self.parent.loading_media_subs_need_abort \
               or (not self.sub_path.endswith(".lrc")
                   and not self.sub_path.endswith(".srt")):
                self.signals.error_message.emit("")
                return
            media_path_no_ext = self.sub_path[:-4]
            if not os.path.split(media_path_no_ext)[1]:
                self.signals.error_message.emit("Bad file name: %s" % self.sub_path)
                return
            folder_name = os.path.split(os.path.split(media_path_no_ext)[1])[1]
            if self.sub_path.endswith(".lrc"):
                media_ext = ".mp3"
                if not os.path.isfile(media_path_no_ext + ".mp3"):
                    self.signals.error_message.emit("File not found: %s" % media_path_no_ext + ".mp3")
                    return
            else:
                video_ext = (".mp4", ".mkv", ".avi", ".flv", ".m4v", ".f4v", ".rmvb")
                media_ext = ""
                for ext in video_ext:
                    if os.path.isfile(media_path_no_ext + ext):
                        media_ext = ext
                        break
                if not media_ext:
                    self.signals.error_message.emit("Can found media file for: %s" % self.sub_path)
                    return
            # try to open the sub file
            is_ok, sub_data = get_file_data(self.sub_path)
            if not is_ok:
                self.signals.error_message.emit("Encoding should be utf-8: %s" % self.sub_path)
            # save sub_text as <<<start=23,end=43||say something>>>
            # pattern = r"<<<id=(\d+),start=(\d+),end=(\d+)\|\|(.*?)>>>"
            struct_sub = ""
            # parse lrc text
            if self.sub_path.endswith(".lrc"):
                lrc_dict = {}
                re_lrc_line = re.compile(r"(\[\d+:\d+\.\d+\])")
                re_lrc_time = re.compile(r"\[(\d+):(\d+)\.\d+\]")
                for line_text in sub_data.splitlines():
                    line_text = line_text.strip()
                    if not line_text or not re_lrc_time.match(line_text):
                        continue
                    line_time_points = []
                    line_sub_text = ""
                    for element in re_lrc_line.split(line_text):
                        if element:
                            if re_lrc_line.match(element):
                                minute, second = re_lrc_time.match(element).groups()
                                line_time_points.append(int(minute) * 60 + int(second))
                            else:
                                line_sub_text += element.strip()
                    if line_sub_text:
                        for second in line_time_points:
                            if second in lrc_dict:
                                lrc_dict[second] += line_sub_text
                            else:
                                lrc_dict[second] = line_sub_text
                if lrc_dict:
                    struct_master = "<<<start=%d,end=0||%s>>>"
                    for second in sorted(lrc_dict.keys()):
                        struct_sub += struct_master % (second, lrc_dict[second])
            # parse srt text
            else:
                sub_data = sub_data.replace("\r", "").split("\n\n")
                re_srt = re.compile(r"\d+\s*\n(\d+):(\d+):(\d+),\d+ --> (\d+):(\d+):(\d+),\d+\s*\n(.*)", re.DOTALL)
                struct_master = "<<<start=%d,end=%d||%s>>>"
                for data_block in sub_data:
                    if re_srt.match(data_block):
                        # ('00', '00', '10', '00', '00', '11', "想不出来了\nI'm out.")
                        mg = re_srt.match(data_block).groups()
                        if len(mg) < 7:
                            continue
                        struct_sub += struct_master % \
                                      (int(mg[0]) * 3600 + int(mg[1]) * 60 + int(mg[2]),
                                       int(mg[3]) * 3600 + int(mg[4]) * 60 + int(mg[5]),
                                       mg[6].strip())
            # write to db
            conn = sqlite3.connect(get_path("user_files", "doc.db"))
            conn.execute("insert or replace into subs "
                         + "(media_path_no_ext, media_ext, folder_name, sub_text, create_date) values "
                         + "(?, ?, ?, ?, current_timestamp)",
                         (media_path_no_ext, media_ext, folder_name, struct_sub))
            conn.commit()
            conn.close()
            self.signals.error_message.emit("")

    class LoadMediaDialog(QDialog):

        def __init__(self, parent, load_media_subs_paths):
            super().__init__(parent)
            self.parent = parent
            self.load_media_subs_paths = load_media_subs_paths

            self.verticalLayout =QVBoxLayout(self)

            self.progress_bar = QProgressBar(self)
            self.progress_bar.setProperty("value", 0)
            self.progress_bar.setObjectName("progress_bar")
            self.verticalLayout.addWidget(self.progress_bar)
            self.status_label = QLabel(self)
            self.status_label.setText("")
            self.status_label.setObjectName("")
            self.verticalLayout.addWidget(self.status_label)
            self.abort_button = QPushButton(self)
            self.abort_button.setText("Abort The Loading")
            self.abort_button.clicked.connect(self.abort)
            self.verticalLayout.addWidget(self.abort_button)

            # start the work
            self.load_subs_error_message = ""
            self.loading_media_subs_need_abort = False
            self.load_subs_completed_thread_count = 0
            for sub_path in self.load_media_subs_paths:
                load_thread = LoadSubsThread(self, sub_path)
                load_thread.signals.error_message.connect(self.load_error_msg_slot)
                thread_pool = QThreadPool.globalInstance()
                thread_pool.start(load_thread)

        def load_error_msg_slot(self, signal_error_msg):
            self.load_subs_completed_thread_count += 1
            if signal_error_msg:
                self.load_subs_error_message += signal_error_msg + "<p>"
            self.progress_bar.setValue(int(self.load_subs_completed_thread_count * 100
                                           / len(self.load_media_subs_paths)))
            self.status_label.setText("Completed Subs %s / %s"
                                      % (self.load_subs_completed_thread_count,
                                         len(self.load_media_subs_paths)))
            if self.load_subs_completed_thread_count == len(self.load_media_subs_paths):
                if not self.loading_media_subs_need_abort:
                    self.status_label.setText("Completed loading.")
                if self.load_subs_error_message:
                    show_text(self.load_subs_error_message)
                if mw.addon_RTMD.loading_media_subs:
                    mw.addon_RTMD.loading_media_subs = False
                self.abort_button.setEnabled(False)

        def abort(self):
            self.loading_media_subs_need_abort = True

        def closeEvent(self, event):
            if not mw.addon_RTMD.loading_media_subs:
                event.accept()
            else:
                event.ignore()

    LoadMediaDialog(mw, load_media_subs_paths).show()


def export_media_subs_list():

    import_dir = mw.pm.profile.get("importDirectory", "")
    myfilter = "Text (*.txt);;All Files (*.*)"
    save_file_dialog = QFileDialog()
    save_file_path = save_file_dialog.getSaveFileName(mw,
                                                      "Select Filename to Save",
                                                      import_dir + os.sep + "DB with-Sub Media Path List",
                                                      myfilter)[0]
    if save_file_path:
        data_str = ""
        conn = sqlite3.connect(get_path("user_files", "doc.db"))
        for row in conn.execute("select media_path_no_ext||media_ext from subs order by media_path_no_ext"):
            data_str += row[0] + '\n'
        conn.close()
        with open(save_file_path, "w", encoding="utf-8") as f:
            f.write(data_str)
    show_text("Export Completed!")


def clean_missing_file_subs():

    media_path_no_ext_list = []
    media_path_list = []
    conn = sqlite3.connect(get_path("user_files", "doc.db"))
    for row in conn.execute("select media_path_no_ext, media_path_no_ext||media_ext "
                            + "from subs order by media_path_no_ext"):
        media_path_no_ext_list.append(row[0])
        media_path_list.append(row[1])
    conn.close()
    to_del_subs_list = []
    for i in range(len(media_path_no_ext_list)):
        if not os.path.isfile(media_path_list[i]):
            # each element is acturally a tuple
            to_del_subs_list.append((media_path_no_ext_list[i],))
    if to_del_subs_list:
        conn = sqlite3.connect(get_path("user_files", "doc.db"))
        conn.executemany("delete from subs where media_path_no_ext = ?", to_del_subs_list)
        conn.commit()
        conn.close()
        show_text("Cleaned %d missing-file subs in DB" % len(to_del_subs_list))

