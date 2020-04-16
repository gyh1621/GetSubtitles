# coding: utf-8

import unittest
from getsub.models import Video
from getsub.downloader.zimuku import ZimukuDownloader


class TestZimuku(unittest.TestCase):
    def test_season_filter(self):
        video_name = "supernatural.s08.mkv"
        video = Video(video_name)
        results = ZimukuDownloader().get_subtitles(video, sub_num=1)
        self.assertEqual(len(results), 1)

    def test_shooter_page(self):
        video_name = "supernatural.s08e10.mkv"
        ZimukuDownloader.search_url = ZimukuDownloader.site_url + "/search?t=onlyst&q="
        video = Video(video_name)
        results = ZimukuDownloader().get_subtitles(video, sub_num=1)
        self.assertEqual(len(results), 1)

    def test_get_season_from_subtitle(self):
        # from issue #68 and pr #66
        video_name = "The.Morning.Show.S01E01.mkv"
        video = Video(video_name)
        results = ZimukuDownloader().get_subtitles(video, sub_num=1)
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
