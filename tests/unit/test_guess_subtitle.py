# coding: utf-8

import unittest

from getsub.util import guess_subtitle, compute_subtitle_score


class TestGuessSubtitle(unittest.TestCase):

    test_episode_info = {
        "title": "the walking dead",
        "season": 10,
        "episode": 1,
        "type": "episode",
    }
    test_episode_subs = (
        ("the.walking.dead.s10e01.web.h264-tbs.chs.eng.简体.ass", 7),
        ("the.walking.dead.s10e01.web.h264-tbs.chs.eng.简体&英文.srt", 10),
        ("the.walking.dead.s10e01.web.h264-tbs.chs.eng.简体&英文.ass", 11),
        ("the.walking.dead.s10e01.web.h264-tbs.cht.ass", 3),
        ("the.walking.dead.s10e01.web.h264-tbs.chs.srt", 4),
        ("s10e01.srt", 1),
        ("the.walking.dead.s10e02.web.h264-tbs.chs.srt", -1),
        ("the.flash.s10e01.web.h264-tbs.chs.srt", -1),
        ("the.flash.s01e01.web.h264-tbs.chs.srt", -1),
    )
    test_episode_package = (("the.walking.dead.S10.1080p.BluRay.x265.zip", 1),)

    test_movie_info = {"title": "Pulp Fiction", "year": 1994, "type": "movie"}
    test_movie_subs = (
        ("Pulp.Fiction.1994.BluRay.720p.x264.DTS-WiKi.eng.srt", 3),
        ("Pulp.Fiction.1994.RERiP.1080p.BluRay.x264.DTS-WiKi.chs&eng.srt", 7),
        ("Pulp.Fiction.RERiP.1080p.BluRay.x264.DTS-WiKi.chs&eng.srt", 6),
        ("Frozen.chs.srt", -1),
    )

    test_archive_list1 = [
        "Pulp.Fiction.1994/",
        "Pulp.Fiction.1994/Pulp.Fiction.1994.BluRay.720p.x264.DTS-WiKi.eng.srt",
        "Pulp.Fiction.1994.BluRay.x264.DTS-WiKi.chs&eng.srt",
    ]
    test_archive_result1 = (
        True,
        "Pulp.Fiction.1994.BluRay.x264.DTS-WiKi.chs&eng.srt",
    )

    test_archive_list2 = ["Frozen.chs.srt"]
    test_archive_result2 = (False, "Frozen.chs.srt")

    def test_compute_subtitle_score(self):
        for test_sub, score in TestGuessSubtitle.test_episode_subs:
            self.assertEqual(
                compute_subtitle_score(TestGuessSubtitle.test_episode_info, test_sub),
                score,
            )
        for test_sub, score in TestGuessSubtitle.test_movie_subs:
            self.assertEqual(
                compute_subtitle_score(TestGuessSubtitle.test_movie_info, test_sub),
                score,
            )

    def test_compute_subtitle_score_not_match_episode(self):
        for test_package, score in TestGuessSubtitle.test_episode_package:
            self.assertEqual(
                compute_subtitle_score(
                    TestGuessSubtitle.test_episode_info,
                    test_package,
                    match_episode=False,
                ),
                score,
            )

    def test_guess_with_empty_list(self):
        success, subname = guess_subtitle([], {})
        self.assertEqual((success, subname), (False, None))

    def test_guess_with_success(self):
        success, subname = guess_subtitle(
            TestGuessSubtitle.test_archive_list1, TestGuessSubtitle.test_movie_info,
        )
        self.assertEqual((success, subname), TestGuessSubtitle.test_archive_result1)

    def test_guess_with_fail(self):
        success, subname = guess_subtitle(
            TestGuessSubtitle.test_archive_list2, TestGuessSubtitle.test_movie_info,
        )
        self.assertEqual((success, subname), TestGuessSubtitle.test_archive_result2)


if __name__ == "__main__":
    unittest.main()
