#!/usr/bin/env python3
"""
Mock SPI module for testing on non-Raspberry Pi systems.
"""

class SpiDev:
    def __init__(self, bus, device):
        self.bus = bus
        self.device = device
        self.mode = 0
        self.max_speed_hz = 0
        self.bits_per_word = 8
        self._buffer = []

    def open(self, bus, device):
        """Open the SPI device"""
        self.bus = bus
        self.device = device

    def close(self):
        """Close the SPI device"""
        pass

    def xfer2(self, data):
        """Transfer data to and from the SPI device"""
        self._buffer.extend(data)
        return [0] * len(data)  # Return dummy data

    def writebytes(self, data):
        """Write bytes to the SPI device"""
        self._buffer.extend(data)

    def readbytes(self, length):
        """Read bytes from the SPI device"""
        return [0] * length  # Return dummy data

    def fileno(self):
        """Return the file descriptor"""
        return -1  # Dummy file descriptor 