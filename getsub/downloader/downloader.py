# coding: utf-8

from requests.utils import quote


class Downloader(object):

    header = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) "
        "AppleWebKit 537.36 (KHTML, like Gecko) Chrome",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/webp,*/*;q=0.8",
    }

    service_short_names = {"amazon prime": "amzn"}

    @classmethod
    def get_keywords(cls, video):

        """ 解析视频名
        Args:
            video: Video 对象
        Return:
            keywords: list
        """

        keywords = []

        info_dict = video.info
        title = info_dict["title"]
        keywords.append(title)

        if info_dict.get("season"):
            keywords.append("s%s" % str(info_dict["season"]).zfill(2))

        if info_dict.get("year") and info_dict.get("type") == "movie":
            keywords.append(str(info_dict["year"]))  # 若为电影添加年份

        if info_dict.get("episode"):
            keywords.append("e%s" % str(info_dict["episode"]).zfill(2))
        if info_dict.get("source"):
            keywords.append(info_dict["source"].replace("-", ""))
        if info_dict.get("release_group"):
            keywords.append(info_dict["release_group"])
        if info_dict.get("streaming_service"):
            service_name = info_dict["streaming_service"]
            short_names = cls.service_short_names.get(service_name.lower())
            if short_names:
                keywords.append(short_names)
        if info_dict.get("screen_size"):
            keywords.append(str(info_dict["screen_size"]))

        # 对关键字进行 URL 编码
        keywords = [quote(_keyword) for _keyword in keywords]
        return keywords

    def get_subtitles(self, video, sub_num=5):

        """ 搜索字幕
        Args:
            video：Video 对象
            sub_num: 字幕结果数，默认为5
        Return：
            字幕字典: 按语言值降序排列
            eg: {'字幕名': {'lan': '语言值', 'link': '字幕链接', 'session': '查询session'}}
            字幕包含语言值：英文加1， 繁体加2， 简体加4， 双语加8
        """

        raise NotImplementedError

    def download_file(self, file_name, sub_url, session=None):

        """ 下载字幕包
        Args:
            file_name: 字幕包名
            sub_url: 下载链接，为 'get_subtitles' 返回结果中 'link' 值
            session: 查询session
        Return:
            data_type: 压缩文件类型，如 '.rar', '.zip', '.7z'
            sub_data_bytes: 字幕包二进制数据
            err_msg : 错误消息，无则返回 ''
        """

        raise NotImplementedError
