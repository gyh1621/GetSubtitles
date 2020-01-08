# coding: utf-8

from __future__ import print_function
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin
from contextlib import closing
from collections import OrderedDict as order_dict

import requests
from bs4 import BeautifulSoup
from guessit import guessit

from getsub.downloader.downloader import Downloader
from getsub.sys_global_var import py, prefix
from getsub.progress_bar import ProgressBar


''' Zimuku 字幕下载器
'''


class ZimukuDownloader(Downloader):

    name = 'zimuku'
    choice_prefix = '[ZIMUKU]'
    site_url = 'http://www.zimuku.la'
    search_url = 'http://www.zimuku.la/search?q='

    def get_subtitles(self, video_name, sub_num=10):

        print(prefix + ' Searching ZIMUKU...', end='\r')

        keywords, info_dict = Downloader.get_keywords(video_name)
        keyword = ' '.join(keywords)

        info = guessit(keyword)
        keywords.pop(0)
        keywords.insert(0, info['title'])
        if info.get('season'):
            season = str(info['season']).zfill(2)
            keywords.insert(1, 's' + season)

        sub_dict = order_dict()
        s = requests.session()
        s.headers.update(Downloader.header)

        while True:
            # 当前关键字搜索
            r = s.get(ZimukuDownloader.search_url + keyword, timeout=10)
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
                            a_link = ZimukuDownloader.site_url + \
                                a.attrs['href']
                            if py == 2:
                                a_title = a.text.encode('utf8')
                            else:
                                a_title = a.text
                            a_title = ZimukuDownloader.choice_prefix + a_title
                            sub_dict[a_title] = {'type': 'default',
                                                 'link': a_link}
                elif bs_obj.find('div', {'class': 'persub'}):
                    # 射手字幕页面
                    for persub in bs_obj.find_all('div', {'class': 'persub'}):
                        if py == 2:
                            a_title = persub.h1.text.encode('utf8')
                        else:
                            a_title = persub.h1.text
                        a_link = ZimukuDownloader.site_url + \
                            persub.h1.a.attrs['href']
                        a_title = ZimukuDownloader.choice_prefix + a_title
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
                download_link = bs_obj.find('a', {'id': 'down1'}).attrs['href']
                download_link = urljoin(
                    ZimukuDownloader.site_url, download_link)
                r = s.get(download_link, timeout=60)
                bs_obj = BeautifulSoup(r.text, 'html.parser')
                download_link = bs_obj.find('a', {'rel': 'nofollow'})
                download_link = download_link.attrs['href']
                download_link = urljoin(
                    ZimukuDownloader.site_url, download_link)
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
            backup_session = requests.session()
            backup_session.headers.update(s.headers)
            backup_session.headers['Referer'] = sub_info['link']
            backup_session.cookies.update(s.cookies)
            sub_info['session'] = backup_session

        if (len(sub_dict.items()) > 0
                and list(sub_dict.items())[0][1]['lan'] < 8):
            # 第一个候选字幕没有双语
            sub_dict = order_dict(
                sorted(sub_dict.items(),
                       key=lambda e: e[1]['lan'], reverse=True)
            )
        keys = list(sub_dict.keys())[:sub_num]
        return {key: sub_dict[key] for key in keys}

    def download_file(self, file_name, download_link, session=None):

        try:
            if not session:
                session = requests.session()
            with closing(session.get(download_link, stream=True)) as response:
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

        return datatype, sub_data_bytes, ''
