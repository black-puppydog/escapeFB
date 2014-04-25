#! /usr/bin/env python

import io, json
import sys
import os
import fnmatch
from PIL import Image
from datetime import datetime
import imagehash

COMMON_IMAGE_PATTERNS = ["*.jpg", "*.JPG", "*.png", "*.PNG"]

__author__ = 'daan'


def find_images(root_path, patterns):
    for current_folder, subdirs, files in os.walk(os.path.abspath(root_path)):
        for pattern in patterns:
            for filename in fnmatch.filter(files, pattern):
                yield os.path.relpath(os.path.join(current_folder, filename), root_path)


def image_descriptor(image_path):
    img = Image.open(image_path)
    result = {'width': img.size[0],
              'height': img.size[1],
              'aHash': str(imagehash.average_hash(img)),
              'pHash': str(imagehash.phash(img)),
              'dHash': str(imagehash.dhash(img)),
    }
    return result


def write_dict_to_json(data, filename):
    with io.open(filename, 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(data, ensure_ascii=False, indent=4)))


def build_image_db(root_path, db_filename, patterns=COMMON_IMAGE_PATTERNS):
    filenames = find_images(root_path, patterns)
    data = {"root_path": root_path}
    time_started = datetime.now()
    print("{0}: Starting scan of {1}".format(time_started, root_path))

    images = {}
    data["images"] = images

    for filename_rel in filenames:
        print("{0}: Extracting descriptor for {1}".format(datetime.now(), filename_rel))
        filename_abs = os.path.join(root_path, filename_rel)
        images[filename_rel] = image_descriptor(filename_abs)

    time_finished = datetime.now()
    time_taken = time_finished - time_started
    print("{0}: Scan finished, took {1}".format(time_finished, time_taken))
    data["timing"] = {
        "scan_start": str(time_started),
        "scan_end": str(time_finished),
        "scan_duration": str(time_taken),
    }

    print("{0}: Writing resulting database to {1}".format(datetime.now(), db_filename))
    write_dict_to_json(data, db_filename)

    print("FINISHED\n")


if __name__ == "__main__":

    root_path = sys.argv[1]
    db_filename = sys.argv[2]

    build_image_db(root_path, db_filename)

    sys.exit(0)

    # test file finding
    root_path = sys.argv[1]
    print("Root: {0}".format(root_path))

    if len(sys.argv) > 2:
        patterns = sys.argv[2:]
    else:
        patterns = COMMON_IMAGE_PATTERNS

    filenames = find_images(root_path, patterns)

    for filename in filenames:
        print(filename)

    # test json writing
    write_dict_to_json({'bla': {"one": {1: 2, 4: 3}, "two": {"foo": "bar"}}}, "test.json")
