# coding: utf-8

import unittest
from os import path

import zipfile
import rarfile

from tests.unit import assets_path
from getsub.util import P7ZIP
from getsub.util import get_file_list


class TestGetFileList(unittest.TestCase):
    def test_zip_archive(self):
        with open(path.join(assets_path, "archive.zip"), "rb") as f:
            data = f.read()
        sub_lists = get_file_list(data, ".zip")
        result = {
            "archive/sub4.sub": zipfile.ZipFile,
            "dir1/sub1.ass": zipfile.ZipFile,
            "dir2/sub2.ass": zipfile.ZipFile,
            "dir3/sub.srt": zipfile.ZipFile,
            "dir3/dir4/sub.ass": zipfile.ZipFile,
        }
        for sub, handler in sub_lists.items():
            self.assertTrue(isinstance(handler, result[sub]))

    def test_rar_archive(self):
        with open(path.join(assets_path, "archive.rar"), "rb") as f:
            data = f.read()
        sub_lists = get_file_list(data, ".rar")
        result = {
            "dir3/sub.srt": rarfile.RarFile,
            "dir3/dir4/sub.ass": rarfile.RarFile,
            "archive/sub4.sub": rarfile.RarFile,
            "dir1/sub1.ass": zipfile.ZipFile,
            "dir2/sub2.ass": zipfile.ZipFile,
        }
        for sub, handler in sub_lists.items():
            self.assertTrue(isinstance(handler, result[sub]))

    def test_7z_archive(self):
        with open(path.join(assets_path, "archive.7z"), "rb") as f:
            data = f.read()
        sub_lists = get_file_list(data, ".7z")
        result = {
            "dir1/sub1.ass": zipfile.ZipFile,
            "dir2/sub2.ass": zipfile.ZipFile,
            path.join("dir3", "dir4", "sub.ass"): P7ZIP,
            path.join("dir3", "sub.srt"): P7ZIP,
            path.join("archive", "sub4.sub"): P7ZIP,
        }
        for sub, handler in sub_lists.items():
            self.assertTrue(isinstance(handler, result[sub]))


if __name__ == "__main__":
    unittest.main()
