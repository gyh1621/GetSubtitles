# coding: utf-8

import sys
import rarfile
import argparse
from os import path
from collections import OrderedDict
from traceback import format_exc

from requests import exceptions

from getsub.__version__ import __version__
from getsub.downloader import DownloaderManager
from getsub.util import get_videos, choose_archive, process_archive


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
        self.sub_store_path = sub_path
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

    def get_search_results(self, video_name):
        results = OrderedDict()
        for i, downloader in enumerate(self.downloader):
            try:
                result = downloader.get_subtitles(video_name, sub_num=self.sub_num)
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

    def process_result(self, video_name, video_info, chosen_sub, link, session):

        # download archive
        choice_prefix = chosen_sub[: chosen_sub.find("]") + 1]
        downloader = DownloaderManager.get_downloader_by_choice_prefix(choice_prefix)
        datatype, archive_data, error = downloader.download_file(
            chosen_sub, link, session=session
        )
        if error:
            return error, []

        # process archive
        error, extract_sub_names = process_archive(
            video_name,
            video_info,
            archive_data,
            datatype,
            self.both,
            self.single,
            self.sub_identifier,
        )
        if error:
            return error, []

        # save original archive
        if self.more:
            archive_path = path.join(video_info["store_path"], chosen_sub + datatype)
            with open(archive_path, "wb") as f:
                f.write(archive_data)
            print("save original file.")

        return "", extract_sub_names

    def process_video(self, video_name, video_info):

        extract_sub_names = []

        sub_dict = self.get_search_results(video_name)

        if len(sub_dict) == 0:
            error = "no search results. "
            return error, []

        # 遍历字幕包直到有猜测字幕
        while not extract_sub_names and len(sub_dict) > 0:
            exit, chosen_sub = choose_archive(
                sub_dict, sub_num=self.sub_num, query=self.query
            )
            if exit:
                break

            try:
                error, extract_sub_names = self.process_result(
                    video_name,
                    video_info,
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

        return "", extract_sub_names

    def start(self):

        all_video_dict = get_videos(
            self.arg_name, self.sub_store_path, self.sub_identifier
        )

        for i, item in enumerate(all_video_dict.items()):

            one_video, video_info = item

            self.s_error = ""
            self.f_error = ""

            print("\n- Video:", one_video)  # 打印当前视频及其路径
            print("- Video Path:", video_info["video_path"])
            print("- Subtitles Store Path:", video_info["store_path"] + "\n")
            if video_info["has_subtitle"] and not self.over:
                print("subtitle already exists, add '-o' to replace it.")
                continue

            try:
                extract_sub_names, error = [], ""
                error, extract_sub_names = self.process_video(one_video, video_info)
                self.s_error = error
            except rarfile.RarCannotExec:
                self.s_error += "Unrar not installed?"
            except Exception as e:
                self.s_error += str(e) + ". "
                self.f_error += format_exc()

            # no guessed subtitle in auto mode
            if not extract_sub_names and not error:
                self.s_error += " failed to guess one subtitle,"
                self.s_error += "use '-q' to try query mode."

            if self.s_error and not self.debug:
                self.s_error += "add --debug to get more info of the error"

            if self.s_error:
                self.failed_list.append(
                    {
                        "name": one_video,
                        "path": video_info["video_path"],
                        "error": self.s_error,
                        "trace_back": self.f_error,
                    }
                )
                print("ERROR:" + self.s_error)
            if i == len(all_video_dict) - 1:
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
            % (
                len(all_video_dict),
                len(all_video_dict) - len(self.failed_list),
                len(self.failed_list),
            )
        )

        return {
            "total": len(all_video_dict),
            "success": len(all_video_dict) - len(self.failed_list),
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
