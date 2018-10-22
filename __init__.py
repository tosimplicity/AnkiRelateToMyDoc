#-*- coding:utf-8 -*-
#
# Copyright (C) 2018 sthoo <sth201807@gmail.com>
#
# Support: Report an issue at https://github.com/sth2018/FastWordQuery/issues
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version; http://www.gnu.org/copyleft/gpl.html.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# from . import myRes_rc

__version__ = "0.51"
__license__ = "GNU Affero General Public License, version 3 or later"

import ssl
import sys
from anki.hooks import addHook
from anki.utils import isMac
from aqt import mw
from PyQt5.Qt import *
import logging
from .logging_handlers import TimedRotatingFileHandler
from .main import relate_to_my_doc
from .main import load_feed
from .main import set_note_type_to_relate
from .main import view_doc
from .main import set_pic_dir
from .main import my_test
from .main import load_media_subs, export_media_subs_list, clean_missing_file_subs
from .utils import log, show_text, get_path
from . import myRes_rc

sys.dont_write_bytecode = True
if isMac:
    ssl._create_default_https_context = ssl._create_unverified_context

instructions_media_op = """Subs for audio should be *.lrc in standard LRC format.
Subs for video should be *.srt in standard SRT format.
Video/Audio should be located in same folder with identical file name except file extension.
For example.lrc or example.srt, media files should be example.mp3, example.mp4, example.mkv
For audio, only *.mp3 file would be searched.
For video, search first found: *.mp4, *.mkv, *.avi, *.flv, *.m4v, *.f4v, *.rmvb
(MPlayer can play files in many more formats. But you need to change extension for add-on to search.
Like changing example.rmvb to example.avi)
*** Load Sub: The Subs file will be loaded into local db if media file is found.
*** Load Sub: If an old Sub exists, it will get replaced
*** Clean Subs DB vs Media Files: check if media file in the fisrt found path exists. if not, remove the sub in DB.
"""

class AnkiRelateToMyDoc(object):
    """docstring for ClassName"""
    def __init__(self, mw):
        self.relate_to_my_doc_dialog = None
        self.load_feed_dialog = None
        self.note_type_setting_dialog = None
        self.view_doc_dialog = None
        self.set_pic_dir_dialog = None
        self.loading_media_subs = False
        self.silent_for_new_card = False

    def close(self):
        if self.relate_to_my_doc_dialog:
            self.relate_to_my_doc_dialog.close()
        if self.load_feed_dialog:
            self.load_feed_dialog.close()
        if self.note_type_setting_dialog:
            self.note_type_setting_dialog.close()
        if self.view_doc_dialog:
            self.view_doc_dialog.close()
        if self.set_pic_dir_dialog:
            self.set_pic_dir_dialog.close()

mw.addon_RTMD = AnkiRelateToMyDoc(mw)


def set_up_addon():

    icon_relate = QIcon()
    icon_relate.addPixmap(QPixmap(":/res/res/relate.png"), QIcon.Normal, QIcon.On)
    addon_menu = mw.form.menuTools.addMenu(icon_relate, "Relate To My Doc")

    icon_set_note_type = QIcon()
    icon_set_note_type.addPixmap(QPixmap(":/res/res/set_type.png"), QIcon.Normal, QIcon.On)
    action = QAction(icon_set_note_type, "Set NoteType to Relate", mw)
    action.triggered.connect(set_note_type_to_relate)
    addon_menu.addAction(action)

    addon_menu.addSeparator()
    addon_menu.addSeparator()

    icon_load_feed = QIcon()
    icon_load_feed.addPixmap(QPixmap(":/res/res/loadfeed.png"), QIcon.Normal, QIcon.On)
    action = QAction(icon_load_feed, "Load Feed", mw)
    action.triggered.connect(load_feed)
    addon_menu.addAction(action)

    icon_view_doc = QIcon()
    icon_view_doc.addPixmap(QPixmap(":/res/res/view.png"), QIcon.Normal, QIcon.On)
    action = QAction(icon_view_doc, "View Docs", mw)
    action.triggered.connect(view_doc)
    addon_menu.addAction(action)

    addon_menu.addSeparator()

    icon_set_pic_dir = QIcon()
    icon_set_pic_dir.addPixmap(QPixmap(":/res/res/pic.png"), QIcon.Normal, QIcon.On)
    action = QAction(icon_set_pic_dir, "Set Pic Directory", mw)
    action.triggered.connect(set_pic_dir)
    addon_menu.addAction(action)

    addon_menu.addSeparator()

    icon_load_media = QIcon()
    icon_load_media.addPixmap(QPixmap(":/res/res/media.png"), QIcon.Normal, QIcon.On)
    subMenu = QMenu("Manage Multimedia Subs", mw)
    subMenu.setIcon(icon_load_media)
    addon_menu.addMenu(subMenu)

    # my_test_action = QAction(icon_load_feed, "My Test", mw)
    # my_test_action.triggered.connect(my_test)
    # addon_menu.addAction(my_test_action)


    # submenu for "Load Multimedia Subs"
    action = QAction(icon_load_feed, "Load Multimedia Subs", mw)
    action.triggered.connect(load_media_subs)
    subMenu.addAction(action)
    icon = QIcon()
    icon.addPixmap(QPixmap(":/res/res/list.png"), QIcon.Normal, QIcon.On)
    action = QAction(icon, "Export Complete Sub-Media Path List", mw)
    action.triggered.connect(export_media_subs_list)
    subMenu.addAction(action)
    icon = QIcon()
    icon.addPixmap(QPixmap(":/res/res/clean.png"), QIcon.Normal, QIcon.On)
    action = QAction(icon, "Clean Subs DB vs Media Files", mw)
    action.triggered.connect(clean_missing_file_subs)
    subMenu.addAction(action)
    icon = QIcon()
    icon.addPixmap(QPixmap(":/res/res/info.png"), QIcon.Normal, QIcon.On)
    action = QAction(icon, "Instructions", mw)
    action.triggered.connect(lambda: show_text(instructions_media_op))
    subMenu.addAction(action)

    logger = logging.getLogger(__name__)
    f_handler = TimedRotatingFileHandler(
        get_path("user_files", "addon_log"), when='S', interval=60, backupCount=3, encoding="utf-8")
    f_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    f_handler.setLevel(logging.DEBUG)
    logger.addHandler(f_handler)
    logger.setLevel(logging.DEBUG)

    config = mw.addonManager.getConfig(__name__)
    if "sync_feed_on_start" in config and config["sync_feed_on_start"]:
        load_feed()
        mw.addon_RTMD.load_feed_dialog.load_from_feed()

def close_addon():

    mw.addon_RTMD.close()

def close_relate_dialog_on_leave(newState, oldstate, *args):

    if newState != "review":
        if hasattr(mw.addon_RTMD, "relate_to_my_doc_dialog") and mw.addon_RTMD.relate_to_my_doc_dialog:
            mw.addon_RTMD.relate_to_my_doc_dialog.close()

addHook("profileLoaded", set_up_addon)
addHook("unloadProfile", close_addon)
addHook('afterStateChange', close_relate_dialog_on_leave)
addHook("showAnswer", relate_to_my_doc)