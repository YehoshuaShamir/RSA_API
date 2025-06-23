# RSA_API [![Tektronix](https://tektronix.github.io/media/TEK-opensource_badge.svg)](https://github.com/tektronixofficial/RSA_API)
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Ftektronixofficial%2FRSA_API.svg?type=shield)](https://app.fossa.io/projects/git%2Bgithub.com%2Ftektronixofficial%2FRSA_API?ref=badge_shield)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15.x-green.svg)](https://pypi.org/project/PyQt5/)
[![NumPy](https://img.shields.io/badge/NumPy-1.21.x-orange.svg)](https://numpy.org/)

# RSA306B Spectrum Analyzer GUI

A modern, user-friendly GUI application for real-time spectrum analysis using the Tektronix RSA306B spectrum analyzer. This application provides comprehensive tools for analyzing WiFi signals in both 2.4GHz and 5GHz bands.

## Key Features

### Real-time Spectrum Analysis
- Live spectrum visualization with 801-point resolution
- Max hold functionality for signal persistence
- Color-coded peak detection and tracking
- Real-time scrolling peak data display

### Advanced Signal Analysis
- Multiple peak detection with subcarrier resolution
- WiFi channel identification (2.4GHz: Ch1-13, 5GHz: Ch36-140)
- Standard WiFi mask implementation
- Signal strength categorization
- Mask violation detection

### Spectrum Control Panel
- Reference Level adjustment (-130 to 10 dBm)
- Resolution Bandwidth (RBW) control (1-1000 kHz)
- Video Bandwidth (VBW) control (1-1000 kHz)
- Trace Length configuration (101-801 points)
- Window Type selection (Rectangular, Hamming, Hanning, Blackman, Kaiser)
- Vertical Units options (dBm, dBmV, dBuV, V, W)

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Tektronix RSA306B Spectrum Analyzer
- RSA API DLLs (C:\Tektronix\RSA_API\lib\x64)
- Minimum System Requirements:
  - RAM: 8GB
  - Storage: 500MB free space
  - USB 3.0 port

### Installation

1. Install required Python packages:
```bash
pip install PyQt5 numpy matplotlib pytest
```

2. Download and install the RSA API from Tektronix:
   - Latest version: 3.11.0047
   - Documentation: 077-1031-04

3. Run the application:
```bash
python test_rsa_gui.py
```

## Technical Specifications

### Frequency Bands
- 2.4GHz band: 2.412GHz - 2.484GHz (5MHz spacing)
- 5GHz band: 5.180GHz - 5.825GHz (20MHz spacing)

### Resolution Settings
- Minimum RBW: 1kHz
- Maximum RBW: 1000kHz
- Minimum VBW: 1kHz
- Maximum VBW: 1000kHz

### Signal Processing
- Peak detection threshold: -100dBm
- Mask thresholds:
  - Center channel: -40dBm
  - Adjacent channels: -50dBm
  - Far channels: -60dBm

## Development

### Project Structure
```
RSA_API/
├── Python/
│   └── Cython Version/
│       ├── test_rsa_gui.py
│       └── tests/
│           ├── test_rsa_gui.py
│           └── test_rsa_gui_new.py
└── Documentation/
    └── RSA_Spectrum_Analyzer_Documentation.md
```

### Testing
The application includes a comprehensive test suite using pytest:
```bash
pytest tests/test_rsa_gui.py
```

## License
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Ftektronixofficial%2FRSA_API.svg?type=large)](https://app.fossa.io/projects/git%2Bgithub.com%2Ftektronixofficial%2FRSA_API?ref=badge_large)

## Contributing

Contributions to this project must be accompanied by a Contributor License Agreement. You (or your employer) retain the copyright to your contribution.

## Documentation

For detailed technical documentation, see:
- [Tektronix RSA306B User Manual](https://www.tek.com/spectrum-analyzer/rsa306-manual/rsa306-rsa306b-and-rsa500a-600a-0)
- [RSA API Documentation](https://www.tek.com/model/rsa306-software/rsa-application-programming-interface-api-64-bit-windows-v3110047)
- [Project Documentation](Documentation/RSA_Spectrum_Analyzer_Documentation.md)
