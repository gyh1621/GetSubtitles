import unittest
from getsub.downloader.zimuku import ZimukuDownloader


class TestZimuku(unittest.TestCase):
    def test_season_filter(self):
        video_name = "supernatural.s08.mkv"
        results = ZimukuDownloader().get_subtitles(video_name, sub_num=1)
        self.assertEqual(len(results), 1)

    def test_shooter_page(self):
        video_name = "supernatural.s08e10.mkv"
        ZimukuDownloader.search_url = ZimukuDownloader.site_url + "/search?t=onlyst&q="
        results = ZimukuDownloader().get_subtitles(video_name, sub_num=1)
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
