#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, send_file
import json
import os
from pathlib import Path
from quote_generator import QuoteGenerator
from display_manager import DisplayManager
import threading
import time

app = Flask(__name__)
quote_generator = QuoteGenerator()
display_manager = DisplayManager()

# Global variables for the update thread
update_thread = None
should_update = False

def update_display():
    """Background thread to update the display periodically"""
    global should_update
    while should_update:
        try:
            # Generate new image
            image = quote_generator.create_image()
            quote_generator.save_image(image)
            
            # Update display
            display_manager.init()
            display_manager.display(image)
            display_manager.sleep()
            
            # Wait for the configured interval
            config = quote_generator.config
            time.sleep(config.get('update_interval', 300))
        except Exception as e:
            print(f"Error in update thread: {e}")
            time.sleep(60)  # Wait a minute before retrying

@app.route('/')
def index():
    """Render the main settings page"""
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    try:
        return jsonify(quote_generator.config)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration"""
    try:
        config = request.get_json()
        
        # Validate configuration
        if not isinstance(config, dict):
            raise ValueError("Invalid configuration format")
        
        required_fields = {
            'update_interval': int,
            'display_brightness': int,
            'font_size': int,
            'show_book_info': bool,
            'show_author': bool,
            'content_filter': str
        }
        
        for field, field_type in required_fields.items():
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
            if not isinstance(config[field], field_type):
                raise ValueError(f"Invalid type for {field}: expected {field_type.__name__}")
        
        if config['update_interval'] < 1:
            raise ValueError("Update interval must be positive")
        if not 0 <= config['display_brightness'] <= 100:
            raise ValueError("Display brightness must be between 0 and 100")
        if config['font_size'] < 1:
            raise ValueError("Font size must be positive")
        if config['content_filter'] not in ['sfw', 'nsfw', 'all']:
            raise ValueError("Content filter must be 'sfw', 'nsfw', or 'all'")
        
        # Save configuration
        with open(quote_generator.data_dir / 'config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        # Reload configuration
        quote_generator.load_config()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/quotes', methods=['GET'])
def get_quotes():
    """Get current quotes"""
    try:
        # Filter quotes based on content filter setting
        content_filter = quote_generator.config.get('content_filter', 'all')
        
        if content_filter == 'all':
            return jsonify(quote_generator.quotes)
        else:
            filtered_quotes = {}
            for time_key, quote_data in quote_generator.quotes.items():
                rating = quote_data.get('rating', '').lower()
                if content_filter == 'sfw' and rating == 'sfw':
                    filtered_quotes[time_key] = quote_data
                elif content_filter == 'nsfw' and rating == 'nsfw':
                    filtered_quotes[time_key] = quote_data
                elif content_filter == 'all':
                    filtered_quotes[time_key] = quote_data
            return jsonify(filtered_quotes)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/quotes', methods=['POST'])
def update_quotes():
    """Update quotes from uploaded CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'status': 'error', 'message': 'File must be a CSV'}), 400
        
        # Save the uploaded file
        csv_path = quote_generator.data_dir / 'litclock_annotated.csv'
        file.save(csv_path)
        
        # Convert CSV to JSON
        success = quote_generator.convert_csv_to_json()
        
        if not success:
            return jsonify({'status': 'error', 'message': 'Failed to process the uploaded CSV file'}), 500
        
        # Reload quotes
        quote_generator.load_quotes()
        
        # Generate a new image to reflect the changes
        image = quote_generator.create_image()
        quote_generator.save_image(image)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/display/current-image')
def get_current_image():
    """Get the current display image"""
    try:
        image_path = quote_generator.images_dir / 'current_display.png'
        if not image_path.exists():
            # Generate a new image if none exists
            image = quote_generator.create_image()
            quote_generator.save_image(image)
        return send_file(image_path, mimetype='image/png')
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/display/status', methods=['GET'])
def get_display_status():
    """Get the current display status"""
    global update_thread, should_update
    return jsonify({
        'running': update_thread is not None and update_thread.is_alive() and should_update,
        'content_filter': quote_generator.config.get('content_filter', 'all')
    })

@app.route('/api/display/update', methods=['POST'])
def force_update():
    """Force an immediate display update"""
    try:
        # Generate new image
        image = quote_generator.create_image()
        quote_generator.save_image(image)
        
        # Update display
        display_manager.init()
        display_manager.display(image)
        display_manager.sleep()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/display/start', methods=['POST'])
def start_display():
    """Start the display update thread"""
    global update_thread, should_update
    try:
        if update_thread is None or not update_thread.is_alive():
            should_update = True
            update_thread = threading.Thread(target=update_display)
            update_thread.daemon = True
            update_thread.start()
            return jsonify({'status': 'success'})
        return jsonify({'status': 'already running'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/display/stop', methods=['POST'])
def stop_display():
    """Stop the display update thread"""
    global update_thread, should_update
    try:
        should_update = False
        if update_thread and update_thread.is_alive():
            update_thread.join(timeout=5)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def main():
    # Initialize the display image
    try:
        image = quote_generator.create_image()
        quote_generator.save_image(image)
    except Exception as e:
        print(f"Error initializing display image: {e}")
    
    # Run the Flask app directly, without using start_display here
    app.run(host='0.0.0.0', port=5001)

if __name__ == '__main__':
    main() 