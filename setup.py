#!/usr/bin/env python3
import os
import json
import pandas as pd
from pathlib import Path

def create_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        'data',
        'images/generated',
        'static/css',
        'static/js',
        'templates'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def create_sample_quotes():
    """Create a sample quotes.csv file if it doesn't exist."""
    quotes_file = 'data/quotes.csv'
    if not os.path.exists(quotes_file):
        sample_quotes = [
            "13:35|1:35 P.M.|Fletcher checked his watch again. It was 1:35 P.M. He sighed and asked the receptionist if he could use the washroom.|Sons of Fortune|Jeffrey Archer|sfw",
            "14:00|2:00 P.M.|Time is what we want most, but what we use worst.|The Way of the World|William Congreve|sfw",
            "15:30|3:30 P.M.|The only way to do great work is to love what you do.|Steve Jobs|Walter Isaacson|sfw"
        ]
        with open(quotes_file, 'w') as f:
            f.write("HH:MM|H:MM A.M.|Quote|Book|Author|Rating\n")
            f.write("\n".join(sample_quotes))
        print(f"Created sample quotes file: {quotes_file}")

def convert_csv_to_json():
    """Convert quotes.csv to quotes.json if it exists."""
    csv_file = 'data/quotes.csv'
    json_file = 'data/quotes.json'
    
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file, sep='|')
        quotes_dict = {}
        
        for _, row in df.iterrows():
            time_key = row['HH:MM']
            quotes_dict[time_key] = {
                'display_time': row['H:MM A.M.'],
                'quote': row['Quote'],
                'book': row['Book'],
                'author': row['Author'],
                'rating': row['Rating']
            }
        
        with open(json_file, 'w') as f:
            json.dump(quotes_dict, f, indent=4)
        print(f"Converted {csv_file} to {json_file}")

def create_config_file():
    """Create a default config.json file if it doesn't exist."""
    config_file = 'data/config.json'
    if not os.path.exists(config_file):
        config = {
            'update_interval': 300,  # 5 minutes in seconds
            'display_brightness': 100,
            'font_size': 24,
            'show_book_info': True,
            'show_author': True
        }
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"Created config file: {config_file}")

def main():
    print("Starting setup...")
    create_directories()
    create_sample_quotes()
    convert_csv_to_json()
    create_config_file()
    print("Setup completed successfully!")

if __name__ == "__main__":
    main() 