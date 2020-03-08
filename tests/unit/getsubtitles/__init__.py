# coding: utf-8

from getsub.main import GetSubtitles


def get_function(
    func,
    name="",
    query=False,
    single=False,
    more=False,
    both=False,
    over=False,
    plex=False,
    debug=False,
    sub_num=1,
    downloader=None,
    sub_path="",
):
    obj = GetSubtitles(
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
    )
    return getattr(obj, func)
