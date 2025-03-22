#!/usr/bin/env python3
"""
Mock RPi module for testing on non-Raspberry Pi systems.
"""

from .mock_gpio import GPIO

__all__ = ['GPIO'] 