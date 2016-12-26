import os
from unittest import main, TestCase

from null_test.null import AFile, sixteen_bit

class UnitTests(TestCase):
    def setUp(self):
        self.terminal = AFile()
        self.terminal.open_file('test.txt')

    def tearDown(self):
        self.terminal.close_file()
        os.remove('test.txt')

    def test_sixteen_bit_function(self):
        # TODO: write up some mocks for the ffmpeg subprocess.
        test_file = 'test_01.wav'
        sb = sixteen_bit('/', test_file, self.terminal)
        self.assertEqual(sb, 'test_01_16bit.wav')

main()
