#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import logging
import time
from PIL import Image, ImageDraw, ImageFont
import traceback

# Add the project root to the path so we can import modules
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# Import the e-paper display module
from utils import epd13in3b

# Create pic directory if it doesn't exist
picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
if not os.path.exists(picdir):
    os.makedirs(picdir)

logging.basicConfig(level=logging.DEBUG)

try:
    logging.info("epd13in3b Demo")
    
    # Initialize the display
    epd = epd13in3b.EPD()
    
    logging.info("Init and Clear")
    epd.init()
    epd.Clear()
    
    # Use default fonts
    font24 = ImageFont.load_default()
    font18 = ImageFont.load_default()
    
    # Drawing on the Horizontal image
    logging.info("Drawing on the Horizontal image...")
    HBlackimage = Image.new('1', (epd.width, epd.height), 255)  # 255: white
    HRedimage = Image.new('1', (epd.width, epd.height), 255)    # 255: white
    
    drawblack = ImageDraw.Draw(HBlackimage)
    drawred = ImageDraw.Draw(HRedimage)
    
    # Draw text and shapes
    drawblack.text((10, 0), 'Hello World', font=font24, fill=0)
    drawred.text((10, 30), '13.3inch e-Paper Test', font=font24, fill=0)
    
    # Draw some shapes
    drawred.line((20, 50, 70, 100), fill=0)
    drawblack.line((70, 50, 20, 100), fill=0)
    drawred.rectangle((20, 50, 70, 100), outline=0)
    drawblack.line((165, 50, 165, 100), fill=0)
    drawred.line((140, 75, 190, 75), fill=0)
    drawblack.arc((140, 50, 190, 100), 0, 360, fill=0)
    drawred.rectangle((80, 50, 130, 100), fill=0)
    drawblack.chord((200, 50, 250, 100), 0, 360, fill=0)
    
    # Display the image
    logging.info("Display image")
    epd.display_Base(epd.getbuffer(HBlackimage), epd.getbuffer(HRedimage))
    time.sleep(2)
    
    # Partial update demonstration - show clock for 10 seconds
    logging.info("Show time with partial updates")
    for i in range(10):
        drawblack.rectangle((0, 110, 120, 150), fill=255)  # Clear the time area
        drawblack.text((10, 120), time.strftime('%H:%M:%S'), font=font24, fill=0)
        epd.display_Partial(epd.getbuffer(HBlackimage), 0, 110, 120, 160)
        time.sleep(1)
    
    # Clear the display
    logging.info("Clear...")
    epd.init()
    epd.Clear()
    
    # Put display to sleep
    logging.info("Goto Sleep...")
    epd.sleep()
    
except IOError as e:
    logging.error(f"IOError: {e}")
    traceback.print_exc()
    
except KeyboardInterrupt:    
    logging.info("Ctrl+C pressed, exiting...")
    epd13in3b.epdconfig.module_exit(cleanup=True)
    
except Exception as e:
    logging.error(f"Error: {e}")
    traceback.print_exc()
    
finally:
    # Make sure we clean up
    try:
        logging.info("Cleaning up...")
        epd13in3b.epdconfig.module_exit(cleanup=True)
    except:
        pass 