#!/usr/bin/python3
#coding: utf-8

from __future__ import print_function
from contextlib import closing
from collections import OrderedDict as order_dict

import requests
from bs4 import BeautifulSoup
from guessit import guessit

from sys_global_var import py, prefix
from progress_bar import ProgressBar


''' Zimuku 字幕下载器
'''


class ZimukuDownloader(object):

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\
                            AppleWebKit 537.36 (KHTML, like Gecko) Chrome",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Accept": "text/html,application/xhtml+xml,\
                        application/xml;q=0.9,image/webp,*/*;q=0.8"
        }
        self.site_url = 'http://www.zimuku.cn'
        self.search_url = 'http://www.zimuku.cn/search?q='

    def get_subtitles(self, keywords, sub_num=10):

        print(prefix + ' Searching ZIMUKU...', end='\r')

        keywords = list(keywords)
        keyword = ' '.join(keywords)
        info = guessit(keyword)
        keywords.pop(0)
        keywords.insert(0, info['title'])
        if info.get('season'):
            season = str(info['season']).zfill(2)
            keywords.insert(1, season)

        sub_dict = order_dict()
        s = requests.session()
        s.headers.update(self.headers)

        while True:
            # 当前关键字搜索
            r = s.get(self.search_url + keyword, timeout=10)
            if py == 2:
                html = r.text.encode('utf8')
            else:
                html = r.text

            if '搜索不到相关字幕' not in html:
                bs_obj = BeautifulSoup(r.text, 'html.parser')

                if bs_obj.find('div', {'class': 'item'}):
                    # 综合搜索页面
                    for item in bs_obj.find_all('div', {'class': 'item'}):
                        title_boxes = item.find(
                            'div', {'class': 'title'}).find_all('p')
                        title_box = title_boxes[0]
                        sub_title_box = title_boxes[1]
                        if py == 2:
                            item_title = title_box.text.encode('utf8')
                            item_sub_title = sub_title_box.text.encode('utf8')
                        else:
                            item_title = title_box.text
                            item_sub_title = sub_title_box.text
                        item_info = guessit(item_title)
                        if info.get('year') and item_info.get('year'):
                            if info['year'] != item_info['year']:
                                # 年份不匹配，跳过
                                continue
                        item_titles = [
                            item_info.get('title', '').lower(),
                            item_info.get('alternative_title', '').lower()
                        ] + item_sub_title.lower().strip().split(',')
                        title_included = sum([
                            1 for _ in item_sub_title
                            if info['title'].lower() not in _
                        ])
                        if title_included == 0:
                            # guessit抽取标题不匹配，跳过
                            item_title_split = \
                                [one.split() for one in item_titles]
                            info_title_split = info['title'].lower().split()
                            sum1 = sum([1 for _ in info_title_split
                                        if _ in item_title_split[0]])
                            sum2 = sum([1 for _ in info_title_split
                                        if _ in item_title_split[1]])
                            if not (sum1 / len(info_title_split) >= 0.5
                                    or sum2 / len(info_title_split) >= 0.5):
                                # 标题不匹配，跳过
                                continue
                        for a in item.find_all('td', {'class': 'first'})[:3]:
                            a = a.a
                            a_link = self.site_url + a.attrs['href']
                            if py == 2:
                                a_title = a.text.encode('utf8')
                            else:
                                a_title = a.text
                            a_title = '[ZIMUKU]' + a_title
                            sub_dict[a_title] = {'type': 'default',
                                                 'link': a_link}
                elif bs_obj.find('div', {'class': 'persub'}):
                    # 射手字幕页面
                    for persub in bs_obj.find_all('div', {'class': 'persub'}):
                        if py == 2:
                            a_title = persub.h1.text.encode('utf8')
                        else:
                            a_title = persub.h1.text
                        a_link = self.site_url + persub.h1.a.attrs['href']
                        a_title = '[ZIMUKU]' + a_title
                        sub_dict[a_title] = {'type': 'shooter', 'link': a_link}
                else:
                    raise ValueError('Zimuku搜索结果出现未知结构页面')

            if len(sub_dict) >= sub_num:
                del keywords[:]
                break

            if len(keywords) > 1:
                keyword = keyword.replace(keywords[-1], '').strip()
                keywords.pop(-1)
                continue

            break

        for sub_name, sub_info in sub_dict.items():
            if sub_info['type'] == 'default':
                # 综合搜索字幕页面
                r = s.get(sub_info['link'], timeout=60)
                bs_obj = BeautifulSoup(r.text, 'html.parser')
                lang_box = bs_obj.find('ul', {'class': 'subinfo'}).find('li')
                type_score = 0
                for lang in lang_box.find_all('img'):
                    if 'uk' in lang.attrs['src']:
                        type_score += 1
                    elif 'hongkong' in lang.attrs['src']:
                        type_score += 2
                    elif 'china' in lang.attrs['src']:
                        type_score += 4
                    elif 'jollyroger' in lang.attrs['src']:
                        type_score += 8
                sub_info['lan'] = type_score
                download_link = 'http:' \
                    + bs_obj.find('a', {'id': 'down1'}).attrs['href']
                r = s.get(download_link, timeout=60)
                bs_obj = BeautifulSoup(r.text, 'html.parser')
                download_link = bs_obj.find('a', {'rel': 'nofollow'})
                download_link = 'http://www.subku.net' + \
                    download_link.attrs['href']
                sub_info['link'] = download_link
            else:
                # 射手字幕页面
                r = s.get(sub_info['link'], timeout=60)
                bs_obj = BeautifulSoup(r.text, 'html.parser')
                lang_box = bs_obj.find('ul', {'class': 'subinfo'}).find('li')
                type_score = 0
                if py == 2:
                    text = lang_box.text.encode('utf8')
                else:
                    text = lang_box.text
                if '英' in text:
                    type_score += 1
                elif '繁' in text:
                    type_score += 2
                elif '简' in text:
                    type_score += 4
                elif '双语' in text:
                    type_score += 8
                sub_info['lan'] = type_score
                download_link = bs_obj.find('a', {'id': 'down1'}).attrs['href']
                sub_info['link'] = download_link

        return sub_dict

    def download_file(self, file_name, download_link):

        try:
            with closing(requests.get(download_link, stream=True)) as response:
                filename = response.headers['Content-Disposition']
                chunk_size = 1024  # 单次请求最大值
                # 内容体总大小
                content_size = int(response.headers['content-length'])
                bar = ProgressBar(prefix + ' Get',
                                  file_name.strip(), content_size)
                sub_data_bytes = b''
                for data in response.iter_content(chunk_size=chunk_size):
                    sub_data_bytes += data
                    bar.refresh(len(sub_data_bytes))
        except requests.Timeout:
            return None, None, 'false'
        if '.rar' in filename:
            datatype = '.rar'
        elif '.zip' in filename:
            datatype = '.zip'
        elif '.7z' in filename:
            datatype = '.7z'
        else:
            datatype = 'Unknown'

        with open('test.zip', 'wb') as f:
            f.write(sub_data_bytes)
        return datatype, sub_data_bytes


if __name__ == '__main__':
    from main import GetSubtitles
    keywords, info_dict = GetSubtitles(
        '', 1, 2, 3, 4, 5, 6, 7).sort_keyword('the expanse s01e01')
    zimuku = ZimukuDownloader()
    sub_dict = zimuku.get_subtitles(keywords)
    print('\nResult:')
    for k, v in sub_dict.items():
        print(k, v)
