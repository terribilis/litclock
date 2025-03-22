#!/usr/bin/env python3
import unittest
import os
import json
from datetime import datetime
from PIL import Image
from pathlib import Path
import shutil
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from quote_generator import QuoteGenerator

class TestQuoteGenerator(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        # Create test directories
        self.test_dir = Path('test_data')
        self.test_dir.mkdir(exist_ok=True)
        
        # Create test data directory
        self.data_dir = self.test_dir / 'data'
        self.data_dir.mkdir(exist_ok=True)
        
        # Create test images directory
        self.images_dir = self.test_dir / 'images' / 'generated'
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test quotes.csv
        self.quotes_csv = self.data_dir / 'quotes.csv'
        self.sample_quotes = [
            "13:35|1:35 P.M.|Fletcher checked his watch again. It was 1:35 P.M. He sighed and asked the receptionist if he could use the washroom.|Sons of Fortune|Jeffrey Archer|sfw",
            "14:00|2:00 P.M.|Time is what we want most, but what we use worst.|The Way of the World|William Congreve|sfw",
            "15:30|3:30 P.M.|The only way to do great work is to love what you do.|Steve Jobs|Walter Isaacson|sfw"
        ]
        with open(self.quotes_csv, 'w') as f:
            f.write("HH:MM|H:MM A.M.|Quote|Book|Author|Rating\n")
            f.write("\n".join(self.sample_quotes))
        
        # Create test config.json
        self.config_json = self.data_dir / 'config.json'
        self.test_config = {
            'update_interval': 300,
            'display_brightness': 100,
            'font_size': 24,
            'show_book_info': True,
            'show_author': True
        }
        with open(self.config_json, 'w') as f:
            json.dump(self.test_config, f)
        
        # Initialize QuoteGenerator with test directories
        self.generator = QuoteGenerator()
        self.generator.data_dir = self.data_dir
        self.generator.images_dir = self.images_dir

    def tearDown(self):
        """Clean up test environment after each test"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_load_config(self):
        """Test loading configuration from JSON file"""
        self.generator.load_config()
        self.assertEqual(self.generator.font_size, self.test_config['font_size'])
        self.assertEqual(self.generator.config, self.test_config)

    def test_load_quotes(self):
        """Test loading quotes from JSON file"""
        # First convert CSV to JSON
        self.generator.convert_csv_to_json()
        
        # Then test loading quotes
        self.generator.load_quotes()
        self.assertIsInstance(self.generator.quotes, dict)
        self.assertEqual(len(self.generator.quotes), len(self.sample_quotes))

    def test_get_current_quote(self):
        """Test getting quote for current time"""
        self.generator.load_quotes()
        quote = self.generator.get_current_quote()
        self.assertIsInstance(quote, dict)
        self.assertIn('display_time', quote)
        self.assertIn('quote', quote)
        self.assertIn('book', quote)
        self.assertIn('author', quote)

    def test_create_image(self):
        """Test image creation"""
        image = self.generator.create_image()
        self.assertIsInstance(image, Image.Image)
        self.assertEqual(image.size, (self.generator.width, self.generator.height))
        self.assertEqual(image.mode, 'RGB')

    def test_save_image(self):
        """Test saving generated image"""
        image = self.generator.create_image()
        self.generator.save_image(image)
        saved_image_path = self.images_dir / 'current_display.png'
        self.assertTrue(saved_image_path.exists())
        
        # Verify saved image
        saved_image = Image.open(saved_image_path)
        self.assertEqual(saved_image.size, (self.generator.width, self.generator.height))
        self.assertEqual(saved_image.mode, 'RGB')

    def test_word_wrapping(self):
        """Test quote word wrapping"""
        # Create a long quote that should wrap
        long_quote = "This is a very long quote that should definitely wrap to multiple lines because it contains many words and should not fit on a single line of the display. It should be properly formatted and centered on the display."
        
        # Create a test quote entry
        test_quote = {
            'display_time': '12:00',
            'quote': long_quote,
            'book': 'Test Book',
            'author': 'Test Author'
        }
        
        # Temporarily replace quotes with test quote
        original_quotes = self.generator.quotes
        self.generator.quotes = {'12:00': test_quote}
        
        # Generate image
        image = self.generator.create_image()
        self.assertIsInstance(image, Image.Image)
        
        # Restore original quotes
        self.generator.quotes = original_quotes

    def test_missing_font_fallback(self):
        """Test fallback to default font when system fonts are missing"""
        # Temporarily modify font paths to trigger fallback
        original_font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
        self.generator.font_path = '/nonexistent/font.ttf'
        
        # Should still create image with default font
        image = self.generator.create_image()
        self.assertIsInstance(image, Image.Image)
        
        # Restore original font path
        self.generator.font_path = original_font_path

if __name__ == '__main__':
    unittest.main() 