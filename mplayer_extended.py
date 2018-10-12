# -*- coding: utf-8 -*-
# Anki sound.py is changed and extended to get more functions required by Anki Relate to My Doc add-on

import html
import re, sys, threading, time, subprocess, os, atexit
import  random
from anki.hooks import addHook, runHook
from anki.utils import  tmpdir, isWin, isMac, isLin
from aqt import mw
from .utils import log

# Packaged commands
##########################################################################

# return modified command array that points to bundled command, and return
# required environment
def _packagedCmd(cmd):
    cmd = cmd[:]
    env = os.environ.copy()
    if "LD_LIBRARY_PATH" in env:
        del env['LD_LIBRARY_PATH']
    if isMac:
        dir = os.path.dirname(os.path.abspath(__file__))
        exeDir = os.path.abspath(dir + "/../../Resources/audio")
    else:
        exeDir = os.path.dirname(os.path.abspath(sys.argv[0]))
        if isWin and not cmd[0].endswith(".exe"):
            cmd[0] += ".exe"
    path = os.path.join(exeDir, cmd[0])
    if not os.path.exists(path):
        return cmd, env
    cmd[0] = path
    return cmd, env

##########################################################################

# don't show box on windows
if isWin:
    si = subprocess.STARTUPINFO()
    try:
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    except:
        # python2.7+
        si.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
else:
    si = None

# Mplayer in slave mode
##########################################################################

mplayerCmd = ["mplayer", "-really-quiet", "-noautosub"]
if isWin:
    mplayerCmd += ["-ao", "win32"]

media_to_play = ""
media_in_play = ""
start_sec = 0
end_sec = 0
stop_play_timer = None
mplayerManager = None
mplayerReader = None
mplayerEvt = threading.Event()
mplayerClear = False

class MplayerMonitor(threading.Thread):

    def run(self):
        global mplayerEvt
        global mplayerClear, media_to_play, start_sec, media_in_play
        self.mplayer = None
        self.deadPlayers = []
        while 1:
            mplayerEvt.wait()
            mplayerEvt.clear()
            # clearing queue?
            if mplayerClear and self.mplayer:
                try:
                    self.mplayer.stdin.write(b"stop\n")
                    self.mplayer.stdin.flush()
                except:
                    # mplayer quit by user (likely video)
                    self.deadPlayers.append(self.mplayer)
                    self.mplayer = None
            # loop through files to play
            # modified - Anki RTMD add-on: now we only need to play one file
            # but we keep the loop letting it working only for one file
            while media_to_play:
                # ensure started
                if not self.mplayer:
                    self.startProcess()
                # play target file
                if mplayerClear:
                    mplayerClear = False
                cmd = b'loadfile "%s"\n' % media_to_play.encode("utf8")
                if start_sec:
                    seek_cmd = b'seek %s 2\n' % str(start_sec).encode("utf8")
                try:
                    self.mplayer.stdin.write(cmd)
                    if start_sec:
                        self.mplayer.stdin.write(seek_cmd)
                    self.mplayer.stdin.flush()
                    media_in_play = media_to_play
                    media_to_play = ""
                except:
                    # mplayer has quit and needs restarting
                    self.deadPlayers.append(self.mplayer)
                    self.mplayer = None
                    self.startProcess()
                    self.mplayer.stdin.write(cmd)
                    self.mplayer.stdin.flush()
                # if we feed mplayer too fast it loses files
                time.sleep(1)
            # wait() on finished processes. we don't want to block on the
            # wait, so we keep trying each time we're reactivated
            def clean(pl):
                if pl.poll() is not None:
                    pl.wait()
                    return False
                else:
                    return True
            self.deadPlayers = [pl for pl in self.deadPlayers if clean(pl)]

    def kill(self):
        if not self.mplayer:
            return
        try:
            self.mplayer.stdin.write(b"quit\n")
            self.mplayer.stdin.flush()
            self.deadPlayers.append(self.mplayer)
        except:
            pass
        self.mplayer = None

    def startProcess(self):
        try:
            cmd = mplayerCmd + ["-slave", "-idle"]
            wid_mplayer_container = mw.addon_RTMD.relate_to_my_doc_dialog.wid_mplayer_container
            #cmd = [cmd[0], "-fs", "-wid", str(wid_mplayer_container)] + cmd[1:]
            try:
                cmd += ["-fs", "-wid", str(wid_mplayer_container)]
                cmd, env = _packagedCmd(cmd)
                self.mplayer = subprocess.Popen(
                    cmd, startupinfo=si, stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    env=env)
            except:
                cmd += ["-wid", str(wid_mplayer_container)]
                cmd, env = _packagedCmd(cmd)
                self.mplayer = subprocess.Popen(
                    cmd, startupinfo=si, stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    env=env)
        except OSError:
            mplayerEvt.clear()
            raise Exception("Did you install mplayer?")

def queueMplayer(path, start_sec_p=0, end_sec_p=0):
    global media_to_play, start_sec, end_sec, stop_play_timer
    ensureMplayerThreads()
    if isWin and os.path.exists(path):
        # mplayer on windows doesn't like the encoding, so we create a
        # temporary file instead. oddly, foreign characters in the dirname
        # don't seem to matter.
        config = mw.addonManager.getConfig(__name__)
        if "my_mplayer_need_copying_file_to_temp" in config \
                and config["my_mplayer_need_copying_file_to_temp"]:
            dir = tmpdir()
            name = os.path.join(dir, "audio%s%s" % (
                random.randrange(0, 1000000), os.path.splitext(path)[1]))
            f = open(name, "wb")
            f.write(open(path, "rb").read())
            f.close()
            # it wants unix paths, too!
            path = name
        path = path.replace("\\", "/")
    media_to_play = path
    if isinstance(start_sec_p, int) and start_sec_p >= 0:
        start_sec = start_sec_p
    else:
        start_sec = 0
    if isinstance(end_sec_p, int) and end_sec_p > start_sec:
        end_sec = end_sec_p
        if stop_play_timer and stop_play_timer.is_alive():
            stop_play_timer.cancel()
        stop_play_timer = threading.Timer(10.0, stop_as_planned, kwargs={"media_path_to_stop": media_to_play})
        stop_play_timer.start()
    else:
        end_sec = 0
    mplayerEvt.set()

def stop_as_planned(media_path_to_stop):
    global media_in_play
    if media_path_to_stop == media_in_play:
        clearMplayerPlaying()

def clearMplayerPlaying():
    global mplayerClear, media_to_play, start_sec, end_sec
    media_to_play = ""
    start_sec = 0
    end_sec = 0
    mplayerClear = True
    mplayerEvt.set()
    media_in_play = ""

def ensureMplayerThreads():
    global mplayerManager
    if not mplayerManager:
        mplayerManager = MplayerMonitor()
        mplayerManager.daemon = True
        mplayerManager.start()
        # ensure the tmpdir() exit handler is registered first so it runs
        # after the mplayer exit
        tmpdir()
        # clean up mplayer on exit
        atexit.register(stopMplayer)

def stopMplayer(*args):
    if not mplayerManager:
        return
    mplayerManager.kill()

addHook("unloadProfile", stopMplayer)


# interface
##########################################################################

def play(path, start_sec=0, end_sec=0):
    queueMplayer(path, start_sec, end_sec)

def stop():
    clearMplayerPlaying()
