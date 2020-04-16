# coding: utf-8

import re
import zipfile
import tempfile
import subprocess
from os import path
from io import BytesIO
from shutil import get_terminal_size

import rarfile
from guessit import guessit

from getsub.constants import SUB_FORMATS, ARCHIVE_TYPES


class ProgressBar:
    def __init__(self, prefix_info, title="", total="", count_time=0):
        self.title = title
        self.total = total
        self.prefix_info = prefix_info

    def refresh(self, cur_len):
        terminal_width = get_terminal_size().columns  # 获取终端宽度
        info = "%s '%s'...  %.2f%%" % (
            self.prefix_info,
            self.title,
            cur_len / self.total * 100,
        )
        while len(info) > terminal_width - 20:
            self.title = self.title[0:-4] + "..."
            info = "%s '%s'...  %.2f%%" % (
                self.prefix_info,
                self.title,
                cur_len / self.total * 100,
            )
        end_str = "\r" if cur_len < self.total else "\n"
        print(info, end=end_str)


def num_to_cn(number):
    """
    转化 1-99 的数字至中文
    """
    assert number.isdigit() and 1 <= int(number) <= 99

    trans_map = {n: c for n, c in zip(("123456789"), ("一二三四五六七八九"))}

    if len(number) == 1:
        return trans_map[number]
    else:
        part1 = "十" if number[0] == "1" else trans_map[number[0]] + "十"
        part2 = trans_map[number[1]] if number[1] != "0" else ""
        return part1 + part2


def extract_name(name, en=False):
    """
    提取文字
    若 en 为 True，提取 name 中英文
    若 en 为 False，提取 name 中占比大的语言

    params:
        name: str, name to be processed
    return:
        new_name: str, extracted name
    """
    name, suffix = path.splitext(name)
    c_pattern = "[\u4e00-\u9fff]"
    e_pattern = "[a-zA-Z]"
    c_indices = [m.start(0) for m in re.finditer(c_pattern, name)]
    e_indices = [m.start(0) for m in re.finditer(e_pattern, name)]

    if en or len(c_indices) <= len(e_indices):
        target, discard = e_indices, c_indices
    else:
        target, discard = c_indices, e_indices

    if len(target) == 0:
        return ""

    first_target, last_target = target[0], target[-1]
    first_discard = discard[0] if discard else -1
    last_discard = discard[-1] if discard else -1
    if last_discard < first_target:
        new_name = name[first_target:]
    elif last_target < first_discard:
        new_name = name[:first_discard]
    else:
        # try to find maximum continous part
        result, start, end = [0, 1], -1, 0
        while end < len(name):
            while end not in e_indices and end < len(name):
                end += 1
            if end == len(name):
                break
            start = end
            while end not in c_indices and end < len(name):
                end += 1
            if end - start > result[1] - result[0]:
                result = [start, end]
            start = end
            end += 1
        new_name = name[result[0] : result[1]]
    new_name = new_name.strip() + suffix
    return new_name


def _print_and_choose(items):

    for i, item in enumerate(items):
        print("%3s) %s" % (i, item))

    choice = None
    while choice is None:
        try:
            print()
            choice = input(" choose: ")
            choice = int(choice)
            assert choice < len(items)
        except ValueError:
            print(" only numbers accepted")
            choice = None
        except AssertionError:
            print(" ", end="\r")
            print("choice %d not within the range" % choice)
            choice = None
    print()

    return choice


def choose_archive(sub_dict, sub_num=5, query=True):
    """
    传入候选字幕字典，返回选择的字幕包名称，字幕包下载地址

    params:
        sub_dict: dict, check downloader.py
        sub_num: int, maximum number of subtitles
        query: bool, return first sub if False
    return:
        exit: bool
        chosen_subs: str, subtitle name
    """

    exit = False

    if not query:
        chosen_sub = list(sub_dict.keys())[0]
        return exit, chosen_sub

    items = []
    items.append("Exit. Not downloading any subtitles.")
    for i, key in enumerate(sub_dict.keys()):
        if i == sub_num:
            break
        lang_info = ""
        lang_info += "【简】" if 4 & sub_dict[key]["lan"] else "      "
        lang_info += "【繁】" if 2 & sub_dict[key]["lan"] else "      "
        lang_info += "【英】" if 1 & sub_dict[key]["lan"] else "      "
        lang_info += "【双】" if 8 & sub_dict[key]["lan"] else "      "
        sub_info = "%s  %s" % (lang_info, key)
        items.append(sub_info)

    choice = _print_and_choose(items)
    if choice == 0:
        exit = True
        return exit, []

    return exit, list(sub_dict.keys())[choice - 1]


def choose_subtitle(subtitles):
    """
    传入字幕列表，返回选择字幕名

    params:
        subtitles: list of str
    return:
        subname: str
    """

    items = []
    for subtitle in subtitles:
        try:
            # zipfile: Historical ZIP filename encoding
            subtitle = subtitle.encode("cp437").decode("gbk")
        except Exception:
            pass
        items.append(subtitle)

    choice = _print_and_choose(items)

    return subtitles[choice]


def compute_subtitle_score(video_detail, subname, match_episode=True):
    """
    计算字幕分数

    params:
        video_detail: dict, result of guessit
        subname: str
        match_episode: bool, whether episode number
                       needed to match if video is a TV show
    return:
        score: int, return -1 if not match with videos
    """

    video_name = video_detail["title"].lower()
    season = str(video_detail.get("season"))
    episode = str(video_detail.get("episode"))
    year = str(video_detail.get("year"))
    vtype = str(video_detail.get("type"))

    subname = subname.lower()
    score = 0

    sub_name_info = guessit(subname)
    if sub_name_info.get("title"):
        sub_title = sub_name_info["title"].lower()
    else:
        sub_title = ""
    sub_season = str(sub_name_info.get("season"))
    sub_episode = str(sub_name_info.get("episode"))
    sub_year = str(sub_name_info.get("year"))

    if vtype == "movie":
        if year == sub_year:
            score += 1
        if video_name == sub_title:
            score += 1
        elif sub_title != "":
            return -1
    else:
        if video_name == sub_title:
            if season != sub_season:
                return -1  # title match, season not match
            elif episode != sub_episode and match_episode:
                return -1  # title match, episode not match
            else:
                score += 1  # title and episode match
        elif season == sub_season and episode == sub_episode:
            # title not match, episode match
            if sub_title != "":
                return -1
        else:
            return -1  # title and episode not match

    if "简体" in subname or "chs" in subname or ".gb." in subname:
        score += 2
    if "繁体" in subname or "cht" in subname or ".big5." in subname:
        pass
    if "chs.eng" in subname or "chs&eng" in subname:
        score += 2
    if "中英" in subname or "简英" in subname or "双语" in subname or "简体&英文" in subname:
        score += 4

    score += ("ass" in subname or "ssa" in subname) * 2
    score += ("srt" in subname) * 1

    return score


def guess_subtitle(sublist, video_detail):
    """
    传入字幕列表，视频信息，返回得分最高字幕名

    params:
        sublist: list of str
        video_detail: result of guessit
    return:
        success: bool
        subname: str
    """

    if not sublist:
        return False, None

    scores, subs = [], []
    for one_sub in sublist:
        _, ftype = path.splitext(one_sub)
        if ftype not in SUB_FORMATS:
            continue
        subs.append(one_sub)
        subname = path.split(one_sub)[-1]  # extract subtitle name
        try:
            # zipfile:/Lib/zipfile.py:1211 Historical ZIP filename encoding
            # try cp437 encoding
            subname = subname.encode("cp437").decode("gbk")
        except Exception:
            pass
        score = compute_subtitle_score(video_detail, subname)
        scores.append(score)

    max_score = max(scores)
    max_pos = scores.index(max_score)
    return max_score > 0, subs[max_pos]


def get_file_list(data, datatype):
    """
    传入一个压缩文件控制对象，读取对应压缩文件内文件列表

    params:
        data: binary data of an archive file
        datatype: str, file type
    return:
        sub_lists_dict: dict, {subname: file_handler}
    """

    sub_buff = BytesIO(data)

    if datatype == ".7z":
        try:
            sub_buff.seek(0)
            file_handler = P7ZIP(sub_buff)
        except Exception:
            datatype = ".zip"  # try with zipfile
    if datatype == ".zip":
        try:
            sub_buff.seek(0)
            file_handler = zipfile.ZipFile(sub_buff, mode="r")
        except Exception:
            datatype = ".rar"  # try with rarfile
    if datatype == ".rar":
        sub_buff.seek(0)
        file_handler = rarfile.RarFile(sub_buff, mode="r")

    sub_lists_dict = dict()

    for one_file in file_handler.namelist():

        if path.splitext(one_file)[-1] in SUB_FORMATS:
            sub_lists_dict[one_file] = file_handler
            continue

        if path.splitext(one_file)[-1] in ARCHIVE_TYPES:
            data = file_handler.read(one_file)
            datatype = path.splitext(one_file)[-1]
            sub_lists_dict.update(get_file_list(data, datatype))

    return sub_lists_dict


def run_command(cmd):
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    output, error = process.communicate()
    return output.decode(), error.decode(), process.returncode


class P7ZIP:
    def __init__(self, file):
        self.data = file.read()
        # test if it is a valid 7zip file
        self.namelist()

    def _parse_list_output(self, output):
        header_pattern = r"\s+Date\s+Time\s+Attr\s+Size\s+Compressed\s+Name\s+"
        body = re.split(header_pattern, output)[-1]
        file_names = []
        for line in body.split("\n")[1:]:
            if line.startswith("-----"):  # reach end
                break
            parts = re.split(r"\s", line.strip())
            file_name = parts[-1].strip()
            if path.basename(file_name) == file_name:  # root dir
                continue
            file_names.append(file_name)
        return file_names

    def namelist(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = path.join(tmp_dir, "archive.7z")
            with open(file_path, "wb") as f:
                f.write(self.data)
            cmd = "7z l " + file_path
            output, err, status = run_command(cmd)
            if status != 0:
                raise ValueError(err)
            file_names = self._parse_list_output(output)
        return file_names

    def read(self, name):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = path.join(tmp_dir, "archive.7z")
            with open(file_path, "wb") as f:
                f.write(self.data)
            cmd_lists = ["7z", "e", file_path, "-o" + tmp_dir, name]
            cmd = " ".join(cmd_lists)
            output, err, status = run_command(cmd)
            if status != 0:
                raise ValueError(err)
            sub_file_path = path.join(tmp_dir, path.basename(name))
            with open(sub_file_path, "rb") as f:
                sub_data = f.read()
        return sub_data
