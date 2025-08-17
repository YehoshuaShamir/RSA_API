#!/usr/bin/env python3
"""
Test script for LTE bandwidth analysis functions
"""

import numpy as np
import spectrum_utils

def test_lte_band_detection():
    """Test LTE band detection from frequency"""
    print("=== LTE Band Detection Test ===")
    
    test_frequencies = [
        (2140e6, "Band 1 downlink"),
        (1950e6, "Band 1 uplink"),
        (1850e6, "Band 3 downlink"),
        (1750e6, "Band 3 uplink"),
        (2650e6, "Band 7 downlink"),
        (2550e6, "Band 7 uplink"),
        (940e6, "Band 8 downlink"),
        (900e6, "Band 8 uplink"),
        (810e6, "Band 20 downlink"),
        (850e6, "Band 20 uplink"),
        (780e6, "Band 28 downlink"),
        (720e6, "Band 28 uplink"),
        (1000e6, "Unknown frequency")
    ]
    
    for freq, description in test_frequencies:
        band_info = spectrum_utils.get_lte_band_from_freq(freq)
        if band_info:
            print(f"{freq/1e6:4.0f} MHz ({description:15s}) -> {band_info['name']} ({band_info['type']})")
        else:
            print(f"{freq/1e6:4.0f} MHz ({description:15s}) -> No LTE band found")

def test_lte_bandwidth_estimation():
    """Test LTE bandwidth estimation with synthetic data"""
    print("\n=== LTE Bandwidth Estimation Test ===")
    
    # Create synthetic LTE signal (20 MHz bandwidth centered at 2140 MHz)
    center_freq = 2140e6
    bandwidth = 20e6
    
    # Generate frequency array
    freq_array = np.linspace(center_freq - 30e6, center_freq + 30e6, 1000)
    
    # Generate synthetic power spectrum (Gaussian-like signal)
    noise_floor = -80  # dBm
    peak_power = -30   # dBm
    
    # Create LTE-like signal with main lobe and some side lobes
    main_signal = peak_power * np.exp(-((freq_array - center_freq) / (bandwidth/4))**2)
    noise = noise_floor + 5 * np.random.randn(len(freq_array))
    power_trace = main_signal + noise
    
    # Estimate bandwidth
    result = spectrum_utils.estimate_lte_bandwidth(freq_array, power_trace, threshold_db=-10)
    
    print(f"Synthetic signal parameters:")
    print(f"  Center frequency: {center_freq/1e6:.1f} MHz")
    print(f"  Expected bandwidth: {bandwidth/1e6:.1f} MHz")
    print(f"  Peak power: {peak_power:.1f} dBm")
    
    print(f"\nEstimation results:")
    print(f"  Estimated bandwidth: {result['estimated_bandwidth']/1e6:.1f} MHz")
    print(f"  Peak frequency: {result['peak_freq']/1e6:.1f} MHz")
    print(f"  Peak power: {result['peak_power']:.1f} dBm")
    print(f"  Signal start: {result['signal_start_freq']/1e6:.1f} MHz")
    print(f"  Signal end: {result['signal_end_freq']/1e6:.1f} MHz")
    
    if result['lte_band_info']:
        print(f"  Detected LTE band: {result['lte_band_info']['name']} ({result['lte_band_info']['type']})")
    else:
        print(f"  No LTE band detected")

def test_available_lte_bands():
    """Display available LTE bands"""
    print("\n=== Available LTE Bands ===")
    
    for band_key, band_info in spectrum_utils.LTE_BANDS.items():
        print(f"{band_key}: {band_info['name']}")
        print(f"  Downlink: {band_info['downlink_start']/1e6:.0f} - {band_info['downlink_end']/1e6:.0f} MHz")
        print(f"  Uplink:   {band_info['uplink_start']/1e6:.0f} - {band_info['uplink_end']/1e6:.0f} MHz")
        print(f"  Bandwidth options: {[bw/1e6 for bw in band_info['bandwidth_options']]} MHz")
        print()

if __name__ == "__main__":
    test_available_lte_bands()
    test_lte_band_detection()
    test_lte_bandwidth_estimation()
    
    print("\n=== Function Usage Examples ===")
    print("# Test specific LTE band:")
    print("result = spectrum_utils.test_lte_bandwidth('Band_1', 'downlink', 20e6)")
    print()
    print("# Get LTE bandwidth info:")
    print("info = spectrum_utils.get_lte_bandwidth_info('Band_7', 'downlink')")
    print()
    print("# Scan multiple LTE bands:")
    print("results = spectrum_utils.scan_lte_bands(['Band_1', 'Band_3', 'Band_7'])")
