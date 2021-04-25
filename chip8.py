import random
import struct
import winsound

from font import Font
from opcode import OpcodeData, OpcodeDesc
from bit_buffer import BitBuffer

# Memory layout
# ----------0x1000------------
# |       Frame buffer       |
# ----------0xf00-------------
# |         Stack            |
# ..........0xea0.............
# |         Code             |
# ----------0x200-------------
# |       Reserved           |
# ----------0x052-------------
# |        Keyboard          |
# ----------0x050-------------
# |         Font             |
# ----------0x000-------------

class HardFaultError(BaseException):
   def __init__(self, msg):
      self.msg = msg

class _Handler:
    def __init__(self, handler, get_desc):
        self.handler = handler
        self.get_desc = get_desc


class Chip8Emulator:
    def __init__(self, code):
        self.screen_width = 64
        self.screen_height = 32
        self.pending_clear_screren_buffer = bytearray(
            self.screen_width * self.screen_height)
        self.needs_to_redraw = True
        # Registers
        self.registers = bytearray(16)
        self.I = 0
        self.pc = 0x200
        self.sp = 0xea0
        # RAM
        self.ram = bytearray(0x1000)
        self.screen_buffer = BitBuffer(self.ram, 0xf00)
        self.key_buffer = BitBuffer(self.ram, 0x50)
        # Timer
        self.delay_count = 0
        self.sound_count = 0

        self.ram[self.pc:self.pc + len(code)] = code

        self.opcode_handler = {
            0x0: _Handler(self._clear_or_return, OpcodeDesc.clear_or_return),
            0x1: _Handler(self._jump, OpcodeDesc.jump),
            0x2: _Handler(self._call_subroutine, OpcodeDesc.call_subroutine),
            0x3: _Handler(self._skip_if_x_equal, OpcodeDesc.skip_if_x_equal),
            0x4: _Handler(self._skip_if_x_not_equal, OpcodeDesc.skip_if_x_not_equal),
            0x5: _Handler(self._skip_if_x_equal_to_y, OpcodeDesc.skip_if_x_equal_to_y),
            0x6: _Handler(self._set_x, OpcodeDesc.set_x),
            0x7: _Handler(self._add_x, OpcodeDesc.add_x),
            0x8: _Handler(self._arithmetic, OpcodeDesc.arithmetic),
            0x9: _Handler(self._skip_if_x_not_equal_to_y, OpcodeDesc.skip_if_x_not_equal_to_y),
            0xa: _Handler(self._set_I, OpcodeDesc.set_I),
            0xb: _Handler(self._jump_with_offset, OpcodeDesc.jump_with_offset),
            0xc: _Handler(self._rnd, OpcodeDesc.rnd),
            0xd: _Handler(self._draw_sprite, OpcodeDesc.draw_sprite),
            0xe: _Handler(self._skip_on_key, OpcodeDesc.skip_on_key),
            0xf: _Handler(self._misc, OpcodeDesc.misc),
        }

        self.misc_opcode_handler = {
            0x07: self._set_x_to_delay,
            0x0a: self._wait_for_key,
            0x15: self._set_delay,
            0x18: self._set_sound,
            0x1e: self._add_to_I,
            0x29: self._set_I_for_char,
            0x33: self._binary_coded_decimal,
            0x55: self._save_x,
            0x65: self._load_x,
        }

        self._init_font()

    def reset(self):
        print('Reset')

    def key_down(self, key):
        self.key_buffer[key] = 1

    def key_up(self, key):
        self.key_buffer[key] = 0

    def get_key_status(self):
        buffer = []
        for i in range(16):
            buffer.append(self.key_buffer[i])
        return buffer

    def run_loop(self):
        opcode = struct.unpack_from('>H', self.ram, self.pc)[0]
        self.pc += 2
        data = OpcodeData(opcode)
        something = opcode >> 12
        if something in self.opcode_handler:
            return self.opcode_handler[something].handler(data)
        else:
            raise HardFaultError(f'Unknown opcode : {opcode}')

    def get_description(self, opcode):
        data = OpcodeData(opcode)
        something = opcode >> 12
        return self.opcode_handler[something].get_desc(data)

    def tick60Hz(self):
        if self.delay_count > 0:
            self.delay_count -= 1
        if self.sound_count > 0:
            self.sound_count -= 1
            if self.sound_count == 0:
                winsound.Beep(32000, 100)
        

    def _init_font(self):
        ptr = 0
        arr = [
            Font.D0, Font.D1, Font.D2, Font.D3,
            Font.D4, Font.D5, Font.D6, Font.D7,
            Font.D8, Font.D9, Font.DA, Font.DB,
            Font.DC, Font.DD, Font.DE, Font.DF,
        ]

        for font in arr:
            self.ram[ptr + 0] = (font & 0xF000000000) >> (8 * 4)
            self.ram[ptr + 1] = (font & 0x00F0000000) >> (8 * 3)
            self.ram[ptr + 2] = (font & 0x0000F00000) >> (8 * 2)
            self.ram[ptr + 3] = (font & 0x000000F000) >> (8 * 1)
            self.ram[ptr + 4] = (font & 0x00000000F0) >> (8 * 0)
            ptr += 5

    def _push(self, value):
        struct.pack_into('>H', self.ram, self.sp, value)
        self.sp += 2

    def _pop(self):
        self.sp -= 2
        return struct.unpack_from('>H', self.ram, self.sp)[0]

    def _clear_or_return(self, data):
        if data.NN == 0xe0:
            for i in range(self.screen_width * self.screen_height):
                self.screen_buffer[i] = 0
        elif data.NN == 0xee:
            self.pc = self._pop()
        else:
            raise HardFaultError(f'Unknown opcode, data.NN = {data.NN:X}')

    def _jump(self, data):
        self.pc = data.NNN

    def _call_subroutine(self, data):
        self._push(self.pc)
        self.pc = data.NNN

    def _skip_if_x_equal(self, data):
        if self.registers[data.X] == data.NN:
            self.pc += 2

    def _skip_if_x_not_equal(self, data):
        if self.registers[data.X] != data.NN:
            self.pc += 2

    def _skip_if_x_equal_to_y(self, data):
        if self.registers[data.X] == self.registers[data.Y]:
            self.pc += 2

    def _set_x(self, data):
        self.registers[data.X] = data.NN

    def _add_x(self, data):
        if self.registers[data.X] + data.NN > 0xff:
            self.registers[data.X] = self.registers[data.X] + data.NN - 0x100
        else:
            self.registers[data.X] += data.NN

    def _arithmetic(self, data):
        reg = self.registers
        if data.N == 0x00:
            reg[data.X] = reg[data.Y]
        elif data.N == 0x01:
            reg[data.X] |= reg[data.Y]
        elif data.N == 0x02:
            reg[data.X] &= reg[data.Y]
        elif data.N == 0x03:
            reg[data.X] ^= reg[data.Y]
        elif data.N == 0x04:
            if reg[data.X] + reg[data.Y] > 0xff:
                reg[0xf] = 1
            else:
                reg[0xf] = 0
            reg[data.X] = (reg[data.X] + reg[data.Y]) & 0xff
        elif data.N == 0x05:
            reg[0xf] = 1 if reg[data.X] > reg[data.Y] else 0
            reg[data.X] = (reg[data.X] - reg[data.Y]) & 0xff
        elif data.N == 0x06:
            reg[0xf] = 1 if ((reg[data.X] & 0x01) != 0) else 0
            reg[data.Y] >>= 1
        elif data.N == 0x07:
            reg[0xf] = 1 if reg[data.Y] > reg[data.X] else 0
            reg[data.Y] = (reg[data.Y] - reg[data.X]) & 0xff
        elif data.N == 0x0e:
            reg[0xf] = 1 if (reg[data.X] & 0xf) != 0 else 0
            reg[data.X] = (reg[data.X] << 1) & 0xff
        else:
            raise HardFaultError(f'Invalid data.N({data.N} in arithmetic')

    def _skip_if_x_not_equal_to_y(self, data):
        if self.registers[data.X] != self.registers[data.Y]:
            self.pc += 2

    def _set_I(self, data):
        self.I = data.NNN

    def _jump_with_offset(self, data):
        self.pc = data.NNN + self.registers[0]

    def _rnd(self, data):
        self.registers[data.X] = random.randint(0, 0xff) & data.NN

    def _draw_sprite(self, data):
        start_x = self.registers[data.X]
        start_y = self.registers[data.Y]
        self.registers[0xf] = 0
        for i in range(data.N):
            sprite_line = self.ram[self.I + i]

            for bit in range(8):
                x = (start_x + bit) % self.screen_width
                y = (start_y + i) % self.screen_height

                index = y * self.screen_width + x
                sprite_bit = (sprite_line >> (7 - bit)) & 1
                old_bit = self.screen_buffer[index]

                if old_bit != sprite_bit:
                    self.needs_to_redraw = True

                new_bit = old_bit ^ sprite_bit

                if new_bit != 0:
                    self.screen_buffer[index] = 1
                else:
                    self.screen_buffer[index] = 0
                if old_bit != 0 and new_bit == 0:
                    self.registers[0xf] = 1

    def _skip_on_key(self, data):
        x = self.registers[data.X]
        if data.NN == 0x9e and self.key_buffer[x]:
            self.pc += 2
        elif data.NN == 0xa1 and not self.key_buffer[x]:
            self.pc += 2

    def _misc(self, data):
        if data.NN in self.misc_opcode_handler:
            self.misc_opcode_handler[data.NN](data)
        else:
            raise HardFaultError(f'Unknow misc opcode, data.NN = {data.NN}')

    def _set_x_to_delay(self, data):
        self.registers[data.X] = self.delay_count

    def _wait_for_key(self, data):
        find = False
        for i in range(16):
            if self.key_buffer[i]:
                self.registers[data.X] = i
                find = True
                break
        if not find:
            self.pc -= 2

    def _set_delay(self, data):
        self.delay_count = self.registers[data.X]

    def _set_sound(self, data):
        self.sound_count = self.registers[data.X]

    def _add_to_I(self, data):
        self.I += self.registers[data.X]

    def _set_I_for_char(self, data):
        self.I = self.registers[data.X] * 5

    def _binary_coded_decimal(self, data):
        self.ram[self.I + 0] = (self.registers[data.X] // 100) % 10
        self.ram[self.I + 1] = (self.registers[data.X] // 10) % 10
        self.ram[self.I + 2] = (self.registers[data.X] // 1) % 10

    def _save_x(self, data):
        for i in range(data.X + 1):
            self.ram[self.I + i] = self.registers[i]

    def _load_x(self, data):
        for i in range(data.X + 1):
            self.registers[i] = self.ram[self.I + i]
