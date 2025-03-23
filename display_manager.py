#!/usr/bin/env python3
import os
import time
import sys
from PIL import Image
import numpy as np

# Add the tests directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests'))

# Import mock configuration
from tests.mock_config import USE_MOCKS, MOCK_GPIO_PATH, MOCK_SPIDEV_PATH, MOCK_SPI_PATH

# Import hardware modules
if USE_MOCKS:
    from tests.RPi.GPIO.GPIO import GPIO
    from tests.mock_spi import SpiDev
    import spidev
    spidev.SpiDev = SpiDev
else:
    import RPi.GPIO as GPIO
    import spidev

class DisplayManager:
    # Pin definitions using BOARD numbering (physical pin numbers)
    RST_PIN = 11    # Physical pin 11 (BCM 17)
    DC_PIN = 22     # Physical pin 22 (BCM 25)
    CS_PIN = 24     # Physical pin 24 (BCM 8, CE0)
    BUSY_PIN = 18   # Physical pin 18 (BCM 24)

    # Display resolution
    EPD_WIDTH = 960
    EPD_HEIGHT = 680

    def __init__(self):
        self.reset_pin = self.RST_PIN
        self.dc_pin = self.DC_PIN
        self.busy_pin = self.BUSY_PIN
        self.cs_pin = self.CS_PIN
        self.width = self.EPD_WIDTH
        self.height = self.EPD_HEIGHT
        self.initialized = False
        
        # Set GPIO mode at initialization
        GPIO.setmode(GPIO.BOARD)  # Use physical pin numbers
        GPIO.setwarnings(False)

    def digital_write(self, pin, value):
        if not self.initialized:
            self.init()
        GPIO.output(pin, value)

    def digital_read(self, pin):
        if not self.initialized:
            self.init()
        # For testing purposes, we need to be able to read both input and output pins
        if pin == self.busy_pin:
            return GPIO.input(pin)
        else:
            return GPIO.input(pin) if GPIO.gpio_function(pin) == GPIO.IN else GPIO.LOW

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def send_command(self, command):
        self.digital_write(self.dc_pin, GPIO.LOW)
        self.digital_write(self.cs_pin, GPIO.LOW)
        self.spi.writebytes([command])
        self.digital_write(self.cs_pin, GPIO.HIGH)

    def send_data(self, data):
        self.digital_write(self.dc_pin, GPIO.HIGH)
        self.digital_write(self.cs_pin, GPIO.LOW)
        self.spi.writebytes([data])
        self.digital_write(self.cs_pin, GPIO.HIGH)

    def module_exit(self):
        if not self.initialized:
            return
        # Set all pins to LOW before cleanup
        self.digital_write(self.reset_pin, GPIO.LOW)
        self.digital_write(self.dc_pin, GPIO.LOW)
        self.digital_write(self.cs_pin, GPIO.LOW)
        self.digital_write(self.busy_pin, GPIO.LOW)
        GPIO.cleanup()
        self.initialized = False

    def init(self):
        if self.initialized:
            return
        
        GPIO.setup(self.reset_pin, GPIO.OUT)
        GPIO.setup(self.dc_pin, GPIO.OUT)
        GPIO.setup(self.cs_pin, GPIO.OUT)
        GPIO.setup(self.busy_pin, GPIO.IN)
        
        self.spi = spidev.SpiDev(0, 0)
        self.spi.max_speed_hz = 4000000
        self.spi.mode = 0b00
        self.spi.bits_per_word = 8
        
        self.initialized = True
        
        self.reset()
        self.send_command(0x06)  # BOOSTER_SOFT_START
        self.send_data(0x17)  # 8
        self.send_data(0x17)  # 8
        self.send_data(0x17)  # 8
        self.send_command(0x04)  # POWER_ON
        self.wait_until_idle()
        self.send_command(0x00)  # PANEL_SETTING
        self.send_data(0x8F)  # KW-BF   KWR-AF  BWROTP 0f
        self.send_command(0x30)  # PLL_CONTROL
        self.send_data(0x3C)  # 3A 100HZ   29 150Hz 39 200HZ  31 171HZ
        self.send_command(0x01)  # POWER_SETTING
        self.send_data(0x37)  # VGH=20V,VGL=-20V
        self.send_data(0x00)  # VDH=15V
        self.send_data(0x23)  # VDL=-15V
        self.send_data(0x23)  # VDHR
        self.send_command(0x82)  # VCM_DC_SETTING_REGISTER
        self.send_data(0x12)  # VCOM = -0.1V
        self.send_command(0x06)  # BOOSTER_SOFT_START
        self.send_data(0xC7)  # 0A
        self.send_data(0xC7)  # 0A
        self.send_data(0x1D)  # 03
        self.send_command(0x30)  # PLL_CONTROL
        self.send_data(0x3C)  # 3A 100HZ   29 150Hz 39 200HZ  31 171HZ
        self.send_command(0x82)  # VCM_DC_SETTING_REGISTER
        self.send_data(0x12)  # VCOM = -0.1V
        self.send_command(0x50)  # VCOM AND DATA INTERVAL SETTING
        self.send_data(0x37)  # 00H
        self.send_command(0x60)  # TCON
        self.send_data(0x22)  # 00H
        self.send_command(0x65)  # FLASH CONTROL
        self.send_data(0x00)  # 00H
        self.send_command(0x61)  # RESOLUTION SETTING
        self.send_data(self.width >> 8)  # source 960
        self.send_data(self.width & 0xFF)
        self.send_data(self.height >> 8)  # gate 680
        self.send_data(self.height & 0xFF)
        self.send_command(0x82)  # VCM_DC_SETTING_REGISTER
        self.send_data(0x12)  # VCOM = -0.1V
        self.send_command(0xE5)  # FLASH MODE
        self.send_data(0x03)  # 00H
        self.send_command(0x01)  # POWER_SETTING
        self.send_data(0x37)  # VGH=20V,VGL=-20V
        self.send_data(0x00)  # VDH=15V
        self.send_data(0x23)  # VDL=-15V
        self.send_data(0x23)  # VDHR
        self.send_command(0x82)  # VCM_DC_SETTING_REGISTER
        self.send_data(0x12)  # VCOM = -0.1V
        self.send_command(0x04)  # POWER_ON
        self.wait_until_idle()
        self.send_command(0x10)  # DEEP_SLEEP
        self.send_data(0x00)  # 00H

    def wait_until_idle(self):
        while self.digital_read(self.busy_pin) == 1:
            self.delay_ms(100)

    def reset(self):
        self.digital_write(self.reset_pin, GPIO.HIGH)
        self.delay_ms(200)
        self.digital_write(self.reset_pin, GPIO.LOW)
        self.delay_ms(200)
        self.digital_write(self.reset_pin, GPIO.HIGH)
        self.delay_ms(200)

    def convert_image_to_bytes(self, image):
        """Convert a PIL Image to bytes for the e-paper display."""
        if not isinstance(image, Image.Image):
            raise TypeError("Input must be a PIL Image")
        
        # Convert to grayscale if not already
        if image.mode != 'L':
            image = image.convert('L')
        
        # Resize to display dimensions if needed
        if image.size != (self.width, self.height):
            image = image.resize((self.width, self.height))
        
        # Convert to binary (black and white)
        threshold = 128
        image = image.point(lambda x: 0 if x > threshold else 1, '1')
        
        # Convert to bytes
        pixels = np.array(image)
        bytes_array = []
        
        for y in range(0, self.height, 8):
            for x in range(self.width):
                byte = 0
                for bit in range(min(8, self.height - y)):
                    if y + bit < self.height and pixels[y + bit, x] == 0:
                        byte |= 1 << bit
                bytes_array.append(byte)
        
        return bytes_array

    def display(self, image):
        if not self.initialized:
            self.init()
        
        # Convert image to bytes if needed
        if isinstance(image, Image.Image):
            image_bytes = self.convert_image_to_bytes(image)
        else:
            image_bytes = image
        
        self.send_command(0x10)
        for i in range(0, self.height * self.width // 8):
            self.send_data(0xFF)
        
        self.send_command(0x13)
        for byte in image_bytes:
            self.send_data(byte)
        
        self.send_command(0x12)
        self.wait_until_idle()

    def clear(self):
        if not self.initialized:
            self.init()
        
        self.send_command(0x10)
        for i in range(0, self.height * self.width // 8):
            self.send_data(0xFF)
        
        self.send_command(0x13)
        for i in range(0, self.height * self.width // 8):
            self.send_data(0xFF)
        
        self.send_command(0x12)
        self.wait_until_idle()

    def sleep(self):
        if not self.initialized:
            return
        
        self.send_command(0x02)  # POWER_OFF
        self.wait_until_idle()
        self.send_command(0x07)  # DEEP_SLEEP
        self.send_data(0xA5)  # check code

def main():
    display = DisplayManager()
    display.init()
    display.clear()
    display.sleep()

if __name__ == "__main__":
    main() 