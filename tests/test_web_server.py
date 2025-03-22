#!/usr/bin/env python3
import unittest
import os
import json
import tempfile
import shutil
from pathlib import Path
import requests
import threading
import time
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web_server import app, quote_generator, display_manager

class TestWebServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment before all tests"""
        # Create a temporary directory for test files
        cls.test_dir = Path(tempfile.mkdtemp())
        
        # Create test data directory
        cls.data_dir = cls.test_dir / 'data'
        cls.data_dir.mkdir(exist_ok=True)
        
        # Create test images directory
        cls.images_dir = cls.test_dir / 'images' / 'generated'
        cls.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test quotes.csv
        cls.quotes_csv = cls.data_dir / 'quotes.csv'
        cls.sample_quotes = [
            "13:35|1:35 P.M.|Fletcher checked his watch again. It was 1:35 P.M. He sighed and asked the receptionist if he could use the washroom.|Sons of Fortune|Jeffrey Archer|sfw",
            "14:00|2:00 P.M.|Time is what we want most, but what we use worst.|The Way of the World|William Congreve|sfw",
            "15:30|3:30 P.M.|The only way to do great work is to love what you do.|Steve Jobs|Walter Isaacson|sfw"
        ]
        with open(cls.quotes_csv, 'w') as f:
            f.write("HH:MM|H:MM A.M.|Quote|Book|Author|Rating\n")
            f.write("\n".join(cls.sample_quotes))
        
        # Create test config.json
        cls.config_json = cls.data_dir / 'config.json'
        cls.test_config = {
            'update_interval': 300,
            'display_brightness': 100,
            'font_size': 24,
            'show_book_info': True,
            'show_author': True
        }
        with open(cls.config_json, 'w') as f:
            json.dump(cls.test_config, f)
        
        # Configure the QuoteGenerator to use test directories
        quote_generator.data_dir = cls.data_dir
        quote_generator.images_dir = cls.images_dir
        quote_generator.load_config()
        quote_generator.convert_csv_to_json()
        quote_generator.load_quotes()
        
        # Start the Flask app in a separate thread
        cls.server_thread = threading.Thread(target=app.run, kwargs={'host': '127.0.0.1', 'port': 5001})
        cls.server_thread.daemon = True
        cls.server_thread.start()
        
        # Wait for the server to start
        time.sleep(1)
        
        # Set up the base URL for requests
        cls.base_url = 'http://127.0.0.1:5001'

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment after all tests"""
        # Remove the temporary directory
        shutil.rmtree(cls.test_dir)

    def setUp(self):
        """Set up before each test"""
        # Reset the test files to their initial state
        with open(self.quotes_csv, 'w') as f:
            f.write("HH:MM|H:MM A.M.|Quote|Book|Author|Rating\n")
            f.write("\n".join(self.sample_quotes))
        
        with open(self.config_json, 'w') as f:
            json.dump(self.test_config, f)
        
        # Reload configuration and quotes
        quote_generator.load_config()
        quote_generator.convert_csv_to_json()
        quote_generator.load_quotes()

    def test_index_page(self):
        """Test the main page loads"""
        response = requests.get(f'{self.base_url}/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Quote Clock Settings', response.text)

    def test_get_config(self):
        """Test getting configuration"""
        response = requests.get(f'{self.base_url}/api/config')
        self.assertEqual(response.status_code, 200)
        config = response.json()
        self.assertEqual(config, self.test_config)

    def test_update_config(self):
        """Test updating configuration"""
        new_config = {
            'update_interval': 600,
            'display_brightness': 80,
            'font_size': 28,
            'show_book_info': False,
            'show_author': True
        }
        
        response = requests.post(
            f'{self.base_url}/api/config',
            json=new_config
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify the config was updated
        response = requests.get(f'{self.base_url}/api/config')
        self.assertEqual(response.json(), new_config)

    def test_get_quotes(self):
        """Test getting quotes"""
        response = requests.get(f'{self.base_url}/api/quotes')
        self.assertEqual(response.status_code, 200)
        quotes = response.json()
        self.assertEqual(len(quotes), len(self.sample_quotes))

    def test_upload_quotes(self):
        """Test uploading new quotes"""
        # Create a temporary CSV file with new quotes
        new_quotes = [
            "16:00|4:00 P.M.|New test quote 1|Test Book 1|Test Author 1|sfw",
            "17:00|5:00 P.M.|New test quote 2|Test Book 2|Test Author 2|sfw"
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("HH:MM|H:MM A.M.|Quote|Book|Author|Rating\n")
            f.write("\n".join(new_quotes))
        
        # Upload the file
        with open(f.name, 'rb') as f:
            response = requests.post(
                f'{self.base_url}/api/quotes',
                files={'file': f}
            )
        
        # Clean up the temporary file
        os.unlink(f.name)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify the quotes were updated
        response = requests.get(f'{self.base_url}/api/quotes')
        quotes = response.json()
        self.assertEqual(len(quotes), len(new_quotes))

    def test_display_control(self):
        """Test display control endpoints"""
        # Test starting the display
        response = requests.post(f'{self.base_url}/api/display/start')
        self.assertEqual(response.status_code, 200)
        
        # Test stopping the display
        response = requests.post(f'{self.base_url}/api/display/stop')
        self.assertEqual(response.status_code, 200)
        
        # Test forcing an update
        response = requests.post(f'{self.base_url}/api/display/update')
        self.assertEqual(response.status_code, 200)

    def test_invalid_config(self):
        """Test handling of invalid configuration"""
        invalid_config = {
            'update_interval': -100,  # Invalid value
            'font_size': 'not_a_number'  # Invalid type
        }
        
        response = requests.post(
            f'{self.base_url}/api/config',
            json=invalid_config
        )
        self.assertEqual(response.status_code, 500)

    def test_invalid_quotes_file(self):
        """Test handling of invalid quotes file"""
        # Create an invalid CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Invalid,CSV,Format\n")
            f.write("1,2,3\n")
        
        # Try to upload the invalid file
        with open(f.name, 'rb') as f:
            response = requests.post(
                f'{self.base_url}/api/quotes',
                files={'file': f}
            )
        
        # Clean up the temporary file
        os.unlink(f.name)
        
        self.assertEqual(response.status_code, 500)

if __name__ == '__main__':
    unittest.main() 