import sys
from ImageDescriptor import ImageDescriptor

__author__ = 'daan'
from hashDB import read_dict_from_json, image_descriptor


class SimilarityMatcher:

    def __init__(self, json_filename):
        self.json_filename = json_filename
        self.dictionary = read_dict_from_json(json_filename)
        print("Database {0} loaded.".format(self.json_filename))
        self.images = [ImageDescriptor(f, d) for (f, d) in self.dictionary["images"].items()]
        print("Parsed {0} images into objects".format(len(self.images)))

    def find_similar_images(self, filename_abs, K=3):

        print("Finding closest matches for {0}".format(filename_abs))

        img = ImageDescriptor(filename_abs, image_descriptor(filename_abs))

        print("aHash ranks:")
        sorted_matches = sorted(self.images, key=lambda i: img.aHash-i.aHash)
        sorted_matches = sorted_matches[:K]
        for rank, image in enumerate(sorted_matches):
            print("[{0}] {1}".format(rank, image.filename))

        print("pHash ranks:")
        sorted_matches = sorted(self.images, key=lambda i: img.pHash-i.pHash)
        sorted_matches = sorted_matches[:K]
        for rank, image in enumerate(sorted_matches):
            print("[{0}] {1}".format(rank, image.filename))

        print("dHash ranks:")
        sorted_matches = sorted(self.images, key=lambda i: img.dHash-i.dHash)
        sorted_matches = sorted_matches[:K]
        for rank, image in enumerate(sorted_matches):
            print("[{0}] {1}".format(rank, image.filename))

if __name__ == "__main__":
    json_filename = sys.argv[1]

    matcher = SimilarityMatcher(json_filename)

    for image_filename in sys.argv[2:]:
        matcher.find_similar_images(image_filename)
