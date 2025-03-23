#!/usr/bin/env python3
import os
import sys
import time
from PIL import Image, ImageDraw, ImageFont

# Import directly from the hardware modules, not from mocks
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("ERROR: RPi.GPIO module not found. Make sure you're running on a Raspberry Pi.")
    sys.exit(1)

try:
    import spidev
except ImportError:
    print("ERROR: spidev module not found. Install with 'pip install spidev'")
    sys.exit(1)

# Define the DisplayManager class with only the essential functions for testing
class TestDisplayManager:
    # Pin definitions using BOARD numbering (physical pin numbers)
    RST_PIN = 11    # Physical pin 11 (BCM 17)
    DC_PIN = 22     # Physical pin 22 (BCM 25)
    CS_PIN = 24     # Physical pin 24 (BCM 8, CE0)
    BUSY_PIN = 18   # Physical pin 18 (BCM 24)
    # SPI uses pins 19 (MOSI) and 23 (SCK) automatically

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
        
        print("Initializing GPIO using BOARD numbering...")
        GPIO.setmode(GPIO.BOARD)  # Use physical pin numbers
        GPIO.setwarnings(False)
        
        GPIO.setup(self.reset_pin, GPIO.OUT)
        GPIO.setup(self.dc_pin, GPIO.OUT)
        GPIO.setup(self.cs_pin, GPIO.OUT)
        GPIO.setup(self.busy_pin, GPIO.IN)
        
        print("Initializing SPI...")
        self.spi = spidev.SpiDev(0, 0)
        self.spi.max_speed_hz = 4000000
        self.spi.mode = 0b00
        
        print("Initialization complete.")

    def digital_write(self, pin, value):
        GPIO.output(pin, value)

    def digital_read(self, pin):
        return GPIO.input(pin)

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

    def wait_until_idle(self):
        print("Waiting for display to be idle...")
        print(f"Initial BUSY pin state: {self.digital_read(self.busy_pin)}")
        
        # Add timeout for wait_until_idle
        start_time = time.time()
        timeout = 30  # 30 seconds timeout
        
        while self.digital_read(self.busy_pin) == 1:
            self.delay_ms(100)
            # Check if we've exceeded the timeout
            if time.time() - start_time > timeout:
                print(f"Warning: Timeout waiting for BUSY pin to go LOW after {timeout} seconds")
                print(f"Current BUSY pin state: {self.digital_read(self.busy_pin)}")
                print("Continuing anyway...")
                break
        
        print(f"Final BUSY pin state: {self.digital_read(self.busy_pin)}")

    def reset(self):
        print("Resetting display...")
        self.digital_write(self.reset_pin, GPIO.HIGH)
        self.delay_ms(200)
        self.digital_write(self.reset_pin, GPIO.LOW)
        self.delay_ms(200)
        self.digital_write(self.reset_pin, GPIO.HIGH)
        self.delay_ms(200)

    def init(self):
        print("Initializing e-paper display...")
        print("Testing GPIO pins before reset...")
        print(f"BUSY pin state: {self.digital_read(self.busy_pin)}")
        print(f"RST pin state: {GPIO.input(self.reset_pin)}")
        print(f"DC pin state: {GPIO.input(self.dc_pin)}")
        print(f"CS pin state: {GPIO.input(self.cs_pin)}")
        
        self.reset()
        
        # Print pin states after reset
        print("Pin states after reset:")
        print(f"BUSY pin state: {self.digital_read(self.busy_pin)}")
        
        try:
            # Basic initialization sequence
            print("Sending initialization commands...")
            self.send_command(0x06)  # BOOSTER_SOFT_START
            self.send_data(0x17)
            self.send_data(0x17)
            self.send_data(0x17)
            
            print("Sending POWER_ON command...")
            self.send_command(0x04)  # POWER_ON
            self.wait_until_idle()
            
            print("Sending PANEL_SETTING command...")
            self.send_command(0x00)  # PANEL_SETTING
            self.send_data(0x8F)
            
            print("Sending RESOLUTION_SETTING command...")
            self.send_command(0x61)  # RESOLUTION SETTING
            self.send_data(self.width >> 8)
            self.send_data(self.width & 0xFF)
            self.send_data(self.height >> 8)
            self.send_data(self.height & 0xFF)
            
            print("Display initialization complete.")
        except Exception as e:
            print(f"Error during initialization: {e}")
            raise

    def clear(self):
        print("Clearing display...")
        self.send_command(0x10)  # DATA_START_TRANSMISSION_1
        for i in range(0, int(self.height * self.width / 8)):
            self.send_data(0xFF)  # White
        
        self.send_command(0x13)  # DATA_START_TRANSMISSION_2
        for i in range(0, int(self.height * self.width / 8)):
            self.send_data(0xFF)  # White
        
        self.send_command(0x12)  # DISPLAY_REFRESH
        self.wait_until_idle()
        print("Display cleared.")

    def display_test_pattern(self):
        print("Preparing test pattern...")
        # Create a test pattern (checkerboard)
        image = Image.new('1', (self.width, self.height), 255)  # 255: white
        draw = ImageDraw.Draw(image)
        
        # Draw black rectangles
        square_size = 120
        for y in range(0, self.height, square_size * 2):
            for x in range(0, self.width, square_size * 2):
                draw.rectangle([(x, y), (x + square_size, y + square_size)], fill=0)  # 0: black
                if x + square_size < self.width and y + square_size < self.height:
                    draw.rectangle([(x + square_size, y + square_size), 
                                   (x + square_size * 2, y + square_size * 2)], fill=0)
        
        # Draw text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        except IOError:
            # Fallback to default font if DejaVuSans is not available
            font = ImageFont.load_default()
        
        draw.text((self.width // 4, self.height // 3), "Display Test", fill=0, font=font)
        draw.text((self.width // 4, self.height // 2), "BOARD Mode Test", fill=0, font=font)
        
        # Convert image to bytes
        print("Converting image to bytes...")
        pixels = image.load()
        buffer = []
        
        for y in range(0, self.height, 8):
            for x in range(self.width):
                byte = 0
                for bit in range(8):
                    if y + bit < self.height:
                        if pixels[x, y + bit] == 0:  # Black pixel
                            byte |= 1 << bit
                buffer.append(byte)
        
        # Send image data
        print("Sending test pattern to display...")
        self.send_command(0x10)  # DATA_START_TRANSMISSION_1
        for i in range(len(buffer)):
            self.send_data(0xFF)  # White
        
        self.send_command(0x13)  # DATA_START_TRANSMISSION_2
        for i in range(len(buffer)):
            self.send_data(buffer[i])
        
        # Refresh display
        print("Refreshing display...")
        self.send_command(0x12)  # DISPLAY_REFRESH
        self.wait_until_idle()
        print("Test pattern displayed.")

    def sleep(self):
        print("Putting display to sleep...")
        self.send_command(0x02)  # POWER_OFF
        self.wait_until_idle()
        self.send_command(0x07)  # DEEP_SLEEP
        self.send_data(0xA5)
        print("Display is now in sleep mode.")

    def cleanup(self):
        print("Cleaning up GPIO...")
        GPIO.cleanup()
        print("Cleanup complete.")

def main():
    print("Starting E-Paper Display Test (BOARD pin numbering)")
    
    # Create display manager
    display = TestDisplayManager()
    
    try:
        # Initialize display
        print("Initializing display...")
        display.init()
        
        # Ask user if they want to continue
        user_input = input("Continue with clearing the display? (y/n): ")
        if user_input.lower() != 'y':
            print("Test aborted by user.")
            display.cleanup()
            return
        
        # Clear display
        print("Clearing display...")
        display.clear()
        
        # Ask user if they want to continue
        user_input = input("Continue with displaying the test pattern? (y/n): ")
        if user_input.lower() != 'y':
            print("Test aborted by user.")
            display.cleanup()
            return
        
        # Display test pattern
        display.display_test_pattern()
        
        print("Test completed successfully. You should see a checkerboard pattern with text.")
        print("If you don't see anything on the display, check your connections.")
        
        # Wait for a moment before sleeping
        time.sleep(10)
        
        # Sleep display
        display.sleep()
    
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        display.cleanup()
        print("Test finished.")

if __name__ == "__main__":
    main() 