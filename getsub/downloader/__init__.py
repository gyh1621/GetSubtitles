# coding: utf-8

import os
import importlib
from os import path
from abc import ABCMeta, abstractmethod

from getsub.constants import SERVICE_SHORT_NAMES

from requests.utils import quote


downloaders = {}


class DownloaderMeta(ABCMeta):
    def __new__(cls, name, bases, attrs):
        newclass = super().__new__(cls, name, bases, attrs)
        if name == "Downloader":
            return newclass
        if not hasattr(newclass, "name"):
            raise NotImplementedError(
                "Static variable '{}' is not declared in class: {}".format("name", name)
            )
        if not hasattr(newclass, "choice_prefix"):
            raise NotImplementedError(
                "Static variable '{}' is not declared in class: {}".format(
                    "choice_prefix", name
                )
            )
        downloaders[newclass.name] = newclass()
        return newclass


class Downloader(metaclass=DownloaderMeta):

    header = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) "
        "AppleWebKit 537.36 (KHTML, like Gecko) Chrome",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/webp,*/*;q=0.8",
    }

    @staticmethod
    def get_downloaders():
        return downloaders.values()

    @staticmethod
    def get_downloader_names():
        return downloaders.keys()

    @staticmethod
    def get_downloader_by_name(name):
        return downloaders.get(name)

    @staticmethod
    def get_downloader_by_choice_prefix(choice_prefix):
        for downloader in downloaders.values():
            if downloader.__class__.choice_prefix == choice_prefix:
                return downloader
        return None

    @staticmethod
    def get_keywords(video):

        """ get video's information
        Args:
            video: Video object
        Return:
            keywords: list
        """

        keywords = []

        info_dict = video.info
        title = info_dict["title"]
        keywords.append(title)

        if info_dict.get("season"):
            keywords.append("s%s" % str(info_dict["season"]).zfill(2))

        # add year infomation if it's a movie
        if info_dict.get("year") and info_dict.get("type") == "movie":
            keywords.append(str(info_dict["year"]))

        if info_dict.get("episode"):
            keywords.append("e%s" % str(info_dict["episode"]).zfill(2))
        if info_dict.get("source"):
            keywords.append(info_dict["source"].replace("-", ""))
        if info_dict.get("release_group"):
            keywords.append(info_dict["release_group"])
        if info_dict.get("streaming_service"):
            service_name = info_dict["streaming_service"]
            short_names = SERVICE_SHORT_NAMES.get(service_name.lower())
            if short_names:
                keywords.append(short_names)
        if info_dict.get("screen_size"):
            keywords.append(str(info_dict["screen_size"]))

        # url encoded
        keywords = [quote(_keyword) for _keyword in keywords]
        return keywords

    @abstractmethod
    def get_subtitles(self, video, sub_num=5):

        """ search subtitles and return a result dict
        every subtitle contains a language score:
            English, add 1; Traditional Chinese, add 2;
            Simplified Chinese, add 4; Double languages, add 8;
        Args:
            video：Video object
            sub_num: number of subtitles, default is 5
        Return：
            subtitle dict, in desending order of language scores
            example:
                {
                    <subtitle name, str>: {
                        "lan": <language score, int>,
                        "link": <subtitle link, str>,
                        "session": <request session>
                    }
                }
        """
        pass

    @abstractmethod
    def download_file(self, file_name, sub_url, session=None):

        """ download subtitle
        Args:
            file_name: subtitle name
            sub_url: download link，from result of 'get_subtitles'
            session: request session
        Return:
            data_type: str, file type, e.g., ".rar", ".zip", ".7z"
            sub_data_bytes: bytes, file bytes
            err_msg: str, error message
        """
        pass


# find all downloader module
for file in os.listdir(path.dirname(__file__)):
    if not file.endswith(".py") or file == "__init__.py":
        continue
    importlib.import_module("getsub.downloader." + file.split(".")[0])
