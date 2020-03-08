# coding: utf-8

import unittest
from unittest import mock

from getsub.util import choose_archive, choose_subtitle


class TestChoose(unittest.TestCase):

    archive_dict = {
        "sub1": {"lan": 1, "link": "link", "session": None},
        "sub2": {"lan": 2, "link": "link", "session": None},
        "sub3": {"lan": 4, "link": "link", "session": None},
        "sub4": {"lan": 8, "link": "link", "session": None},
    }

    sublist = ["sub1", "sub2", "sub3", "sub4"]

    @mock.patch("builtins.input", return_value="0")
    def test_choose_archive_exit(self, mock_input):
        exit, choices = choose_archive(TestChoose.archive_dict)
        self.assertEqual((exit, choices), (True, []))

    @mock.patch("builtins.input", side_effect=["a", "b", "1"])
    def test_choose_archive_invalid_input(self, mock_input):
        exit, choices = choose_archive(TestChoose.archive_dict)
        self.assertEqual((exit, choices), (False, "sub1"))

    @mock.patch("builtins.input", side_effect=["2"])
    def test_choose_archive_valid_input(self, mock_input):
        exit, choices = choose_archive(TestChoose.archive_dict)
        self.assertEqual((exit, choices), (False, "sub2"))

    @mock.patch("builtins.input", side_effect=["5", "2"])
    def test_choose_archive_out_of_range_choice(self, mock_input):
        exit, choices = choose_archive(TestChoose.archive_dict)
        self.assertEqual(
            (exit, choices), (False, "sub2"),
        )

    @mock.patch("builtins.input", side_effect=["3", "2"])
    def test_choose_archive_sub_num(self, mock_input):
        exit, choices = choose_archive(TestChoose.archive_dict, sub_num=2)
        self.assertEqual(
            (exit, choices), (False, "sub2"),
        )

    @mock.patch("builtins.input", side_effect=["1"])
    def test_choose_archive_query_mode(self, mock_input):
        exit, choices = choose_archive(TestChoose.archive_dict, query=False)
        self.assertEqual((exit, choices), (False, "sub1"))

    @mock.patch("builtins.input", side_effect=["a", "1"])
    def test_choose_subtitle_input(self, mock_input):
        subname = choose_subtitle(TestChoose.sublist)
        self.assertEqual(subname, TestChoose.sublist[1])

    @mock.patch("builtins.input", side_effect=["5", "1"])
    def test_choose_subtitle_out_of_range_input(self, mock_input):
        subname = choose_subtitle(TestChoose.sublist)
        self.assertEqual(subname, TestChoose.sublist[1])


if __name__ == "__main__":
    unittest.main()
