import ctypes
import sys

mp3 = sys.argv[1]
mci = ctypes.windll.winmm.mciSendStringW
r = mci(f'open "{mp3}" type mpegvideo alias t1', None, 0, 0)
print('open:', r)
r = mci('play t1', None, 0, 0)
print('play:', r)
import time
time.sleep(3)
r = mci('close t1', None, 0, 0)
print('close:', r)
