# Quote Clock for Raspberry Pi Zero 2 with E-Paper Display

A Python-based application that displays quotes on a 13.3-inch e-paper HAT (B) device connected to a Raspberry Pi Zero 2. The system includes a web interface for configuration and quote management.

I want to give thanks to JohannesNE as I used their quotes csv.

## Features

- Displays quotes and time on an e-paper display
- Web-based settings interface
- Configurable update intervals
- CSV to JSON quote conversion
- Automatic startup on boot
- Test mode for development without hardware

## Hardware Requirements

- Raspberry Pi Zero 2 (for production)
- 13.3-inch e-paper HAT (B) (for production)
- MicroSD card with Raspberry Pi OS (for production)
- Internet connection

## Software Requirements

- Python 3.7+
- Required Python packages (see requirements.txt)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/quote_clock.git
   cd quote_clock
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
   When testing locally and not on a raspberry pi install `requirements-dev.txt`

3. Create a `quotes.csv` file in the `data` directory with your quotes:
   ```
   HH:MM|H:MM A.M.|Quote|Book|Author|Rating
   13:35|1:35 P.M.|Fletcher checked his watch again...|Sons of Fortune|Jeffrey Archer|sfw
   ```

## Raspberry Pi Setup

1. Enable SPI interface:
   ```bash
   sudo raspi-config
   ```
   Navigate to "Interface Options" > "SPI" > "Yes" to enable SPI.

2. Add your user to the gpio group:
   ```bash
   sudo usermod -a -G gpio $USER
   ```
   Note: You'll need to log out and back in for this to take effect.

3. Connect the e-paper display to your Raspberry Pi:
   - RST_PIN (17) -> RST
   - DC_PIN (25) -> DC
   - CS_PIN (8) -> CS
   - BUSY_PIN (24) -> BUSY
   - VCC -> 3.3V
   - GND -> GND
   - CLK -> SCLK
   - DIN -> MOSI

4. Run the initial setup:
   ```bash
   python setup.py
   ```

5. (Optional) Set up automatic startup:
   ```bash
   sudo cp quote_clock.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable quote_clock
   sudo systemctl start quote_clock
   ```

## Development/Testing Without Raspberry Pi

1. The application includes a mock mode for testing without hardware:
   - Mock GPIO module for testing display functionality
   - Mock SPI module for testing communication
   - Test suite for validating functionality

2. Run the test suite:
   ```bash
   python run_tests.py
   ```

3. Test the web interface:
   ```bash
   python web_server.py
   ```
   Access the web interface at `http://localhost:5001`

## Usage

### On Raspberry Pi

1. Start the web interface:
   ```bash
   python web_server.py
   ```

2. Access the web interface at `http://<raspberry_pi_ip>:5001`

3. Configure your display settings and upload new quotes through the web interface.

### Development/Testing

1. Run the test suite:
   ```bash
   python run_tests.py
   ```

2. Test the web interface:
   ```bash
   python web_server.py
   ```

3. Test display functionality:
   ```bash
   python display_manager.py
   ```

## Directory Structure

```
quote_clock/
├── data/
│   ├── quotes.csv
│   └── quotes.json
├── images/
│   └── generated/
├── static/
│   ├── css/
│   └── js/
├── templates/
├── tests/
│   ├── RPi/
│   │   └── GPIO/
│   │       └── GPIO.py
│   ├── mock_config.py
│   ├── mock_spi.py
│   └── test_*.py
├── requirements.txt
├── README.md
├── setup.py
├── web_server.py
├── quote_generator.py
├── display_manager.py
└── run_tests.py
```

## Troubleshooting

### Raspberry Pi Issues

1. SPI not working:
   - Verify SPI is enabled: `ls /dev/spi*`
   - Check user permissions: `groups $USER`
   - Verify connections are correct

2. Display not responding:
   - Check power supply (3.3V)
   - Verify all connections
   - Check GPIO permissions

3. Web interface not accessible:
   - Verify the server is running
   - Check firewall settings
   - Ensure correct IP address

### Development Issues

1. Tests failing:
   - Check Python version (3.7+ required)
   - Verify all dependencies are installed
   - Check mock configuration

2. Web interface issues:
   - Check port 5001 is available
   - Verify all dependencies are installed
   - Check browser console for errors

## License

MIT License - see LICENSE file for details 