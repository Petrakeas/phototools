#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib
import os
import sys
import shutil
import win32file, win32con
from timeit import default_timer

source_path = r'C:\Lots_of_files'
albums_paths = [r'C:\Album Collection',
                r'F:\Album Collection']
out_path = r'C:\Output'

use_hashes = True

ignored_files = {'Thumbs.db', 'desktop.ini', 'Folder.jpg', 'feed.rss'}
ignored_file_extensions = {'.ini', '.url'}


def copy_orphans(source_path, albums_paths, out_path):
    """ Copies orphan files.

    Method iterates over the files in the first level of source_path and detects
    the files that do not exist under any level of albums_path. These are considered
    orphans files and are copied to out_path.

    Keyword arguments:
    source_path -- the path that contains the potentially orphan files in its first level
    albums_paths -- a list of paths that contain all the media organized in albums
    out_path -- the path to copy the orphan files to
    """
    # Scan all files in albums_path
    start_time = default_timer()

    count = 0
    files_set = set()
    for album_path in albums_paths:
        for root, directories, files in os.walk(album_path):
            #    print('--Dir: ' + root)
            for directory in directories:
                full_dir = os.path.join(root, directory)
            #        print(full_dir)
            for name in files:
                filename, file_extension = os.path.splitext(name)
                if file_extension.lower() in ignored_file_extensions:
                    continue
                if name in ignored_files:
                    continue
                count += 1
                if name in files_set:
                    print("duplicate file found: " + name)
                    continue
                files_set.add(get_id(root, name))
                # print(os.path.join(root, name))
    print('\nTotal number of unique files found in albums path: %d (total files: %d)' % (len(files_set), count))

    # Check files in source_path
    files = list(file for file in os.listdir(source_path)
                 if os.path.isfile(os.path.join(source_path, file))
                 and file not in ignored_files
                 and os.path.splitext(file)[1].lower() not in ignored_file_extensions)

    print('\nTotal number of files found in source path: %d' % (len(files)))

    id_map = {}
    for file in files:
        id_map[get_id(source_path, file)] = file

    orphan_ids = set(id_map.keys()) - files_set
    orphan_files = [id_map[orphan_id] for orphan_id in orphan_ids]

    print('\nTotal number of orphan files found: %d' % len(orphan_files))

    # Copy orphan files to out_path
    for file in orphan_files:
        print(file)
        src = os.path.join(source_path, file)
        dst = os.path.join(out_path, file)

        shutil.copy2(src, dst)
        copy_file_time(src, dst)

    end_time = default_timer()

    print('\nCoping of orphan files to out path finished. Total time: %d seconds' % (end_time - start_time))

    return


def copy_file_time(source, destination):
    if os.name == 'nt':
        src_file = win32file.CreateFile(
            source, win32file.GENERIC_READ,
            0,
            None, win32file.OPEN_EXISTING,
            win32con.FILE_ATTRIBUTE_NORMAL, 0)
        ct, at, wt = win32file.GetFileTime(src_file)
        src_file.close()
        dst_file = win32file.CreateFile(
            destination, win32file.GENERIC_READ | win32con.GENERIC_WRITE,
            0,
            None, win32con.OPEN_EXISTING,
            win32con.FILE_ATTRIBUTE_NORMAL, None)
        win32file.SetFileTime(dst_file, ct, at, wt)
        dst_file.close()


def getMD5(filepath):
    BLOCKSIZE = 65536
    hasher = hashlib.md5()
    with open(filepath, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()


def get_id(path, filename):
    if use_hashes:
        return getMD5(os.path.join(path, filename))
    else:
        return filename



########################
# main
########################


def main(argv):
    copy_orphans(source_path, albums_paths, out_path)


if __name__ == "__main__":
    main(sys.argv)
