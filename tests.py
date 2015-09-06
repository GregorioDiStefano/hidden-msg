import unittest
import hiddenmsg
import os
import shutil
import random
import string
import glob
import base64

class Helpers(object):

    @staticmethod
    def file_to_data(f):
        with open(f, "r") as myfile:
            return myfile.read()

    @staticmethod
    def cleanup(dir="encoded"):
        try:
            shutil.rmtree(dir)
        except:
            pass

    @staticmethod
    def random_dir():
        dir = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        return dir + '/'

class MyTests(unittest.TestCase):

    def setUp(self):
        Helpers.cleanup()

    def test_lsb_1(self):
        self.assertEqual(0xFF, hiddenmsg.Utils.calculate_lsb(0xFE, 1))

    def test_lsb_2(self):
        self.assertEqual(0xFE, hiddenmsg.Utils.calculate_lsb(0xFE, 0))

    def test_encode_decode_1(self):
        file_to_encode = "test/test-data-1.txt"
        data_to_encode =  Helpers.file_to_data(file_to_encode)

        encode_images = ["test-images/test1/64.png", "test-images/test1/64_1.png"]
        e = hiddenmsg.Encode(data_file = file_to_encode, images_to_encode=encode_images)
        e.encode()
        d = hiddenmsg.Decode()
        self.assertEqual(d.get_data(), data_to_encode)

    def test_encode_decode_2(self):
        file_to_encode = "test/test-data-2.txt"
        data_to_encode =  Helpers.file_to_data(file_to_encode)

        encode_images = ["test-images/test2/64.png", "test-images/test2/huge.png"]
        e = hiddenmsg.Encode(data_file = file_to_encode, images_to_encode=encode_images)
        e.encode()
        d = hiddenmsg.Decode()
        self.assertEqual(d.get_data(), data_to_encode)

    def test_encode_decode_3(self):
        file_to_encode = "test/test-data-3.txt"
        data_to_encode =  Helpers.file_to_data(file_to_encode)

        encode_images = ["test-images/test2/huge.png"]
        e = hiddenmsg.Encode(data_file = file_to_encode, images_to_encode=encode_images)
        e.encode()
        d = hiddenmsg.Decode()
        self.assertEqual(d.get_data(), data_to_encode)

    def test_encode_decode_4_single_byte(self):
        file_to_encode = "test/test-data-4.txt"
        data_to_encode =  Helpers.file_to_data(file_to_encode)

        encode_images = ["test-images/test2/huge.png"]
        e = hiddenmsg.Encode(data_file = file_to_encode, images_to_encode=encode_images)
        e.encode()
        d = hiddenmsg.Decode()
        self.assertEqual(d.get_data(), data_to_encode)

    def test_encode_decode_4_single_byte_small_image(self):
        file_to_encode = "test/test-data-4.txt"
        data_to_encode =  Helpers.file_to_data(file_to_encode)

        encode_images = ["test-images/test2/64.png"]
        e = hiddenmsg.Encode(data_file = file_to_encode, images_to_encode=encode_images)
        e.encode()
        d = hiddenmsg.Decode()
        self.assertEqual(d.get_data(), data_to_encode)

    def test_encode_decode_4_single_byte_huge_image(self):
        file_to_encode = "test/test-data-4.txt"
        data_to_encode =  Helpers.file_to_data(file_to_encode)

        encode_images = ["test-images/test2/huge.png"]
        e = hiddenmsg.Encode(data_file = file_to_encode, images_to_encode=encode_images)
        e.encode()
        d = hiddenmsg.Decode()
        self.assertEqual(d.get_data(), data_to_encode)

    def test_encode_decode_5_huge_zeros(self):
        file_to_encode = "test/200kb_zero.txt"
        data_to_encode =  Helpers.file_to_data(file_to_encode)

        encode_images = ["test-images/test2/huge.png"]
        e = hiddenmsg.Encode(data_file = file_to_encode, images_to_encode=encode_images)
        e.encode()
        d = hiddenmsg.Decode()
        self.assertEqual(d.get_data(), data_to_encode)

    def test_encode_decode_6_huge_random(self):
        file_to_encode = "test/1mb"
        data_to_encode =  Helpers.file_to_data(file_to_encode)

        encode_images = ["test-images/test6/1.jpg", "test-images/test6/2.jpg", "test-images/test6/3.jpg"]
        e = hiddenmsg.Encode(data_file = file_to_encode, images_to_encode=encode_images)
        e.encode()
        d = hiddenmsg.Decode()
        self.assertEqual(d.get_data(), data_to_encode)

    def test_encode_decode_7_specfic_dir(self):
        file_to_encode = "test/test-data-1.txt"
        data_to_encode =  Helpers.file_to_data(file_to_encode)
        random_dir = Helpers.random_dir()

        e = hiddenmsg.Encode(data_file = file_to_encode, output_dir = random_dir)
        e.encode()
        d = hiddenmsg.Decode(images_dir=random_dir)
        self.assertEqual(d.get_data(), data_to_encode)
        Helpers.cleanup(random_dir)

    def test_encode_decode_limited_files(self):
        file_to_encode = "test/test-data-4.txt"
        data_to_encode =  Helpers.file_to_data(file_to_encode)

        encode_images = ["test-images/test6/1.jpg", "test-images/test6/2.jpg", "test-images/test6/3.jpg"]
        e = hiddenmsg.Encode(data_file = file_to_encode, images_to_encode=encode_images)
        e.encode()
        d = hiddenmsg.Decode()
        self.assertEqual(d.get_data(), data_to_encode)
        self.assertTrue(len(glob.glob("encoded/*")) == 1)

    def test_encode_decode_base64_data(self):
        input_base64 = "VGhpcyBpcyBhIHRlc3QgbWVzc2FnZQo="
        expected_output = base64.b64decode(input_base64)

        e = hiddenmsg.Encode(base64_data = input_base64)
        e.encode()
        d = hiddenmsg.Decode()
        self.assertEqual(d.get_data(), expected_output)

if __name__ == '__main__':
    unittest.main()
