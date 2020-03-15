import os
import copy
import shutil
import unittest
from os import path
from unittest import mock

from tests import create_test_directory
from getsub.main import GetSubtitles
from getsub.constants import SUB_FORMATS


class TestMain(unittest.TestCase):

    test_dir = "TESTMAIN"
    args = dict(
        name="",
        query=False,
        single=False,
        more=False,
        both=False,
        over=False,
        plex=False,
        debug=False,
        sub_num=None,
        downloader=None,
        sub_path="",
    )

    @classmethod
    def build_args(cls, args):
        new_args = copy.copy(TestMain.args)
        new_args.update(args)
        return new_args

    def tearDown(self):
        if path.exists(TestMain.test_dir):
            shutil.rmtree(TestMain.test_dir)

    def test_override_subtitles(self):
        """
        1. test not override existed subtitles
        2. test override existed subtitles
        3. test 1 and 2 with '--plex'
        """

        print("===========================================")
        print("=== Test not override existed subtitles ===")
        print("===========================================")
        dir_structure = {
            "the.flash.s01e01.mkv": None,
            "the.flash.s01e01.ass": None,
            "the.flash.s01e01.zh.ass": None,
        }
        create_test_directory(dir_structure, TestMain.test_dir)
        args = TestMain.build_args({"name": TestMain.test_dir})
        result = GetSubtitles(**args).start()
        self.assertEqual(result["success"], 1)
        statinfo = os.stat(path.join(TestMain.test_dir, "the.flash.s01e01.ass"))
        self.assertEqual(statinfo.st_size, 0)

        print("=======================================")
        print("=== Test override existed subtitles ===")
        print("=======================================")
        args = TestMain.build_args({"name": TestMain.test_dir, "over": True})
        result = GetSubtitles(**args).start()
        self.assertEqual(result["success"], 1)
        statinfo = os.stat(path.join(TestMain.test_dir, "the.flash.s01e01.ass"))
        self.assertNotEqual(statinfo.st_size, 0)
        statinfo = os.stat(path.join(TestMain.test_dir, "the.flash.s01e01.zh.ass"))
        self.assertEqual(statinfo.st_size, 0)
        shutil.rmtree(TestMain.test_dir)

        print("======================================================")
        print("=== Test not override existed subtitles (with .zh) ===")
        print("======================================================")
        dir_structure = {
            "the.flash.s01e01.mkv": None,
            "the.flash.s01e01.zh.ass": None,
        }
        create_test_directory(dir_structure, TestMain.test_dir)
        args = TestMain.build_args({"name": TestMain.test_dir, "plex": True})
        result = GetSubtitles(**args).start()
        self.assertEqual(result["success"], 1)
        statinfo = os.stat(path.join(TestMain.test_dir, "the.flash.s01e01.zh.ass"))
        self.assertEqual(statinfo.st_size, 0)

        print("=====================================================")
        print("=== Test not override existed subtitles (with .zh)===")
        print("=====================================================")
        args = TestMain.build_args(
            {"name": TestMain.test_dir, "plex": True, "over": True}
        )
        result = GetSubtitles(**args).start()
        self.assertEqual(result["success"], 1)
        statinfo = os.stat(path.join(TestMain.test_dir, "the.flash.s01e01.zh.ass"))
        self.assertNotEqual(statinfo.st_size, 0)
        shutil.rmtree(TestMain.test_dir)

    def test_directory(self):
        """
        1. test -p
        """

        print("===============================")
        print("=== Test external directory ===")
        print("===============================")
        dir_structure = {
            "the.flash.s01e01.mkv": None,
            "the.flash.s01e01.ass": None,
            "subdir": [],
        }
        create_test_directory(dir_structure, TestMain.test_dir)
        args = TestMain.build_args(
            {
                "name": TestMain.test_dir,
                "sub_path": path.join(TestMain.test_dir, "subdir"),
            }
        )
        result = GetSubtitles(**args).start()
        self.assertEqual(result["success"], 1)
        statinfo = os.stat(path.join(TestMain.test_dir, "the.flash.s01e01.ass"))
        self.assertEqual(statinfo.st_size, 0)
        statinfo = os.stat(
            path.join(TestMain.test_dir, "subdir", "the.flash.s01e01.ass")
        )
        self.assertNotEqual(statinfo.st_size, 0)
        shutil.rmtree(TestMain.test_dir)

        dir_structure = {
            "the.flash.s01e01.mkv": None,
            "subdir": ["the.flash.s01e01.ass"],
        }
        create_test_directory(dir_structure, TestMain.test_dir)
        args = TestMain.build_args(
            {
                "name": TestMain.test_dir,
                "sub_path": path.join(TestMain.test_dir, "subdir"),
            }
        )
        result = GetSubtitles(**args).start()
        self.assertEqual(result["success"], 1)
        statinfo = os.stat(
            path.join(TestMain.test_dir, "subdir", "the.flash.s01e01.ass")
        )
        self.assertEqual(statinfo.st_size, 0)
        shutil.rmtree(TestMain.test_dir)

    def test_assign_downloader(self):
        print("=================================")
        print("=== Test unexisted downloader ===")
        print("=================================")
        dir_structure = {
            "the.expanse.s01e01.mkv": None,
        }
        create_test_directory(dir_structure, TestMain.test_dir)
        args = TestMain.build_args(
            {"name": TestMain.test_dir, "downloader": "unexisted_downloader"}
        )
        with self.assertRaises(SystemExit) as cm:
            GetSubtitles(**args).start()
        self.assertEqual(cm.exception.code, 1)

        print("===============================")
        print("=== Test existed downloader ===")
        print("===============================")
        args = TestMain.build_args({"name": TestMain.test_dir, "downloader": "zimuku"})
        result = GetSubtitles(**args).start()
        self.assertEqual(result["success"], 1)
        self.assertTrue(
            path.exists(path.join(TestMain.test_dir, "the.expanse.s01e01.ass"))
        )

    def test_save_archive(self):
        print("============================")
        print("=== Test save the archive===")
        print("============================")
        dir_structure = {
            "the.flash.s01e01.mkv": None,
        }
        create_test_directory(dir_structure, TestMain.test_dir)
        args = TestMain.build_args(
            {"name": TestMain.test_dir, "more": True, "downloader": "zimuzu"}
        )
        result = GetSubtitles(**args).start()
        self.assertTrue(result["success"], 1)
        files = os.listdir(TestMain.test_dir)
        types = set([path.splitext(file)[1] for file in files])
        self.assertTrue(".rar" in types or ".zip" in types or ".7z" in types)

    @mock.patch("getsub.constants.ARCHIVE_TYPES", [])
    def test_download_subtitles(self):
        print("===============================")
        print("=== Test download subtitles ===")
        print("===============================")
        # zimuku should have subtitle results for this video
        video_name, video_type = (
            "Young.Sheldon.S03E15.1080p.WEB.x264-XLF[rarbg]",
            ".mkv",
        )
        dir_structure = {video_name + video_type: None}
        create_test_directory(dir_structure, TestMain.test_dir)
        args = TestMain.build_args({"name": TestMain.test_dir, "downloader": "zimuku"})
        result = GetSubtitles(**args).start()
        self.assertTrue(result["success"], 1)
        files = os.listdir(TestMain.test_dir)
        possible_subs = [video_name + sub_type for sub_type in SUB_FORMATS]
        self.assertTrue(set(files).intersection(possible_subs))


if __name__ == "__main__":
    unittest.main()
