# coding: utf-8

from py7zlib import Archive7z


class Py7z:

    def __init__(self, file):
        self.archive = Archive7z(file)

    def namelist(self):
        return self.archive.getnames()

    def read(self, name):
        return self.archive.getmember(name).read()
