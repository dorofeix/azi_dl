'''
批量提取并下载收藏夹视频中的音频
'''

import asyncio
from bilibili_api import video, Credential, favorite_list
import aiohttp
import os

ROOT_DIR = os.path.dirname(__file__)

tot = 0
save_dir = os.path.join(ROOT_DIR, 'temp')
async def fetch_videos(MEDIA_ID, cre=None):
    print('获取收藏夹第 1 页...', end='')
    page_data = await favorite_list.get_video_favorite_list_content(media_id=MEDIA_ID, page=1, credential=cre)
    fl_title = page_data['info']['title'] # 收藏夹标题
    videos_li = [ [i['title'], i['bvid']] for i in page_data['medias']]
    print('ok')
    for page in range(2, 999):
        if not page_data['has_more']: break
        print('获取收藏夹第', page, '页...', end='')
        page_data = await favorite_list.get_video_favorite_list_content(media_id=MEDIA_ID, page=page, credential=cre)
        videos_li.extend([ [i['title'], i['bvid']] for i in page_data['medias']])
        print('ok')
    global tot
    tot = len(videos_li)
    print('收藏夹数据获取完毕, 共', tot, '个视频')
    if not tot: return []
    global save_dir
    save_dir = os.path.join(ROOT_DIR, fl_title) # 收藏夹标题作为下载文件夹名
    if not os.path.isdir(save_dir):
        os.mkdir(save_dir)
    with open(os.path.join(save_dir, 'videos.txt'), 'w', encoding='utf-8') as f:
        for v in videos_li:
            f.write(f"{v[1]}\t{v[0]}\n")
    return videos_li

counter = 0
_filter = {
    '？': '',
    '、': ' ',
    '╲': '',
    '*': '※',
    '“': '"',
    '”': '"',
    '<': '《',
    '>': '》',
    '|': '‖',
    '.': ' '
}
def filter_fn(fn):
    _fn = fn
    for c in _fn:
        if c in _filter: fn = fn.replace(c, _filter[c])
    return fn

async def dl(bvid, fn, cre=None, session=None):
    global counter
    fn = filter_fn(fn)
    abs_fn = os.path.join(save_dir, fn + '.m4s')
    if (fn=='已失效视频') or os.path.isfile(abs_fn):
        # 跳过已失效视频和之前下载过的文件
        counter += 1
        # print('下载进度：', counter, '/', tot)
        return

    print('开始下载:', fn)

    try:
        # 实例化 Video 类
        v = video.Video(bvid=bvid, credential=cre)
        # 获取视频下载链接
        url = await v.get_download_url(0)
        # 音频轨链接
        audio_url = url["dash"]["audio"][0]['baseUrl']
    except Exception as e:
        prnit(fn, e)
        counter += 1
        # print('下载进度：', counter, '/', tot)
        return

    # 下载音频流
    close_session = False
    if session is None:
        timeout = aiohttp.ClientTimeout(total=60*60, sock_read=240)
        session = aiohttp.ClientSession(timeout=timeout)
        close_session = True
    HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.bilibili.com/"
    }
    resp = 'null'
    try:
        async with session.get(audio_url, headers=HEADERS) as resp:
            length = resp.headers.get('content-length')
            with open(abs_fn, 'wb') as f: # m4s
                async for chunk in resp.content.iter_chunked(2048):
                    # https://stackoverflow.com/questions/56346811/response-payload-is-not-completed-using-asyncio-aiohttp
                    await asyncio.sleep(0)
                    f.write(chunk)
    except Exception as e:
        # print(resp)
        # print(resp.headers.get('content-type'))
        # raise e
        try: # 下载失败删掉无效文件
            if os.path.isfile(abs_fn): os.remove(abs_fn)
        except:
            pass
        # 写错误日志
        with open(os.path.join(save_dir, 'error.log'), 'a', encoding='utf-8') as f:
            f.write(f"{bvid} \t {fn}\n")
        print("下载失败：", fn)
    if close_session: await session.close()

    counter += 1
    print('下载进度：', counter, '/', tot)

async def main(MEDIA_ID, cre, max_retry=3, videos_li=None, retry=0):
    # await dl("BV1f54y1j7X8", "test.m4s", cre)
    # return
    if retry > max_retry: return
    global counter
    counter = 0
    if not videos_li:
        videos_li = await fetch_videos(MEDIA_ID, cre)
    if not videos_li: return
    timeout = aiohttp.ClientTimeout(total=60*60, sock_read=240)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # 音频文件不是很大，不需要开很多的并发连接去下载，设置每10个一组同时下载
        for i in range(0, tot, 10):
            task_list = [ dl(v[1], v[0], cre=cre, session=session) for v in videos_li[i:i+10]]
            await asyncio.gather(*task_list)

    error_fn = os.path.join(save_dir, 'error.log')

    if (retry < max_retry) and os.path.isfile(error_fn):
        os.remove(error_fn)
        print('检查到有下载失败项目，开始重试...')
        await main(MEDIA_ID, cre, max_retry, videos_li, retry+1)

    if retry == 0:
        if os.path.isfile(error_fn):
            print('全部任务已完成，程序已多次重试，但仍有项目下载失败...')
            print('请检查error.log文件，尝试重新运行！')
        else:
            print('全部任务已完成，所有项目下载完毕！')


if __name__ == '__main__':
    MEDIA_ID = 1156105580 # 收藏夹id

    SESSDATA = "" # 登录信息
    BILI_JCT = ""
    BUVID3 = ""
    cre = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)

    asyncio.get_event_loop().run_until_complete(main(MEDIA_ID, cre))