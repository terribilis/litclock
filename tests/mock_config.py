#!/usr/bin/env python3
import os

# Flag to determine whether to use mock modules
USE_MOCKS = os.environ.get('USE_MOCKS', '1') == '1'

# Import paths for mock modules
MOCK_GPIO_PATH = 'tests.RPi.GPIO.GPIO'
MOCK_SPIDEV_PATH = 'tests.spidev'
MOCK_SPI_PATH = 'tests.mock_spi' 