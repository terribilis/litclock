#!/usr/bin/env python3
"""
Mock GPIO module for testing on non-Raspberry Pi systems.
"""

# GPIO modes
BCM = 11
BOARD = 10
OUT = 1
IN = 0
HIGH = 1
LOW = 0
PUD_UP = 22
PUD_DOWN = 21
RISING = 31
FALLING = 32
BOTH = 33

# GPIO function names
FUNCTION_NAMES = {
    IN: "IN",
    OUT: "OUT",
    BCM: "BCM",
    BOARD: "BOARD",
    HIGH: "HIGH",
    LOW: "LOW",
    PUD_UP: "PUD_UP",
    PUD_DOWN: "PUD_DOWN",
    RISING: "RISING",
    FALLING: "FALLING",
    BOTH: "BOTH"
}

class GPIO:
    # Class variables to store pin states
    _mode = None
    _pins = {}
    _callbacks = {}

    @classmethod
    def setmode(cls, mode):
        """Set the GPIO mode (BCM or BOARD)"""
        if mode not in [BCM, BOARD]:
            raise ValueError("Invalid mode")
        cls._mode = mode
        cls._pins = {}

    @classmethod
    def getmode(cls):
        """Get the current GPIO mode"""
        return cls._mode

    @classmethod
    def setup(cls, pin, mode, pull_up_down=None):
        """Set up a GPIO pin"""
        cls._pins[pin] = {
            'mode': mode,
            'pull_up_down': pull_up_down,
            'value': LOW if pull_up_down == PUD_DOWN else HIGH
        }

    @classmethod
    def output(cls, pin, value):
        """Set the output value of a GPIO pin"""
        if pin not in cls._pins:
            raise RuntimeError("Pin not set up")
        if cls._pins[pin]['mode'] != OUT:
            raise RuntimeError("Pin not set up as output")
        cls._pins[pin]['value'] = value

    @classmethod
    def input(cls, pin):
        """Get the input value of a GPIO pin"""
        if pin not in cls._pins:
            raise RuntimeError("Pin not set up")
        return cls._pins[pin]['value']

    @classmethod
    def gpio_function(cls, pin):
        """Get the current function of a GPIO pin"""
        if pin not in cls._pins:
            return None
        return cls._pins[pin]['mode']

    @classmethod
    def digital_read(cls, pin):
        """Read the digital value of a GPIO pin"""
        return cls.input(pin)

    @classmethod
    def digital_write(cls, pin, value):
        """Write a digital value to a GPIO pin"""
        cls.output(pin, value)

    @classmethod
    def add_event_detect(cls, pin, edge, callback=None, bouncetime=None):
        """Add event detection to a GPIO pin"""
        if pin not in cls._pins:
            raise RuntimeError("Pin not set up")
        cls._callbacks[pin] = {
            'edge': edge,
            'callback': callback,
            'bouncetime': bouncetime
        }

    @classmethod
    def remove_event_detect(cls, pin):
        """Remove event detection from a GPIO pin"""
        if pin in cls._callbacks:
            del cls._callbacks[pin]

    @classmethod
    def cleanup(cls):
        """Clean up all GPIO settings"""
        cls._pins = {}
        cls._callbacks = {}
        cls._mode = None

    @classmethod
    def setwarnings(cls, flag):
        """Enable or disable warnings"""
        pass  # Mock implementation doesn't need to do anything 