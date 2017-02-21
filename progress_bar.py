# coding: utf-8
# !/usr/bin/env python3

import shutil


class ProgressBar(object):

    def __init__(self, prefix_info, title, total):
        self.title = title
        self.total = total
        self.prefix_info = prefix_info

    def refresh(self, cur_len):
        terminal_width = shutil.get_terminal_size().columns  # 获取终端宽度
        info = "%s '%s'...  %.2f%%" % (self.prefix_info, self.title, cur_len/self.total * 100)
        while len(info) > terminal_width - 20:
            self.title = self.title[0:-4] + '...'
            info = "%s '%s'...  %.2f%%" % (self.prefix_info, self.title, cur_len/self.total * 100)
        end_str = '\r' if cur_len < self.total else '\n'
        print(info, end=end_str)


def main():

    import time

    bar = ProgressBar('Downloading', 'test', 100)
    for i in range(101):
        # print('1')
        time.sleep(0.07)
        bar.refresh(i)

if __name__ == '__main__':
    main()