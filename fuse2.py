import os
import sys
import errno
import stat

from fuse import FUSE, FuseOSError, Operations

from time import time

import arfile
import lzma
import tarfile

class Passthrough(Operations):
    fd = 0

    def __init__(self, debfile):
        self.debfile = debfile
        self.fds = {}

        f = open(debfile, 'rb')
        a = arfile.ArFile(f)

        f2 = a.open('data.tar.xz')
        xz = lzma.LZMAFile(f2)
        tar = tarfile.open(fileobj=xz)

        self.store = tar

        print(tar.getmembers())

    def readdir(self, path, fh):
        dirents = ['.', '..']

        for r in dirents:
            yield r

        fnames = self.store.getnames()
        out = []
        for fname in fnames:
            if fname[:1] == '.':
                fname = fname[1:]

            if (fname[:len(path)] == path):
                remainder = fname[len(path):]
                if len(remainder) > 0 and remainder[0] == '/':
                    remainder = remainder[1:]

                if remainder != '' and '/' not in remainder:
                    out.append(remainder)
        for entry in out:
            yield entry

    def _getfile(self, path):
        if path == '/':
            path = ''
        try:
            info = self.store.getmember('.'+path)
        except:
            raise FuseOSError(errno.ENOENT)

        return info

    def getattr(self, path, fh=None):
        info = self._getfile(path)

        ret = {
            'st_mode': info.mode,
            'st_atime': time(),
            'st_ctime': float(info.mtime),
            'st_mtime': float(info.mtime),
            'st_uid': info.uid,
            'st_gid': info.gid,
            'st_size': info.size,
        }

        if info.isdir():
            ret['st_mode'] |= stat.S_IFDIR
        if info.isreg():
            ret['st_mode'] |= stat.S_IFREG
        if info.issym():
            ret['st_mode'] |= stat.S_IFLNK
        if info.isblk():
            ret['st_mode'] |= stat.S_IFBLK
        if info.ischr():
            ret['st_mode'] |= stat.S_IFCHR
        if info.isfifo():
            ret['st_mode'] |= stat.S_IFIFO

        return ret

    def open(self, path, flags):
        info = self._getfile(path)

        file = self.store.extractfile(info)

        self.fd += 1
        self.fds[self.fd] = file

        return self.fd

    def readlink(self, path):
        info = self._getfile(path)
        if (info.issym()):
            return info.linkname
        else:
            return path

    def read(self, path, size, offset, fh):

        file = self.fds[fh]
        file.seek(offset, 0)
        buf = file.read(size)

        return buf

def main(mountpoint, root):
    print('started')
    FUSE(Passthrough(root), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])
