#! /usr/bin/env python3
import os
import sys

from ImageDescriptor import ImageDescriptor

__author__ = 'daan'
from hashDB import read_dict_from_json, image_descriptor


def sum_of_differences(img, i):
    """
    Calculates the sum of all hashes' hamming distances for the two images.
    :type img: ImageDescriptor
    :type i: ImageDescriptor
    """
    return (i.aHash - img.aHash) + (i.pHash - img.pHash) + (i.dHash - img.dHash)


class SimilarityMatcher:
    def __init__(self, json_filename):
        self.json_filename = json_filename
        self.dictionary = read_dict_from_json(json_filename)
        print("Database {0} loaded.".format(self.json_filename))
        self.images = [ImageDescriptor(f, d) for (f, d) in self.dictionary["images"].items()]
        print("Parsed {0} images into objects".format(len(self.images)))

    def find_similar_images(self, filename_abs, root_path="", K=1):
        # print("Finding closest matches for {0}".format(filename_abs))

        img = ImageDescriptor(filename_abs, image_descriptor(filename_abs))

        # print("aHash ranks:")
        # sorted_matches_aHash = sorted(self.images, key=lambda i: img.aHash-i.aHash)
        # sorted_matches_aHash = sorted_matches_aHash[:K]
        # for rank, image in enumerate(sorted_matches_aHash):
        #     print("[{0}] {1}".format(rank, image.filename))
        #
        # print("pHash ranks:")
        # sorted_matches_pHash = sorted(self.images, key=lambda i: img.pHash-i.pHash)
        # sorted_matches_pHash = sorted_matches_pHash[:K]
        # for rank, image in enumerate(sorted_matches_pHash):
        #     print("[{0}] {1}".format(rank, image.filename))
        #
        # print("dHash ranks:")
        # sorted_matches_dHash = sorted(self.images, key=lambda i: img.dHash-i.dHash)
        # sorted_matches_dHash = sorted_matches_dHash[:K]
        # for rank, image in enumerate(sorted_matches_dHash):
        #     print("[{0}] {1}".format(rank, image.filename))

        # print("sum of differences ranks:")
        sorted_matches_combined = sorted(self.images, key=lambda i: sum_of_differences(img, i))
        # sorted_matches_combined = sorted_matches_combined[:K]
        # for rank, image in enumerate(sorted_matches_combined):
        #     print("{0} --> {1}".format(img.filename, image.filename))

        best_aHash = min(self.images, key=lambda i: img.aHash - i.aHash)
        best_pHash = min(self.images, key=lambda i: img.pHash - i.pHash)
        best_dHash = min(self.images, key=lambda i: img.dHash - i.dHash)

        best_matches = [best_aHash, best_pHash, best_dHash]

        best_voted = max(best_matches, key=lambda i: best_matches.count(i))
        best_votes = best_matches.count(best_voted)

        # print("{0} -- {1} --> {2}".format(img.filename, best_votes, os.path.join(root_path, best_voted.filename)))

        return best_votes, os.path.join(root_path, best_voted.filename)


if __name__ == "__main__":

    json_filename = sys.argv[1]

    matcher = SimilarityMatcher(json_filename)

    results = []

    for image_filename in sorted(sys.argv[2:]):
        votes, result = matcher.find_similar_images(image_filename, root_path=matcher.dictionary["root_path"])
        results.append({"votes": votes, "fb_image": image_filename, "original_image": result})

    results = sorted(results, key=lambda r: r["votes"], reverse=True)

    print("all images matched")

    from jinja2 import Template

    with open("template.html", "r") as f:
        template_txt = "\n".join(f.readlines())
    template = Template(template_txt)

    print("loaded template")

    rendered = template.render(
        results=results
    )

    print("rendered html")

    with open("matching.html", "w") as f:
        f.write(rendered)

    print("done")
