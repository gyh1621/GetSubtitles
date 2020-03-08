# coding: utf-8

import unittest
from getsub.models import Video
from getsub.util import num_to_cn
from getsub.downloader.downloader import Downloader


class TestDownloader(unittest.TestCase):
    def test_number_convert(self):
        """
        Test numbers converting to chinese.
        """
        self.assertEqual(num_to_cn("1"), "一")
        self.assertEqual(num_to_cn("10"), "十")
        self.assertEqual(num_to_cn("12"), "十二")
        self.assertEqual(num_to_cn("20"), "二十")
        self.assertEqual(num_to_cn("22"), "二十二")

    def test_get_keywords(self):
        """
        Test video info extracting
        """

        names = (
            "Show.S01E01.ShowName.1080p.AMZN.WEB-DL.DDP5.1.H.264-GRP.mkv",
            "Hanzawa.Naoki.Ep10.Final.Chi_Jap.BDrip.1280X720-ZhuixinFan.mp4",
            "Homeland.S02E12.PROPER.720p.HDTV.x264-EVOLVE.mkv",
            "La.La.Land.2016.1080p.BluRay.x264.Atmos.TrueHD.7.1-HDChina.mkv",
        )
        results = (
            ["Show", "s01", "e01", "Web", "GRP", "amzn", "1080p"],
            ["Hanzawa%20Naoki", "e10", "Bluray", "ZhuixinFan", "720p"],
            ["Homeland", "s02", "e12", "HDTV", "EVOLVE", "720p"],
            ["La%20La%20Land", "2016", "Bluray", "HDChina", "1080p"],
        )
        for n, r in zip(names, results):
            video = Video(n)
            self.assertEqual(Downloader.get_keywords(video), r)


if __name__ == "__main__":
    unittest.main()
