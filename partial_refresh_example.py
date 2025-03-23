#!/usr/bin/env python3
"""
Example script demonstrating partial refresh with the 13.3 inch e-ink display.
This example creates a digital clock that only refreshes the time area.
"""

from e_ink_display_manager import DisplayManager
from PIL import Image, ImageDraw, ImageFont
import time
import sys

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
        
        # Create a blank white image for the base display
        width = display.width
        height = display.height
        base_image = Image.new('L', (width, height), 255)  # 255: white
        draw = ImageDraw.Draw(base_image)
        
        # Draw a black border and title
        draw.rectangle([(0, 0), (width-1, height-1)], outline=0, width=5)
        
        # Try to load a font (fallbacks provided)
        title_font_size = 60
        time_font_size = 120
        
        try:
            # Try to load system fonts
            title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", title_font_size)
            time_font = ImageFont.truetype("DejaVuSans-Bold.ttf", time_font_size)
        except IOError:
            try:
                # Try another common font
                title_font = ImageFont.truetype("Arial.ttf", title_font_size)
                time_font = ImageFont.truetype("Arial.ttf", time_font_size)
            except IOError:
                # Final fallback to default
                title_font = ImageFont.load_default()
                time_font = ImageFont.load_default()
                print("Using default font, specified fonts not found.")
        
        # Add static text
        title_text = "E-Ink Digital Clock with Partial Refresh"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_position = ((width - title_width) // 2, 50)
        draw.text(title_position, title_text, font=title_font, fill=0)
        
        # Draw a rectangle around the time area
        time_text = "00:00:00"
        time_bbox = draw.textbbox((0, 0), time_text, font=time_font)
        time_width = time_bbox[2] - time_bbox[0]
        time_height = time_bbox[3] - time_bbox[1]
        
        # Center the time on the screen
        time_x = (width - time_width) // 2
        time_y = (height - time_height) // 2
        
        # Add some padding around the time for the partial refresh area
        padding = 20
        time_area = (
            time_x - padding, 
            time_y - padding,
            time_x + time_width + padding,
            time_y + time_height + padding
        )
        
        # Draw a light gray rectangle around the time area to show the partial refresh region
        draw.rectangle(time_area, outline=128, width=2)
        
        # Add a footer text
        footer_text = "Partial refresh demo - only the time area updates"
        footer_bbox = draw.textbbox((0, 0), footer_text, font=title_font)
        footer_width = footer_bbox[2] - footer_bbox[0]
        footer_position = ((width - footer_width) // 2, height - 100)
        draw.text(footer_position, footer_text, font=title_font, fill=0)
        
        # Display the base image
        print("Displaying base image...")
        display.display_base(base_image)
        time.sleep(2)  # Give the display time to refresh
        
        # Initialize the display for partial refresh
        display.init_partial()
        
        # Update the time every second with partial refresh
        print("Starting partial refresh updates...")
        try:
            for _ in range(10):  # Update for 10 seconds
                # Create a new image for the time area
                time_image = Image.new('L', (
                    time_area[2] - time_area[0], 
                    time_area[3] - time_area[1]
                ), 255)
                time_draw = ImageDraw.Draw(time_image)
                
                # Get current time
                current_time = time.strftime("%H:%M:%S")
                
                # Calculate the position of the time text within the time area image
                time_text_bbox = time_draw.textbbox((0, 0), current_time, font=time_font)
                time_text_width = time_text_bbox[2] - time_text_bbox[0]
                time_text_height = time_text_bbox[3] - time_text_bbox[1]
                time_text_x = (time_image.width - time_text_width) // 2
                time_text_y = (time_image.height - time_text_height) // 2
                
                # Draw the time on the partial image
                time_draw.text((time_text_x, time_text_y), current_time, font=time_font, fill=0)
                
                # Update only the time area
                print(f"Updating time to {current_time}")
                display.display_partial(
                    time_image, 
                    time_area[0], 
                    time_area[1], 
                    time_area[2], 
                    time_area[3]
                )
                
                # Wait for 1 second
                time.sleep(1)
            
            print("Partial refresh demo completed.")
        except KeyboardInterrupt:
            print("Interrupted by user.")
        
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