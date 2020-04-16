# coding: utf-8

from urllib.parse import urljoin
from contextlib import closing
from collections import OrderedDict

import re
import copy
import requests
from bs4 import BeautifulSoup
from guessit import guessit

from getsub.constants import SUB_FORMATS
from getsub.downloader.downloader import Downloader
from getsub.util import ProgressBar, extract_name, compute_subtitle_score, num_to_cn


""" Zimuku 字幕下载器
"""


class ZimukuDownloader(Downloader):

    name = "zimuku"
    choice_prefix = "[ZIMUKU]"
    site_url = "http://www.zimuku.la"
    search_url = "http://www.zimuku.la/search?q="

    def get_keywords(self, video):
        if video.info["type"] == "episode":
            keywords = [video.info["title"], "s%s" % str(video.info["season"]).zfill(2)]
            return keywords
        else:  # TODO: examine movies' search results
            return super().get_keywords(video)

    def _parse_episode_page(self, session, link, info, match_episode=True):
        """
        compute scores for each subtitle in the episode page
        params:
            session: request.Session
            link: str, episode page link
            info: dict, result of guessit
        return:
            subs: OrderedDict, format same as get_subtitles
                  sorted in ascending order of scores
        """

        def _get_archive_dowload_link(sub_page_link):
            r = session.get(sub_page_link)
            bs_obj = BeautifulSoup(r.text, "html.parser")
            down_page_link = bs_obj.find("a", {"id": "down1"}).attrs["href"]
            down_page_link = urljoin(ZimukuDownloader.site_url, down_page_link)
            r = session.get(down_page_link)
            bs_obj = BeautifulSoup(r.text, "html.parser")
            download_link = bs_obj.find("a", {"rel": "nofollow"})
            download_link = download_link.attrs["href"]
            download_link = urljoin(ZimukuDownloader.site_url, download_link)
            return download_link

        r = session.get(link)
        bs_obj = BeautifulSoup(r.text, "html.parser")
        subs_body = bs_obj.find("div", class_="subs box clearfix").find("tbody")
        subs = dict()
        for sub in subs_body.find_all("tr"):
            a = sub.find("a")
            name = extract_name(a.text, en=True)

            score = compute_subtitle_score(info, name, match_episode=match_episode)
            if score == -1:
                continue
            type_score = 0
            for img in sub.find("td", class_="tac lang").find_all("img"):
                if "uk" in img.attrs["src"]:
                    type_score += 1
                elif "hongkong" in img.attrs["src"]:
                    type_score += 2
                elif "china" in img.attrs["src"]:
                    type_score += 4
                elif "jollyroger" in img.attrs["src"]:
                    type_score += 8

            sub_page_link = urljoin(ZimukuDownloader.site_url, a.attrs["href"])
            download_link = _get_archive_dowload_link(sub_page_link)

            backup_session = copy.deepcopy(session)
            backup_session.headers["Referer"] = link

            # TODO: consider download times when computing scores
            subs[ZimukuDownloader.choice_prefix + name] = {
                "link": download_link,
                "lan": type_score,
                "session": backup_session,
                "score": score,
            }

        return subs

    def _parse_shooter_episode_page(self, session, title, link):
        sub = dict()
        r = session.get(link)
        bs_obj = BeautifulSoup(r.text, "html.parser")
        lang_box = bs_obj.find("ul", {"class": "subinfo"}).find("li")
        type_score = 0
        text = lang_box.text
        if "英" in text:
            type_score += 1
        elif "繁" in text:
            type_score += 2
        elif "简" in text:
            type_score += 4
        elif "双语" in text:
            type_score += 8
        download_link = bs_obj.find("a", {"id": "down1"}).attrs["href"]
        backup_session = copy.deepcopy(session)
        backup_session.headers["Referer"] = link
        sub[ZimukuDownloader.choice_prefix + title] = {
            "lan": type_score,
            "link": download_link,
            "session": backup_session,
        }
        return sub

    def get_subtitles(self, video, sub_num=10):

        print("Searching ZIMUKU...", end="\r")

        keywords = self.get_keywords(video)
        info_dict = video.info

        s = requests.session()
        s.headers.update(Downloader.header)

        sub_dict = dict()
        for i in range(len(keywords), 1, -1):
            keyword = ".".join(keywords[:i])
            r = s.get(ZimukuDownloader.search_url + keyword, timeout=10)
            html = r.text

            if "搜索不到相关字幕" in html:
                continue

            bs_obj = BeautifulSoup(r.text, "html.parser")

            # 综合搜索页面
            if bs_obj.find("div", {"class": "item"}):
                for item in bs_obj.find_all("div", {"class": "item"}):
                    title_a = item.find("p", class_="tt clearfix").find("a")
                    if info_dict["type"] == "episode":
                        title = title_a.text
                        try:
                            season_cn1 = re.search("第(.*)季", title).group(1).strip()
                        except AttributeError:
                            # try getting season from subtitles
                            sample_title = (
                                item.find("td", class_="first").find("a").get("title")
                            )
                            sample_dict = guessit(extract_name(sample_title, en=True))
                            season_cn1 = num_to_cn(str(sample_dict["season"]))
                        season_cn2 = num_to_cn(str(info_dict["season"]))
                        if season_cn1 != season_cn2:
                            continue
                    episode_link = ZimukuDownloader.site_url + title_a.attrs["href"]
                    new_subs = self._parse_episode_page(s, episode_link, info_dict)
                    if not new_subs:
                        new_subs = self._parse_episode_page(
                            s, episode_link, info_dict, match_episode=False
                        )
                    sub_dict.update(new_subs)

            # 射手字幕页面
            elif bs_obj.find("div", {"class": "persub"}):
                for persub in bs_obj.find_all("div", {"class": "persub"}):
                    title = persub.h1.text.split("/")[-1]
                    # NOTE: this will filter out all subtitle packages
                    score = compute_subtitle_score(info_dict, title)
                    if score == -1:
                        continue
                    link = ZimukuDownloader.site_url + persub.h1.a.attrs["href"]
                    sub = self._parse_shooter_episode_page(s, title, link)
                    sub[list(sub.keys())[0]]["score"] = score
                    sub_dict.update(sub)

            else:
                raise ValueError("zimuku downloader needs updates")

            if len(sub_dict) >= sub_num:
                del keywords[:]
                break

        sub_dict = OrderedDict(
            sorted(sub_dict.items(), key=lambda e: e[1]["score"], reverse=True)
        )
        keys = list(sub_dict.keys())[:sub_num]
        return {key: sub_dict[key] for key in keys}

    def download_file(self, file_name, download_link, session=None):

        try:
            if not session:
                session = requests.session()
            with closing(session.get(download_link, stream=True)) as response:
                filename = response.headers["Content-Disposition"]
                chunk_size = 1024  # 单次请求最大值
                # 内容体总大小
                content_size = int(response.headers["content-length"])
                bar = ProgressBar("Get", file_name.strip(), content_size)
                sub_data_bytes = b""
                for data in response.iter_content(chunk_size=chunk_size):
                    sub_data_bytes += data
                    bar.refresh(len(sub_data_bytes))
        except requests.Timeout:
            return None, None, "false"
        if ".rar" in filename:
            datatype = ".rar"
        elif ".zip" in filename:
            datatype = ".zip"
        elif ".7z" in filename:
            datatype = ".7z"
        else:
            datatype = "Unknown"
            for sub_type in SUB_FORMATS:
                if sub_type in filename:
                    datatype = sub_type
                    break

        return datatype, sub_data_bytes, ""
