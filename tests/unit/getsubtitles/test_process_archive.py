# coding: utf-8

import os
from os import path
import copy
import shutil
import unittest
from unittest import mock

import rarfile

from tests import create_test_directory
from tests.unit import assets_path
from tests.unit.getsubtitles import get_function as get_f
from getsub.models import Video


def get_function(**kwargs):
    return get_f("process_archive", **kwargs)


class TestProcessArchive(unittest.TestCase):

    test_dir = "testPA"
    test_video = Video(path.join(test_dir, "video.mkv"), test_dir)
    test_dir_structure = {}

    def tearDown(self):
        if path.exists(TestProcessArchive.test_dir):
            shutil.rmtree(TestProcessArchive.test_dir)

    def test_unsupported_archive(self):
        process_archive = get_function()
        err, subnames = process_archive(TestProcessArchive.test_video, b"", ".tar")
        self.assertEqual((err, subnames), ("unsupported file type .tar", []))

    def test_invalid_archive(self):
        process_archive = get_function()
        self.assertRaises(
            rarfile.BadRarFile,
            process_archive,
            TestProcessArchive.test_video,
            b"",
            ".7z",
        )

    def test_empty_archive(self):
        with open(path.join(assets_path, "empty.zip"), "rb") as f:
            data = f.read()
        process_archive = get_function()
        err, subnames = process_archive(TestProcessArchive.test_video, data, ".zip")
        self.assertEqual((err, subnames), ("no subtitle in this archive", []))

    def test_fail_guess(self):
        with open(path.join(assets_path, "archive.zip"), "rb") as f:
            data = f.read()
        process_archive = get_function()
        err, subnames = process_archive(TestProcessArchive.test_video, data, ".zip")
        self.assertEqual((err, subnames), ("no guess result in auto mode", []))

    @mock.patch("builtins.input", side_effect=["1"])
    def test_choose_subtitle(self, mock_input):
        create_test_directory(
            TestProcessArchive.test_dir_structure,
            parent_dir=TestProcessArchive.test_dir,
        )
        with open(path.join(assets_path, "archive.zip"), "rb") as f:
            data = f.read()
        test_video = Video(path.join(TestProcessArchive.test_dir, "sub1.mkv"))
        process_archive = get_function(single=True)
        err, subnames = process_archive(test_video, data, ".zip")
        self.assertEqual((err, subnames), ("", [["dir1/sub1.ass", ".ass"]]))

    def test_save_both_subtitles_success(self):
        create_test_directory(
            TestProcessArchive.test_dir_structure,
            parent_dir=TestProcessArchive.test_dir,
        )
        with open(path.join(assets_path, "archive.zip"), "rb") as f:
            data = f.read()
        test_video = Video(path.join(TestProcessArchive.test_dir, "sub.mkv"))
        process_archive = get_function(both=True)
        err, subnames = process_archive(test_video, data, ".zip")
        self.assertTrue(
            "sub.ass" in os.listdir(TestProcessArchive.test_dir)
            and "sub.srt" in os.listdir(TestProcessArchive.test_dir)
        )

    def test_save_both_subtitles_fail(self):
        create_test_directory(
            TestProcessArchive.test_dir_structure,
            parent_dir=TestProcessArchive.test_dir,
        )
        with open(path.join(assets_path, "archive.zip"), "rb") as f:
            data = f.read()
        process_archive = get_function(both=True)
        test_video = Video(path.join(TestProcessArchive.test_dir, "sub1.mkv"))
        err, subnames = process_archive(test_video, data, ".zip")
        self.assertTrue(
            "sub1.ass" in os.listdir(TestProcessArchive.test_dir)
            and "sub1.srt" not in os.listdir(TestProcessArchive.test_dir)
        )

    def test_delete_existed_subtitles(self):
        dir_structure = copy.copy(TestProcessArchive.test_dir_structure)
        dir_structure["sub1.ass"] = None
        dir_structure["sub1.srt"] = None
        create_test_directory(
            dir_structure, parent_dir=TestProcessArchive.test_dir,
        )
        with open(path.join(assets_path, "archive.zip"), "rb") as f:
            data = f.read()
        process_archive = get_function(both=True)
        test_video = Video(path.join(TestProcessArchive.test_dir, "sub1.mkv"))
        err, subnames = process_archive(test_video, data, ".zip")
        self.assertTrue(
            "sub1.ass" in os.listdir(TestProcessArchive.test_dir)
            and "sub1.srt" not in os.listdir(TestProcessArchive.test_dir)
        )

    def test_identifier(self):
        dir_structure = copy.copy(TestProcessArchive.test_dir_structure)
        dir_structure["sub1.ass"] = None
        dir_structure["sub1.zh.srt"] = None
        create_test_directory(
            dir_structure, parent_dir=TestProcessArchive.test_dir,
        )
        with open(path.join(assets_path, "archive.zip"), "rb") as f:
            data = f.read()
        process_archive = get_function()
        test_video = Video(
            path.join(TestProcessArchive.test_dir, "sub1.mkv"), identifier=".zh"
        )
        err, subnames = process_archive(test_video, data, ".zip")
        self.assertTrue(
            "sub1.ass" in os.listdir(TestProcessArchive.test_dir)
            and "sub1.zh.ass" in os.listdir(TestProcessArchive.test_dir)
            and "sub1.zh.srt" not in os.listdir(TestProcessArchive.test_dir)
        )


if __name__ == "__main__":
    unittest.main()
