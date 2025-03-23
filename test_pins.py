#!/usr/bin/env python3
import sys
import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("ERROR: RPi.GPIO module not found. Make sure you're running on a Raspberry Pi.")
    sys.exit(1)

# Pin definitions using BOARD numbering (physical pin numbers)
RST_PIN = 11    # Physical pin 11 (BCM 17)
DC_PIN = 22     # Physical pin 22 (BCM 25)
CS_PIN = 24     # Physical pin 24 (BCM 8, CE0)
BUSY_PIN = 18   # Physical pin 18 (BCM 24)

def setup_pins():
    print("Setting up GPIO pins...")
    # Use BOARD pin numbering
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    
    # Set up pins
    GPIO.setup(RST_PIN, GPIO.OUT)
    GPIO.setup(DC_PIN, GPIO.OUT)
    GPIO.setup(CS_PIN, GPIO.OUT)
    GPIO.setup(BUSY_PIN, GPIO.IN)
    
    print("GPIO pins set up successfully.")

def test_output_pins():
    print("\nTesting output pins...")
    pins = [RST_PIN, DC_PIN, CS_PIN]
    pin_names = ["RST", "DC", "CS"]
    
    for i, pin in enumerate(pins):
        name = pin_names[i]
        print(f"\nTesting {name} pin (Pin {pin}):")
        
        # Set pin HIGH
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.5)
        state = GPIO.input(pin)
        print(f"  {name} pin set to HIGH, reading: {state} (should be 1)")
        
        # Set pin LOW
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.5)
        state = GPIO.input(pin)
        print(f"  {name} pin set to LOW, reading: {state} (should be 0)")
        
        # End with pin HIGH
        GPIO.output(pin, GPIO.HIGH)
    
    print("\nOutput pin tests completed.")

def test_busy_pin():
    print("\nTesting BUSY input pin...")
    # Read the BUSY pin
    state = GPIO.input(BUSY_PIN)
    print(f"BUSY pin (Pin {BUSY_PIN}) current state: {state}")
    print("Note: The BUSY pin is an input pin, its state depends on the e-paper display.")
    print("Typically it should be LOW (0) when the display is idle, HIGH (1) when busy.")
    print("\nMonitoring BUSY pin for 5 seconds...")
    
    start_time = time.time()
    changes = 0
    last_state = state
    
    while time.time() - start_time < 5:
        current_state = GPIO.input(BUSY_PIN)
        if current_state != last_state:
            changes += 1
            last_state = current_state
            print(f"  BUSY pin changed to: {current_state} at {time.time() - start_time:.2f}s")
        time.sleep(0.1)
    
    print(f"BUSY pin changed state {changes} times in 5 seconds.")
    print("If the BUSY pin never changes, it might indicate a connection issue.")
    print("BUSY pin test completed.")

def reset_sequence():
    print("\nTesting reset sequence...")
    print("Setting RST pin HIGH")
    GPIO.output(RST_PIN, GPIO.HIGH)
    time.sleep(0.2)
    print("Setting RST pin LOW")
    GPIO.output(RST_PIN, GPIO.LOW)
    time.sleep(0.2)
    print("Setting RST pin HIGH")
    GPIO.output(RST_PIN, GPIO.HIGH)
    time.sleep(0.2)
    print("Reset sequence completed.")
    print("Monitoring BUSY pin for 3 seconds after reset...")
    
    start_time = time.time()
    changes = 0
    last_state = GPIO.input(BUSY_PIN)
    
    while time.time() - start_time < 3:
        current_state = GPIO.input(BUSY_PIN)
        if current_state != last_state:
            changes += 1
            last_state = current_state
            print(f"  BUSY pin changed to: {current_state} at {time.time() - start_time:.2f}s")
        time.sleep(0.1)
    
    print(f"BUSY pin changed state {changes} times in 3 seconds after reset.")

def main():
    print("E-Paper Display Pin Test")
    print("========================")
    print("This script tests the GPIO pins used for the e-paper display.")
    print("Pin assignments (BOARD numbering):")
    print(f"RST:  Pin {RST_PIN}")
    print(f"DC:   Pin {DC_PIN}")
    print(f"CS:   Pin {CS_PIN}")
    print(f"BUSY: Pin {BUSY_PIN}")
    print("SPI: Uses hardware SPI (MOSI: Pin 19, SCK: Pin 23)")
    
    try:
        setup_pins()
        test_output_pins()
        test_busy_pin()
        reset_sequence()
        
        print("\nPin test completed successfully!")
        print("If all tests passed, your GPIO pins are correctly connected.")
        print("If the BUSY pin is not changing state, check your connections.")
        
    except Exception as e:
        print(f"\nError during pin test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\nCleaning up GPIO...")
        GPIO.cleanup()
        print("GPIO cleanup completed.")

if __name__ == "__main__":
    main() 