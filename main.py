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
    part = 0x00

    for x in xrange(0, max_x):
        for y in xrange(0, max_y):
            r, g, b = im[x, y]
            r_lsb = r & 1
            g_lsb = g & 1
            b_lsb = b & 1
            bits += str(r_lsb) + str(g_lsb) + str(b_lsb)
            if not crc and not length and len(bits) == (9 * 16):
                partial_bytes = bytes(frombits(bits))
                part = int(partial_bytes[0], 16)
                length = int(partial_bytes[1:9], 16)
                crc = int(partial_bytes[9:17], 16)
            if length and len(bits) >= (length) * 10 + (16 * 9):
                break
        else:
            continue
        break

    bytes_from_bits = bytes(frombits(bits))
    payload = bytes_from_bits[16:length + 16]
    print payload
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
                    r = calculate_lsb(r, bits[0])
                if len(bits) >= 2:
                    g = calculate_lsb(g, bits[1])
                if len(bits) >= 3:
                    b = calculate_lsb(b, bits[2])

                im[x, y] = (r, g, b)
            else:
                break
    return im_open


def bytes_to_bits(data):
    bits = ''.join(format(ord(i),'b').zfill(8) for i in data)
    return bits

if __name__ == "__main__":

    print read_pixels("new_0.png")
    sys.exit(-1)


    with open ("data.txt", "r") as myfile:
        msg=myfile.read()
    print len(msg)
    msg_hash = "{:08x}".format(binascii.crc32(msg) & 0xFFFFFFFF)
    msg_length = "{:08x}".format(len(msg))
    part = "{:01x}".format(0)

    total_payload = part + msg_length + msg_hash + msg

    total_bits = bytes_to_bits(total_payload)
    required_pixels = int((len(total_bits) / 3) + 1)

    if len(msg) > 2 ** 32 - 1:
        logging.critical("Huge payload. Try with a smaller filesize!")
        sys.exit(-1)

    logging.debug("Payload: " + total_payload)
    logging.debug("Bits to be written: " + total_bits)
    logging.debug("Pixels required: " + str(required_pixels))

    images_to_encode = load_images(required_pixels)
    last_written_bit = 0

    for count, image in enumerate(images_to_encode):
        bits = bytes_to_bits("{:01x}".format(count)) + total_bits[8:]

        pixels_in_image = images_to_encode[image]

        if pixels_in_image < required_pixels:
            bits = bits[last_written_bit:pixels_in_image * 3]
            last_written_bit = (pixels_in_image * 3)
            #print bits[-200:], "....."
        elif last_written_bit > 0:
            bits = bits[0:(16*8)] + bits[last_written_bit:]
            #print bits[0:200], "..."

        im = modify_pixels(image, bits)
        print "Saving image..."
        im.save("new_" + str(count) + ".png", lossless=True)
        required_pixels -= images_to_encode[image]
