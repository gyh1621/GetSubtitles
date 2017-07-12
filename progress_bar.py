# coding: utf-8

from __future__ import print_function
from __future__ import division
from time import sleep

from sys_global_var import py

if py == 2:
    from backports.shutil_get_terminal_size.get_terminal_size \
         import get_terminal_size
else:
    from shutil import get_terminal_size


class ProgressBar(object):

    def __init__(self, prefix_info, title='', total='', count_time=0):
        self.title = title
        self.total = total
        self.count_time = count_time
        self.prefix_info = prefix_info

    def refresh(self, cur_len):
        terminal_width = get_terminal_size().columns  # 获取终端宽度
        info = "%s '%s'...  %.2f%%" % (self.prefix_info,
                                       self.title,
                                       cur_len/self.total * 100)
        while len(info) > terminal_width - 20:
            self.title = self.title[0:-4] + '...'
            info = "%s '%s'...  %.2f%%" % (self.prefix_info,
                                           self.title,
                                           cur_len/self.total * 100)
        end_str = '\r' if cur_len < self.total else '\n'
        print(info, end=end_str)

    def count_down(self):
        terminal_width = get_terminal_size().columns

        for i in range(self.count_time + 1):
            info = "%s %ss" % (self.prefix_info, self.count_time - i)
            print(' ' * (terminal_width - 5), end='\r')
            print(info, end='\r')
            sleep(1)


def main():

    import time

    bar = ProgressBar('Downloading', 'test', 100)
    for i in range(101):
        # print('1')
        time.sleep(0.05)
        bar.refresh(i)
    bar = ProgressBar('Count down...', count_time=10)
    bar.count_down()


if __name__ == '__main__':
    main()
