# coding: utf-8

from __future__ import print_function
import time
import json
import re
from contextlib import closing
from collections import OrderedDict as order_dict

import requests
from bs4 import BeautifulSoup

from getsub.downloader.downloader import Downloader
from getsub.sys_global_var import py, prefix
from getsub.progress_bar import ProgressBar


''' SubHD 字幕下载器
'''


class SubHDDownloader(Downloader):

    name = 'subhd'
    choice_prefix = '[SUBHD]'
    site_url = 'https://subhd.tv'
    search_url = 'https://subhd.tv/search/'

    def get_subtitles(self, video_name, sub_num=5):

        print(prefix + ' Searching SUBHD...', end='\r')

        keywords, info_dict = Downloader.get_keywords(video_name)
        keyword = ' '.join(keywords)

        sub_dict = order_dict()
        s = requests.session()
        while True:
            # 当前关键字查询
            r = s.get(SubHDDownloader.search_url + keyword,
                      headers=Downloader.header, timeout=10)
            bs_obj = BeautifulSoup(r.text, 'html.parser')
            try:
                if py == 2:
                    small_text = bs_obj.find('small').text.encode('utf8')
                else:
                    small_text = bs_obj.find('small').text
            except AttributeError as e:
                char_error = 'The URI you submitted has disallowed characters'
                if char_error in bs_obj.text:
                    print(prefix + ' [SUBHD ERROR] '
                          + char_error + ': ' + keyword)
                    return sub_dict
                # 搜索验证按钮
                time.sleep(2)
                continue

            if '总共 0 条' not in small_text:
                for one_box in bs_obj.find_all('div', {'class': 'box'}):

                    if info_dict['type'] == 'movie' \
                       and not one_box.find('div', {'class': 'movielist'}):
                        continue

                    a = one_box.find('div', {'class': 'd_title'}).find('a')
                    sub_url = SubHDDownloader.site_url + a.attrs['href']
                    sub_name = SubHDDownloader.choice_prefix + a.text.encode('utf8') if py == 2 \
                        else SubHDDownloader.choice_prefix + a.text
                    if py == 2:
                        text = one_box.text.encode('utf8')
                    else:
                        text = one_box.text
                    if '/ar' in a.attrs['href']:
                        type_score = 0
                        type_score += ('英文' in text) * 1
                        type_score += ('繁体' in text) * 2
                        type_score += ('简体' in text) * 4
                        type_score += ('双语' in text) * 8
                        sub_dict[sub_name] = {
                            'lan': type_score,
                            'link': sub_url,
                            'session': None
                        }
                    if len(sub_dict) >= sub_num:
                        del keywords[:]  # 字幕条数达到上限，清空keywords
                        break

            if len(keywords) > 1:  # 字幕数未满，更换关键词继续查询
                keyword = keyword.replace(keywords[-1], '')
                keywords.pop(-1)
                continue

            break

        if (len(sub_dict.items()) > 0
                and list(sub_dict.items())[0][1]['lan'] < 8):
            # 第一个候选字幕没有双语
            sub_dict = order_dict(
                sorted(sub_dict.items(),
                       key=lambda e: e[1]['lan'], reverse=True)
            )
        return sub_dict

    def download_file(self, file_name, sub_url, session=None):

        sid = sub_url.split('/')[-1]
        r = requests.get(sub_url, headers=Downloader.header)
        bs_obj = BeautifulSoup(r.text, 'html.parser')
        dtoken = bs_obj.find('button', {'id': 'down'})['dtoken']

        r = requests.post(SubHDDownloader.site_url + '/ajax/down_ajax',
                          data={'sub_id': sid, 'dtoken': dtoken},
                          headers=Downloader.header)

        content = r.content.decode('unicode-escape')
        if json.loads(content)['success'] is False:
            msg = 'download too frequently with subhd downloader,' + \
                ' please change to other downloaders'
            return None, None, msg
        res = re.search('http:.*(?=")', r.content.decode('unicode-escape'))
        download_link = res.group(0).replace('\\/', '/')
        try:
            with closing(requests.get(download_link, stream=True)) as response:
                chunk_size = 1024  # 单次请求最大值
                # 内容体总大小
                content_size = int(response.headers['content-length'])
                bar = ProgressBar(prefix + ' Get',
                                  file_name.strip(), content_size)
                sub_data_bytes = b''
                for data in response.iter_content(chunk_size=chunk_size):
                    sub_data_bytes += data
                    bar.refresh(len(sub_data_bytes))
            # sub_data_bytes = requests.get(download_link, timeout=10).content
        except requests.Timeout:
            return None, None, 'false'
        if 'rar' in download_link:
            datatype = '.rar'
        elif 'zip' in download_link:
            datatype = '.zip'
        elif '7z' in download_link:
            datatype = '.7z'
        else:
            datatype = 'Unknown'

        return datatype, sub_data_bytes, ''
