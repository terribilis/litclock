#!/usr/bin/env python3
"""
Mock spidev module for testing on non-Raspberry Pi systems.
"""

from .mock_spi import SpiDev

__all__ = ['SpiDev'] 