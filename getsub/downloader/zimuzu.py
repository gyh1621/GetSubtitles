# coding: utf-8

from collections import OrderedDict as order_dict
from contextlib import closing
import json

import requests
from bs4 import BeautifulSoup

from getsub.downloader.downloader import Downloader
from getsub.util import ProgressBar


""" Zimuzu 字幕下载器
"""


class ZimuzuDownloader(Downloader):

    name = "zimuzu"
    choice_prefix = "[ZIMUZU]"
    site_url = "http://www.rrys2019.com"
    search_url = "http://www.rrys2019.com/search?keyword={0}&type=subtitle"

    def get_subtitles(self, video, sub_num=5):

        print("Searching ZIMUZU...", end="\r")

        keywords = Downloader.get_keywords(video)
        keyword = " ".join(keywords)

        sub_dict = order_dict()
        s = requests.session()
        while True:
            # 当前关键字查询
            r = s.get(
                ZimuzuDownloader.search_url.format(keyword),
                headers=Downloader.header,
                timeout=10,
            )
            bs_obj = BeautifulSoup(r.text, "html.parser")
            tab_text = bs_obj.find("div", {"class": "article-tab"}).text
            if "字幕(0)" not in tab_text:
                for one_box in bs_obj.find_all("div", {"class": "search-item"}):
                    sub_name = (
                        ZimuzuDownloader.choice_prefix
                        + one_box.find("strong", {"class": "list_title"}).text
                    )

                    if video.info["type"] == "movie" and "美剧字幕" in sub_name:
                        continue

                    a = one_box.find("a")
                    text = a.text
                    sub_url = ZimuzuDownloader.site_url + a.attrs["href"]
                    type_score = 0
                    type_score += ("英文" in text) * 1
                    type_score += ("繁体" in text) * 2
                    type_score += ("简体" in text) * 4
                    type_score += ("中英" in text) * 8
                    sub_dict[sub_name] = {
                        "lan": type_score,
                        "link": sub_url,
                        "session": None,
                    }
                    if len(sub_dict) >= sub_num:
                        del keywords[:]  # 字幕条数达到上限，清空keywords
                        break

            if len(keywords) > 1:  # 字幕数未满，更换关键词继续查询
                keyword = keyword.replace(keywords[-1], "")
                keywords.pop(-1)
                continue

            break

        # 第一个候选字幕没有双语
        if len(sub_dict.items()) > 0 and list(sub_dict.items())[0][1]["lan"] < 8:
            sub_dict = order_dict(
                sorted(sub_dict.items(), key=lambda e: e[1]["lan"], reverse=True)
            )
        return sub_dict

    def download_file(self, file_name, sub_url, session=None):

        s = requests.session()
        header = Downloader.header.copy()
        r = s.get(sub_url, headers=Downloader.header)
        bs_obj = BeautifulSoup(r.text, "html.parser")
        a = bs_obj.find("div", {"class": "subtitle-links"}).a
        download_link = a.attrs["href"]
        header["Referer"] = download_link
        ajax_url = "http://got001.com/api/v1/static/subtitle/detail?"
        ajax_url += download_link.split("?")[-1]
        r = s.get(ajax_url, headers=header)
        json_obj = json.loads(r.text)
        download_link = json_obj["data"]["info"]["file"]

        try:
            with closing(requests.get(download_link, stream=True)) as response:
                chunk_size = 1024  # 单次请求最大值
                if response.headers.get("content-length"):
                    # 内容体总大小
                    content_size = int(response.headers["content-length"])
                    bar = ProgressBar("Get", file_name.strip(), content_size)
                    sub_data_bytes = b""
                    for data in response.iter_content(chunk_size=chunk_size):
                        sub_data_bytes += data
                        bar.refresh(len(sub_data_bytes))
                else:
                    bar = ProgressBar("Get", file_name.strip())
                    sub_data_bytes = b""
                    for data in response.iter_content(chunk_size=chunk_size):
                        sub_data_bytes += data
                        bar.point_wait()
                    bar.point_wait(end=True)
            # sub_data_bytes = requests.get(download_link, timeout=10).content
        except requests.Timeout:
            return None, None
        if "rar" in download_link:
            datatype = ".rar"
        elif "zip" in download_link:
            datatype = ".zip"
        elif "7z" in download_link:
            datatype = ".7z"
        else:
            if ".rar" in file_name:
                datatype = ".rar"
            elif ".zip" in file_name:
                datatype = ".zip"
            elif ".7z" in file_name:
                datatype = ".7z"
            else:
                datatype = "Unknown"

        return datatype, sub_data_bytes, ""
