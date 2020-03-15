# coding: utf-8

import os
from os.path import basename, dirname, abspath
from os.path import exists, join, splitext

from guessit import guessit

from getsub.util import extract_name
from getsub.constants import SUB_FORMATS


class Video:
    @classmethod
    def sub_exists(cls, video_name, store_path, identifier):
        sub_types = [identifier + sub_type for sub_type in SUB_FORMATS]
        for sub_type in sub_types:
            if exists(join(store_path, video_name + sub_type)):
                return True
        return False

    def __init__(self, video_path, sub_store_path="", identifier=""):
        self.name, self.type = splitext(basename(video_path))
        self.path = abspath(dirname(video_path))
        self.sub_store_path = abspath(sub_store_path) if sub_store_path else self.path
        self.sub_identifier = identifier
        self.has_subtitle = Video.sub_exists(
            self.name, self.sub_store_path, self.sub_identifier
        )
        self.extracted_name = extract_name(self.name)
        self.info = guessit(self.extracted_name + self.type)

    def delete_existed_subtitles(self):
        if not self.has_subtitle:
            return
        for one_sub_type in SUB_FORMATS:
            delete_name = self.name + self.sub_identifier + one_sub_type
            delete_file = join(self.sub_store_path, delete_name)

            if exists(delete_file):
                os.remove(delete_file)
