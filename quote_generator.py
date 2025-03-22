#!/usr/bin/env python3
import os
import json
import pandas as pd
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

class QuoteGenerator:
    def __init__(self):
        self.width = 960  # 13.3" e-paper HAT (B) resolution
        self.height = 680
        self.background_color = (255, 255, 255)  # White
        self.text_color = (0, 0, 0)  # Black
        self.font_size = 24
        self.data_dir = Path('data')
        self.images_dir = Path('images/generated')
        self.load_config()
        self.load_quotes()

    def load_config(self):
        """Load configuration from config.json"""
        config_path = self.data_dir / 'config.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.config = json.load(f)
                self.font_size = self.config.get('font_size', 24)
        else:
            self.config = {
                'update_interval': 300,
                'display_brightness': 100,
                'font_size': 24,
                'show_book_info': True,
                'show_author': True,
                'content_filter': 'all'  # Options: 'sfw', 'nsfw', 'all'
            }
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)

    def convert_csv_to_json(self):
        """Convert quotes.csv to quotes.json"""
        csv_file = self.data_dir / 'litclock_annotated.csv'
        if not csv_file.exists():
            csv_file = self.data_dir / 'quotes.csv'
        
        json_file = self.data_dir / 'quotes.json'
        
        if csv_file.exists():
            try:
                # Read CSV with pipe delimiter and no header
                df = pd.read_csv(csv_file, sep='|', header=None, 
                                names=['time_key', 'display_time', 'quote', 'book', 'author', 'rating'])
                
                quotes_dict = {}
                
                for _, row in df.iterrows():
                    time_key = row['time_key']
                    
                    # Default to 'unknown' if rating is missing or empty
                    rating = row.get('rating', 'unknown')
                    if pd.isna(rating) or rating == '':
                        rating = 'unknown'
                        
                    quotes_dict[time_key] = {
                        'display_time': row['display_time'],
                        'quote': row['quote'],
                        'book': row['book'],
                        'author': row['author'],
                        'rating': rating.lower()
                    }
                
                with open(json_file, 'w') as f:
                    json.dump(quotes_dict, f, indent=4)
                print(f"Converted {csv_file} to {json_file}")
                return True
            except Exception as e:
                print(f"Error converting CSV to JSON: {e}")
                return False
        else:
            print(f"CSV file not found: {csv_file}")
            return False

    def load_quotes(self):
        """Load quotes from quotes.json"""
        quotes_path = self.data_dir / 'quotes.json'
        if quotes_path.exists():
            with open(quotes_path, 'r') as f:
                self.quotes = json.load(f)
        else:
            self.quotes = {}

    def get_current_quote(self):
        """Get the quote for the current time"""
        current_time = datetime.now().strftime('%H:%M')
        
        # Apply content filter if set
        content_filter = self.config.get('content_filter', 'all')
        available_quotes = {}
        
        if content_filter == 'all':
            available_quotes = self.quotes
        else:
            for time_key, quote_data in self.quotes.items():
                rating = quote_data.get('rating', '').lower()
                if content_filter == 'sfw' and rating == 'sfw':
                    available_quotes[time_key] = quote_data
                elif content_filter == 'nsfw' and rating == 'nsfw':
                    available_quotes[time_key] = quote_data
                elif content_filter == 'unknown' or content_filter == 'all':
                    available_quotes[time_key] = quote_data
        
        # Try to find a quote for the current time
        quote = available_quotes.get(current_time)
        
        # If no exact match, try with leading zeros for hour (e.g., '2:30' to '02:30')
        if not quote and ':' in current_time:
            hour, minute = current_time.split(':')
            padded_time = f"{int(hour):02d}:{minute}"
            quote = available_quotes.get(padded_time)
        
        # Return quote or default message
        if quote:
            return quote
        else:
            return {
                'display_time': current_time,
                'quote': 'No quote available for this time.',
                'book': '',
                'author': '',
                'rating': 'sfw'
            }

    def create_image(self):
        """Create a new image with the current quote"""
        # Create a new image with white background
        image = Image.new('RGB', (self.width, self.height), self.background_color)
        draw = ImageDraw.Draw(image)

        # Load fonts
        try:
            time_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', self.font_size * 2)
            quote_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', self.font_size)
            info_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Italic.ttf', self.font_size - 4)
        except:
            # Fallback to default font if DejaVu is not available
            time_font = ImageFont.load_default()
            quote_font = ImageFont.load_default()
            info_font = ImageFont.load_default()

        # Get current quote
        quote_data = self.get_current_quote()
        
        # Draw time
        time_text = quote_data['display_time']
        time_bbox = draw.textbbox((0, 0), time_text, font=time_font)
        time_width = time_bbox[2] - time_bbox[0]
        time_height = time_bbox[3] - time_bbox[1]
        draw.text(
            ((self.width - time_width) // 2, 50),
            time_text,
            font=time_font,
            fill=self.text_color
        )

        # Draw quote
        quote_text = quote_data['quote']
        # Word wrap the quote
        words = quote_text.split()
        lines = []
        current_line = []
        current_width = 0
        max_width = self.width - 100  # Leave 50px margin on each side

        for word in words:
            word_width = draw.textbbox((0, 0), word + ' ', font=quote_font)[2]
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
        if current_line:
            lines.append(' '.join(current_line))

        # Draw each line of the quote
        y_position = 150
        for line in lines:
            line_bbox = draw.textbbox((0, 0), line, font=quote_font)
            line_width = line_bbox[2] - line_bbox[0]
            draw.text(
                ((self.width - line_width) // 2, y_position),
                line,
                font=quote_font,
                fill=self.text_color
            )
            y_position += self.font_size + 10

        # Draw book and author if configured
        if self.config.get('show_book_info', True):
            info_text = f"{quote_data['book']}"
            if self.config.get('show_author', True) and quote_data['author']:
                info_text += f" by {quote_data['author']}"
            
            info_bbox = draw.textbbox((0, 0), info_text, font=info_font)
            info_width = info_bbox[2] - info_bbox[0]
            draw.text(
                ((self.width - info_width) // 2, self.height - 100),
                info_text,
                font=info_font,
                fill=self.text_color
            )

        return image

    def save_image(self, image):
        """Save the generated image"""
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as PNG
        image.save(self.images_dir / 'current_display.png', 'PNG')
        print("Generated new display image")

def main():
    generator = QuoteGenerator()
    image = generator.create_image()
    generator.save_image(image)

if __name__ == "__main__":
    main() 