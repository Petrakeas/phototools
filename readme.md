photo tools
=========

Some scripts that help me automate organizing my photos & videos.

* rename.py: renames the folders according the creation date of the included media files
* orphan.py: finds which files are not already included in your collection

 Usage
 -----

Here's an example that will demonstrate how these scripts are used.

## rename.py

If you have a folder with the following structure:


```
albums
├── foo album
└── bar album
```
and `foo album` and `bar album` contain photos and videos, running `rename.py` will rename the folders to something like:

```
albums
├── 2018-04-19 foo album
└── 2018-02-25 bar album
```

by adding a date before the original album name. 

The date corresponds the creation date of the oldest media file contained in each folder (EXIF data or file modification date is used as fallback).

## orphan.py

The following folder contains a list of media files:

```
lots_of_files
├── photo.jpeg
└── video.mp4
.
.
```

and you want to find out which of these files are not already included under the previous example's `albums` folder.

Running `orphan.py` script will parse all files under the `albums` directory, by diving into all nested subfolders, and compare their hash with the hash of the files under `lots_of_files`. The files that don't match (and hence you don't already have their copy stored), will be moved to the output folder.

