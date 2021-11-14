'''
    给mp3文件加上metadata（艺术家、专辑、标题...）
'''

import os
import eyed3

src_dir = './梓宝歌曲切片mp3/'

li = [i.rsplit('.', 1)[0] for i in os.listdir(src_dir) if i.endswith('.mp3')]
counter = 0
_len = len(li)
for fn in li:
    title = fn.split('】', 1)[-1]
    title = title.split('《', 1)[-1]
    title = title.split('》', 1)[0]
    fn = os.path.join(src_dir, fn+'.mp3')
    audiofile = eyed3.load(fn)
    audiofile.tag.artist = "阿梓"
    audiofile.tag.album = "阿梓歌曲切片"
    audiofile.tag.title = title
    audiofile.tag.save()
    counter += 1
    print(counter, '/', _len)
    
print('ok')