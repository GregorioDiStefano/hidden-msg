import unittest
import main
import os
import shutil

class Helpers(object):

    @staticmethod
    def file_to_data(f):
        with open(f, "r") as myfile:
            return myfile.read()

    @staticmethod
    def cleanup():
        shutil.rmtree("encoded")
        os.mkdir("encoded")

class MyTests(unittest.TestCase):

    def setUp(self):
        pass


    def test_lsb_1(self):
        self.assertEqual(0xFF, main.Utils.calculate_lsb(0xFE, 1))

    def test_lsb_2(self):
        self.assertEqual(0xFE, main.Utils.calculate_lsb(0xFE, 0))

    def test_encode_decode_1(self):
        file_to_encode = "test/test-data-1.txt"
        data_to_encode =  Helpers.file_to_data(file_to_encode)

        encode_images = ["test-images/test1/64.png", "test-images/test1/64_1.png"]
        e = main.Encode(file_to_encode, encode_images)
        e.encode()
        d = main.Decode()
        self.assertEqual(d.get_data(), data_to_encode)
        Helpers.cleanup()

    def test_encode_decode_2(self):
        file_to_encode = "test/test-data-2.txt"
        data_to_encode =  Helpers.file_to_data(file_to_encode)

        encode_images = ["test-images/test2/64.png", "test-images/test2/huge.png"]
        e = main.Encode(file_to_encode, encode_images)
        e.encode()
        d = main.Decode()
        self.assertEqual(d.get_data(), data_to_encode)
        Helpers.cleanup()

    def test_encode_decode_3(self):
        file_to_encode = "test/test-data-3.txt"
        data_to_encode =  Helpers.file_to_data(file_to_encode)

        encode_images = ["test-images/test2/huge.png"]
        e = main.Encode(file_to_encode, encode_images)
        e.encode()
        d = main.Decode()
        self.assertEqual(d.get_data(), data_to_encode)
        Helpers.cleanup()

if __name__ == '__main__':
    unittest.main()
