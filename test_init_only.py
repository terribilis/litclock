#!/usr/bin/env python3
import sys
import time

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

# Pin definitions using BOARD numbering (physical pin numbers)
RST_PIN = 11    # Physical pin 11 (BCM 17)
DC_PIN = 22     # Physical pin 22 (BCM 25)
CS_PIN = 24     # Physical pin 24 (BCM 8, CE0)
BUSY_PIN = 18   # Physical pin 18 (BCM 24)
# SPI uses pins 19 (MOSI) and 23 (SCK) automatically

def digital_write(pin, value):
    GPIO.output(pin, value)

def digital_read(pin):
    return GPIO.input(pin)

def delay_ms(delaytime):
    time.sleep(delaytime / 1000.0)

def wait_until_idle(busy_pin, timeout_seconds=5):
    print("Waiting for display to be idle...")
    print(f"Initial BUSY pin state: {digital_read(busy_pin)}")
    
    start_time = time.time()
    
    while digital_read(busy_pin) == 1:
        delay_ms(100)
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            print(f"Warning: Timeout waiting for BUSY pin to go LOW after {timeout_seconds} seconds")
            print(f"Current BUSY pin state: {digital_read(busy_pin)}")
            return False
        
        # Print progress every second
        if int(elapsed) != int(elapsed - 0.1):
            print(f"Waiting... BUSY pin is still HIGH after {elapsed:.1f} seconds")
    
    print(f"Final BUSY pin state: {digital_read(busy_pin)}")
    print(f"BUSY pin went LOW after {time.time() - start_time:.2f} seconds")
    return True

def send_command(dc_pin, cs_pin, spi, command):
    digital_write(dc_pin, GPIO.LOW)
    digital_write(cs_pin, GPIO.LOW)
    spi.writebytes([command])
    digital_write(cs_pin, GPIO.HIGH)

def send_data(dc_pin, cs_pin, spi, data):
    digital_write(dc_pin, GPIO.HIGH)
    digital_write(cs_pin, GPIO.LOW)
    spi.writebytes([data])
    digital_write(cs_pin, GPIO.HIGH)

def reset_display(reset_pin):
    print("Resetting display...")
    print(f"  Setting RST pin HIGH")
    digital_write(reset_pin, GPIO.HIGH)
    delay_ms(200)
    print(f"  Setting RST pin LOW")
    digital_write(reset_pin, GPIO.LOW)
    delay_ms(200)
    print(f"  Setting RST pin HIGH again")
    digital_write(reset_pin, GPIO.HIGH)
    delay_ms(200)
    print("Reset sequence completed")

def setup_pins_and_spi():
    print("Setting up GPIO pins...")
    # Use BOARD pin numbering
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    
    # Set up pins
    GPIO.setup(RST_PIN, GPIO.OUT)
    GPIO.setup(DC_PIN, GPIO.OUT)
    GPIO.setup(CS_PIN, GPIO.OUT)
    GPIO.setup(BUSY_PIN, GPIO.IN)
    
    # Initialize all output pins to HIGH
    GPIO.output(RST_PIN, GPIO.HIGH)
    GPIO.output(DC_PIN, GPIO.HIGH)
    GPIO.output(CS_PIN, GPIO.HIGH)
    
    print("Initializing SPI...")
    spi = spidev.SpiDev(0, 0)
    spi.max_speed_hz = 4000000
    spi.mode = 0b00
    
    print("GPIO and SPI setup complete")
    return spi

def init_display(spi):
    print("\nStarting display initialization sequence")
    # Check BUSY pin before reset
    print(f"BUSY pin state before reset: {digital_read(BUSY_PIN)}")
    
    # Reset display
    reset_display(RST_PIN)
    
    # Check BUSY pin after reset
    print(f"BUSY pin state after reset: {digital_read(BUSY_PIN)}")
    
    # Basic initialization sequence
    print("\nSending initialization commands...")
    
    print("  Sending BOOSTER_SOFT_START command (0x06)")
    send_command(DC_PIN, CS_PIN, spi, 0x06)
    send_data(DC_PIN, CS_PIN, spi, 0x17)
    send_data(DC_PIN, CS_PIN, spi, 0x17)
    send_data(DC_PIN, CS_PIN, spi, 0x17)
    
    print("  Sending POWER_ON command (0x04)")
    send_command(DC_PIN, CS_PIN, spi, 0x04)
    
    # Wait for the display to finish processing the POWER_ON command
    if not wait_until_idle(BUSY_PIN, 10):
        print("WARNING: Display did not respond to POWER_ON command!")
        print("Continuing with initialization anyway...")
    
    print("  Sending PANEL_SETTING command (0x00)")
    send_command(DC_PIN, CS_PIN, spi, 0x00)
    send_data(DC_PIN, CS_PIN, spi, 0x8F)
    
    # Wait briefly after PANEL_SETTING
    delay_ms(100)
    
    return True

def main():
    print("E-Paper Display Initialization Test")
    print("===================================")
    print(f"RST pin: {RST_PIN}")
    print(f"DC pin: {DC_PIN}")
    print(f"CS pin: {CS_PIN}")
    print(f"BUSY pin: {BUSY_PIN}")
    
    try:
        # Setup pins and SPI
        spi = setup_pins_and_spi()
        
        # Initialize display
        if init_display(spi):
            print("\nDisplay initialization completed!")
            print("If everything worked correctly, the BUSY pin should have")
            print("responded during the initialization sequence.")
        else:
            print("\nDisplay initialization failed!")
            print("Check your wiring and connections.")
        
    except Exception as e:
        print(f"\nError during initialization: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\nCleaning up GPIO...")
        GPIO.cleanup()
        print("Test finished.")

if __name__ == "__main__":
    main() 