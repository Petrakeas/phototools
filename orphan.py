#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import hashlib
import os
import re
import sys
import shutil
import win32file, win32con
from timeit import default_timer
import exifread

source_path = r'C:\Lots_of_files'
albums_paths = [r'C:\Album Collection',
                r'F:\Album Collection']
out_path = r'C:\Output'

# If enabled, files that don't have the same hash but have similarities (same filename, date, filesize) won't be
# copied to the out_path. This is useful for ignoring files that may be re-compressed or edited versions.
check_for_similar_files = True
SIZE_MAX_DIFFERENCE = 500000

use_MD5_optimization = True
MD5_MAX_READ_BYTE = 655360

print_files = False

SAME_FILENAME_FOLDER = "same filename"
ignored_files = {'Thumbs.db', 'desktop.ini', 'Folder.jpg', 'feed.rss'}
ignored_file_extensions = {'.ini', '.url'}


def copy_orphans(source_path, albums_paths, out_path):
    """ Copies orphan files.

    Method iterates over the files in the first level of source_path and detects
    the files that do not exist under any level of albums_path. These are considered
    orphans files and are copied to out_path. Files that have the same filename as other
    files in albums_path but have possibly different content are placed in a separate folder.

    Keyword arguments:
    source_path -- the path that contains the potentially orphan files in its first level
    albums_paths -- a list of paths that contain all the media organized in albums
    out_path -- the path to copy the orphan files to
    """
    # Scan all files in albums_path
    start_time = default_timer()

    count = 0
    album_files_dic = {}  # hash -> [filename lowercased, filepath, filesize]
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
                path = os.path.join(root, name)
                album_files_dic[get_id(root, name)] = [name.casefold(), path, os.path.getsize(path)]
                # print(os.path.join(root, name))
    print('\nTotal number of unique files found in albums path: %d (total files: %d)' % (len(album_files_dic), count))

    # Scan files in source_path
    files = list(file for file in os.listdir(source_path)
                 if os.path.isfile(os.path.join(source_path, file))
                 and file not in ignored_files
                 and os.path.splitext(file)[1].lower() not in ignored_file_extensions)

    print('\nTotal number of files found in source path: %d' % (len(files)))

    # Detect orphan files
    source_files_dic = {}  # hash -> [filename lowercased, filepath, filesize]
    for file in files:
        path = os.path.join(source_path, file)
        source_files_dic[get_id(source_path, file)] = [file.casefold(), path, os.path.getsize(path), ]

    orphan_ids = set(source_files_dic.keys()) - album_files_dic.keys()
    orphan_files = [source_files_dic[orphan_id] for orphan_id in orphan_ids]
    orphan_same_name_files = []

    orphan_files2 = []
    for [orphan_name, orphan_path, orphan_size] in orphan_files:
        found_similar = False
        found_same_name = False
        for [filename, filepath, size] in album_files_dic.values():
            if orphan_name == filename:
                found_same_name = True
                # Find files with same filename that are similar. These files probably contain the same image data
                # and should not be considered orphan files.
                if check_for_similar_files and is_similar_file(orphan_path, orphan_size, filepath, size):
                    found_similar = True
                    break
        if not found_similar:
            # Non similar files that have a filename that exists in the albums_path are possibly orphan files, but
            # we are not 100% sure. That's why we store them to a different list: orphan_same_name_files and
            # copy them to a different folder so that the user can check them out.
            if found_same_name:
                orphan_same_name_files.append([orphan_name, orphan_path, orphan_size])
            else:
                orphan_files2.append([orphan_name, orphan_path, orphan_size])
    orphan_files = orphan_files2

    print('\nTotal number of orphan files found: %d' % len(orphan_files))
    print('Total number of orphan files with same filename found: %d' % len(orphan_same_name_files))
    print('')

    # Copy orphan files to out_path
    for file in orphan_files:
        filename = os.path.basename(file[1])
        if print_files:
            print(filename)
        src = file[1]
        dst = os.path.join(out_path, filename)

        shutil.copy2(src, dst)
        copy_file_time(src, dst)

    if orphan_same_name_files:
        if print_files:
            print('\n---Same filename---')
        out_path2 = os.path.join(out_path, SAME_FILENAME_FOLDER)
        if not os.path.exists(out_path2):
            os.makedirs(out_path2)
        for file in orphan_same_name_files:
            filename = os.path.basename(file[1])
            if print_files:
                print(filename)
            src = file[1]
            dst = os.path.join(out_path2, filename)

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
            if use_MD5_optimization and afile.tell() > MD5_MAX_READ_BYTE:
                break
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()


def get_id(path, filename):
    return getMD5(os.path.join(path, filename))



def is_similar_file(path1, filesize1, path2, filesize2):
    # If 2 files were modified at exactly the same time they are considered similar. If not, we compare their filesize.
    date1 = get_created_date(path1)
    date2 = get_created_date(path2)
    if date1 is not None and date2 is not None:
        if date1 == date2:
            return True

    if abs(filesize1 - filesize2) < SIZE_MAX_DIFFERENCE:
        return True
    return False


def get_created_date(filepath):
    created_date = None
    if re.search("\.(jpeg|jpg|cr2)$", filepath.lower()):
        image = open(filepath, "rb")
        tags = exifread.process_file(image, details=False, stop_tag="Image DateTime")
        if "Image DateTime" in tags:
            created_date = datetime.datetime.strptime(tags["Image DateTime"].values, "%Y:%m:%d %H:%M:%S")

    if created_date is None:
        created_date = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))

    return created_date


########################
# main
########################


def main(argv):
    if not isinstance(albums_paths, list):
        print('\n albums_path is not an array of paths')
        exit()
    copy_orphans(source_path, albums_paths, out_path)


if __name__ == "__main__":
    main(sys.argv)
