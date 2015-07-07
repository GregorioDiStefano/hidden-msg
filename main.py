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
        if last_bit_on and last_bit == '0':
            color = color & ~1
        elif not last_bit_on and last_bit == '1':
            color = color | 0x01
        return color

def load_images():
    usable_images = {}
    images = glob.glob("images/*")

    random.shuffle(images)

    for image in images:
        if imghdr.what(image):
            width, height = Image.open(image).size
            usable_images[image] = width * height

    return usable_images


def read_pixels(image, only_meta=False):

    im_open = Image.open(image)
    im = im_open.load()
    max_x, max_y = im_open.size

    bits = ""
    crc = 0x00
    length = 0x00
    part = 0x00

    for x in xrange(0, max_x):
        for y in xrange(0, max_y):
            r, g, b = im[x, y]
            r_lsb = r & 1
            g_lsb = g & 1
            b_lsb = b & 1
            bits += str(r_lsb) + str(g_lsb) + str(b_lsb)
            if not crc and not length and len(bits) >= (9 * 16):
                partial_bytes = bytes(Utils.frombits(bits))
                part = int(partial_bytes[0], 16)
                length = int(partial_bytes[1:9], 16)
                crc = int(partial_bytes[9:17], 16)
            if crc and len(bits) >= (length) * 10 + (16 * 9):
                    break
        else:
            continue
        break

    bytes_from_bits = bytes(Utils.frombits(bits))
    payload = bytes_from_bits[17:length + 16]

    if only_meta:
        return part, length, crc

    return payload, length, crc

def modify_pixels(image, data):


    im_open = Image.open(image)
    im = im_open.load()

    max_x, max_y = im_open.size

    for x in xrange(0, max_x):
        for y in xrange(0, max_y):
            if len(data):
                bits = data[0:3]
                data = data[3:]
            else:
                break

            if len(bits):
                logging.debug("Bits to write to this pixel: " + bits)

                r, g, b = im[x, y]

                if len(bits) >= 1:
                    r = Utils.calculate_lsb(r, bits[0])
                if len(bits) >= 2:
                    g = Utils.calculate_lsb(g, bits[1])
                if len(bits) >= 3:
                    b = Utils.calculate_lsb(b, bits[2])
                im[x, y] = (r, g, b)
            else:
                break

    data_left = data
    return data_left, im_open



def find_encoded_images(dir):
        files = {}
        for encoded_image in glob.glob("encoded/*"):
                part, length, crc = read_pixels(encoded_image, only_meta=True)
                if not files.get(crc, False):
                    files[crc] = []
                files[crc].append({"file" : encoded_image, "part" : part, "length" : length})
        return files

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "read":
        encoded_files = find_encoded_images("encoded/*")
        data = ""
        length = ""

        for key in encoded_files.keys():
            sorted_by_part = sorted(encoded_files[key], key=lambda k: k['part'])
            length = encoded_files[key][0]["length"]
            for f in sorted_by_part:
                payload, _, _ = read_pixels(f["file"])
                data += payload
        print sorted_by_part
        if hex(binascii.crc32(data[0:length]) & 0xFFFFFFFF) == hex(key):
            sys.stdout.write(zlib.decompress(data[0:length]))
        else:
            sys.stdout.write(zlib.decompress(data[0:length]))
        sys.exit(-1)


    with open ("data.txt", "r") as myfile:
        msg=zlib.compress(myfile.read())
    print repr(msg)
    msg_hash = "{:08x}".format(binascii.crc32(msg) & 0xFFFFFFFF)
    print msg_hash
    msg_length = "{:08x}".format(len(msg))
    part = "{:01x}".format(0)

    total_payload = part + msg_length + msg_hash + msg

    total_bits = Utils.bytes_to_bits(total_payload)
    required_pixels = int((len(total_bits) / 3))

    if len(msg) > 2 ** 32 - 1:
        logging.critical("Huge payload. Try with a smaller filesize!")
        sys.exit(-1)

    logging.debug("Payload: " + total_payload)
    logging.debug("Bits to be written: " + total_bits)
    logging.debug("Pixels required: " + str(required_pixels))

    images_to_encode = load_images()

    bits = Utils.bytes_to_bits("{:01x}".format(0)) + total_bits[8:]

    for count, image in enumerate(images_to_encode):
        if count == 0:
            data_left, im = modify_pixels(image, bits)

        elif data_left:
            data_left = Utils.bytes_to_bits("{:01x}".format(count + 1)) + total_bits[8:(17*8)] + data_left
            print "Data left: ", Utils.frombits(data_left)
            data_left , im = modify_pixels(image, data_left)

        im.save("encoded/" + "new_" + str(count) + ".png", lossless=True)

        if not data_left:
            break

    if data_left:
        print "Oppps, not enough images!"
