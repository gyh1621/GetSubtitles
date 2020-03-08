# coding: utf-8

import os
import inspect
import importlib
import unittest

from getsub.models import Video
from getsub.downloader.downloader import Downloader


class TestSubDownloaders(unittest.TestCase):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.subclasses = set()
        for file in os.listdir("getsub/downloader"):
            if not file.endswith(".py"):
                continue
            module = importlib.import_module("getsub.downloader." + file.split(".")[0])
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj != Downloader and issubclass(obj, Downloader):
                    self.subclasses.add(obj)

    def test_downloader(self):
        """
        Test all downloaders
        """

        def _check_format(result, dname):
            msg = dname + "'s 'get_subtitles' return wrong format"
            self.assertIsInstance(result, dict, msg=msg)
            for k, v in result.items():
                self.assertTrue("lan" in v, msg=msg)
                self.assertIsInstance(v["lan"], int, msg=msg)
                self.assertTrue("link" in v, msg=msg)
                self.assertTrue("session" in v, msg=msg)

        test_name = "The.Flash.S01E01.mkv"

        for downloader in self.subclasses:

            dname = downloader.__name__

            # test basic attributes
            self.assertIsNotNone(
                getattr(downloader, "name"), dname + " has no attribute: name"
            )
            self.assertIsNotNone(
                getattr(downloader, "choice_prefix"),
                dname + " has no attribute: choice_prefix",
            )

            # test search
            video = Video(test_name)
            result = downloader().get_subtitles(video, sub_num=2)
            self.assertEqual(len(result), 2, dname + " has wrong search result number")
            _check_format(result, dname)

            # test download
            sub_info = list(result.values())[0]
            link = sub_info["link"]
            session = sub_info["session"]
            data_type, sub_date_bytes, _ = downloader().download_file(
                "", link, session=session
            )
            self.assertIsNotNone(sub_date_bytes, dname + " fails downloading file")


if __name__ == "__main__":
    unittest.main()
