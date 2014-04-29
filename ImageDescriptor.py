import imagehash

__author__ = 'daan'


class ImageDescriptor:

    def __init__(self, filename, descriptor):
        # print(filename+" \t"+str(descriptor))
        self.filename = filename
        self.height = descriptor["height"]
        self.width = descriptor["width"]
        self.aHash = imagehash.hex_to_hash(descriptor["aHash"])
        self.pHash = imagehash.hex_to_hash(descriptor["pHash"])
        self.dHash = imagehash.hex_to_hash(descriptor["dHash"])
        self.cTime = descriptor["created"]
        self.mTime = descriptor["modified"]

    def compare(self, other):
        """
        Compare all three hash values and return the hamming distances in a tuple.
        :type other: ImageDescriptor
        """
        return (self.aHash-other.aHash,
                self.pHash-other.pHash,
                self.dHash-other.dHash,
                )
