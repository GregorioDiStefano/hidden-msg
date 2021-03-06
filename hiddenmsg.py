import binascii
import logging
import sys
from PIL import Image
import glob
import imghdr
import random
import os
import string
import base64
from PIL import Image

logging.basicConfig(level=logging.CRITICAL,
                    format='%(asctime)s %(name)-6s %(levelname)-2s %(message)s')


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

    """
        Optimize the image size in relation to the payload size
    """
    @staticmethod
    def resize_image_to_datasize(image, tbytes):
        w, h = image.size

        if ((w * h) / 3) < tbytes:
            return image

        for i in range(100, 20, -1):
            percentage = float(i/100.00)
            new_w = int(w * percentage)
            new_h = int(h * percentage)
            new_pixels = new_w * new_h
            bytes_that_fit = int(new_pixels / 3)

            if bytes_that_fit < tbytes:
                #print "Image too small for required bytes, adjusting 5per up"
                return image.resize((int(new_w * 1.01), int(new_h * 1.01)), Image.ANTIALIAS)
        return image.resize((new_w, new_h), Image.ANTIALIAS)

class Decode():

    images_to_decode = []
    images_dir = ""

    def __init__(self, images_to_decode=None, images_dir=None):
        if images_dir:
            self.images_to_decode = self._find_encoded_images(images_dir + "*")
        else:
            self.images_to_decode = images_to_decode or self._find_encoded_images("encoded/*")

    def _find_encoded_images(self, dir):
            files = {}
            for encoded_image in glob.glob(dir):
                    part, length, crc = self._read_pixels(encoded_image, only_meta=True)
                    if not files.get(crc, False):
                        files[crc] = []
                    files[crc].append({"file": encoded_image, "part": part, "length": length})
            return files

    def _read_pixels(self, image, only_meta=False):
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
                payload, _, _ = self._read_pixels(f["file"])
                data += payload
        data = (data[0:length])
        if hex(binascii.crc32(data) & 0xFFFFFFFF) == hex(key):
            return data
        else:
            sys.stdout.write("Fail, data:" + repr(data))
            return False


class Encode():

    data_file = ""
    msg = ""
    msg_hash = ""
    msg_length = 0
    total_payload = ""
    images_to_encode = []
    output_dir = ""

    def __init__(self, data_file = None, base64_data = None, images_to_encode=None, output_dir=None):
        if data_file and base64_data:
            print "You cant specify two data sources!"

        self.data_file = data_file
        self.data_base64 = base64_data
        self.output_dir = output_dir or "encoded/"
        self.images_to_encode = images_to_encode or self._load_images()

    def _load_images(self):
        usable_images = {}
        images = glob.glob("images/*")
        random.shuffle(images)

        for image in images:
            if imghdr.what(image):
                width, height = Image.open(image).size
                usable_images[image] = width * height

        return usable_images

    def _modify_pixels(self, image, data):
        im_open = Utils.resize_image_to_datasize(Image.open(image), len(data)/8)

        im = im_open.load()

        max_x, max_y = im_open.size


        data = Utils.list_of_3(data)

        random_bits = [bin(i)[2:].zfill(3) for i in range(8)]
        iteration = 0

        for x in xrange(0, max_x):
            for y in xrange(0, max_y):

                if 0 <= iteration < len(data):
                    bits = data[iteration]
                else:
                    """
                        Add noise to the rest of the image.
                        Makes encoding a lot slower, but required for good obfsucation.
                    """
                    bits = random.choice(random_bits)

                if len(im[x, y]) == 3:
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
        if self.data_base64:
            self.msg = base64.b64decode(self.data_base64)
        else:
            with open(self.data_file, "r") as myfile:
                self.msg = (myfile.read())

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

        used_images = []
        for count, image in enumerate(images_to_encode):
            if count == 0:
                data_left, im = self._modify_pixels(image, bits)
                used_images.append(im)
            elif data_left:
                data_left = Utils.bytes_to_bits("{:01x}".format(count + 1)) + self.total_bits[8:(17*8)] + data_left
                data_left, im = self._modify_pixels(image, data_left)
                used_images.append(im)

        if data_left:
            logging.critical("oppps, not enough images!")

        if not os.access(self.output_dir, os.W_OK):
            os.mkdir(self.output_dir)


        random_fn = ''.join(random.choice(string.lowercase) for i in range(8)) + "_"
        files_used = []

        for count, used_image in enumerate(used_images):
                filename = random_fn + str(count) + ".png"
                used_image.save(self.output_dir + filename, lossless=True)
                files_used.append(filename)

        return files_used

