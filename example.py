#!/usr/bin/env python3
"""
Example script for using the DisplayManager with the 13.3 inch e-ink display.
This example creates a simple image with text and shapes, then displays it.
"""

from e_ink_display_manager import DisplayManager
from PIL import Image, ImageDraw, ImageFont
import os
import time

def main():
    # Initialize the display manager - use mock mode if needed for testing
    # For real hardware, remove the use_mocks parameter or set it to False
    display = DisplayManager(use_mocks=True)  # Change to False for real hardware
    
    try:
        print("Initializing display...")
        display.init()
        
        print("Clearing display...")
        display.clear()
        time.sleep(1)  # Give the display time to refresh
        
        # Create a blank white image
        print("Creating image...")
        width = display.width
        height = display.height
        image = Image.new('L', (width, height), 255)  # 255: white
        
        # Get a drawing context
        draw = ImageDraw.Draw(image)
        
        # Draw a black border
        draw.rectangle([(0, 0), (width-1, height-1)], outline=0, width=5)
        
        # Draw some shapes
        margin = 50
        draw.rectangle([(margin, margin), (width//2 - margin, height//2 - margin)], 
                        fill=0, outline=0)  # Black rectangle
        
        # Draw a circle
        draw.ellipse([(width//2 + margin, margin), (width - margin, height//2 - margin)], 
                    fill=128, outline=0)  # Gray circle with black outline
        
        # Try to load a font (fallbacks provided)
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Common on Linux
        font_size = 60
        
        try:
            # First try the specified font
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            try:
                # Try a default system font - works on many systems
                font = ImageFont.truetype("Arial.ttf", font_size)
            except IOError:
                # Final fallback to default
                font = ImageFont.load_default()
                print("Using default font, specified fonts not found.")
        
        # Add text in the middle bottom area
        text = "13.3 inch e-ink Display"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_position = ((width - text_width) // 2, height - margin - text_height)
        
        draw.text(text_position, text, font=font, fill=0)
        
        # Add timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        draw.text((margin, height - margin//2), f"Generated: {timestamp}", fill=0)
        
        # Display the image
        print("Displaying image...")
        display.display(image)
        
        # Wait for a while
        print("Image displayed. Waiting 5 seconds before sleep...")
        time.sleep(5)
        
        # Put the display to sleep
        print("Putting display to sleep...")
        display.sleep()
        print("Done.")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        # Clean up
        display.module_exit()

if __name__ == "__main__":
    main() 