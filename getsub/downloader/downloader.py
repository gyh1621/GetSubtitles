# coding: utf-8

import re
import sys

from guessit import guessit
from requests.utils import quote

from getsub.sys_global_var import py


class Downloader(object):

    header = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\
                            AppleWebKit 537.36 (KHTML, like Gecko) Chrome",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,\
                            image/webp,*/*;q=0.8"
    }

    service_short_names = {
        'amazon prime': 'amzn'
    }

    @classmethod
    def num_to_cn(cls, number):

        """ 转化 1-99 的数字至中文 """

        assert number.isdigit() and 1 <= int(number) <= 99

        trans_map = {n: c for n, c in zip(('123456789'), ('一二三四五六七八九'))}

        if len(number) == 1:
            return trans_map[number]
        else:
            part1 = '十' if number[0] == '1' else trans_map[number[0]] + '十'
            part2 = trans_map[number[1]] if number[1] != '0' else ''
            return part1 + part2

    @classmethod
    def get_keywords(cls, video_name):

        """ 解析视频名
        Args:
            video_name: 视频文件名
        Return:
            keywords: list
            info_dict: guessit原始结果
        """

        name = video_name.replace('[', '')
        name = video_name.replace(']', '')
        keywords = []
        info_dict = guessit(video_name)

        # 若视频名中英混合，去掉字少的语言
        title = info_dict['title']
        if py == 2:
            if sys.stdout.encoding == 'cp936':
                encoding = 'gbk'
            else:
                encoding = 'utf8'
            title = title.decode(encoding)
            c_pattern = u'[\u4e00-\u9fff]'
            e_pattern = u'[a-zA-Z]'
            c_num = len(re.findall(c_pattern, title))
            e_num = len(re.findall(e_pattern, title))
            if c_num > e_num:
                title = re.sub(e_pattern, '', title).encode('utf8')
            else:
                title = re.sub(c_pattern, '', title).encode('utf8')
        elif py == 3:
            c_pattern = '[\u4e00-\u9fff]'
            e_pattern = '[a-zA-Z]'
            c_num = len(re.findall(c_pattern, title))
            e_num = len(re.findall(e_pattern, title))
            if c_num > e_num:
                title = re.sub(e_pattern, '', title)
            else:
                title = re.sub(c_pattern, '', title)
        title = title.strip()

        base_keyword = title

        if info_dict.get('season'):
            base_keyword += (' s%s' % str(info_dict['season']).zfill(2))
        keywords.append(base_keyword)

        if info_dict.get('year') and info_dict.get('type') == 'movie':
            keywords.append(str(info_dict['year']))  # 若为电影添加年份

        if info_dict.get('episode'):
            keywords.append('e%s' % str(info_dict['episode']).zfill(2))
        if info_dict.get('source'):
            keywords.append(info_dict['source'].replace('-', ''))
        if info_dict.get('release_group'):
            keywords.append(info_dict['release_group'])
        if info_dict.get('streaming_service'):
            service_name = info_dict['streaming_service']
            short_names = cls.service_short_names.get(service_name.lower())
            if short_names:
                keywords.append(short_names)
        if info_dict.get('screen_size'):
            keywords.append(str(info_dict['screen_size']))

        # 对关键字进行 URL 编码
        keywords = [quote(_keyword) for _keyword in keywords]
        return keywords, info_dict

    def get_subtitles(self, video_name, sub_num=5):

        """ 搜索字幕
        Args:
            video_name: 视频文件名
            sub_num: 字幕结果数，默认为5
        Return：
            字幕字典: 按语言值降序排列
            eg: {'字幕名': {'lan': '语言值', 'link': '字幕链接', 'session': '查询session'}}
            字幕包含语言值：英文加1， 繁体加2， 简体加4， 双语加8
        """

        raise NotImplementedError

    def download_file(self, file_name, sub_url, session=None):

        """ 下载字幕包
        Args:
            file_name: 字幕包名
            sub_url: 下载链接，为 'get_subtitles' 返回结果中 'link' 值
            session: 查询session
        Return:
            data_type: 压缩文件类型，如 '.rar', '.zip', '.7z'
            sub_data_bytes: 字幕包二进制数据
            err_msg : 错误消息，无则返回 ''
        """

        raise NotImplementedError