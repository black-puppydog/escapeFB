#! /usr/bin/env python

import io
import json
import sys
import os
import fnmatch
from PIL import Image
from datetime import datetime, timedelta
import traceback
from concurrent.futures import ThreadPoolExecutor
import imagehash


COMMON_IMAGE_PATTERNS = ["*.jpg", "*.JPG", "*.png", "*.PNG"]

__author__ = 'Daan Wynen'


def find_images(root_path, patterns):
    for current_folder, subdirs, files in os.walk(os.path.abspath(root_path)):
        for pattern in patterns:
            for filename in fnmatch.filter(files, pattern):
                yield os.path.relpath(os.path.join(current_folder, filename), root_path)


def image_descriptor(image_path, prior=None):
    mtime = os.path.getmtime(image_path)
    ctime = os.path.getctime(image_path)

    if not prior or (not prior.get('modified')):
        img = Image.open(image_path)
        result = {'width': img.size[0],
                  'height': img.size[1],
                  'created': mtime,
                  'modified': ctime,
                  'aHash': str(imagehash.average_hash(img)),
                  'pHash': str(imagehash.phash(img)),
                  'dHash': str(imagehash.dhash(img)),
                  }
        return result

    changed = prior['modified'] < mtime
    img = Image.open(image_path)

    if changed or not prior["width"]:
        prior["width"] = img.size[0 ]
    if changed or not prior["height"]:
        prior["height"] = img.size[1]

    if changed or not prior["aHash"]:
        prior["aHash"] = str(imagehash.average_hash(img))
    if changed or not prior["pHash"]:
        prior["pHash"] = str(imagehash.phash(img))
    if changed or not prior["dHash"]:
        prior["dHash"] = str(imagehash.dhash(img))
    return prior


def read_dict_from_json(filename):
    with open(filename, 'r') as f:
        result = json.load(f, encoding='utf-8')
    return result


def write_dict_to_json(data, filename):
    with io.open(filename, 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(data, ensure_ascii=False, indent=4)))


def _descriptor(root_path, images):
    return lambda (idx, filename_rel): (idx, filename_rel, image_descriptor(os.path.join(root_path, filename_rel), images.get(filename_rel)))


def build_image_db(root_path, db_filename, patterns=COMMON_IMAGE_PATTERNS, resume=True):
    if resume:
        try:
            data = read_dict_from_json(db_filename)
            if data['root_path'] != root_path:
                print("Root paths do not match!")
                sys.exit(1)

            # remove images that have been removed from the library
            img = data["images"]
            for fname in img.keys():
                if not os.path.isfile(os.path.join(root_path, fname)):
                    del img[fname]
            print("Loaded {0} images from old database file.".format(len(data["images"])))

        except:
            print("Could not load prior database. Starting from scratch.")
            data = {'root_path': root_path, "images": {}}
    else:
        data = {'root_path': root_path}
    time_started = datetime.now()
    print("{0}: Starting scan of {1}".format(time_started, root_path))
    filenames = list(find_images(root_path, patterns))
    images_total = len(filenames)
    print("{0}: Found {1} images".format(datetime.now(), images_total))

    images = data["images"]

    try:
        with ThreadPoolExecutor(4) as executor:
            for (idx, filename_rel, desc) in executor.map(_descriptor(root_path, images), enumerate(filenames)):
                images[filename_rel] = desc

                now = datetime.now()
                done = float(idx + 1) / images_total
                time_so_far = (now - time_started).total_seconds()
                eta = timedelta(seconds=time_so_far * (images_total - idx - 1) / float(idx + 1))
                print("{0}: {1:.2f}% ({2} / {3}) ETA: {4} File: {5}"
                      .format(now, done * 100, idx + 1, images_total, eta, filename_rel))

        data["successful"] = True

    except KeyboardInterrupt:
        print("{0}: Caught keyboard interrupt. Aborting."
              .format(datetime.now()))

        data["successful"] = False
    except Exception as e:
        print("Caught Exception. Saving Progress so far.")
        print(e)
        tb = traceback.format_exc()
        print(tb)
        data["successful"] = False

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
