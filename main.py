import binascii
import logging
import sys
from PIL import Image
import glob
import imghdr
import random

logging.basicConfig(level=logging.CRITICAL,
                    format='%(asctime)s %(name)-6s %(levelname)-2s %(message)s'
                   )


def load_images(needed_bits):
    usable_images = {}
    images = glob.glob("images/*")

    random.shuffle(images)

    for image in images:
        if imghdr.what(image):
            width, height = Image.open(image).size
            needed_bits -= width * height
            usable_images[image] = width * height

            if needed_bits <= 0:
                logging.debug("No need for more images")
                break

    if needed_bits > 0:
        logging.critical("Ouch, not enough images to encode the message in!")
        return []

    return usable_images


def read_pixels(image):

    def frombits(bits):
        chars = []
        for b in range(len(bits) / 8):
            byte = bits[b*8:(b+1)*8]
            chars.append(chr(int(''.join([str(bit) for bit in byte]), 2)))
        return ''.join(chars)

    im_open = Image.open(image)
    im = im_open.load()
    max_x, max_y = im_open.size

    bits = ""
    crc = 0x00
    length = 0x00

    for x in xrange(0, max_x):
        for y in xrange(0, max_y):
            r, g, b = im[x, y]
            r_lsb = r & 1
            g_lsb = g & 1
            b_lsb = b & 1
            bits += str(r_lsb) + str(g_lsb) + str(b_lsb)
            if not crc and not length and len(bits) == (9 * 16):
                partial_bytes = bytes(frombits(bits))
                crc = int(partial_bytes[0:8], 16)
                length = int(partial_bytes[8:16], 16)

            if length and len(bits) >= (length) * 10 + (16 * 9):
                print length, bits
                print frombits(bits)
                break
        else:
            continue
        break

    bytes_from_bits = bytes(frombits(bits))
    payload = bytes_from_bits[16:length + 16]

    if crc == binascii.crc32(payload) & 0xFFFFFFFF:
        print "Extracted successfully."


def modify_pixels(image, data):

    def calculate_lsb(color, last_bit):
        last_bit_on = color & 1
        if last_bit_on and last_bit == '0':
            color = color & ~1 #replace LSB with zero
        elif not last_bit_on and last_bit == '1':
            color = color | 0x01 #set last bit on
        return color

    im_open = Image.open(image)
    im = im_open.load()

    max_x, max_y = im_open.size

    for x in xrange(0, max_x):
        for y in xrange(0, max_y):
            if len(data):
                bits = data[0:3]
                data = data[3:]

                logging.debug("Bits to write to this pixel: " + bits)

                r, g, b = im[x, y]

                if len(bits) >= 1:
                    new_r = calculate_lsb(r, bits[0])
                if len(bits) >= 2:
                    new_g = calculate_lsb(g, bits[1])
                if len(bits) >= 3:
                    new_b = calculate_lsb(b, bits[2])


                im[x, y] = (new_r, new_g, new_b)
            else:
                break
    return im_open

if __name__ == "__main__":


    msg = "This is a secret" * 00001000
    msg_hash = "{:08x}".format(binascii.crc32(msg) & 0xFFFFFFFF)

    if len(msg) > 2 ** 16 - 1:
        logging.critical("Huge payload. Try with a smaller filesize!")
        sys.exit(-1)

    msg_length = "{:08x}".format(len(msg))

    payload = msg_hash + msg_length + msg
    bits = ''.join(format(ord(i),'b').zfill(8) for i in payload)
    required_pixels = int(len(bits) / 3)

    logging.debug("Payload: " + payload)
    logging.debug("Bits to be written: " + bits)
    logging.debug("Pixels required: " + str(required_pixels))

    images_to_encode = load_images(required_pixels)

    for image in images_to_encode:
        if images_to_encode[image] > required_pixels:
            im = modify_pixels(image, bits)
            im.save("new.png", optimize=True)
        else:
            pass


    print read_pixels("new.png")
    sys.exit(-1)
