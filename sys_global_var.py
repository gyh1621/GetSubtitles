# coding: utf-8

import sys


# python version
if sys.version_info[0] == 2:
    py = 2
else:
    py = 3

# system encoding
if sys.stdout.encoding == 'cp936':
    is_gbk = True
else:
    is_gbk = False

# set prefix
if py == 2 and is_gbk:
    prefix = '├ '.decode('utf8').encode('gbk')
else:
    prefix = '├ '
