#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"

# Check if Python virtual environment exists, if not create it
if [ ! -d "myenv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv myenv
    source myenv/bin/activate
    pip install --upgrade pip
    pip install flask pillow pandas RPi.GPIO spidev
else
    source myenv/bin/activate
fi

# Run the setup script if needed
if [ ! -d "data" ] || [ ! -f "data/config.json" ]; then
    echo "Running setup script..."
    python setup.py
fi

# Convert CSV to JSON if litclock_annotated.csv exists
if [ -f "data/litclock_annotated.csv" ]; then
    echo "Converting quotes CSV to JSON..."
    python -c "from quote_generator import QuoteGenerator; generator = QuoteGenerator(); generator.convert_csv_to_json(); generator.load_quotes(); image = generator.create_image(); generator.save_image(image)"
fi

# First test the e-paper display with the BOARD pin numbering
echo "Testing e-paper display using BOARD pin numbering..."
python test_e_paper_board.py

# If the test is successful, start the web server
echo "Starting web server..."
python web_server.py 