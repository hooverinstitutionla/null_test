import os
from unittest import main, TestCase

from null import check_channels, run_command, sixteen_bit

class UnitTests(TestCase):
    valid_mono = 'valid_mono.wav'
    valid_stereo = 'valid_stereo.wav'

    def setUp(self):
        command = ['ffmpeg','-f','lavfi','-i',
            'sine=frequency=1000:duration=5',self.valid_mono]
        run_command(command, '')

        command = ['ffmpeg', '-f', 'lavfi', '-i',
            'sine=frequency=1000:duration=5', '-c:a', 'pcm_s16le',
            '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=5', '-c:a', 'pcm_s16le',
            '-filter_complex', '[0]apad[a];[a][1]amerge[aout]', '-map',
            '[aout]', self.valid_stereo]
        run_command(command, '')

    def tearDown(self):
        os.remove(self.valid_mono)
        os.remove(self.valid_stereo)

    def test_check_channels(self):
        dir1 = os.getcwd()
        channels = check_channels(self.valid_mono, dir1)
        self.assertEqual(channels, 1)
        channels = check_channels(self.valid_stereo, dir1)
        self.assertEqual(channels, 2)

    def test_sixteen_bit_function(self):
        # TODO: write up some mocks for the ffmpeg subprocess.
        test_file = 'test_01.wav'
        sb = sixteen_bit('/', test_file)
        self.assertEqual(sb, 'test_01_16bit.wav')

main()
