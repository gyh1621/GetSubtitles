# coding: utf-8

import os
import sys
import rarfile
import argparse
from os import path
from collections import OrderedDict
from traceback import format_exc

from requests import exceptions

from getsub.__version__ import __version__
from getsub.constants import SUB_FORMATS, VIDEO_FORMATS, ARCHIVE_TYPES
from getsub.downloader import DownloaderManager
from getsub.util import choose_archive, choose_subtitle, get_file_list, guess_subtitle
from getsub.models import Video


class GetSubtitles(object):
    def __init__(
        self,
        name,
        query,
        single,
        more,
        both,
        over,
        plex,
        debug,
        sub_num,
        downloader,
        sub_path,
    ):
        self.arg_name = name
        self.both = both
        self.query, self.single = query, single
        self.more, self.over = more, over
        if not sub_num:
            self.sub_num = 5
        else:
            self.sub_num = int(sub_num)
        self.plex = plex
        self.debug = debug
        self.s_error = ""
        self.f_error = ""
        if not downloader:
            self.downloader = DownloaderManager.downloaders
        else:
            if downloader not in DownloaderManager.downloader_names:
                print(
                    "\nNO SUCH DOWNLOADER:",
                    "PLEASE CHOOSE FROM",
                    ", ".join(DownloaderManager.downloader_names),
                    "\n",
                )
                sys.exit(1)
            self.downloader = [DownloaderManager.get_downloader_by_name(downloader)]
        self.failed_list = []  # [{'name', 'path', 'error', 'trace_back'}
        self.sub_identifier = "" if not self.plex else ".zh"
        self.sub_store_path = sub_path.replace('"', "")
        if not path.isdir(self.sub_store_path):
            if self.sub_store_path:
                print("store path is invalid: " + self.sub_store_path)
            self.sub_store_path = ""
        else:
            print("subtitles will be saved to: " + self.sub_store_path)

    def get_videos(self, raw_path):
        """
        传入视频名称或路径，返回 Video 对象列表
        若指定 store_path ，则是否存在字幕会在 store_path 中查找

        params:
            raw_path: str, video path/name or a directory path
        return:
            videos: list of "Video" objects
        """

        raw_path = raw_path.replace('"', "")

        videos = []

        if path.isdir(raw_path):  # directory
            for root, dirs, files in os.walk(raw_path):
                for file in files:
                    v_type = path.splitext(file)[-1]
                    if v_type not in VIDEO_FORMATS:
                        continue
                    video = Video(
                        path.join(root, file),
                        sub_store_path=self.sub_store_path,
                        identifier=self.sub_identifier,
                    )
                    videos.append(video)
        elif path.isabs(raw_path):  # video's absolute path
            v_type = path.splitext(raw_path)[-1]
            if v_type in VIDEO_FORMATS:
                video = Video(
                    raw_path,
                    sub_store_path=self.sub_store_path,
                    identifier=self.sub_identifier,
                )
                videos.append(video)
        else:  # single video name, no path
            s_path = os.getcwd() if not self.sub_store_path else self.sub_store_path
            video = Video(
                raw_path, sub_store_path=s_path, identifier=self.sub_identifier
            )
            videos.append(video)

        return videos

    def get_search_results(self, video):
        results = OrderedDict()
        for i, downloader in enumerate(self.downloader):
            try:
                result = downloader.get_subtitles(video, sub_num=self.sub_num)
                results.update(result)
            except ValueError as e:
                print("error: " + str(e))
            except (exceptions.Timeout, exceptions.ConnectionError):
                print("connect timeout, search next site.")
                if i == (len(self.downloader) - 1):
                    print("PLEASE CHECK YOUR NETWORK STATUS")
                    sys.exit(0)
                else:
                    continue
            # TODO: search all sites or exit after collecting enough results
            if len(results) >= self.sub_num:
                break
        return results

    def process_archive(
        self, video, archive_data, datatype,
    ):
        """
        解压字幕包，返回解压字幕名列表

        params:
            video: Video object
            archive_data: binary archive data
            datatype: str, archive type
        return:
            error: str, error message
            extract_subs: list, [<subname, subtype>, ...]
        """

        error = ""

        if datatype not in ARCHIVE_TYPES:
            error = "unsupported file type " + datatype
            return error, []

        sub_lists_dict = get_file_list(archive_data, datatype)

        if len(sub_lists_dict) == 0:
            error = "no subtitle in this archive"
            return error, []

        # get subtitles to extract
        if not self.single:
            success, sub_name = guess_subtitle(list(sub_lists_dict.keys()), video.info)
            if not success:
                error = "no guess result in auto mode"
                return error, []
        else:
            sub_name = choose_subtitle(list(sub_lists_dict.keys()))

        # build new names
        sub_title, sub_type = path.splitext(sub_name)
        extract_subs = [[sub_name, sub_type]]
        if self.both:
            another_sub_type = ".srt" if sub_type == ".ass" else ".ass"
            another_sub = sub_name.replace(sub_type, another_sub_type)
            another_sub = path.basename(another_sub)
            for subname in list(sub_lists_dict.keys()):
                if another_sub in subname:
                    extract_subs.append([subname, another_sub_type])
                    break
            if len(extract_subs) == 1:
                print("no %s subtitles in this archive" % another_sub_type)

        # delete existed subtitles
        video.delete_existed_subtitles()

        # extract subtitles
        for one_sub, one_sub_type in extract_subs:
            sub_new_name = video.name + video.sub_identifier + one_sub_type
            extract_path = path.join(video.sub_store_path, sub_new_name)
            with open(extract_path, "wb") as sub:
                file_handler = sub_lists_dict[one_sub]
                sub.write(file_handler.read(one_sub))

        return error, extract_subs

    def process_subtitle(self, video, sub_data, datatype):

        # delete existed subtitles
        video.delete_existed_subtitles()

        # save subtitle
        sub_name = video.name + video.sub_identifier + datatype
        extract_path = path.join(video.sub_store_path, sub_name)
        with open(extract_path, "wb") as sub:
            sub.write(sub_data)

        extract_subs = [[sub_name, datatype]]
        return "", extract_subs

    def process_result(self, video, chosen_sub, link, session):

        # download archive
        choice_prefix = chosen_sub[: chosen_sub.find("]") + 1]
        downloader = DownloaderManager.get_downloader_by_choice_prefix(choice_prefix)
        datatype, data, error = downloader.download_file(
            chosen_sub, link, session=session
        )
        if error:
            return error, []

        # process archive or subtitles downloaded
        if datatype in ARCHIVE_TYPES:
            error, extract_subs = self.process_archive(video, data, datatype)
        elif datatype in SUB_FORMATS:
            error, extract_subs = self.process_subtitle(video, data, datatype)
        else:
            error = "unsupported file type " + datatype

        if error:
            return error, []

        for extract_sub_name, extract_sub_type in extract_subs:
            extract_sub_name = extract_sub_name.split("/")[-1]
            try:
                # zipfile: Historical ZIP filename encoding
                # try cp437 encoding
                extract_sub_name = extract_sub_name.encode("cp437").decode("gbk")
            except Exception:
                pass
            try:
                print("\nExtracted:", extract_sub_name)
            except UnicodeDecodeError:
                print("\nExtracted:".encode("gbk"), extract_sub_name.encode("gbk"))

        # save original archive
        if self.more and datatype in ARCHIVE_TYPES:
            archive_path = path.join(video.sub_store_path, chosen_sub + datatype)
            with open(archive_path, "wb") as f:
                f.write(data)
            print("save original file.")

        return "", extract_subs

    def process_video(self, video):

        extract_subs = []

        sub_dict = self.get_search_results(video)

        if len(sub_dict) == 0:
            error = "no search results. "
            return error, []

        # 遍历字幕包直到有猜测字幕
        while not extract_subs and len(sub_dict) > 0:
            exit, chosen_sub = choose_archive(
                sub_dict, sub_num=self.sub_num, query=self.query
            )
            if exit:
                break

            try:
                error, extract_subs = self.process_result(
                    video,
                    chosen_sub,
                    sub_dict[chosen_sub]["link"],
                    sub_dict[chosen_sub]["session"],
                )
                if error:
                    print("error: " + error + "\n")
            except Exception as e:
                print("error:" + str(e))
            finally:
                sub_dict.pop(chosen_sub)

        return "", extract_subs

    def start(self):

        videos = self.get_videos(self.arg_name)

        for i, video in enumerate(videos):

            # one_video, video_info = item

            self.s_error = ""
            self.f_error = ""

            print("\n- Video:", video.name)  # 打印当前视频及其路径
            print("- Video Path:", video.path)
            print("- Subtitles Store Path:", video.sub_store_path + "\n")
            if video.has_subtitle and not self.over:
                print("subtitle already exists, add '-o' to replace it.")
                continue

            try:
                extract_subs, error = [], ""
                error, extract_subs = self.process_video(video)
                self.s_error = error
            except rarfile.RarCannotExec:
                self.s_error += "Unrar not installed?"
            except Exception as e:
                self.s_error += str(e) + ". "
                self.f_error += format_exc()

            # no guessed subtitle in auto mode
            if not extract_subs and not error:
                self.s_error += " failed to guess one subtitle,"
                self.s_error += "use '-q' to try query mode."

            if self.s_error and not self.debug:
                self.s_error += "add --debug to get more info of the error"

            if self.s_error:
                self.failed_list.append(
                    {
                        "name": video.name,
                        "path": video.path,
                        "error": self.s_error,
                        "trace_back": self.f_error,
                    }
                )
                print("ERROR:" + self.s_error)
            if i == len(videos) - 1:
                break
            print("\n========================================================")

        if len(self.failed_list):
            print("\n===============================", end="")
            print("FAILED LIST===============================\n")
            for i, one in enumerate(self.failed_list):
                print("%2s. name: %s" % (i + 1, one["name"]))
                print("%3s path: %s" % ("", one["path"]))
                print("%3s info: %s" % ("", one["error"]))
                if self.debug:
                    print("%3s TRACE_BACK: %s" % ("", one["trace_back"]))

        print(
            "\ntotal: %s  success: %s  fail: %s\n"
            % (len(videos), len(videos) - len(self.failed_list), len(self.failed_list),)
        )

        return {
            "total": len(videos),
            "success": len(videos) - len(self.failed_list),
            "fail": len(self.failed_list),
            "fail_videos": self.failed_list,
        }


def main():

    arg_parser = argparse.ArgumentParser(
        prog="GetSubtitles",
        epilog="getsub %s\n\n@guoyuhang" % (__version__),
        description="download subtitles easily",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    arg_parser.add_argument(
        "name", help="the video's name or full path or a dir with videos"
    )
    arg_parser.add_argument(
        "-p",
        "--directory",
        default="",
        action="store",
        help="set specified subtitle download path",
    )
    arg_parser.add_argument(
        "-q",
        "--query",
        action="store_true",
        help="show search results and choose one to download",
    )
    arg_parser.add_argument(
        "-s",
        "--single",
        action="store_true",
        help="show subtitles in the compacted file and choose one to download",
    )
    arg_parser.add_argument(
        "-o", "--over", action="store_true", help="replace the subtitle already exists"
    )
    arg_parser.add_argument(
        "-m", "--more", action="store_true", help="save original download file."
    )
    arg_parser.add_argument(
        "-n",
        "--number",
        action="store",
        help="set max number of subtitles to be choosen when in query mode",
    )
    arg_parser.add_argument(
        "-b",
        "--both",
        action="store_true",
        help="save .srt and .ass subtitles at the same time "
        "if two types exist in the same archive",
    )
    arg_parser.add_argument(
        "-d",
        "--downloader",
        action="store",
        help="choose downloader from " + ", ".join(DownloaderManager.downloader_names),
    )
    arg_parser.add_argument(
        "--debug", action="store_true", help="show more info of the error"
    )
    arg_parser.add_argument(
        "--plex",
        action="store_true",
        help="add .zh to the subtitle's name for plex to recognize",
    )

    args = arg_parser.parse_args()

    if args.over:
        print("\nThe script will replace the old subtitles if exist...\n")

    GetSubtitles(
        args.name,
        args.query,
        args.single,
        args.more,
        args.both,
        args.over,
        args.plex,
        args.debug,
        sub_num=args.number,
        downloader=args.downloader,
        sub_path=args.directory,
    ).start()


if __name__ == "__main__":
    main()
