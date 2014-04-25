#! /usr/bin/env python

import sys
import os
import fnmatch
from PIL import Image

COMMON_IMAGE_PATTERNS = ["*.jpg", "*.JPG", "*.png", "*.PNG"]

__author__ = 'daan'


def find_images(root_path, patterns):
    for current_folder, subdirs, files in os.walk(os.path.abspath(root_path)):
        for pattern in patterns:
            for filename in fnmatch.filter(files, pattern):
                yield os.path.relpath(os.path.join(current_folder, filename), root_path)


if __name__ == "__main__":
    root_path = sys.argv[1]
    print("Root: {0}".format(root_path))

    if len(sys.argv) > 2:
        patterns = sys.argv[2:]
    else:
        patterns = COMMON_IMAGE_PATTERNS

    filenames = find_images(root_path, patterns)

    for filename in filenames:
        print(filename)
