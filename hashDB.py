#! /usr/bin/env python3

import json
import sys
import os
import fnmatch
from PIL import Image, ImageFile
from datetime import datetime, timedelta
import traceback
from concurrent.futures import ThreadPoolExecutor
import imagehash

# be more flexible when processing bad images
ImageFile.LOAD_TRUNCATED_IMAGES = True


WORKER_THREADS = 4

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
        prior["width"] = img.size[0]
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
    with open(filename, 'r', encoding='utf-8') as f:
        result = json.load(f, encoding='utf-8')
    return result


def write_dict_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))


def build_image_db(root_path, db_filename, patterns=COMMON_IMAGE_PATTERNS, resume=True, save_every=600):
    if resume:
        try:
            data = read_dict_from_json(db_filename)
            if not os.path.samefile(data['root_path'], root_path):
                print("Root paths do not match!")
                sys.exit(1)

            print("Loaded {0} images from old database file.".format(len(data["images"])))

            # remove images that have been removed from the library
            img = data["images"]
            bad = []
            for fname in img.keys():
                if not os.path.isfile(os.path.join(root_path, fname)):
                    bad.append(fname)
            for fname in bad:
                del img[fname]
            print("Removed {0} non-existing images, left with {1} that could be skipped".format(len(bad), len(img)))

        except SystemExit:
            raise

        except Exception as e:
            print("Could not load prior database ({0}). Starting from scratch.".format(e))
            data = {'root_path': root_path, "images": {}}
    else:
        data = {'root_path': root_path}


    def write_result():
        '''helper to write results'''
        time_finished = datetime.now()
        time_taken = time_finished - time_started

        if (data["finished"]):
            print("{0}: Scan finished, took {1}".format(time_finished, time_taken))
        else:
            print("{0}: Saving {1} intermediate results after {2}"
                  .format(time_finished, len(data["images"]), time_taken))
        data["timing"] = {
            "scan_start": str(time_started),
            "scan_end": str(time_finished),
            "scan_duration": str(time_taken),
        }

        print("{0}: Writing resulting database to {1}".format(datetime.now(), db_filename))
        write_dict_to_json(data, db_filename)

    time_started = datetime.now()
    print("{0}: Starting scan of {1}".format(time_started, root_path))
    filenames = list(find_images(root_path, patterns))
    images_total = len(filenames)
    images = data["images"]
    images_prior = len(data["images"])
    print("{0}: Found {1} images ({2} new)".format(datetime.now(), images_total, images_total - images_prior))

    data["finished"] = False
    data["successful"] = True

    last_checkpoint = 0

    def descriptor_helper(t):
        """return tuple containing the index, a flag that is true if
        there was prior data, filename, and the actual descriptor"""

        idx, filename_rel = t

        result = {'idx': idx, # index of the image
                  'had_prior': filename_rel in images, # True iff we had prior information on the image
                  'filename': filename_rel, # relative file name
                  'descriptor': image_descriptor(os.path.join(root_path, filename_rel), images.get(filename_rel)) # the actual descriptor
        }

        return result

    processed = 0
    time_spent = timedelta(0)
    try:
        with ThreadPoolExecutor(WORKER_THREADS) as executor:
            for datapoint in executor.map(descriptor_helper, enumerate(filenames)):

                filename_rel = datapoint["filename"]
                desc = datapoint["descriptor"]
                idx = datapoint["idx"]
                had_prior = datapoint["had_prior"]

                images[filename_rel] = desc

                now = datetime.now()
                done = float(idx + 1) / images_total
                time_so_far = (now - time_started)
                seconds_so_far = time_so_far.total_seconds()

                # save temporary progress, just to be sure
                if int(seconds_so_far / save_every) > last_checkpoint:
                    write_result()
                    last_checkpoint = int(seconds_so_far / save_every)

                # if this image had prior information then it cannot be counted as an advantage as of now
                if had_prior:
                    images_prior -= 1
                else:
                    processed += 1

                images_left = images_total - images_prior - processed
                processing_time_avg = seconds_so_far / float(processed) if processed != 0 else 0
                eta = timedelta(seconds=images_left * processing_time_avg)
                print("{0}: {1:.2f}% ({2} / {3}) ETA: {4} File: {5}"
                      .format(now, done * 100, idx + 1, images_total, eta, filename_rel))

        data["finished"] = True
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

    write_result()

    print("FINISHED\n")


if __name__ == "__main__":
    root_path = sys.argv[1]
    db_filename = sys.argv[2]

    print("Starting database build...")
    build_image_db(root_path, db_filename)
