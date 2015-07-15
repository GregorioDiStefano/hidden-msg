import binascii
import logging
import sys
from PIL import Image
import glob
import imghdr
import random
import zlib

logging.basicConfig(level=logging.CRITICAL,
                    format='%(asctime)s %(name)-6s %(levelname)-2s %(message)s'
                   )

class Utils(object):

    @staticmethod
    def frombits(bits):
        chars = []
        for b in range(len(bits) / 8):
            byte = bits[b*8:(b+1)*8]
            chars.append(chr(int(''.join([str(bit) for bit in byte]), 2)))
        return ''.join(chars)

    @staticmethod
    def bytes_to_bits(data):
        bits = ''.join(format(ord(i), 'b').zfill(8) for i in data)
        return bits

    @staticmethod
    def calculate_lsb(color, last_bit):
        last_bit_on = color & 1
        if last_bit_on and last_bit == 0:
            color = color & ~1
        elif not last_bit_on and last_bit == 1:
            color = color | 0x01
        return color

    @staticmethod
    def list_of_3(s):
        n = 3
        return [s[i:i+n] for i in range(0, len(s), n)]

class Decode():

    images_to_decode = []

    def __init__(self, images_to_decode = None):
        self.images_to_decode = images_to_decode or self.find_encoded_images("images/*")

    def find_encoded_images(self, dir):
            files = {}
            for encoded_image in glob.glob("encoded/*"):
                    part, length, crc = self.read_pixels(encoded_image, only_meta=True)
                    if not files.get(crc, False):
                        files[crc] = []
                    files[crc].append({"file" : encoded_image, "part" : part, "length" : length})
            return files

    def read_pixels(self, image, only_meta=False):
        im_open = Image.open(image)
        im = im_open.load()
        max_x, max_y = im_open.size

        bits = ""
        crc = 0x00
        length = 0x00
        part = 0x00

        for x in xrange(0, max_x):
            for y in xrange(0, max_y):
                if len(im[x, y]) == 3:
                    r, g, b = im[x, y]
                else:
                    r, g, b, _ = im[x, y]
                r_lsb = r & 1
                g_lsb = g & 1
                b_lsb = b & 1
                bits += str(r_lsb) + str(g_lsb) + str(b_lsb)
                if not crc and not length and len(bits) >= (9 * 16):
                    partial_bytes = bytes(Utils.frombits(bits))
                    part = int(partial_bytes[0], 16)
                    length = int(partial_bytes[1:9], 16)
                    crc = int(partial_bytes[9:17], 16)
                if crc and len(bits) > (length) * 10 + (16 * 9):
                    break
            else:
                continue
            break

        bytes_from_bits = bytes(Utils.frombits(bits))
        payload = bytes_from_bits[17:length + 16 + 8]

        if only_meta:
            return part, length, crc

        return payload, length, crc

    def get_data(self):
        data = ""
        length = ""

        for key in self.images_to_decode.keys():
            sorted_by_part = sorted(self.images_to_decode[key], key=lambda k: k['part'])
            length = self.images_to_decode[key][0]["length"]
            for f in sorted_by_part:
                payload, _, _ = self.read_pixels(f["file"])
                data += payload
        data = (data[0:length])
        if hex(binascii.crc32(data) & 0xFFFFFFFF) == hex(key):
            return data
        else:
            sys.stdout.write("Fail, data:" + repr(data))

class Encode():

    data_file = ""
    msg = ""
    msg_hash = ""
    msg_length = 0
    total_payload = ""
    images_to_encode = []

    def __init__(self, data_file, images_to_encode=None):
        self.data_file = data_file
        self.images_to_encode =  images_to_encode or self.load_images()

    def load_images(self):
        usable_images = {}
        images = glob.glob("images/*")

        random.shuffle(images)

        for image in images:
            if imghdr.what(image):
                width, height = Image.open(image).size
                usable_images[image] = width * height

        return usable_images


    def modify_pixels(self, image, data):
        im_open = Image.open(image)
        im = im_open.load()

        max_x, max_y = im_open.size
        data = Utils.list_of_3(data)

        iteration = 0

        for x in xrange(0, max_x):
            for y in xrange(0, max_y):

                if 0 <= iteration < len(data):
                    bits = data[iteration]
                else:
                    bits = random.choice(["000", "001", "010", "011", "100", "101", "111", "110"])

                if len(im[x,y]) == 3:
                    r, g, b = im[x, y]
                else:
                    r, g, b, _ = im[x, y]

                if len(bits) >= 1:
                    r = Utils.calculate_lsb(r, int(bits[0]))
                if len(bits) >= 2:
                    g = Utils.calculate_lsb(g, int(bits[1]))
                if len(bits) >= 3:
                    b = Utils.calculate_lsb(b, int(bits[2]))
                im[x, y] = (r, g, b)
                iteration += 1

        data_left = "".join(data[iteration:])
        return data_left, im_open

    def encode(self):

        with open (self.data_file, "r") as myfile:
            self.msg=(myfile.read())

        self.msg_hash = "{:08x}".format(binascii.crc32(self.msg) & 0xFFFFFFFF)
        self.msg_length = "{:08x}".format(len(self.msg))
        self.part = "{:01x}".format(0)

        self.total_payload = self.part + self.msg_length + self.msg_hash + self.msg

        self.total_bits = Utils.bytes_to_bits(self.total_payload)

        if len(self.msg) > 2 ** 32 - 1:
            logging.critical("Huge payload. Try with a smaller filesize!")
            sys.exit(-1)

        logging.debug("Payload: " + self.total_payload)
        logging.debug("Bits to be written: " + self.total_bits)

        images_to_encode = self.images_to_encode

        bits = Utils.bytes_to_bits("{:01x}".format(0)) + self.total_bits[8:]
        for count, image in enumerate(images_to_encode):
            if count == 0:
                data_left, im = self.modify_pixels(image, bits)

            elif data_left:
                data_left = Utils.bytes_to_bits("{:01x}".format(count + 1)) + self.total_bits[8:(17*8)] + data_left
                data_left, im = self.modify_pixels(image, data_left)

            im.save("encoded/" + "new_" + str(count) + ".png", lossless=True)

        if data_left:
            logging.critical("oppps, not enough images!")

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "read":
        decode = Decode()
        print decode.get_data()
        sys.exit(-1)
    else:
        a = Encode("data.txt")
        a.encode()
