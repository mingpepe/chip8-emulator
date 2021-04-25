class OpcodeData:
    def __init__(self, opcode):
        self.opcode = opcode
        self.NNN = opcode & 0xfff
        self.NN = opcode & 0xff
        self.N = opcode & 0xf
        self.X = (opcode & 0xf00) >> 8
        self.Y = (opcode & 0xf0) >> 4

class OpcodeDesc:
    @staticmethod
    def clear_or_return(data):
        if data.NN == 0xe0:
            return 'Clear screen buffer'
        elif data.NN == 0xee:
            return 'PC = stack top'
        else:
            return f'Unknown opcode, data.NN = {data.NN:X}'

    @staticmethod
    def jump(data):
        return f'Jump : PC = {data.NNN:x}'

    @staticmethod
    def call_subroutine(data):
        return f'Call subroutine : PC = {data.NNN:x}'

    @staticmethod
    def skip_if_x_equal(data):
        return f'Skip if x equal : X = {data.X:x}, NN = {data.NN:x}'

    @staticmethod
    def skip_if_x_not_equal(data):
        return f'Skip if x not equal : X = {data.X:x}, NN = {data.NN:x}'

    @staticmethod
    def skip_if_x_equal_to_y(data):
        return f'Skip if x == y : X = {data.X:x}, Y = {data.Y:x}'

    @staticmethod
    def set_x(data):
        return f'Set x : X = {data.X:x}, NN = {data.NN:X}'

    @staticmethod
    def add_x(data):
        return f'Add x : X = {data.X:x}, NN = {data.NN:x}'

    @staticmethod
    def arithmetic(data):
        return 'arithmetic'

    @staticmethod
    def skip_if_x_not_equal_to_y(data):
        return f'Skip if reg[{data.X:x}] != reg[{data.Y:x}]'

    @staticmethod
    def set_I(data):
        return f'I = {data.NNN:x}'

    @staticmethod
    def jump_with_offset(data):
        return f'Jump with offset, PC = {data.NNN:x} + reg[0]'

    @staticmethod
    def rnd(data):
        return f'reg[{data.X:x}] = rand() % {data.NN:x}'

    @staticmethod
    def draw_sprite(data):
        return 'draw sprite'

    @staticmethod
    def skip_on_key(data):
        return 'Skip on key'

    @staticmethod
    def misc(data):
        misc_opcode_get_desc = {
            0x07: OpcodeDesc.set_x_to_delay,
            0x0a: OpcodeDesc.wait_for_key,
            0x15: OpcodeDesc.set_delay,
            0x18: OpcodeDesc.set_sound,
            0x1e: OpcodeDesc.add_to_I,
            0x29: OpcodeDesc.set_I_for_char,
            0x33: OpcodeDesc.binary_coded_decimal,
            0x55: OpcodeDesc.save_x,
            0x65: OpcodeDesc.load_x,
        }
        if data.NN in misc_opcode_get_desc:
            return misc_opcode_get_desc[data.NN](data)
        else:
            return 'Unknown misc opcode'

    @staticmethod
    def set_x_to_delay(data):
        return f'reg[{data.X}] = delay count'

    @staticmethod
    def wait_for_key(data):
        return 'get_key()'
    
    @staticmethod
    def set_delay(data):
        return f'delay count = reg[{data.X}]'

    @staticmethod
    def set_sound(data):
        return f'sound count = reg[{data.X}]'

    @staticmethod
    def add_to_I(data):
        return f'I += reg[{data.X}]'

    @staticmethod
    def set_I_for_char(data):
        return f'I = reg[{data.X}] * 5(font size)'

    @staticmethod
    def binary_coded_decimal(data):
        return f'set_BCD(V{data.X})'

    @staticmethod
    def save_x(data):
        return f'reg_dump(V{data.X},&I)'

    @staticmethod
    def load_x(data):
        return f'reg_load(V{data.X},&I)'

    
