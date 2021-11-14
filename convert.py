'''
    把m4s转成mp3
'''

import os
import time
import subprocess

src_dir = './梓宝歌曲切片/'
dst_dir = './梓宝歌曲切片mp3/'
ffmpeg  = './ffmpeg/ffmpeg.exe'
cpu_cores = 8

if not os.path.isdir(dst_dir): os.mkdir(dst_dir)

li = [i.rsplit('.', 1)[0] for i in os.listdir(src_dir) if i.endswith('.m4s')]

counter = 0
_len = len(li)
for i in range(0, _len, cpu_cores):
    tasks = []
    for f in li[i:i+cpu_cores]:
        f1, f2 = os.path.join(src_dir, f+'.m4s'), os.path.join(dst_dir, f+'.mp3')
        p = subprocess.Popen([ffmpeg, '-i', f1, f2], shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tasks.append(p)
    while not all([ (i.poll() is not None) for i in tasks ]):
        time.sleep(1)
    counter += 8
    if counter > _len: counter = _len
    print(counter, '/', _len)

print('ok')