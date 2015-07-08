import unittest
import main

class MyTests(unittest.TestCase):

    def setUp(self):
        pass

    def test_lsb_1(self):
        self.assertEqual(0xFF, main.Utils.calculate_lsb(0xFE, 1))

    def test_lsb_2(self):
        self.assertEqual(0xFE, main.Utils.calculate_lsb(0xFE, 0))


if __name__ == '__main__':
    unittest.main()
