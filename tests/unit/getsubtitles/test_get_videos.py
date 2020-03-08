# coding: utf-8

import os
import copy
import shutil
import unittest
from os import path

from tests import create_test_directory
from tests.unit.getsubtitles import get_function as get_f


def get_function(**kwargs):
    return get_f("get_videos", **kwargs)


def videos_to_dict(videos):
    video_dict = dict()
    for video in videos:
        video_dict[video.name + video.type] = {
            "video_path": video.path,
            "store_path": video.sub_store_path,
            "has_subtitle": video.has_subtitle,
        }
    return video_dict


class TestGetVideos(unittest.TestCase):

    test_dir = path.join(os.getcwd(), "TESTGETVIDEOS")
    test_dir_structure1 = {
        "sub1": ["file1.mkv", "file2", "file1.ass"],
        "sub2": ["fil3", "file4.mkv", "file4.zh.srt"],
        "file5.mkv": None,
        "file6.mkv": None,
        "file6.zh.ass": None,
        "storepath": ["file1.ass", "file5.ass"],
    }
    file1_result = {
        "video_path": path.join(test_dir, "sub1"),
        "store_path": path.join(test_dir, "sub1"),
        "has_subtitle": True,
    }
    file4_result = {
        "video_path": path.join(test_dir, "sub2"),
        "store_path": path.join(test_dir, "sub2"),
        "has_subtitle": False,
    }
    file5_result = {
        "video_path": test_dir,
        "store_path": test_dir,
        "has_subtitle": False,
    }
    file6_result = {
        "video_path": test_dir,
        "store_path": test_dir,
        "has_subtitle": False,
    }
    # test directory
    desired_result1 = {
        "file5.mkv": file5_result,
        "file6.mkv": file6_result,
        "file1.mkv": file1_result,
        "file4.mkv": file4_result,
    }
    # test absolute path
    desired_result2 = {"file1.mkv": file1_result}
    desired_result3 = {"file5.mkv": file5_result}
    desired_result4 = {"file6.mkv": file6_result}
    # test single video name
    desired_result5 = {"file5.mkv": file5_result.copy()}
    desired_result5["file5.mkv"]["video_path"] = os.getcwd()
    desired_result5["file5.mkv"]["store_path"] = os.getcwd()
    # test store path
    test_dir_structure2 = copy.deepcopy(test_dir_structure1)
    test_dir_structure2["sub1"].remove("file1.ass")
    test_dir_structure2["sub2"].remove("file4.zh.srt")
    desired_result6 = copy.deepcopy(desired_result1)
    desired_result6["file4.mkv"]["has_subtitle"] = False
    desired_result6["file5.mkv"]["has_subtitle"] = True
    desired_result6["file6.mkv"]["has_subtitle"] = False
    desired_result6["file1.mkv"]["store_path"] = path.join(test_dir, "storepath")
    desired_result6["file4.mkv"]["store_path"] = path.join(test_dir, "storepath")
    desired_result6["file5.mkv"]["store_path"] = path.join(test_dir, "storepath")
    desired_result6["file6.mkv"]["store_path"] = path.join(test_dir, "storepath")

    def tearDown(self):
        shutil.rmtree(TestGetVideos.test_dir)

    def test_directory_with_identifier(self):
        create_test_directory(
            TestGetVideos.test_dir_structure1, parent_dir=TestGetVideos.test_dir,
        )
        desired_result = copy.deepcopy(TestGetVideos.desired_result1)
        desired_result["file1.mkv"]["has_subtitle"] = False
        desired_result["file4.mkv"]["has_subtitle"] = True
        desired_result["file6.mkv"]["has_subtitle"] = True
        get_videos = get_function(plex=True)
        videos = get_videos(TestGetVideos.test_dir)
        videos = videos_to_dict(videos)
        self.assertDictEqual(videos, desired_result)

    def test_absolute_video_path(self):
        create_test_directory(
            TestGetVideos.test_dir_structure1, parent_dir=TestGetVideos.test_dir,
        )
        get_videos = get_function()
        videos = get_videos(path.join(TestGetVideos.test_dir, "sub1", "file1.mkv"))
        videos = videos_to_dict(videos)
        self.assertDictEqual(videos, TestGetVideos.desired_result2)
        videos = get_videos(path.join(TestGetVideos.test_dir, "file5.mkv"))
        videos = videos_to_dict(videos)
        self.assertDictEqual(videos, TestGetVideos.desired_result3)
        videos = get_videos(path.join(TestGetVideos.test_dir, "file6.mkv"))
        videos = videos_to_dict(videos)
        self.assertDictEqual(videos, TestGetVideos.desired_result4)

    def test_single_video_name(self):
        create_test_directory(
            TestGetVideos.test_dir_structure1, parent_dir=TestGetVideos.test_dir,
        )
        get_videos = get_function()
        videos = get_videos("file5.mkv")
        videos = videos_to_dict(videos)
        self.assertDictEqual(videos, TestGetVideos.desired_result5)

    def test_store_path(self):
        create_test_directory(
            TestGetVideos.test_dir_structure2, parent_dir=TestGetVideos.test_dir,
        )
        get_videos = get_function(
            sub_path=path.join(TestGetVideos.test_dir, "storepath")
        )
        videos = get_videos(TestGetVideos.test_dir)
        videos = videos_to_dict(videos)
        self.assertDictEqual(videos, (TestGetVideos.desired_result6))

    def test_invalid_store_path(self):
        create_test_directory(
            TestGetVideos.test_dir_structure1, parent_dir=TestGetVideos.test_dir,
        )
        get_videos = get_function(
            sub_path=path.join(TestGetVideos.test_dir, "unexisted_dir")
        )
        videos = get_videos(TestGetVideos.test_dir)
        videos = videos_to_dict(videos)
        self.assertDictEqual(videos, (TestGetVideos.desired_result1))


if __name__ == "__main__":
    unittest.main()
