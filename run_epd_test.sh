#!/bin/bash
# Run this script to test the e-paper display module

# Change to the utils directory to ensure local imports work
cd "$(dirname "$0")/utils"

# Run the test script
python3 epd13in3_test.py

# Return to original directory
cd - 