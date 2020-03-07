# coding: utf-8

import unittest

from getsub.util import extract_name


class TestExtractName(unittest.TestCase):
    def test_all_en(self):
        name = "Young.Sheldon.S01.1080p.WEB-DL.DD5.1.H.264-YFN[v].rar"
        new_name = extract_name(name)
        self.assertEqual(new_name, name)

    def test_mixed(self):
        name = "[SPS辛普森一家字幕组].[丑陋的美国人.第一季].Ugly.Amricans.S01E01.rmvb"
        new_name = extract_name(name)
        self.assertEqual(new_name, "[SPS].[.].Ugly.Amricans.S01E01.rmvb")

    def test_most_en(self):
        name = "少年谢尔顿 第一季(第22集-简繁英双语字幕)Young.Sheldon.S01E22.720p.HDTV.rar"
        new_name = extract_name(name)
        self.assertEqual(new_name, "Young.Sheldon.S01E22.720p.HDTV.rar")

    def test_most_ch(self):
        name = "少年谢尔顿 第一季(第22集-简繁英双语字幕)Young.Sheldon.S01E22.720p.rar"
        new_name = extract_name(name)
        self.assertEqual(new_name, "少年谢尔顿 第一季(第22集-简繁英双语字幕).rar")

    def test_force_en(self):
        name = "少年谢尔顿 第一季(第22集-简繁英双语字幕)Young.Sheldon.S01E22.720p.rar"
        new_name = extract_name(name, en=True)
        self.assertEqual(new_name, "Young.Sheldon.S01E22.720p.rar")
