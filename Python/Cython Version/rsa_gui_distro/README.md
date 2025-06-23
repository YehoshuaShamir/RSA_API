# RSA306B Spectrum Analyzer GUI - Minimal Distribution

This folder contains all necessary files to run the RSA306B Spectrum Analyzer GUI application on a different PC.

## Contents

- `rsa_gui.py`: Main application file
- `requirements.txt`: Python dependencies
- `rsa_api.dll`: RSA API DLL (required for hardware control)
- `rsa_api.pyd`: Python wrapper for RSA API
- `rsa_api.h`: Header file for RSA API
- `rsa_api.lib`: Library file for RSA API

## System Requirements

1. Windows PC
2. Python 3.10 or higher
3. Tektronix RSA306B Spectrum Analyzer
4. USB 3.0 port
5. Minimum 8GB RAM
6. Minimum 500MB free disk space

## Installation Instructions

1. **Install Python**
   - Download Python 3.10 or higher from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

2. **Install Dependencies**
   - Open Command Prompt
   - Navigate to this folder
   - Run: `pip install -r requirements.txt`

3. **Install RSA API**
   - Download RSA API from Tektronix:
     - Latest version: 3.11.0047
     - Download from: https://www.tek.com/model/rsa306-software/rsa-application-programming-interface-api-64-bit-windows-v3110047
   - Install the downloaded package

4. **Run the Application**
   - Open Command Prompt
   - Navigate to this folder
   - Run: `python rsa_gui.py`

## Troubleshooting

1. **RSA API DLL Missing**
   - Error: "DLL load failed"
   - Solution: Install RSA API from Tektronix website

2. **Python Version Issue**
   - Error: "Python version mismatch"
   - Solution: Install Python 3.10 or higher

3. **Spectrum Analyzer Not Found**
   - Error: "Device not found"
   - Solution: 
     - Ensure RSA306B is connected via USB
     - Check USB port and cable
     - Restart the application

## Contact
For support or issues, please contact the project maintainer.
