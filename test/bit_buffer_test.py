import unittest
from bit_buffer import BitBuffer

class TestBitBuffer(unittest.TestCase):
    def test_read(self):
        buffer = bytearray(1)
        buffer[0] = 0b10101010
        bit_buffer = BitBuffer(buffer, 0)
        for i in range(4):
            self.assertEqual(bit_buffer[i*2], 0)
            self.assertEqual(bit_buffer[i*2 + 1], 1)

    def test_write(self):
        buffer = bytearray(1)
        bit_buffer = BitBuffer(buffer, 0)
        for i in range(4):
            bit_buffer[i*2] = 0
            bit_buffer[i*2+1] = 1
        self.assertEqual(buffer[0], 0b10101010)

    def test_offset(self):
        buffer = bytearray(2)
        bit_buffer = BitBuffer(buffer, 1)
        bit_buffer[0] = 1
        self.assertEqual(buffer[0], 0)
        self.assertEqual(buffer[1], 1)

if __name__ == '__main__':
    unittest.main()
