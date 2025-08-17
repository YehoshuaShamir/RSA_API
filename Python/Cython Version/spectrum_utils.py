"""
Spectrum Analyzer Utility Functions
Simple functions to get peak power and WiFi channel information from RSA spectrum analyzer.
Based on main_rsa_gui.py functionality.
"""

import os
import numpy as np
import time

USE_MOCK_RSA = False
if os.environ.get('RSA_API_TESTING'):
    USE_MOCK_RSA = True

if not USE_MOCK_RSA:
    try:
        # Try to import RSA API for normal operation
        rsa_dll_path = r"C:\Tektronix\RSA_API\lib\x64"
        os.add_dll_directory(rsa_dll_path)
        from rsa_api import *
    except ImportError:
        USE_MOCK_RSA = True

if USE_MOCK_RSA:
    # Create mock implementations for testing
    class MockRSA:
        @staticmethod
        def DEVICE_Connect_py():
            return True

        @staticmethod
        def DEVICE_Run_py():
            return True

        @staticmethod
        def SPECTRUM_SetEnable_py(enable):
            return True

        @staticmethod
        def SPECTRUM_SetDefault_py():
            return True

        @staticmethod
        def CONFIG_SetCenterFreq_py(freq):
            return True

        @staticmethod
        def CONFIG_SetReferenceLevel_py(level):
            return True

        @staticmethod
        def SPECTRUM_SetSettings_py(**kwargs):
            return True

        @staticmethod
        def SPECTRUM_GetSettings_py():
            return {
                'actualStartFreq': 2.4e9,
                'actualStopFreq': 2.4835e9,
                'actualFreqStepSize': 104312.5,
                'traceLength': 801
            }

        @staticmethod
        def SPECTRUM_AcquireTrace_py():
            return True

        @staticmethod
        def SPECTRUM_WaitForTraceReady_py(timeout):
            return True

        @staticmethod
        def SPECTRUM_GetTrace_py(**kwargs):
            # Generate mock data with a peak for testing
            trace = np.random.normal(-80, 5, 801)
            trace[400] = -30  # Peak at center
            return trace

    # Create mock RSA API
    DEVICE_Connect_py = MockRSA.DEVICE_Connect_py
    DEVICE_Run_py = MockRSA.DEVICE_Run_py
    SPECTRUM_SetEnable_py = MockRSA.SPECTRUM_SetEnable_py
    SPECTRUM_SetDefault_py = MockRSA.SPECTRUM_SetDefault_py
    CONFIG_SetCenterFreq_py = MockRSA.CONFIG_SetCenterFreq_py
    CONFIG_SetReferenceLevel_py = MockRSA.CONFIG_SetReferenceLevel_py
    SPECTRUM_SetSettings_py = MockRSA.SPECTRUM_SetSettings_py
    SPECTRUM_GetSettings_py = MockRSA.SPECTRUM_GetSettings_py
    SPECTRUM_AcquireTrace_py = MockRSA.SPECTRUM_AcquireTrace_py
    SPECTRUM_WaitForTraceReady_py = MockRSA.SPECTRUM_WaitForTraceReady_py
    SPECTRUM_GetTrace_py = MockRSA.SPECTRUM_GetTrace_py

    # Define dummy SpectrumTraces to satisfy calls
    class SpectrumTraces:
        SpectrumTrace1 = 0

# WiFi channel definitions
WIFI_CHANNELS = {
    '2.4GHz': {
        'channels': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
        'center_freqs': [
            2412e6, 2417e6, 2422e6, 2427e6, 2432e6, 2437e6, 2442e6, 
            2447e6, 2452e6, 2457e6, 2462e6, 2467e6, 2472e6
        ]
    },
    '5GHz': {
        'channels': list(range(36, 64, 4)) + list(range(100, 141, 4)),
        'center_freqs': [
            5180e6, 5200e6, 5220e6, 5240e6, 5260e6, 5280e6, 5300e6, 5320e6,
            5500e6, 5520e6, 5540e6, 5560e6, 5580e6, 5600e6, 5620e6, 5640e6,
            5660e6, 5680e6, 5700e6
        ]
    }
}

# LTE band definitions (common bands with their frequency ranges)
LTE_BANDS = {
    'Band_1': {
        'name': 'Band 1 (2100 MHz)',
        'downlink_start': 2110e6,
        'downlink_end': 2170e6,
        'uplink_start': 1920e6,
        'uplink_end': 1980e6,
        'bandwidth_options': [1.4e6, 3e6, 5e6, 10e6, 15e6, 20e6]  # MHz
    },
    'Band_3': {
        'name': 'Band 3 (1800 MHz)',
        'downlink_start': 1805e6,
        'downlink_end': 1880e6,
        'uplink_start': 1710e6,
        'uplink_end': 1785e6,
        'bandwidth_options': [1.4e6, 3e6, 5e6, 10e6, 15e6, 20e6]
    },
    'Band_7': {
        'name': 'Band 7 (2600 MHz)',
        'downlink_start': 2620e6,
        'downlink_end': 2690e6,
        'uplink_start': 2500e6,
        'uplink_end': 2570e6,
        'bandwidth_options': [1.4e6, 3e6, 5e6, 10e6, 15e6, 20e6]
    },
    'Band_8': {
        'name': 'Band 8 (900 MHz)',
        'downlink_start': 925e6,
        'downlink_end': 960e6,
        'uplink_start': 880e6,
        'uplink_end': 915e6,
        'bandwidth_options': [1.4e6, 3e6, 5e6, 10e6, 15e6, 20e6]
    },
    'Band_20': {
        'name': 'Band 20 (800 MHz)',
        'downlink_start': 791e6,
        'downlink_end': 821e6,
        'uplink_start': 832e6,
        'uplink_end': 862e6,
        'bandwidth_options': [1.4e6, 3e6, 5e6, 10e6, 15e6, 20e6]
    },
    'Band_28': {
        'name': 'Band 28 (700 MHz)',
        'downlink_start': 758e6,
        'downlink_end': 803e6,
        'uplink_start': 703e6,
        'uplink_end': 748e6,
        'bandwidth_options': [1.4e6, 3e6, 5e6, 10e6, 15e6, 20e6]
    }
}

def initialize_spectrum_analyzer():
    """
    Initialize the RSA spectrum analyzer device.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        DEVICE_Connect_py()
        DEVICE_Run_py()
        SPECTRUM_SetEnable_py(True)
        SPECTRUM_SetDefault_py()
        return True
    except Exception as e:
        print(f"Error initializing spectrum analyzer: {e}")
        return False

def configure_spectrum(center_freq, span, rbw=1e3, ref_level=-60):
    """
    Configure spectrum analyzer settings.
    
    Args:
        center_freq (float): Center frequency in Hz
        span (float): Frequency span in Hz
        rbw (float): Resolution bandwidth in Hz (default: 1kHz)
        ref_level (float): Reference level in dBm (default: -60)
    
    Returns:
        dict: Spectrum settings from the device
    """
    try:
        CONFIG_SetCenterFreq_py(center_freq)
        CONFIG_SetReferenceLevel_py(ref_level)
        SPECTRUM_SetSettings_py(span=span, rbw=rbw, traceLength=801)
        return SPECTRUM_GetSettings_py()
    except Exception as e:
        print(f"Error configuring spectrum: {e}")
        return None

def create_frequency_array(spec_settings):
    """
    Create frequency array from spectrum settings.
    
    Args:
        spec_settings (dict): Spectrum settings from SPECTRUM_GetSettings_py()
    
    Returns:
        numpy.ndarray: Array of frequencies in Hz
    """
    if not spec_settings:
        return None
    
    freq = np.arange(
        spec_settings['actualStartFreq'],
        spec_settings['actualStartFreq'] + spec_settings['actualFreqStepSize'] * spec_settings['traceLength'],
        spec_settings['actualFreqStepSize']
    )
    return freq

def get_spectrum_trace():
    """
    Acquire a spectrum trace from the analyzer.
    
    Returns:
        numpy.ndarray: Power trace in dBm, or None if failed
    """
    try:
        SPECTRUM_AcquireTrace_py()
        SPECTRUM_WaitForTraceReady_py(100)
        trace = SPECTRUM_GetTrace_py(trace=SpectrumTraces.SpectrumTrace1, tracePoints=801)
        return trace
    except Exception as e:
        print(f"Error acquiring trace: {e}")
        return None

def find_peak_power(freq_array, trace):
    """
    Find the peak power and its frequency from a spectrum trace.
    
    Args:
        freq_array (numpy.ndarray): Array of frequencies in Hz
        trace (numpy.ndarray): Power trace in dBm
    
    Returns:
        tuple: (peak_power_dbm, peak_frequency_hz) or (None, None) if failed
    """
    if freq_array is None or trace is None:
        return None, None
    
    if len(freq_array) != len(trace):
        print("Error: Frequency array and trace length mismatch")
        return None, None
    
    # Find the index of maximum power
    peak_idx = np.argmax(trace)
    peak_power = trace[peak_idx]
    peak_freq = freq_array[peak_idx]
    
    return peak_power, peak_freq

def get_channel_from_freq(freq):
    """
    Get WiFi channel number from frequency.
    
    Args:
        freq (float): Frequency in Hz
    
    Returns:
        int: WiFi channel number, or None if not a valid WiFi frequency
    """
    if freq < 3e9:  # 2.4GHz band
        centers = WIFI_CHANNELS["2.4GHz"]["center_freqs"]
        channels = WIFI_CHANNELS["2.4GHz"]["channels"]
    else:  # 5GHz band
        centers = WIFI_CHANNELS["5GHz"]["center_freqs"]
        channels = WIFI_CHANNELS["5GHz"]["channels"]
    
    if not centers or not channels:
        return None
    
    # Find closest channel
    min_idx = int(np.argmin([abs(freq - cf) for cf in centers]))
    
    if min_idx >= len(channels):
        return None
    
    return channels[min_idx]

def get_wifi_peak_info(band="2.4GHz"):
    """
    Get peak power and WiFi channel information for a specific band.
    
    Args:
        band (str): WiFi band ("2.4GHz" or "5GHz")
    
    Returns:
        dict: Dictionary with keys:
            - 'peak_power': Peak power in dBm
            - 'peak_frequency': Peak frequency in Hz
            - 'peak_frequency_mhz': Peak frequency in MHz
            - 'wifi_channel': WiFi channel number
            - 'success': Boolean indicating if operation was successful
    """
    result = {
        'peak_power': None,
        'peak_frequency': None,
        'peak_frequency_mhz': None,
        'wifi_channel': None,
        'success': False
    }
    
    # Initialize if not already done
    if not initialize_spectrum_analyzer():
        return result
    
    # Configure for the specified band
    if band == "2.4GHz":
        center_freq = 2.4415e9  # Center of 2.4GHz band
        span = 83.5e6  # Full 2.4GHz band span
    elif band == "5GHz":
        center_freq = 5.4875e9  # Center of 5GHz band
        span = 675e6  # Full 5GHz band span
    else:
        print(f"Invalid band: {band}. Use '2.4GHz' or '5GHz'")
        return result
    
    # Configure spectrum analyzer
    spec_settings = configure_spectrum(center_freq, span)
    if not spec_settings:
        return result
    
    # Create frequency array
    freq_array = create_frequency_array(spec_settings)
    if freq_array is None:
        return result
    
    # Get spectrum trace
    trace = get_spectrum_trace()
    if trace is None:
        return result
    
    # Find peak
    peak_power, peak_freq = find_peak_power(freq_array, trace)
    if peak_power is None or peak_freq is None:
        return result
    
    # Get WiFi channel
    wifi_channel = get_channel_from_freq(peak_freq)
    
    # Fill result
    result['peak_power'] = peak_power
    result['peak_frequency'] = peak_freq
    result['peak_frequency_mhz'] = peak_freq / 1e6
    result['wifi_channel'] = wifi_channel
    result['success'] = True
    
    return result

def get_peak_power_at_frequency_1min(target_freq_hz=2442e6):
    """
    Measure for 60 seconds and return the maximum power observed at a specific
    frequency (nearest bin to target_freq_hz).

    Settings forced as requested:
    - Span: 200 MHz
    - RBW: 10 MHz
    - Reference Level: 0 dBm

    Args:
        target_freq_hz (float): Target frequency in Hz (default: 2442 MHz)

    Returns:
        dict: {
            'target_frequency_hz': float,
            'bin_frequency_hz': float,        # actual nearest frequency bin
            'max_power_dbm': float | None,    # maximum observed power at that bin
            'samples_taken': int,
            'elapsed_sec': float,
            'success': bool,
        }
    """
    result = {
        'target_frequency_hz': float(target_freq_hz),
        'bin_frequency_hz': None,
        'max_power_dbm': None,
        'samples_taken': 0,
        'elapsed_sec': 0.0,
        'success': False,
    }

    # Initialize analyzer
    if not initialize_spectrum_analyzer():
        return result

    # Configure analyzer per request
    center_freq = float(target_freq_hz)
    span = 200e6
    rbw = 10e6
    ref_level = 0.0

    spec_settings = configure_spectrum(center_freq, span, rbw=rbw, ref_level=ref_level)
    if not spec_settings:
        return result

    # Build frequency axis and find the closest bin to the target frequency
    freq_array = create_frequency_array(spec_settings)
    if freq_array is None or len(freq_array) == 0:
        return result

    # Find nearest bin to target frequency
    bin_idx = int(np.argmin(np.abs(freq_array - target_freq_hz)))
    bin_freq = float(freq_array[bin_idx])
    result['bin_frequency_hz'] = bin_freq

    # Run for 60 seconds
    duration_sec = 60.0
    start = time.time()
    samples = 0
    max_power = -1e9  # very low sentinel

    while True:
        now = time.time()
        if now - start >= duration_sec:
            break

        trace = get_spectrum_trace()
        if trace is None or len(trace) <= bin_idx:
            continue

        samples += 1
        power_at_bin = trace[bin_idx]
        if np.isfinite(power_at_bin) and power_at_bin > max_power:
            max_power = float(power_at_bin)

    result['samples_taken'] = samples
    result['elapsed_sec'] = time.time() - start

    if samples > 0 and np.isfinite(max_power):
        result['max_power_dbm'] = max_power
        result['success'] = True

    return result

def get_max_peak_over_duration(duration_sec=30, band="2.4GHz"):
    """
    Continuously read spectrum for a duration and return the maximum observed
    peak power and its frequency.

    Args:
        duration_sec (float): Duration to read in seconds (default: 30).
        band (str): "2.4GHz" or "5GHz". Used for simple configuration.

    Returns:
        dict: {
            'max_power': float | None,          # dBm
            'max_frequency': float | None,      # Hz
            'max_frequency_mhz': float | None,  # MHz
            'wifi_channel': int | None,         # if within WiFi bands
            'samples_taken': int,
            'elapsed_sec': float,
            'success': bool,
        }
    """
    result = {
        'max_power': None,
        'max_frequency': None,
        'max_frequency_mhz': None,
        'wifi_channel': None,
        'samples_taken': 0,
        'elapsed_sec': 0.0,
        'success': False,
    }

    # Initialize analyzer
    if not initialize_spectrum_analyzer():
        return result

    # Configure for band
    if band == "2.4GHz":
        center_freq = 2.4415e9
        span = 83.5e6
    elif band == "5GHz":
        center_freq = 5.4875e9
        span = 675e6
    else:
        # Allow custom numeric center freq passed in band param? Keep simple per request.
        print(f"Invalid band: {band}. Use '2.4GHz' or '5GHz'")
        return result

    spec_settings = configure_spectrum(center_freq, span)
    if not spec_settings:
        return result

    freq_array = create_frequency_array(spec_settings)
    if freq_array is None:
        return result

    max_power = -np.inf
    max_freq = None

    start = time.time()
    samples = 0
    while True:
        # Stop when duration reached
        now = time.time()
        if now - start >= duration_sec:
            break

        trace = get_spectrum_trace()
        if trace is None:
            # Skip this iteration
            continue

        samples += 1
        peak_power, peak_freq = find_peak_power(freq_array, trace)
        if peak_power is None or peak_freq is None:
            continue

        if peak_power > max_power:
            max_power = peak_power
            max_freq = peak_freq

    result['samples_taken'] = samples
    result['elapsed_sec'] = time.time() - start

    if max_freq is not None and np.isfinite(max_power):
        result['max_power'] = float(max_power)
        result['max_frequency'] = float(max_freq)
        result['max_frequency_mhz'] = float(max_freq / 1e6)
        result['wifi_channel'] = get_channel_from_freq(max_freq)
        result['success'] = True

    return result

def get_all_peaks_info(band="2.4GHz", threshold=-100):
    """
    Get information about all peaks above a threshold in the spectrum.
    
    Args:
        band (str): WiFi band ("2.4GHz" or "5GHz")
        threshold (float): Minimum power level in dBm to consider as a peak
    
    Returns:
        list: List of dictionaries, each containing peak information
    """
    # Initialize if not already done
    if not initialize_spectrum_analyzer():
        return []
    
    # Configure for the specified band
    if band == "2.4GHz":
        center_freq = 2.4415e9
        span = 83.5e6
    elif band == "5GHz":
        center_freq = 5.4875e9
        span = 675e6
    else:
        print(f"Invalid band: {band}. Use '2.4GHz' or '5GHz'")
        return []
    
    # Configure spectrum analyzer
    spec_settings = configure_spectrum(center_freq, span)
    if not spec_settings:
        return []
    
    # Create frequency array
    freq_array = create_frequency_array(spec_settings)
    if freq_array is None:
        return []
    
    # Get spectrum trace
    trace = get_spectrum_trace()
    if trace is None:
        return []
    
    # Find all peaks (local maxima above threshold)
    peaks = []
    for i in range(1, len(trace) - 1):
        if (trace[i] > trace[i - 1] and 
            trace[i] > trace[i + 1] and 
            trace[i] > threshold):
            
            peak_info = {
                'power': trace[i],
                'frequency': freq_array[i],
                'frequency_mhz': freq_array[i] / 1e6,
                'wifi_channel': get_channel_from_freq(freq_array[i])
            }
            peaks.append(peak_info)
    
    # Sort by power level (strongest first)
    peaks.sort(key=lambda x: x['power'], reverse=True)
    
    return peaks

# Convenience function for backward compatibility
def get_peak_power_and_channel(band="2.4GHz"):
    """
    Simple function to get peak power and WiFi channel.
    
    Args:
        band (str): WiFi band ("2.4GHz" or "5GHz")
    
    Returns:
        tuple: (peak_power_dbm, wifi_channel) or (None, None) if failed
    """
    result = get_wifi_peak_info(band)
    if result['success']:
        return result['peak_power'], result['wifi_channel']
    else:
        return None, None

def get_lte_band_from_freq(freq):
    """
    Determine LTE band from frequency.
    
    Args:
        freq: Frequency in Hz
        
    Returns:
        dict: LTE band information or None if not found
    """
    for band_key, band_info in LTE_BANDS.items():
        # Check downlink frequency range
        if band_info['downlink_start'] <= freq <= band_info['downlink_end']:
            return {
                'band': band_key,
                'name': band_info['name'],
                'type': 'downlink',
                'freq_range': (band_info['downlink_start'], band_info['downlink_end'])
            }
        # Check uplink frequency range
        elif band_info['uplink_start'] <= freq <= band_info['uplink_end']:
            return {
                'band': band_key,
                'name': band_info['name'],
                'type': 'uplink',
                'freq_range': (band_info['uplink_start'], band_info['uplink_end'])
            }
    return None

def estimate_lte_bandwidth(freq_array, power_trace, threshold_db=-10):
    """
    Estimate LTE signal bandwidth by analyzing the power spectrum.
    
    Args:
        freq_array: Array of frequencies in Hz
        power_trace: Array of power values in dBm
        threshold_db: Threshold below peak power to define signal edges
        
    Returns:
        dict: Bandwidth estimation results
    """
    if len(freq_array) != len(power_trace):
        raise ValueError("Frequency array and power trace must have same length")
    
    # Find peak power and frequency
    peak_idx = np.argmax(power_trace)
    peak_power = power_trace[peak_idx]
    peak_freq = freq_array[peak_idx]
    
    # Define threshold for signal edges
    threshold_power = peak_power + threshold_db
    
    # Find signal edges (where power drops below threshold)
    above_threshold = power_trace >= threshold_power
    
    # Find continuous regions above threshold
    signal_regions = []
    start_idx = None
    
    for i, above in enumerate(above_threshold):
        if above and start_idx is None:
            start_idx = i
        elif not above and start_idx is not None:
            signal_regions.append((start_idx, i-1))
            start_idx = None
    
    # Handle case where signal extends to end of array
    if start_idx is not None:
        signal_regions.append((start_idx, len(above_threshold)-1))
    
    if not signal_regions:
        return {
            'estimated_bandwidth': 0,
            'peak_power': peak_power,
            'peak_freq': peak_freq,
            'signal_start_freq': None,
            'signal_end_freq': None,
            'lte_band_info': None
        }
    
    # Find the region containing the peak
    main_region = None
    for start_idx, end_idx in signal_regions:
        if start_idx <= peak_idx <= end_idx:
            main_region = (start_idx, end_idx)
            break
    
    if main_region is None:
        main_region = signal_regions[0]  # Fallback to first region
    
    start_idx, end_idx = main_region
    signal_start_freq = freq_array[start_idx]
    signal_end_freq = freq_array[end_idx]
    estimated_bandwidth = signal_end_freq - signal_start_freq
    
    # Get LTE band information
    lte_band_info = get_lte_band_from_freq(peak_freq)
    
    return {
        'estimated_bandwidth': estimated_bandwidth,
        'peak_power': peak_power,
        'peak_freq': peak_freq,
        'signal_start_freq': signal_start_freq,
        'signal_end_freq': signal_end_freq,
        'lte_band_info': lte_band_info,
        'threshold_used': threshold_db
    }

def test_lte_bandwidth(band_key, link_type='downlink', expected_bandwidth=20e6):
    """
    Test LTE bandwidth analysis for a specific band.
    
    Args:
        band_key: LTE band key (e.g., 'Band_1', 'Band_3')
        link_type: 'downlink' or 'uplink'
        expected_bandwidth: Expected bandwidth in Hz (default 20 MHz)
        
    Returns:
        dict: Test results including bandwidth estimation
    """
    if band_key not in LTE_BANDS:
        raise ValueError(f"Unknown LTE band: {band_key}")
    
    band_info = LTE_BANDS[band_key]
    
    # Determine frequency range based on link type
    if link_type == 'downlink':
        freq_start = band_info['downlink_start']
        freq_end = band_info['downlink_end']
    elif link_type == 'uplink':
        freq_start = band_info['uplink_start']
        freq_end = band_info['uplink_end']
    else:
        raise ValueError("link_type must be 'downlink' or 'uplink'")
    
    # Calculate center frequency and span
    center_freq = (freq_start + freq_end) / 2
    span = freq_end - freq_start
    
    # Initialize analyzer
    if not initialize_spectrum_analyzer():
        return {'error': 'Failed to initialize spectrum analyzer'}

    try:
        # Configure for LTE band
        spec_settings = configure_spectrum(center_freq, span, rbw=100e3)
        if not spec_settings:
            return {'error': 'Configuration failed'}

        # Frequency axis
        freq_array = create_frequency_array(spec_settings)
        if freq_array is None:
            return {'error': 'Failed to build frequency array'}

        # Acquire spectrum
        power_trace = get_spectrum_trace()
        if power_trace is None:
            return {'error': 'Failed to acquire spectrum trace'}

        # Estimate bandwidth
        bandwidth_result = estimate_lte_bandwidth(freq_array, power_trace)

        # Add test-specific information
        bandwidth_result.update({
            'test_band': band_key,
            'test_link_type': link_type,
            'expected_bandwidth': expected_bandwidth,
            'bandwidth_match': abs(bandwidth_result['estimated_bandwidth'] - expected_bandwidth) < (expected_bandwidth * 0.1),  # 10% tolerance
            'band_name': band_info['name'],
            'freq_range_tested': (freq_start, freq_end)
        })

        return bandwidth_result

    except Exception as e:
        return {'error': f'Test failed: {str(e)}'}

def get_lte_bandwidth_info(band_key, link_type='downlink'):
    """
    Get LTE bandwidth information for a specific band.
    
    Args:
        band_key: LTE band key (e.g., 'Band_1', 'Band_3')
        link_type: 'downlink' or 'uplink'
        
    Returns:
        dict: LTE bandwidth analysis results
    """
    return test_lte_bandwidth(band_key, link_type)

def scan_lte_bands(bands_to_scan=None, link_type='downlink'):
    """
    Scan multiple LTE bands and return bandwidth information.
    
    Args:
        bands_to_scan: List of band keys to scan (default: all available bands)
        link_type: 'downlink' or 'uplink'
        
    Returns:
        dict: Results for each scanned band
    """
    if bands_to_scan is None:
        bands_to_scan = list(LTE_BANDS.keys())
    
    results = {}
    
    for band_key in bands_to_scan:
        print(f"Scanning {band_key} ({link_type})...")
        result = test_lte_bandwidth(band_key, link_type)
        results[band_key] = result
        
        if 'error' not in result:
            print(f"  Estimated bandwidth: {result['estimated_bandwidth']/1e6:.1f} MHz")
            print(f"  Peak power: {result['peak_power']:.1f} dBm")
            if result['lte_band_info']:
                print(f"  Detected band: {result['lte_band_info']['name']}")
        else:
            print(f"  Error: {result['error']}")
    
    return results

if __name__ == "__main__":
    # Example usage
    print("Testing WiFi spectrum analysis...")
    
    # Test 2.4GHz band
    result_24 = get_wifi_peak_info('2.4GHz')
    if result_24['success'] and result_24['peak_power'] is not None:
        print(f"2.4GHz - Peak Power: {result_24['peak_power']:.2f} dBm, Channel: {result_24['wifi_channel']}")
    else:
        print("2.4GHz - Failed to get spectrum data (using mock data)")
    
    # Test 5GHz band
    result_5 = get_wifi_peak_info('5GHz')
    if result_5['success'] and result_5['peak_power'] is not None:
        print(f"5GHz - Peak Power: {result_5['peak_power']:.2f} dBm, Channel: {result_5['wifi_channel']}")
    else:
        print("5GHz - Failed to get spectrum data (using mock data)")
    
    print("\nTesting LTE bandwidth analysis...")
    
    # Test LTE Band 1 (2100 MHz)
    lte_result = test_lte_bandwidth('Band_1', 'downlink', 20e6)
    if 'error' not in lte_result and lte_result.get('peak_power') is not None:
        print(f"LTE Band 1 - Estimated bandwidth: {lte_result['estimated_bandwidth']/1e6:.1f} MHz")
        print(f"LTE Band 1 - Peak power: {lte_result['peak_power']:.1f} dBm")
        if lte_result['lte_band_info']:
            print(f"LTE Band 1 - Detected: {lte_result['lte_band_info']['name']}")
    else:
        print(f"LTE Band 1 - Error: {lte_result.get('error', 'Failed to get spectrum data')}")
    
    # Test LTE band detection
    print("\nTesting LTE band detection...")
    test_freqs = [2140e6, 1850e6, 2650e6, 940e6, 810e6, 780e6]
    for freq in test_freqs:
        band_info = get_lte_band_from_freq(freq)
        if band_info:
            print(f"{freq/1e6:.0f} MHz -> {band_info['name']} ({band_info['type']})")
        else:
            print(f"{freq/1e6:.0f} MHz -> No LTE band found")
    
    # Test simple function
    print("\n--- Simple Function Test ---")
    power, channel = get_peak_power_and_channel("2.4GHz")
    if power is not None:
        print(f"Simple function result: {power:.2f} dBm on channel {channel}")
    else:
        print("Simple function failed")
