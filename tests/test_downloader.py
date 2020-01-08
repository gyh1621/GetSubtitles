# coding: utf-8

import os
import inspect
import importlib
import unittest
from getsub.downloader.downloader import Downloader


class TestDownloader(unittest.TestCase):

    def test_number_convert(self):
        """
        Test numbers converting to chinese.
        """
        self.assertEqual(Downloader.num_to_cn("1"), '一')
        self.assertEqual(Downloader.num_to_cn("10"), '十')
        self.assertEqual(Downloader.num_to_cn("12"), '十二')
        self.assertEqual(Downloader.num_to_cn("20"), '二十')
        self.assertEqual(Downloader.num_to_cn("22"), '二十二')

    def test_get_keywords(self):
        """
        Test video info extracting
        """

        names = (
            'Show.S01E01.ShowName.1080p.AMZN.WEB-DL.DDP5.1.H.264-GRP.mkv',
            'Hanzawa.Naoki.Ep10.Final.Chi_Jap.BDrip.1280X720-ZhuixinFan.mp4',
            'Homeland.S02E12.PROPER.720p.HDTV.x264-EVOLVE.mkv',
            'La.La.Land.2016.1080p.BluRay.x264.Atmos.TrueHD.7.1-HDChina.mkv'
        )
        results = (
            ['Show%20s01', 'e01', 'Web', 'GRP', 'amzn', '1080p'],
            ['Hanzawa%20Naoki', 'e10', 'Bluray', 'ZhuixinFan', '720p'],
            ['Homeland%20s02', 'e12', 'HDTV', 'EVOLVE', '720p'],
            ['La%20La%20Land', '2016', 'Bluray', 'HDChina', '1080p']
        )
        for n, r in zip(names, results):
            self.assertEqual(Downloader.get_keywords(n)[0], r)


class TestSubDownloaders(unittest.TestCase):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.subclasses = set()
        for file in os.listdir('getsub/downloader'):
            if not file.endswith('.py'):
                continue
            module = importlib.import_module(
                'getsub.downloader.'+file.split('.')[0])
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj != Downloader and issubclass(obj, Downloader):
                    self.subclasses.add(obj)

    def test_downloader(self):
        """
        Test all downloaders
        """

        def _check_format(result, dname):
            msg = dname + "'s 'get_subtitles' return wrong format"
            self.assertIsInstance(result, dict, msg=msg)
            for k, v in result.items():
                self.assertTrue('lan' in v, msg=msg)
                self.assertIsInstance(v['lan'], int, msg=msg)
                self.assertTrue('link' in v, msg=msg)
                self.assertTrue('session' in v, msg=msg)

        test_name = 'The.Flash.S01E01.mkv'

        for downloader in self.subclasses:

            dname = downloader.__name__

            # test basic attributes
            self.assertIsNotNone(
                getattr(downloader, 'name'),
                dname + ' has no attribute: name')
            self.assertIsNotNone(
                getattr(downloader, 'choice_prefix'),
                dname + ' has no attribute: choice_prefix')

            # test search
            result = downloader().get_subtitles(test_name, sub_num=2)
            self.assertEqual(len(result), 2, dname +
                             ' has wrong search result number')
            _check_format(result, dname)

            # test download
            link = list(result.values())[0]['link']
            data_type, sub_date_bytes, _ = downloader().download_file('', link)
            self.assertIsNotNone(sub_date_bytes, dname +
                                 ' fails downloading file')


if __name__ == '__main__':
    unittest.main()
