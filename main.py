import time
import string
from enum import Enum

import pygame

from chip8 import Chip8Emulator, HardFaultError
from color import Color

class EmulatorControlType(Enum):
    HELP = -1
    MAIN = 0
    INSTRUCTION = 1
    REGISTER = 2
    MEMORY = 3

class Emulator:
    def __init__(self, machine, width, height, screen_scale, caption):
        self.machine = machine
        self.width = width
        self.height = height
        self.screen_scale = screen_scale
        self.control_type = EmulatorControlType.MAIN
        pygame.init()
        self.clock = pygame.time.Clock()

        pygame.display.set_caption(caption)
        self.screen = pygame.display.set_mode((width, height))

        self.font_size = 20
        self.font = pygame.font.Font('resources\\Anonymous_Pro.ttf', self.font_size)
        self.help_screen = pygame.Surface((width, height))
        self.chip_screen_scale = pygame.Surface((machine.screen_width * screen_scale, machine.screen_height * screen_scale))
        self.chip_screen = pygame.Surface((machine.screen_width, machine.screen_height))
        self.keyboard_screen = pygame.Surface((80, self.chip_screen_scale.get_height()))
        self.main_screen = pygame.Surface((width // 2, height // 2))
        self.memory_screen = pygame.Surface((width // 2, height // 2))
        self.register_screen = pygame.Surface((width // 2, height // 2))
        self.instruction_screen = pygame.Surface((width // 2, height // 2))

        self.memory_address = 0
        self.memory_address_text = '0000'
        self.step = False
        self.fps = 0
        self.target_fps = 180
        self.key_mapping = {}
        self.key_mapping[pygame.K_1] = 0x0
        self.key_mapping[pygame.K_2] = 0x1
        self.key_mapping[pygame.K_3] = 0x2
        self.key_mapping[pygame.K_4] = 0x3
        self.key_mapping[pygame.K_q] = 0x4
        self.key_mapping[pygame.K_w] = 0x5
        self.key_mapping[pygame.K_e] = 0x6
        self.key_mapping[pygame.K_r] = 0x7
        self.key_mapping[pygame.K_a] = 0x8
        self.key_mapping[pygame.K_s] = 0x9
        self.key_mapping[pygame.K_d] = 0xa
        self.key_mapping[pygame.K_f] = 0xb
        self.key_mapping[pygame.K_z] = 0xc
        self.key_mapping[pygame.K_x] = 0xd
        self.key_mapping[pygame.K_c] = 0xe
        self.key_mapping[pygame.K_v] = 0xf
        
    def handle_keyboard_input(self, event):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            self.control_type = EmulatorControlType.MAIN
            print('control type = Main')
            return

        if self.control_type == EmulatorControlType.MAIN:
            if keys[pygame.K_LCTRL]:
                if keys[pygame.K_h]:
                    self.control_type = EmulatorControlType.HELP
                    print('control type = Help')
                elif keys[pygame.K_s]:
                    self.control_type = EmulatorControlType.INSTRUCTION
                    print('control type = Instruction')
                elif keys[pygame.K_r]:
                    self.control_type = EmulatorControlType.REGISTER
                    print('control type = Register')
                elif keys[pygame.K_m]:
                    self.control_type = EmulatorControlType.MEMORY
                    print('control type = Memory')
        elif self.control_type == EmulatorControlType.INSTRUCTION:
            if keys[pygame.K_s]:
                self.step = True
        elif self.control_type == EmulatorControlType.REGISTER:
            pass
        elif self.control_type == EmulatorControlType.MEMORY:
            if keys[pygame.K_RETURN]:
                if all(c in string.hexdigits for c in self.memory_address_text):
                    self.memory_address = int(self.memory_address_text, 16)
                else:
                    print(f'Invalid address : {self.memory_address_text}')
            else:
                if keys[pygame.K_BACKSPACE]:
                    self.memory_address_text = self.memory_address_text[:-1]
                else:
                    self.memory_address_text += chr(event.key)
        elif self.control_type == EmulatorControlType.HELP:
            pass
        else:
            raise Exception('Unknown control type')

    def draw_help_screen(self, screen):
        x, y = (10, 30)
        text = [
            'Ctrl + S : Single step instrcution',
            'Ctrl + R : Select memory sub screen',
            'Ctrl + M : Select memory sub screen',
            'Esc to leave',
        ]
        for i in range(len(text)):
            self.draw_text(screen, text[i], x, y + i * self.font_size)

    def draw_main_screen(self, screen):
        screen.fill(Color.BLACK)
        
        self.draw_text(screen, f'fps = {self.fps}(target = {self.target_fps})', 10, 200)

    def draw_machine_screen(self, screen, screen_scale):
        if not self.machine.needs_to_redraw:
            return

        self.machine.needs_to_redraw = False
        screen.fill(Color.BLACK)

        for y in range(self.machine.screen_height):
            for x in range(self.machine.screen_width):
                index = y * self.machine.screen_width + x
                if self.machine.screen_buffer[index] > 0:
                    screen.set_at((x, y), Color.GREEN)
        size = (self.machine.screen_width * self.screen_scale, self.machine.screen_height * self.screen_scale)
        pygame.transform.scale(screen, size, screen_scale)

    def draw_keyboard_screen(self, screen, key_status):
        screen.fill(Color.BLUE)
        w = screen.get_width() / 2
        h = screen.get_height() / 8
        for i in range(16):
            x = 0 if i % 2 == 0 else w
            y = (i // 2) * h
            rect = pygame.Rect(x, y, w, h)
            if key_status[i]:
                pygame.draw.rect(screen, Color.GREEN, rect)
            else:
                pygame.draw.rect(screen, Color.GRAY, rect)
            self.draw_text(screen, f'{i:#0{2}}', x, y)

    def draw_instruction_screen(self, screen):
        screen.fill(Color.BLACK)
        start_address = self.machine.pc
        y_offset = 50
        self.draw_text(screen, 'Instruction', 10, 10)
        for i in range(0, 20, 2):
            address = self.machine.pc + i
            opcode = (self.machine.ram[address] << 8) | self.machine.ram[address + 1]
            description = self.machine.get_description(opcode)
            y = i / 2 * self.font_size + y_offset
            self.draw_text(screen, f'{address:#0{4}x} : {opcode:#0{4}x}({description})', 10, y)

    def draw_register_screen(self, screen):
        screen.fill(Color.BLACK)
        self.draw_text(screen, 'Register', 10, 10)
        y_offset = 50
        for i in range(8):
            y = i * self.font_size + y_offset
            self.draw_text(screen, f'reg[{i:#0{4}x}] : {self.machine.registers[i]:#0{4}x}', 10, y)
        for i in range(8):
            y = i * self.font_size + y_offset
            index = i + 8
            self.draw_text(screen, f'reg[{index:#0{4}x}] : {self.machine.registers[index]:#0{4}x}', 200, y)

        self.draw_text(screen, f'I  = {self.machine.I:#0{6}x}', 10, 9 * self.font_size + y_offset)
        self.draw_text(screen, f'PC = {self.machine.pc:#0{6}x}', 10, 10 * self.font_size + y_offset)
        self.draw_text(screen, f'SP = {self.machine.sp:#0{6}x}', 10, 11 * self.font_size + y_offset)

    def draw_memory_screen(self, screen):
        x = 10
        y_offset = 50
        screen.fill(Color.BLACK)
        self.draw_text(screen, f'Address : 0x{self.memory_address_text}', x, 10)
        for i in range(10):
            address = self.memory_address + i * 4
            y = i * self.font_size + y_offset
            text = f'{address:#0{6}x} : {self.machine.ram[address]:#0{4}x}'
            for j in range(3):
                text += f' {self.machine.ram[address + j]:#0{4}x} '
            
            self.draw_text(screen, text, x, y)

    def draw_screen_border(self, screen):
        border_thickness = 2
        width, height = screen.get_size()

        width -= border_thickness
        height -= border_thickness
        
        pygame.draw.line(screen, Color.RED, (0, 0), (width, 0), border_thickness)
        pygame.draw.line(screen, Color.RED, (width, 0), (width, height), border_thickness)
        pygame.draw.line(screen, Color.RED, (width, height), (0, height), border_thickness)
        pygame.draw.line(screen, Color.RED, (0, height), (0, 0), border_thickness)

    def run(self):
        start_time = time.time()
        fps = 0
        
        while True:
            now = time.time()
            if (now - start_time) > 1:
                start_time = now
                self.fps = fps
                fps = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key in self.key_mapping:
                        self.machine.key_down(self.key_mapping[event.key])
                    self.handle_keyboard_input(event)
                    if event.key == pygame.K_o:
                        if self.target_fps < 250:
                            self.target_fps += 5
                    elif event.key == pygame.K_p:
                        if self.target_fps > 5:
                            self.target_fps -= 5 
                        
                if event.type == pygame.KEYUP:
                    if event.key in self.key_mapping:
                        self.machine.key_up(self.key_mapping[event.key])

            if self.control_type != EmulatorControlType.HELP:
                try:
                    if self.control_type == EmulatorControlType.INSTRUCTION:
                        if self.step:
                            self.step = False
                            self.machine.run_loop()
                            fps += 1
                        else:
                            pass
                    else:
                        self.machine.run_loop()
                        fps += 1
                except HardFaultError as e:
                    print(f'Hard fault : {e.msg}')
            
            if self.control_type == EmulatorControlType.HELP:
                self.draw_help_screen(self.help_screen)
                self.screen.blit(self.help_screen, (0, 0))
            else:
                self.draw_main_screen(self.main_screen)
                self.draw_machine_screen(self.chip_screen, self.chip_screen_scale)
                self.draw_keyboard_screen(self.keyboard_screen, self.machine.get_key_status())
                self.draw_memory_screen(self.memory_screen)
                self.draw_register_screen(self.register_screen)
                self.draw_instruction_screen(self.instruction_screen)

                if self.control_type == EmulatorControlType.INSTRUCTION:
                    self.draw_screen_border(self.instruction_screen)
                elif self.control_type == EmulatorControlType.REGISTER:
                    self.draw_screen_border(self.register_screen)
                elif self.control_type == EmulatorControlType.MEMORY:
                    self.draw_screen_border(self.memory_screen)

                self.main_screen.blit(self.chip_screen_scale, (0, 0))
                self.main_screen.blit(self.keyboard_screen, (self.chip_screen_scale.get_width(), 0))
                self.screen.blit(self.main_screen, (0, 0))
                self.screen.blit(self.memory_screen, (self.width // 2, self.height // 2))
                self.screen.blit(self.register_screen, (0, self.height // 2))
                self.screen.blit(self.instruction_screen, (self.width // 2, 0))

            pygame.display.flip()
            self.machine.tick60Hz()
            self.clock.tick(self.target_fps)

    def draw_text(self, screen, msg, x, y, color = Color.WHITE):
        text = self.font.render(msg, True, color)
        text_rect = text.get_rect()
        text_rect.x = x
        text_rect.y = y
        screen.blit(text, text_rect)


def main():
    SCREEN_WIDTH = 1200
    SCREEN_HEIGHT = 600
    SCREEN_SCALE = 6
    TITLE = 'chip8 enumlator'
    with open(r'programs\PONG2', 'rb') as f:
        code = bytearray(f.read())
    chip = Chip8Emulator(code)
    machine = Emulator(chip, SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_SCALE, TITLE)
    machine.run()

if __name__ == '__main__':
    main()
