#!/usr/bin/env python3
import os
import time
import sys
from PIL import Image
import numpy as np

class DisplayManager:
    """
    DisplayManager class for 13.3 inch e-ink display.
    This is a standalone implementation that does not depend on external modules.
    """
    # Pin definitions using BOARD numbering (physical pin numbers)
    RST_PIN = 11    # Physical pin 11 (BCM 17)
    DC_PIN = 22     # Physical pin 22 (BCM 25)
    CS_PIN = 24     # Physical pin 24 (BCM 8, CE0)
    BUSY_PIN = 18   # Physical pin 18 (BCM 24)
    PWR_PIN = 12    # Physical pin 12 (BCM 18)

    # Display resolution
    EPD_WIDTH = 960
    EPD_HEIGHT = 680

    # Gray levels
    GRAY1 = 0xff  # white
    GRAY2 = 0xC0
    GRAY3 = 0x80  # gray
    GRAY4 = 0x00  # black

    def __init__(self, use_mocks=False):
        """
        Initialize the DisplayManager.
        
        Args:
            use_mocks (bool): Use mock GPIO and SPI for testing.
        """
        self.use_mocks = use_mocks
        self.reset_pin = self.RST_PIN
        self.dc_pin = self.DC_PIN
        self.busy_pin = self.BUSY_PIN
        self.cs_pin = self.CS_PIN
        self.pwr_pin = self.PWR_PIN
        self.width = self.EPD_WIDTH
        self.height = self.EPD_HEIGHT
        self.initialized = False
        
        # Import the appropriate modules based on whether we're using mocks
        if use_mocks:
            mock_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests')
            if mock_path not in sys.path:
                sys.path.append(mock_path)
            
            try:
                from tests.RPi.GPIO.GPIO import GPIO
                from tests.mock_spi import SpiDev
                # Monkey patch spidev
                import spidev
                spidev.SpiDev = SpiDev
                self.GPIO = GPIO
                self.spidev = spidev
            except ImportError:
                print("Mock modules not found. Creating minimal mock objects.")
                # Create minimal mock classes if the mock modules aren't available
                class MockGPIO:
                    BOARD = 1
                    OUT = 1
                    IN = 0
                    HIGH = 1
                    LOW = 0
                    
                    @staticmethod
                    def setmode(mode): pass
                    
                    @staticmethod
                    def setwarnings(flag): pass
                    
                    @staticmethod
                    def setup(pin, mode): pass
                    
                    @staticmethod
                    def output(pin, value): pass
                    
                    @staticmethod
                    def input(pin): return 0
                    
                    @staticmethod
                    def cleanup(): pass
                    
                    @staticmethod
                    def gpio_function(pin): return MockGPIO.OUT

                class MockSpiDev:
                    def __init__(self):
                        self.max_speed_hz = 0
                        self.mode = 0
                        self.bits_per_word = 0
                    
                    def open(self, bus, device): pass
                    
                    def writebytes(self, data): pass
                    
                    def writebytes2(self, data): pass
                    
                    def close(self): pass
                
                self.GPIO = MockGPIO
                self.spidev = type('', (), {})
                self.spidev.SpiDev = MockSpiDev
        else:
            # Use the real hardware modules
            import RPi.GPIO as GPIO
            import spidev
            self.GPIO = GPIO
            self.spidev = spidev
        
        # Set GPIO mode at initialization
        self.GPIO.setmode(self.GPIO.BOARD)  # Use physical pin numbers
        self.GPIO.setwarnings(False)

        # LUT tables for partial refresh
        self.Lut_Partial = [
            0x15, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x2A, 0x88, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x15, 0x44, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x01, 0x01, 0x01, 0x00,
            0x0A, 0x00, 0x05, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x01, 0x01,
            0x22, 0x22, 0x22, 0x22, 0x22,
            0x17, 0x41, 0xA8, 0x32, 0x18,
            0x00, 0x00,
        ]

        # LUT tables for 4 gray levels
        self.LUT_DATA_4Gray = [
            0x80, 0x48, 0x4A, 0x22, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x0A, 0x48, 0x68, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x88, 0x48, 0x60, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0xA8, 0x48, 0x45, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x07, 0x23, 0x17, 0x02, 0x00,
            0x05, 0x01, 0x05, 0x01, 0x02,
            0x08, 0x02, 0x01, 0x04, 0x04,
            0x00, 0x02, 0x00, 0x02, 0x01,
            0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x01,
            0x22, 0x22, 0x22, 0x22, 0x22,
            0x17, 0x41, 0xA8, 0x32, 0x30,
            0x00, 0x00,
        ]

    def digital_write(self, pin, value):
        """Write digital value to a GPIO pin."""
        if not self.initialized:
            self.init()
        self.GPIO.output(pin, value)

    def digital_read(self, pin):
        """Read digital value from a GPIO pin."""
        if not self.initialized:
            self.init()
        # For testing purposes, we need to be able to read both input and output pins
        if pin == self.busy_pin:
            return self.GPIO.input(pin)
        else:
            return self.GPIO.input(pin) if self.GPIO.gpio_function(pin) == self.GPIO.IN else self.GPIO.LOW

    def delay_ms(self, delaytime):
        """Delay for a specified number of milliseconds."""
        time.sleep(delaytime / 1000.0)

    def send_command(self, command):
        """Send a command to the display."""
        self.digital_write(self.dc_pin, self.GPIO.LOW)
        self.digital_write(self.cs_pin, self.GPIO.LOW)
        self.spi.writebytes([command])
        self.digital_write(self.cs_pin, self.GPIO.HIGH)

    def send_data(self, data):
        """Send data to the display."""
        self.digital_write(self.dc_pin, self.GPIO.HIGH)
        self.digital_write(self.cs_pin, self.GPIO.LOW)
        self.spi.writebytes([data])
        self.digital_write(self.cs_pin, self.GPIO.HIGH)

    def send_data2(self, data):
        """Send data to the display using writebytes2."""
        self.digital_write(self.dc_pin, self.GPIO.HIGH)
        self.digital_write(self.cs_pin, self.GPIO.LOW)
        self.spi.writebytes2(data)
        self.digital_write(self.cs_pin, self.GPIO.HIGH)

    def lut(self, lut_table):
        """Load a LUT (Look-Up Table) for the display."""
        self.send_command(0x32)
        for i in range(105):
            self.send_data(lut_table[i])

        self.send_command(0x03) 
        self.send_data(lut_table[105])

        self.send_command(0x04)  
        self.send_data(lut_table[106])
        self.send_data(lut_table[107]) 
        self.send_data(lut_table[108])

        self.send_command(0x2C)
        self.send_data(lut_table[109])

    def wait_until_idle(self):
        """Wait until the display is idle (not busy)."""
        print("e-Paper busy")
        busy = self.digital_read(self.busy_pin)
        while busy == 1:
            busy = self.digital_read(self.busy_pin)
            self.delay_ms(20)
        self.delay_ms(20)
        print("e-Paper busy release")

    def turn_on_display(self):
        """Turn on the display with full refresh."""
        self.send_command(0x22)  # Display Update Control
        self.send_data(0xF7)
        self.send_command(0x20)  # Activate Display Update Sequence
        self.wait_until_idle()

    def turn_on_display_partial(self):
        """Turn on the display with partial refresh."""
        self.send_command(0x22)  # Display Update Control
        self.send_data(0xCF)
        self.send_command(0x20)  # Activate Display Update Sequence
        self.wait_until_idle()

    def turn_on_display_4gray(self):
        """Turn on the display with 4 gray levels."""
        self.send_command(0x22)  # Display Update Control
        self.send_data(0xC7)
        self.send_command(0x20)  # Activate Display Update Sequence
        self.wait_until_idle()

    def module_exit(self):
        """Clean up GPIO and SPI resources."""
        if not self.initialized:
            return
        # Set all pins to LOW before cleanup
        self.digital_write(self.reset_pin, self.GPIO.LOW)
        self.digital_write(self.dc_pin, self.GPIO.LOW)
        self.digital_write(self.cs_pin, self.GPIO.LOW)
        self.digital_write(self.busy_pin, self.GPIO.LOW)
        self.GPIO.cleanup()
        self.initialized = False

    def reset(self):
        """Reset the display."""
        self.digital_write(self.reset_pin, self.GPIO.HIGH)
        self.delay_ms(200)
        self.digital_write(self.reset_pin, self.GPIO.LOW)
        self.delay_ms(200)
        self.digital_write(self.reset_pin, self.GPIO.HIGH)
        self.delay_ms(200)

    def init(self):
        """Initialize the display with default settings."""
        if self.initialized:
            return
        
        # Set up GPIO pins
        self.GPIO.setup(self.reset_pin, self.GPIO.OUT)
        self.GPIO.setup(self.dc_pin, self.GPIO.OUT)
        self.GPIO.setup(self.cs_pin, self.GPIO.OUT)
        self.GPIO.setup(self.busy_pin, self.GPIO.IN)
        self.GPIO.setup(self.pwr_pin, self.GPIO.OUT)
        
        # Set up SPI
        self.spi = self.spidev.SpiDev(0, 0)
        self.spi.max_speed_hz = 4000000
        self.spi.mode = 0b00
        self.spi.bits_per_word = 8
        
        self.initialized = True
        
        # Turn on power
        self.digital_write(self.pwr_pin, self.GPIO.HIGH)
        
        # Hardware reset and initialization
        self.reset()
        self.wait_until_idle()

        self.send_command(0x12)  # SWRESET
        self.wait_until_idle()

        self.send_command(0x0C)
        self.send_data(0xAE)
        self.send_data(0xC7)
        self.send_data(0xC3)
        self.send_data(0xC0)
        self.send_data(0x80)

        self.send_command(0x01)
        self.send_data(0xA7)
        self.send_data(0x02)
        self.send_data(0x00)

        self.send_command(0x11)
        self.send_data(0x03)

        self.send_command(0x44)  # Set RAM X start/end position
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0xBF)
        self.send_data(0x03)
        
        self.send_command(0x45)  # Set RAM Y start/end position
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0xA7)
        self.send_data(0x02)

        self.send_command(0x3C)  # VBD
        self.send_data(0x05)

        self.send_command(0x18)  # Read built-in temperature sensor
        self.send_data(0x80)

        self.send_command(0x4E)  # Set RAM X address
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x4F)  # Set RAM Y address
        self.send_data(0x00)
        self.send_data(0x00)

    def init_partial(self):
        """Initialize the display for partial refresh."""
        self.reset()

        self.send_command(0x3C)
        self.send_data(0x80)

        self.lut(self.Lut_Partial)

        self.send_command(0x37)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x40)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x3C)
        self.send_data(0x80)

        self.send_command(0x22)
        self.send_data(0xC0)
        self.send_command(0x20)
        self.wait_until_idle()

    def init_4gray(self):
        """Initialize the display for 4 gray levels."""
        self.reset()
        self.wait_until_idle()

        self.send_command(0x12)  # SWRESET
        self.wait_until_idle()

        self.send_command(0x0C)  # BTST
        self.send_data(0xAE)
        self.send_data(0xC7)
        self.send_data(0xC3)
        self.send_data(0xC0)
        self.send_data(0x80)

        self.send_command(0x01)  # POWER SETTING
        self.send_data(0xA7)
        self.send_data(0x02)
        self.send_data(0x00)

        self.send_command(0x11)  # DATA ENTRY
        self.send_data(0x03)

        self.send_command(0x44)  # Set RAM X start/end position
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0xBF)
        self.send_data(0x03)

        self.send_command(0x45)  # Set RAM Y start/end position
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0xA7)
        self.send_data(0x02)

        self.send_command(0x3C)  # VBD
        self.send_data(0x05)

        self.send_command(0x18)  # Read built-in temperature sensor
        self.send_data(0x80)

        self.send_command(0x4E)  # Set RAM X address
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x4F)  # Set RAM Y address
        self.send_data(0x00)
        self.send_data(0x00)

        self.lut(self.LUT_DATA_4Gray)

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

    def getbuffer_4gray(self, image):
        """Convert a PIL Image to bytes for 4 gray levels."""
        if not isinstance(image, Image.Image):
            raise TypeError("Input must be a PIL Image")
        
        # Convert to grayscale if not already
        if image.mode != 'L':
            image = image.convert('L')
        
        # Resize to display dimensions if needed
        if image.size != (self.width, self.height):
            image = image.resize((self.width, self.height))
        
        buf_4gray = [0x00] * (int(self.width * self.height // 4))
        
        pixels = image.load()
        for y in range(self.height):
            for x in range(self.width):
                # Get the pixel value and map it to one of the 4 gray levels
                gray = 0
                if pixels[x, y] >= 192:
                    gray = 0  # white
                elif pixels[x, y] >= 128:
                    gray = 1  # light gray
                elif pixels[x, y] >= 64:
                    gray = 2  # dark gray
                else:
                    gray = 3  # black
                
                # Pack two gray values into one byte
                newx = y * self.width + x
                value4 = (gray << ((newx % 4) * 2))
                
                buf_4gray[newx//4] |= value4
        
        return buf_4gray

    def clear(self):
        """Clear the display (all white)."""
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

    def display(self, image):
        """Display an image on the e-paper screen."""
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

    def display_base(self, image):
        """Display base image for partial refresh mode."""
        if not self.initialized:
            self.init()
        
        # Convert image to bytes if needed
        if isinstance(image, Image.Image):
            image_bytes = self.convert_image_to_bytes(image)
        else:
            image_bytes = image
        
        self.send_command(0x10)
        for byte in image_bytes:
            self.send_data(byte)
            
        self.send_command(0x13)
        for i in range(0, self.height * self.width // 8):
            self.send_data(0xFF)
            
        self.turn_on_display()

    def display_partial(self, image, x_start, y_start, x_end, y_end):
        """Display a partial update of the screen."""
        if x_start > x_end or y_start > y_end:
            return
        if x_end > self.width or y_end > self.height:
            return
        
        if not self.initialized:
            self.init_partial()
        
        # Convert image to bytes if needed
        if isinstance(image, Image.Image):
            # For partial update, we need to crop the image to the region we want to update
            if image.size != (x_end - x_start, y_end - y_start):
                image = image.crop((x_start, y_start, x_end, y_end))
            image_bytes = self.convert_image_to_bytes(image)
        else:
            image_bytes = image
        
        self.send_command(0x44)
        self.send_data(x_start & 0xFF)
        self.send_data((x_start >> 8) & 0xFF)
        self.send_data((x_end-1) & 0xFF)
        self.send_data(((x_end-1) >> 8) & 0xFF)
        
        self.send_command(0x45)
        self.send_data(y_start & 0xFF)
        self.send_data((y_start >> 8) & 0xFF)
        self.send_data((y_end-1) & 0xFF)
        self.send_data(((y_end-1) >> 8) & 0xFF)
        
        self.send_command(0x4E)
        self.send_data(x_start & 0xFF)
        self.send_data((x_start >> 8) & 0xFF)
        
        self.send_command(0x4F)
        self.send_data(y_start & 0xFF)
        self.send_data((y_start >> 8) & 0xFF)
        
        self.send_command(0x13)
        for byte in image_bytes:
            self.send_data(byte)
        
        self.turn_on_display_partial()

    def display_4gray(self, image):
        """Display an image with 4 gray levels."""
        if not self.initialized:
            self.init_4gray()
        
        # Convert image to 4 gray levels
        if isinstance(image, Image.Image):
            image_bytes = self.getbuffer_4gray(image)
        else:
            image_bytes = image
        
        self.send_command(0x10)
        for i in range(0, self.height * self.width // 8):
            self.send_data(0x00)
            
        self.send_command(0x13)
        for i in range(0, int(self.height * self.width // 4)):
            temp3 = 0
            for j in range(4):
                temp1 = image_bytes[i]
                temp2 = temp1 & 0x03
                if j == 0:
                    temp3 |= (temp2 << 6)
                elif j == 1:
                    temp3 |= (temp2 << 4)
                elif j == 2:
                    temp3 |= (temp2 << 2)
                else:
                    temp3 |= temp2
                temp1 = (temp1 >> 2)
                image_bytes[i] = temp1
            self.send_data(temp3)
            
        self.turn_on_display_4gray()

    def sleep(self):
        """Put the display to sleep to save power."""
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