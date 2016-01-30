import struct
import os
from tarfile import _FileInFile as __FileInFile
import tarfile
import lzma

class _FileInFile(__FileInFile):
    def seek(self, position, mode=0):
        """Seek to a position in the file.
        """
        if mode == 0:
            self.position = position
        elif mode == 1:
            self.position += position
        elif mode == 2:
            self.position = self.size - position

    def seekable(self):
        return True

class ArFile:
    def __init__(self, fileObj):
        self.fileObj = fileObj
        self.files = {}
        self.indexFiles()

    def indexFiles(self):
        self.files = {}
        fileObj = self.fileObj
        fileObj.seek(8) #skip header


        while fileObj.tell() != os.fstat(fileObj.fileno()).st_size:
            entry = ArFileEntry(self)
            self.files[entry.ar_name] = entry

    def getFile(self, name):
        return self.files[name]
    def open(self, name):
        return self.files[name].open()

class ArFileEntry:
    ar_name = ''
    ar_date = ''
    ar_uid = ''
    ar_gid = ''
    ar_mode = ''
    ar_size = ''
    ar_fmag = ''
    def __init__(self, arfile):
        self.arfile = arfile

        f = arfile.fileObj
        self.ar_name = str.rstrip(f.read(16).decode())
        self.ar_date = str.rstrip(f.read(12).decode())
        self.ar_uid = str.rstrip(f.read(6).decode())
        self.ar_gid = str.rstrip(f.read(6).decode())
        self.ar_mode = str.rstrip(f.read(8).decode())
        self.ar_size = int(str.rstrip(f.read(10).decode()))
        self.ar_fmag = str.rstrip(f.read(2).decode())
        self.offset = f.tell()

        phys_size = self.ar_size
        if self.ar_size % 2 != 0:
            phys_size = self.ar_size + 1

        f.seek(phys_size, 1)

    def open(self):
        return _FileInFile(
            self.arfile.fileObj,
            self.offset,
            self.ar_size,
            None
        )