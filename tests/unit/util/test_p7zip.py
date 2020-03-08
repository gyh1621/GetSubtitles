# coding: utf-8

import unittest
from os import path
from io import BytesIO

from getsub.util import P7ZIP
from tests.unit import assets_path


class TestP7ZIP(unittest.TestCase):
    def test_namelist(self):
        supposed_namelist = {
            path.join("archive", "dir1.zip"),
            path.join("archive", "dir3.7z"),
            path.join("archive", "sub4.sub"),
        }
        with open(path.join(assets_path, "archive.7z"), "rb") as f:
            data = f.read()
        file = BytesIO(data)
        p7zip = P7ZIP(file)
        namelist = p7zip.namelist()
        self.assertEqual(supposed_namelist, set(namelist))

    def test_read(self):
        with open(path.join(assets_path, "archive.7z"), "rb") as f:
            data = f.read()
        file = BytesIO(data)
        p7zip = P7ZIP(file)
        data = p7zip.read("archive/sub4.sub")
        self.assertEqual(data.decode().strip(), "sub")


if __name__ == "__main__":
    unittest.main()
