# coding: utf-8

from __future__ import print_function
import os
import zipfile
import rarfile
import argparse
from io import BytesIO
from collections import OrderedDict as order_dict
from traceback import format_exc

import chardet
from guessit import guessit
from requests import exceptions
from requests import get

from sys_global_var import py, prefix, is_gbk
from __init__ import __version__
from subhd import SubHDDownloader
from zimuzu import ZimuzuDownloader


class GetSubtitles(object):

    def __init__(self, name, query, more, over, debug, sub_num, downloader):
        self.video_format_list = ['.webm', '.mkv', '.flv', '.vob', '.ogv',
                                  '.ogg', '.drc', '.gif', '.gifv', '.mng',
                                  '.avi', '.mov', '.qt', '.wmv', '.yuv',
                                  '.rm', '.rmvb', '.asf', '.amv', '.mp4',
                                  '.m4p', '.m4v', 'mpg', '.mp2', '.mpeg',
                                  '.mpe', '.mpv', '.mpg', '.m2v', '.svi',
                                  '.3gp', '.3g2', '.mxf', '.roq', '.nsv',
                                  '.flv', '.f4v', '.f4p', '.f4a', '.f4b']
        self.sub_format_list = ['.ass', '.srt', '.ssa', '.sub']
        self.support_file_list = ['.zip', '.rar']
        self.arg_name = name
        self.query, self.more, self.over = query, more, over
        if not sub_num:
            self.sub_num = 5
        else:
            self.sub_num = int(sub_num)
        self.debug = debug
        self.s_error = ''
        self.f_error = ''
        self.subhd = SubHDDownloader()
        self.zimuzu = ZimuzuDownloader()
        if not downloader:
            self.downloader = [self.zimuzu, self.subhd]
        elif downloader == 'subhd':
            self.downloader = [self.subhd]
        elif downloader == 'zimuzu':
            self.downloader = [self.zimuzu]
        else:
            print("no such downloader, please choose from 'subhd','zimuzu'")
        self.failed_list = []  # [{'name', 'path', 'error', 'trace_back'}

    def get_path_name(self, args):

        """ 传入输入的视频名称或路径,
            构造一个包含视频路径和是否存在字幕信息的字典返回。
            video_dict: {'path': path, 'have_subtitle': sub_exists} """

        mix_str = args.replace('"', '')
        video_dict = order_dict()
        if os.path.isdir(mix_str):  # 一个文件夹
            for root, dirs, files in os.walk(mix_str):
                for one_name in files:
                    suffix = os.path.splitext(one_name)[1]
                    # 检查后缀是否为视频格式
                    if suffix not in self.video_format_list:
                        continue
                    v_name_no_format = os.path.splitext(one_name)[0]
                    sub_exists = max(
                        list(
                            map(
                                lambda sub_type:
                                    int(v_name_no_format + sub_type in files),
                                    self.sub_format_list
                            )
                        )
                    )
                    video_dict[one_name] = {'path': root,
                                            'have_subtitle': sub_exists}

        elif os.path.isabs(mix_str):  # 视频绝对路径
            v_path, v_name = os.path.split(mix_str)
            v_name_no_format = os.path.splitext(v_name)[0]
            sub_exists = max(
                list(
                    map(
                        lambda sub_type:
                            os.path.exists(
                                os.path.join(v_path, v_name_no_format+sub_type)
                            ),
                            self.sub_format_list
                    )
                )
            )
            video_dict[v_name] = {'path': os.path.dirname(mix_str),
                                  'have_subtitle': sub_exists}
        else:  # 单个视频名字，无路径
            video_dict[mix_str] = {'path': os.getcwd(), 'have_subtitle': 0}
        return video_dict

    def sort_keyword(self, name):

        """ 解析视频名
            返回将各个关键字按重要度降序排列的列表，原始视频信息 """

        name = name.replace('[', '')
        name = name.replace(']', '')
        keywords = []
        info_dict = guessit(name)

        base_keyword = info_dict['title']
        if info_dict.get('year') and info_dict.get('type') == 'movie':
            base_keyword += (' ' + str(info_dict['year']))  # 若为电影添加年份
        if info_dict.get('season'):
            base_keyword += (' s%s' % str(info_dict['season']).zfill(2))
        keywords.append(base_keyword)
        if info_dict.get('episode'):
            keywords.append(' e%s' % str(info_dict['episode']).zfill(2))
        if info_dict.get('screen_size'):
            keywords.append(str(info_dict['screen_size']))
        if info_dict.get('format'):
            keywords.append(info_dict['format'])
        if info_dict.get('release_group'):
            keywords.append(info_dict['release_group'])
        return keywords, info_dict

    def choose_subtitle(self, sub_dict):

        """ 传入候选字幕字典
            若为查询模式返回选择的字幕包名称，字幕包下载地址
            否则返回字幕字典第一个字幕包的名称，字幕包下载地址 """

        if not self.query:
            chosen_sub = list(sub_dict.keys())[0]
            link = sub_dict[chosen_sub]['link']
            if py == 2:
                encoding = chardet.detect(chosen_sub)['encoding']
                chosen_sub = chosen_sub.decode(encoding)
                if is_gbk:
                    chosen_sub = chosen_sub.encode('gbk')
                else:
                    chosen_sub = chosen_sub.encode('utf8')
            return chosen_sub, link

        for i, key in enumerate(sub_dict.keys()):
            if i == self.sub_num:
                break
            lang_info = ''
            lang_info += '【简】' if 4 & sub_dict[key]['lan'] else '      '
            lang_info += '【繁】' if 2 & sub_dict[key]['lan'] else '      '
            lang_info += '【英】' if 1 & sub_dict[key]['lan'] else '      '
            lang_info += '【双】' if 8 & sub_dict[key]['lan'] else '      '
            a_sub_info = ' %3s) %s  %s' % (i + 1, lang_info, key)
            if py == 2 and is_gbk:
                a_sub_info = a_sub_info.decode('utf8').encode('gbk')
            a_sub_info = prefix + a_sub_info
            print(a_sub_info)

        indexes = range(len(sub_dict.keys()))
        choice = None
        while not choice:
            try:
                print(prefix)
                choice = int(input(prefix + '  choose subtitle: '))
            except ValueError:
                print(prefix + '  Error: only numbers accepted')
                continue
            if not choice - 1 in indexes:
                print(prefix + '  Error: numbers not within the range')
                choice = None
        chosen_sub = list(sub_dict.keys())[choice - 1]
        link = sub_dict[chosen_sub]['link']
        if py == 2:
            encoding = chardet.detect(chosen_sub)['encoding']
            chosen_sub = chosen_sub.decode(encoding)
            if is_gbk:
                chosen_sub = chosen_sub.encode('gbk')
            else:
                chosen_sub = chosen_sub.encode('utf8')
        return chosen_sub, link

    def guess_subtitle(self, sublist, video_info):

        """ 传入压缩包字幕列表，视频信息，返回最佳字幕名称。
            若没有符合字幕，查询模式下返回第一条字幕， 否则返回None """

        video_name = video_info['title'].lower()
        season = str(video_info.get('season'))
        episode = str(video_info.get('episode'))

        score = []
        for one_sub in sublist:
            one_sub = one_sub.lower()
            score.append(0)  # 字幕起始分数

            if one_sub[-1] == '/':  # 压缩包内文件夹，跳过
                continue

            one_sub = os.path.split(one_sub)[-1]  # 提取文件名
            try:
                # zipfile:/Lib/zipfile.py:1211 Historical ZIP filename encoding
                # try cp437 encoding
                one_sub = one_sub.encode('cp437').decode('gbk')
            except:
                pass
            sub_name_info = guessit(one_sub)
            if sub_name_info.get('title'):
                sub_title = sub_name_info['title'].lower()
            else:
                sub_title = ''
            sub_season = str(sub_name_info.get('season'))
            sub_episode = str(sub_name_info.get('episode'))
            if video_name == sub_title:
                if not (season == sub_season and episode == sub_episode):
                    continue  # 名字匹配，剧集不匹配
                else:
                    score[-1] += 2  # 名字剧集都匹配
            elif season == sub_season and episode == sub_episode:
                score[-1] += 2  # 名字不匹配，剧集匹配
            else:
                score[-1] -= 2
                continue  # 名字剧集都不匹配

            try:
                if '简体' in one_sub or 'chs' in one_sub or '.gb.' in one_sub:
                    score[-1] += 5
                if '繁体' in one_sub or 'cht' in one_sub or '.big5.' in one_sub:
                    score[-1] += 3
                if '中英' in one_sub or '简英' in one_sub or '双语' in one_sub \
                        or 'chs&eng' in one_sub or '简体&英文' in one_sub:
                    score[-1] += 7
            # py2 strange decode error, happens time to time
            except UnicodeDecodeError:
                if '简体'.decode('utf8') in one_sub \
                        or 'chs' in one_sub or '.gb.' in one_sub:
                    score[-1] += 5
                if '繁体'.decode('utf8') in one_sub \
                        or 'cht' in one_sub or '.big5.' in one_sub:
                    score[-1] += 3
                if '中英'.decode('utf8') in one_sub \
                        or '简英'.decode('utf8') in one_sub \
                        or '双语'.decode('utf8') in one_sub \
                        or '简体&英文'.decode('utf8') in one_sub \
                        or 'chs&eng' in one_sub :
                    score[-1] += 7

            score[-1] += ('ass' in one_sub or 'ssa' in one_sub) * 2
            score[-1] += ('srt' in one_sub) * 1

        max_score = max(score)
        if max_score == 0 and not self.query:
            return None
        max_pos = score.index(max_score)

        return sublist[max_pos]

    def get_file_list(self, file_handler):

        """ 传入一个压缩文件控制对象，读取对应压缩文件内文件列表。
            返回 {one_sub: file_handler} """

        sub_lists_dict = dict()
        for one_file in file_handler.namelist():

            if one_file[-1] == '/':
                continue
            if os.path.splitext(one_file)[-1] in self.sub_format_list:
                sub_lists_dict[one_file] = file_handler
                continue

            if os.path.splitext(one_file)[-1] in self.support_file_list:
                sub_buff = BytesIO(file_handler.read(one_file))
                datatype = os.path.splitext(one_file)[-1]
                if datatype == '.zip':
                    sub_file_handler = zipfile.ZipFile(sub_buff, mode='r')
                elif datatype == '.rar':
                    sub_file_handler = rarfile.RarFile(sub_buff, mode='r')
                sub_lists_dict.update(self.get_file_list(sub_file_handler))

        return sub_lists_dict

    def extract_subtitle(self, v_name, v_path, datatype, sub_data_b, v_info_d):

        """ 接受下载好的字幕包字节数据， 猜测字幕并解压。 """

        sub_buff = BytesIO()
        sub_buff.write(sub_data_b)

        if datatype == '.zip':
            file_handler = zipfile.ZipFile(sub_buff, mode='r')
        elif datatype == '.rar':
            file_handler = rarfile.RarFile(sub_buff, mode='r')

        sub_lists_dict = dict()
        sub_lists_dict.update(self.get_file_list(file_handler))

        # sub_lists = [x for x in file_handler.namelist() if x[-1] != '/']

        sub_name = self.guess_subtitle(list(sub_lists_dict.keys()), v_info_d)

        if not sub_name:  # 自动模式下无最佳猜测
            return None

        os.chdir(v_path)  # 切换到视频所在文件夹

        v_name_without_format = os.path.splitext(v_name)[0]
        # video_name + sub_type
        sub_new_name = v_name_without_format + os.path.splitext(sub_name)[1]

        for one_sub_type in self.sub_format_list:  # 删除若已经存在的字幕
            if os.path.exists(v_name_without_format + one_sub_type):
                os.remove(v_name_without_format + one_sub_type)

        with open(sub_new_name, 'wb') as sub:  # 保存字幕
            file_handler = sub_lists_dict[sub_name]
            sub.write(file_handler.read(sub_name))

        if self.more:  # 保存原字幕压缩包
            with open(v_name_without_format + datatype, 'wb') as f:
                f.write(sub_data_b)
            print(prefix + ' save original file.')

        return sub_name

    def start(self):

        all_video_dict = self.get_path_name(self.arg_name)

        for one_video, video_info in all_video_dict.items():

            self.s_error = ''  # 重置错误记录
            self.f_error = ''

            print('\n' + prefix + ' ' + one_video)  # 打印当前视频及其路径
            print(prefix + ' ' + video_info['path'] + '\n' + prefix)

            if video_info['have_subtitle'] and not self.over:
                print(prefix
                      + " subtitle already exists, add '-o' to replace it.")
                continue
            try:
                keywords, info_dict = self.sort_keyword(one_video)
                sub_dict = order_dict()
                for downloader in self.downloader:
                    sub_dict.update(
                        downloader.get_subtitles(
                                tuple(keywords), sub_num=self.sub_num)
                    )
                    if len(sub_dict) >= self.sub_num:
                        break
                if len(sub_dict) == 0:
                    self.s_error += 'no search results'
                    continue

                extract_sub_name = None
                # 遍历字幕包直到有猜测字幕
                while not extract_sub_name and len(sub_dict) > 0:
                    sub_choice, link = self.choose_subtitle(sub_dict)
                    if self.query:
                        print(prefix + ' ')
                    if '[ZMZ]' in sub_choice:
                        datatype, sub_data_bytes = self.zimuzu.download_file(
                            sub_choice, link
                        )
                    elif '[SUBHD]' in sub_choice:
                        datatype, sub_data_bytes, msg = self.subhd.\
                            download_file(sub_choice, link)
                        if msg == 'false':
                            print(prefix + ' error: '
                                  'download too frequently '
                                  'with subhd downloader, '
                                  'please change to other downloaders')
                            return

                    if datatype in self.support_file_list:
                        # 获得猜测字幕名称
                        # 查询模式必有返回值，自动模式无猜测值返回None
                        extract_sub_name = self.extract_subtitle(
                                one_video, video_info['path'], datatype,
                                sub_data_bytes, info_dict
                                )
                        if extract_sub_name:
                            try:
                                # zipfile: Historical ZIP filename encoding
                                # try cp437 encoding
                                pass
                                extract_sub_name = extract_sub_name.\
                                    encode('cp437').decode('gbk')
                            except:
                                pass
                            try:
                                print(prefix + ' ' + extract_sub_name + '\n')
                            except UnicodeDecodeError:
                                print(prefix + ' '
                                      + extract_sub_name.encode('gbk') + '\n')
                    elif self.query:  # 查询模式下下载字幕包为不支持类型
                        print(prefix
                              + '  unsupported file type %s' % datatype[1:])

            except exceptions.Timeout or exceptions.ConnectionError:
                self.s_error += 'connect failed, check network status.'
            except rarfile.RarCannotExec:
                self.s_error += 'Unrar not installed?'
            except AttributeError:
                self.s_error += 'unknown error. try again.'
                self.f_error += format_exc()
            except Exception as e:
                self.s_error += str(e) + '. '
                self.f_error += format_exc()
            finally:
                if ('extract_sub_name' in dir()
                        and not extract_sub_name
                        and len(sub_dict) == 0):
                    # 自动模式下所有字幕包均没有猜测字幕
                    self.s_error += " failed to guess one subtitle,"
                    self.s_error += "use '-q' to try query mode."

                if self.s_error and not self.debug:
                    self.s_error += "add --debug to get more info of the error"

                if self.s_error:
                    self.failed_list.append({'name': one_video,
                                             'path': video_info['path'],
                                             'error': self.s_error,
                                             'trace_back': self.f_error})
                    print(prefix + ' error:' + self.s_error)

        if len(self.failed_list):
            print('\n===============================', end='')
            print('FAILED LIST===============================\n')
            for i, one in enumerate(self.failed_list):
                print('%2s. name: %s' % (i + 1, one['name']))
                print('%3s path: %s' % ('', one['path']))
                print('%3s info: %s' % ('', one['error']))
                if self.debug:
                    print('%3s TRACE_BACK: %s' % ('', one['trace_back']))

        print('\ntotal: %s  success: %s  fail: %s\n' % (
            len(all_video_dict),
            len(all_video_dict) - len(self.failed_list),
            len(self.failed_list)
        ))


def test_network():
    try:
        get('http://baidu.com')
    except exceptions.ConnectionError:
        return 0
    except:
        return -1
    return 1


def main():

    arg_parser = argparse.ArgumentParser(
        prog='GetSubtitles',
        epilog='getsub %s \n\n@guoyuhang' % __version__,
        description='download subtitles easily',
        formatter_class=argparse.RawTextHelpFormatter
    )
    arg_parser.add_argument(
        'name',
        help="the video's name or full path or a dir with videos"
    )
    arg_parser.add_argument(
        '-q',
        '--query',
        action='store_true',
        help='show search results and choose one to download'
    )
    arg_parser.add_argument(
        '-o',
        '--over',
        action='store_true',
        help='replace the subtitle already exists'
    )
    arg_parser.add_argument(
        '-m',
        '--more',
        action='store_true',
        help='save original download file.'
    )
    arg_parser.add_argument(
        '-n',
        '--number',
        action='store',
        help='set max number of subtitles to be choosen when in query mode'
    )
    arg_parser.add_argument(
        '-d',
        '--downloader',
        action='store',
        help='choose downloader'
    )
    arg_parser.add_argument(
        '--debug',
        action='store_true',
        help='show more info of the error'
    )

    args = arg_parser.parse_args()

    if args.over:
        print('\nThe script will replace the old subtitles if exist...\n')

    if test_network() == 0:
        print('check your network connection')
        return
    elif test_network() == -1:
        print('unknown error, add --debug to show detailed infomation')
        return

    GetSubtitles(args.name, args.query, args.more,
                 args.over, args.debug, sub_num=args.number,
                 downloader=args.downloader).start()


if __name__ == '__main__':
    main()
