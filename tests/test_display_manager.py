#!/usr/bin/env python3
import unittest
import os
import time
import sys
from PIL import Image
import numpy as np

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import mock configuration
from tests.mock_config import USE_MOCKS, MOCK_GPIO_PATH, MOCK_SPIDEV_PATH, MOCK_SPI_PATH

# Import mock modules if needed
if USE_MOCKS:
    # Import mock modules first
    from tests.RPi.GPIO.GPIO import GPIO
    from tests.mock_spi import SpiDev
    import spidev
    spidev.SpiDev = SpiDev
else:
    # Import real modules
    import RPi.GPIO as GPIO
    import spidev

# Now import the display manager after GPIO is properly set up
from display_manager import DisplayManager

class TestDisplayManager(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        # Reset GPIO state before each test
        if USE_MOCKS:
            GPIO.cleanup()
        self.display = DisplayManager()
        
        # Create a test image
        self.test_image = Image.new('RGB', (self.display.width, self.display.height), (255, 255, 255))
        self.test_image_draw = self.test_image.load()
        
        # Draw some test content
        for x in range(self.display.width):
            for y in range(self.display.height):
                if x % 2 == 0 and y % 2 == 0:
                    self.test_image_draw[x, y] = (0, 0, 0)

    def test_pin_setup(self):
        """Test GPIO pin setup"""
        # Test pin mode
        self.assertEqual(GPIO.getmode(), GPIO.BCM)
        
        # Test pin directions
        self.assertEqual(GPIO.gpio_function(self.display.reset_pin), GPIO.OUT)
        self.assertEqual(GPIO.gpio_function(self.display.dc_pin), GPIO.OUT)
        self.assertEqual(GPIO.gpio_function(self.display.cs_pin), GPIO.OUT)
        self.assertEqual(GPIO.gpio_function(self.display.busy_pin), GPIO.IN)

    def test_spi_setup(self):
        """Test SPI setup"""
        self.display.init()
        self.assertEqual(self.display.spi.mode, 0b00)
        self.assertEqual(self.display.spi.max_speed_hz, 4000000)
        self.assertEqual(self.display.spi.bits_per_word, 8)

    def test_display_initialization(self):
        """Test display initialization sequence"""
        self.display.init()
        # Verify display is ready
        self.assertEqual(self.display.digital_read(self.display.busy_pin), 0)

    def test_display_clear(self):
        """Test display clear function"""
        self.display.init()
        self.display.clear()
        # Verify display is cleared
        self.assertEqual(self.display.digital_read(self.display.busy_pin), 0)

    def test_display_sleep(self):
        """Test display sleep function"""
        self.display.init()
        self.display.sleep()
        # Verify display is in sleep mode
        self.assertEqual(self.display.digital_read(self.display.busy_pin), 0)

    def test_display_image(self):
        """Test displaying an image"""
        self.display.init()
        self.display.display(self.test_image)
        # Verify display is updated
        self.assertEqual(self.display.digital_read(self.display.busy_pin), 0)

    def test_reset_sequence(self):
        """Test display reset sequence"""
        self.display.reset()
        # Verify reset sequence completed
        self.assertEqual(self.display.digital_read(self.display.busy_pin), 0)

    def test_wait_until_idle(self):
        """Test wait until idle function"""
        self.display.init()
        start_time = time.time()
        self.display.wait_until_idle()
        end_time = time.time()
        # Verify wait function completed
        self.assertLess(end_time - start_time, 1.0)  # Should complete within 1 second

    def test_module_exit(self):
        """Test module exit function"""
        self.display.module_exit()
        # Verify pins are set to low
        self.assertEqual(self.display.digital_read(self.display.reset_pin), 0)
        self.assertEqual(self.display.digital_read(self.display.dc_pin), 0)
        self.assertEqual(self.display.digital_read(self.display.cs_pin), 0)

    def test_display_commands(self):
        """Test display command sequence"""
        self.display.init()
        # Test sending commands
        self.display.send_command(0x06)  # BOOSTER_SOFT_START
        self.display.send_data(0x17)
        self.display.send_command(0x04)  # POWER_ON
        self.display.wait_until_idle()
        # Verify display is ready
        self.assertEqual(self.display.digital_read(self.display.busy_pin), 0)

    def tearDown(self):
        """Clean up after each test"""
        try:
            self.display.module_exit()
            GPIO.cleanup()
        except:
            pass

if __name__ == '__main__':
    unittest.main() 