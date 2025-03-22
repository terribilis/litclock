#!/usr/bin/env python3
"""
Mock GPIO module for testing on non-Raspberry Pi systems.
"""

import time

class GPIO:
    """Mock GPIO class for testing."""
    # GPIO modes
    BCM = 11
    BOARD = 10

    # GPIO states
    OUT = 0
    IN = 1
    HIGH = 1
    LOW = 0

    # Pin modes
    PUD_OFF = 0
    PUD_DOWN = 1
    PUD_UP = 2

    # Edge detection
    RISING = 31
    FALLING = 32
    BOTH = 33

    # Current mode
    _mode = None
    _warnings = True
    _pin_states = {}
    _pin_modes = {}
    _event_callbacks = {}
    _busy_pin = 24  # BUSY_PIN from DisplayManager
    _busy_state = 0
    _busy_timeout = 0.1  # 100ms timeout for busy state

    @classmethod
    def setwarnings(cls, flag):
        """Enable or disable warnings."""
        cls._warnings = flag

    @classmethod
    def setmode(cls, mode):
        """Set the pin numbering mode."""
        if mode not in [cls.BCM, cls.BOARD]:
            raise ValueError("Invalid GPIO mode")
        cls._mode = mode

    @classmethod
    def getmode(cls):
        """Get the current pin numbering mode."""
        return cls._mode

    @classmethod
    def setup(cls, pin, mode, initial=None):
        """Set up a GPIO pin."""
        if mode not in [cls.OUT, cls.IN]:
            raise ValueError("Invalid pin mode")
        cls._pin_modes[pin] = mode
        if initial is not None:
            cls._pin_states[pin] = initial
        else:
            cls._pin_states[pin] = cls.LOW if mode == cls.OUT else cls.HIGH
        if pin == cls._busy_pin:
            cls._busy_state = 0

    @classmethod
    def output(cls, pin, state):
        """Set the output state of a pin."""
        if pin not in cls._pin_modes:
            cls.setup(pin, cls.OUT)
        cls._pin_states[pin] = state
        if pin == cls._busy_pin:
            cls._busy_state = state

    @classmethod
    def input(cls, pin):
        """Read the state of a pin."""
        if pin not in cls._pin_modes:
            cls.setup(pin, cls.IN)
        if pin == cls._busy_pin:
            # Simulate busy pin behavior
            if cls._busy_state == 1:
                # After a short delay, set busy to 0
                time.sleep(cls._busy_timeout)
                cls._busy_state = 0
            return cls._busy_state
        return cls._pin_states.get(pin, cls.HIGH)

    @classmethod
    def cleanup(cls, pin=None):
        """Clean up GPIO pins."""
        if pin is None:
            # Set all pins to LOW before cleanup
            for p in list(cls._pin_states.keys()):
                cls.output(p, cls.LOW)
            cls._pin_states.clear()
            cls._pin_modes.clear()
            cls._event_callbacks.clear()
            cls._mode = None
            cls._busy_state = 0
        else:
            # Set specific pin to LOW before cleanup
            if pin in cls._pin_states:
                cls.output(pin, cls.LOW)
                del cls._pin_states[pin]
            if pin in cls._pin_modes:
                del cls._pin_modes[pin]
            if pin in cls._event_callbacks:
                del cls._event_callbacks[pin]
            if pin == cls._busy_pin:
                cls._busy_state = 0

    @classmethod
    def add_event_detect(cls, pin, edge, callback=None, bouncetime=None):
        """Add event detection to a pin."""
        cls._event_callbacks[pin] = callback

    @classmethod
    def remove_event_detect(cls, pin):
        """Remove event detection from a pin."""
        if pin in cls._event_callbacks:
            del cls._event_callbacks[pin]

    @classmethod
    def event_detected(cls, pin):
        """Check if an event was detected on a pin."""
        return False

    @classmethod
    def wait_for_edge(cls, pin, edge, timeout=None):
        """Wait for an edge event on a pin."""
        if pin not in cls._pin_modes:
            raise RuntimeError("Pin not set up")
        if edge not in [cls.RISING, cls.FALLING, cls.BOTH]:
            raise ValueError("Invalid edge")
        return True

    @classmethod
    def gpio_function(cls, pin):
        """Get the function of a pin."""
        if pin == cls._busy_pin:
            return cls.IN  # BUSY_PIN is always an input
        return cls._pin_modes.get(pin, cls.OUT)  # Default to OUT for testing

    @classmethod
    def PWM(cls, pin, frequency):
        """Create a PWM instance."""
        class MockPWM:
            def __init__(self, pin, frequency):
                self.pin = pin
                self.frequency = frequency
                self.duty_cycle = 0
                self.started = False
            
            def start(self, duty_cycle):
                self.duty_cycle = duty_cycle
                self.started = True
            
            def stop(self):
                self.started = False
            
            def ChangeDutyCycle(self, duty_cycle):
                self.duty_cycle = duty_cycle
            
            def ChangeFrequency(self, frequency):
                self.frequency = frequency
        return MockPWM(pin, frequency) 