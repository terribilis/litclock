#!/usr/bin/env python3
"""
Example script demonstrating 4-level grayscale with the 13.3 inch e-ink display.
"""

from e_ink_display_manager import DisplayManager
from PIL import Image, ImageDraw, ImageFont, ImageOps
import time
import os
import sys
import numpy as np

def create_gradient_image(width, height):
    """Create a grayscale gradient image."""
    # Create gradient from left to right
    gradient = np.linspace(0, 255, width, dtype=np.uint8)
    # Repeat the gradient for each row
    gradient = np.tile(gradient, (height, 1))
    # Convert numpy array to PIL Image
    return Image.fromarray(gradient)

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
        width = display.width
        height = display.height
        image = Image.new('L', (width, height), 255)  # 255: white
        draw = ImageDraw.Draw(image)
        
        # Draw a black border
        draw.rectangle([(0, 0), (width-1, height-1)], outline=0, width=5)
        
        # Draw title
        title_font_size = 60
        try:
            title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", title_font_size)
        except IOError:
            try:
                title_font = ImageFont.truetype("Arial.ttf", title_font_size)
            except IOError:
                title_font = ImageFont.load_default()
                print("Using default font, specified fonts not found.")
        
        title_text = "4-Level Grayscale Demonstration"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_position = ((width - title_width) // 2, 50)
        draw.text(title_position, title_text, font=title_font, fill=0)
        
        # Create sections for demonstration
        margin = 100
        section_height = 150
        
        # Section 1: Grayscale samples
        y_pos = 150
        draw.text((margin, y_pos), "1. Four Grayscale Levels:", font=title_font, fill=0)
        y_pos += 80
        
        # Draw the four grayscale levels
        box_width = (width - 2*margin) // 4
        box_height = section_height
        for i, gray_level in enumerate([255, 170, 85, 0]):  # White, Light Gray, Dark Gray, Black
            box_left = margin + i * box_width
            box_right = box_left + box_width - 20  # 20px spacing
            draw.rectangle([(box_left, y_pos), (box_right, y_pos + box_height)], fill=gray_level, outline=0)
            
            # Label the gray level
            label = "White" if gray_level == 255 else "Black" if gray_level == 0 else f"Gray {i}"
            label_bbox = draw.textbbox((0, 0), label, font=title_font)
            label_width = label_bbox[2] - label_bbox[0]
            label_x = box_left + (box_width - label_width) // 2 - 10  # 10px adjustment
            draw.text((label_x, y_pos + box_height + 10), label, font=title_font, fill=0)
        
        # Section 2: Gradient
        y_pos += box_height + 80
        draw.text((margin, y_pos), "2. Horizontal Gradient:", font=title_font, fill=0)
        y_pos += 80
        
        # Create gradient image
        gradient_width = width - 2*margin
        gradient_height = section_height
        gradient_image = create_gradient_image(gradient_width, gradient_height)
        
        # Paste gradient into main image
        image.paste(gradient_image, (margin, y_pos))
        
        # Draw border around gradient
        draw.rectangle([(margin, y_pos), (margin + gradient_width - 1, y_pos + gradient_height - 1)], outline=0, width=2)
        
        # Footer
        footer_text = "Note: E-ink displays quantize grayscale to nearest available level"
        footer_bbox = draw.textbbox((0, 0), footer_text, font=title_font)
        footer_width = footer_bbox[2] - footer_bbox[0]
        footer_y = height - 100
        draw.text(((width - footer_width) // 2, footer_y), footer_text, font=title_font, fill=0)
        
        # Display the image with 4 gray levels
        print("Displaying 4-level grayscale image...")
        display.display_4gray(image)
        print("Image displayed.")
        
        # Wait for a while
        time.sleep(10)
        
        # Put the display to sleep
        print("Putting display to sleep...")
        display.sleep()
        print("Done.")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        display.module_exit()

if __name__ == "__main__":
    main() 