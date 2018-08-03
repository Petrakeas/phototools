#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import datetime
import re
import exifread
from timeit import default_timer


albums_path = r'C:\Albums'

time_format = "%Y-%m-%d"

ignored_files = {'Thumbs.db', 'desktop.ini', 'Folder.jpg', 'feed.rss'}
ignored_file_extensions = {'.ini', '.url'}
media_file_extensions = {'.jpg', '.jpeg', '.avi', '.mp4', '.mov', '.mpeg', '.ogg', ".gif", ".png"}


def rename_albums(albums_path):
    """ Renames folders by adding a timestamp in the beginning of the original folder name according to the media
    creation time.

    Method iterates over the folders in the first level of albums_path and tries to find the oldest date of the media
    files that the folder contains. This is done by reading the EXIF data from the included images. If no EXIF data are
    found, the modified date from the included media files is used.

    Keyword arguments:
    albums_path -- the path that contains the albums to be named
    """

    # Scan all files in albums_path
    start_time = default_timer()

    albums = list(album for album in os.listdir(albums_path)
                  if os.path.isdir(os.path.join(albums_path, album)))

    print('\nTotal number of albums in path: %d' % (len(albums)))

    for album in albums:
        album_path = os.path.join(albums_path, album)
        album_date = get_oldest_date(album_path)
        if album_date is None:
            print("Could not find date for album: " + album)
        else:
            date = album_date.strftime(time_format)
            os.rename(album_path, os.path.join(albums_path, date + " " + album))

    end_time = default_timer()

    print('\nRename completed. Total time: %d seconds' % (end_time - start_time))

    return


def get_oldest_date(directory):
    oldest_date = None

    # Try to find the date from the images
    images = list(file for file in os.listdir(directory)
                  if os.path.isfile(os.path.join(directory, file))
                  and os.path.splitext(file)[1].lower() is ".jpg" or ".jpeg")
    for image in images:
        date = get_created_date(os.path.join(directory, image))
        if oldest_date is None:
            oldest_date = date
        elif date < oldest_date:
            oldest_date = date

    # If no images are found, use other media files
    if oldest_date is None:
        media_files = list(file for file in os.listdir(directory)
                           if os.path.isfile(os.path.join(directory, file))
                           and os.path.splitext(file)[1].lower() in media_file_extensions)
        for media_file in media_files:
            date = get_created_date(os.path.join(directory, media_file))
            if oldest_date is None:
                oldest_date = date
            elif date < oldest_date:
                oldest_date = date

    return oldest_date


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
    rename_albums(albums_path)


if __name__ == "__main__":
    main(sys.argv)
