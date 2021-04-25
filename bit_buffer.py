class BitBuffer:
	def __init__(self, buffer:bytes, offset):
		self.buffer = buffer
		self.offset = offset

	def __getitem__(self, i):
		byte_offset = i // 8
		bit_offset = i % 8
		mask = BitBuffer.get_mask(bit_offset)
		return (self.buffer[self.offset + byte_offset] & mask) >> bit_offset

	def __setitem__(self, i, val):
		byte_offset = i // 8
		bit_offset = i % 8
		mask = BitBuffer.get_mask(bit_offset)
		if val == 0:
			v = self.buffer[self.offset + byte_offset] & ~mask
		elif val == 1:
			v = self.buffer[self.offset + byte_offset] | mask
		else:
			raise
		self.buffer[self.offset + byte_offset] = v

	@staticmethod
	def get_mask(i):
		data = [
			0x01, 0x02, 0x04, 0x08,
			0x10, 0x20, 0x40, 0x80,
		]
		return data[i]