# coding: utf-8

from __future__ import print_function
from collections import OrderedDict as order_dict
from contextlib import closing

import requests
from bs4 import BeautifulSoup

from sys_global_var import py, prefix
from progress_bar import ProgressBar


''' Zimuzu 字幕下载器
'''


class ZimuzuDownloader(object):
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\
                            AppleWebKit 537.36 (KHTML, like Gecko) Chrome",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Accept": "text/html,application/xhtml+xml,\
                        application/xml;q=0.9,image/webp,*/*;q=0.8"
        }
        self.site_url = 'http://www.zimuzu.tv'
        self.search_url = 'http://www.zimuzu.tv/search?\
                            keyword={0}&type=subtitle'

    def get_subtitles(self, keywords, sub_num=5):

        print(prefix + ' Searching ZIMUZU...', end='\r')

        keywords = list(keywords)
        keyword = ''
        for one in keywords:
            keyword += (one + ' ')

        sub_dict = order_dict()
        s = requests.session()
        while True:
            # 当前关键字查询
            r = s.get(self.search_url.format(keyword), headers=self.headers)
            bs_obj = BeautifulSoup(r.text, 'html.parser')
            tab_text = bs_obj.find('div', {'class': 'article-tab'}).text
            tab_text = tab_text.encode('utf8') if py == 2 else tab_text
            if '字幕(0)' not in tab_text:
                for one_box in bs_obj.find_all('div',
                                               {'class': 'search-item'}):
                    sub_name = '[ZMZ]' + one_box.find('p').find('font').text
                    sub_name = sub_name.encode('utf8') if py == 2 else sub_name
                    a = one_box.find('a')
                    text = a.text.encode('utf8') if py == 2 else a.text
                    sub_url = self.site_url + a.attrs['href']
                    type_score = 0
                    type_score += ('英文' in text) * 1
                    type_score += ('繁体' in text) * 2
                    type_score += ('简体' in text) * 4
                    type_score += ('中英' in text) * 8
                    sub_dict[sub_name] = {'lan': type_score, 'link': sub_url}
                    if len(sub_dict) >= sub_num:
                        del keywords[:]  # 字幕条数达到上限，清空keywords
                        break

            if len(keywords) > 1:  # 字幕数未满，更换关键词继续查询
                keyword = keyword.replace(keywords[-1], '')
                keywords.pop(-1)
                continue

            break

        # 第一个候选字幕没有双语
        if (len(sub_dict.items()) > 0
                and list(sub_dict.items())[0][1]['lan'] < 8):
            sub_dict = order_dict(
                sorted(sub_dict.items(),
                       key=lambda e: e[1]['lan'],
                       reverse=True)
            )
        return sub_dict

    def download_file(self, file_name, sub_url):

        """ 传入字幕页面链接， 字幕包标题， 返回压缩包类型，压缩包字节数据 """

        s = requests.session()
        r = s.get(sub_url, headers=self.headers)
        bs_obj = BeautifulSoup(r.text, 'html.parser')
        a = bs_obj.find('div', {'class': 'subtitle-links'}).a
        download_link = a.attrs['href']

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
            return None, None
        if 'rar' in download_link:
            datatype = '.rar'
        elif 'zip' in download_link:
            datatype = '.zip'
        elif '7z' in download_link:
            datatype = '.7z'
        else:
            datatype = 'Unknown'

        return datatype, sub_data_bytes
