escapeFB
========

Tries to match a set of processed images to their originals withing a known collection.

When downloading the full data dump that facebook provides, the images are not the originals since facebook compresses them.
This tool aims at generating decent html galleries including all the crucial information from the images (comments, likes, locations...) but replacing the processed versions with their originals where they are available.

In order to make minimal assumptions about correct metadata in both the original collection and the exported image files, this is largely done by image hashes (aHash, pHash, dHash) which are precomputed for the collection.
