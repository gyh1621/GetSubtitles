# coding: utf-8

import unittest

from getsub.util import extract_name


class TestExtractName(unittest.TestCase):
    def test_all_en(self):
        name = "Young.Sheldon.S01.1080p.WEB-DL.DD5.1.H.264-YFN[v].rar"
        new_name = extract_name(name)
        self.assertEqual(new_name, name)

    def test_mixed(self):
        name1 = "[SPS辛普森一家字幕组].[丑陋的美国人.第一季].Ugly.Americans.S01E01.rmvb"
        name2 = (
            "行尸走肉 第10季第15集【本季终】.The.Walking.Dead.[WEB.1080P]中英文字幕【YYeTs字幕组 简繁英双语字幕】"
            "The.Walking.Dead.S10E15.The.Tower.720p/1080p.AMZN.WEB-DL.DD+5.1.H.264-CasStudio"
        )
        result = (extract_name(name1), extract_name(name2))
        self.assertEqual(
            result,
            (
                "Ugly.Americans.S01E01.rmvb",
                "The.Walking.Dead.S10E15.The.Tower.720p/1080p.AMZN.WEB-DL.DD+5.1.H.264-CasStudio",
            ),
        )

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
