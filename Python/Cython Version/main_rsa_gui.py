import os
import sys
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QPushButton, QSpinBox, QTabWidget, QTableWidget,
    QComboBox, QHeaderView, QTableWidgetItem, QScrollArea
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QTimer, Qt
import time

try:
    # Try to import RSA API for normal operation
    if not os.environ.get('RSA_API_TESTING'):
        rsa_dll_path = r"C:\Tektronix\RSA_API\lib\x64"
        os.add_dll_directory(rsa_dll_path)
        from rsa_api import *
except ImportError:
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
            # Return frequency range based on the selected band for correct testing
            # Use a global or class variable to track band selection
            # Fallback to 2.4GHz if not set
            band = getattr(MockRSA, 'current_band', '2.4GHz')
            if band == '5GHz':
                return {
                    'actualStartFreq': 5.15e9,
                    'actualStopFreq': 5.825e9
                }
            else:
                return {
                    'actualStartFreq': 2.4e9,
                    'actualStopFreq': 2.4835e9
                }

        @staticmethod
        def SPECTRUM_AcquireTrace_py():
            return True

        @staticmethod
        def SPECTRUM_WaitForTraceReady_py(timeout):
            return True

        @staticmethod
        def SPECTRUM_GetTrace_py(**kwargs):
            return np.zeros(801)

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

class SpectrumAnalyzerGUI(QWidget):
    """
    A GUI application for controlling and visualizing the RSA306B spectrum analyzer.
    Provides real-time spectrum analysis with features like max hold and trigger levels.
    """
    def __init__(self):
        """
        Initialize the spectrum analyzer GUI application.
        Sets up the window, initializes the RSA device, and creates the GUI layout.
        """
        super().__init__()
        
        # WiFi standard masks
        self.wifi_masks = {
            '2.4GHz': {
                'channels': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
                'center_freqs': [
                    2412e6, 2417e6, 2422e6, 2427e6, 2432e6, 2437e6, 2442e6, 2447e6, 2452e6, 2457e6, 2462e6, 2467e6, 2472e6
                ],  # Regulatory 2.4GHz WiFi center frequencies
                'mask': {
                    'channel_width': 22e6,  # 22MHz channel width
                    'thresholds': {
                        'center': -40,  # Center of channel
                        'adjacent': -50,  # Adjacent channels
                        'far': -60  # Far channels
                    }
                }
            },
            '5GHz': {
                'channels': list(range(36, 64, 4)) + list(range(100, 141, 4)),
                'center_freqs': [
                    5180e6, 5200e6, 5220e6, 5240e6, 5260e6, 5280e6, 5300e6, 5320e6,
                    5500e6, 5520e6, 5540e6, 5560e6, 5580e6, 5600e6, 5620e6, 5640e6,
                    5660e6, 5680e6, 5700e6
                ],  # Regulatory 5GHz WiFi center frequencies
                'mask': {
                    'channel_width': 20e6,  # 20MHz channel width
                    'thresholds': {
                        'center': -40,  # Center of channel
                        'adjacent': -50,  # Adjacent channels
                        'far': -60  # Far channels
                    }
                }
            }
        }
        
        # Signal analysis variables
        self.current_signal_level = None
        self.current_channel = None
        self.current_mask = None
        self.setWindowTitle("RSA306B Spectrum Analyzer")
        self.setGeometry(100, 100, 1000, 600)

        # Initialize RSA device and spectrum analyzer
        # This establishes connection with the hardware and sets up basic spectrum settings
        DEVICE_Connect_py()
        DEVICE_Run_py()
        SPECTRUM_SetEnable_py(True)
        SPECTRUM_SetDefault_py()

        # --- GUI Layout ---
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.spectrum_tab = QWidget()
        self.control_tab = QWidget()

        self.tabs.addTab(self.spectrum_tab, "Live Spectrum")
        self.tabs.addTab(self.control_tab, "Spectrum Control")

        # --- Spectrum Tab Layout ---
        self.spectrum_layout = QVBoxLayout()
        self.spectrum_tab.setLayout(self.spectrum_layout)

        self.config_layout = QHBoxLayout()
        self.spectrum_layout.addLayout(self.config_layout)

        # WiFi Channel Selection
        self.channel_label = QLabel("WiFi Channel:")
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["2.4GHz", "5GHz"])
        self.channel_combo.currentTextChanged.connect(self.update_channel_settings)
        
        # Center Frequency (will be updated based on channel selection)
        self.center_label = QLabel("Center Frequency (GHz):")
        self.center_input = QDoubleSpinBox()
        self.center_input.setRange(0, 10)
        self.center_input.setValue(2.4415)
        
        # Span (will be updated based on channel selection)
        self.span_label = QLabel("Span (MHz):")
        self.span_input = QDoubleSpinBox()
        self.span_input.setRange(0, 1000)
        self.span_input.setValue(83.5)
        
        # Duration (will be updated based on channel selection)
        self.duration_label = QLabel("Duration (s):")
        self.duration_input = QDoubleSpinBox()
        self.duration_input.setRange(1, 120)
        self.duration_input.setValue(30)

        # Create table to display peak information
        self.peak_table = QTableWidget(3, 2)
        self.peak_table.setHorizontalHeaderLabels(['Parameter', 'Value'])
        self.peak_table.setVerticalHeaderLabels(['Peak Level', 'Peak Frequency', 'Channel'])
        self.peak_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.peak_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.peak_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Add channel selection to layout
        self.config_layout.addWidget(self.channel_label)
        self.config_layout.addWidget(self.channel_combo)
        self.config_layout.addWidget(self.center_label)
        self.config_layout.addWidget(self.center_input)
        self.config_layout.addWidget(self.span_label)
        self.config_layout.addWidget(self.span_input)
        self.config_layout.addWidget(self.duration_label)
        self.config_layout.addWidget(self.duration_input)
        
        # Start, Stop, and Clear buttons
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_acquisition)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_acquisition)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_hold)

        # Continue button (for pause-on-violation)
        self.continue_button = QPushButton("Continue")
        self.continue_button.setEnabled(False)
        self.continue_button.clicked.connect(self.continue_acquisition)
        
        self.config_layout.addWidget(self.start_button)
        self.config_layout.addWidget(self.stop_button)
        self.config_layout.addWidget(self.clear_button)
        self.config_layout.addWidget(self.continue_button)

        # Create horizontal layout for plot and data display
        plot_layout = QHBoxLayout()
        
        # --- Plot Initialization ---
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        plot_layout.addWidget(self.canvas)
        
        # Create scrollable table for peak data
        self.peak_table = QTableWidget(20, 4)  # 20 rows for scrolling, 4 columns
        self.peak_table.setHorizontalHeaderLabels(['Peak Level (dBm)', 'Frequency (MHz)', 'Channel', 'Time'])
        self.peak_table.setVerticalHeaderLabels([str(i) for i in range(1, 21)])
        self.peak_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.peak_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.peak_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.peak_table.setSelectionMode(QTableWidget.NoSelection)
        
        # Set up scroll area for peak table
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.peak_table)
        plot_layout.addWidget(self.scroll_area)

        # --- Per-Channel Peak Table (additional view) ---
        self.channel_peak_table = QTableWidget(13, 3)  # Max 13 channels (2.4GHz)
        self.channel_peak_table.setHorizontalHeaderLabels(['Channel', 'Center Freq (MHz)', 'Peak Level (dBm)'])
        self.channel_peak_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.channel_peak_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.channel_peak_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.channel_peak_table.setSelectionMode(QTableWidget.NoSelection)
        # Place below the main table
        self.channel_peak_scroll = QScrollArea()
        self.channel_peak_scroll.setWidgetResizable(True)
        self.channel_peak_scroll.setWidget(self.channel_peak_table)
        plot_layout.addWidget(self.channel_peak_scroll)

        self.spectrum_layout.addLayout(plot_layout)

        # Initialize plot elements
        self.trace_length = 801
        self.freqs = np.linspace(2.4e9, 2.4835e9, self.trace_length)  # Default to 2.4GHz band
        self.max_hold = np.full(self.trace_length, -150.0, dtype=np.float32)
        self.mask_threshold = -45

        self.line_live, = self.ax.plot(self.freqs / 1e6, np.zeros_like(self.freqs), label="Live Trace")
        self.line_max, = self.ax.plot(self.freqs / 1e6, self.max_hold, label="Max Hold", linestyle='--', color='orange')
        self.line_mask = self.ax.hlines(self.mask_threshold, self.freqs[0] / 1e6, self.freqs[-1] / 1e6, colors='red', linestyles='dotted', label="Mask Threshold")
        self.line_marker = self.ax.axvline(x=0, color='green', linestyle='dashdot', label='Peak Marker')

        self.ax.set_xlim(self.freqs[0] / 1e6, self.freqs[-1] / 1e6)
        self.ax.set_ylim(-130, -20)
        self.ax.set_xlabel("Frequency (MHz)")
        self.ax.set_ylabel("Power (dBm)")
        self.ax.set_title("Live Spectrum with Max Hold & Trigger")
        self.ax.legend()
        self.canvas.draw()

        # --- Control Tab Layout ---
        self.control_layout = QVBoxLayout()
        self.control_tab.setLayout(self.control_layout)

        # Reference Level
        self.ref_level_label = QLabel("Reference Level (dBm):")
        self.ref_level_input = QDoubleSpinBox()
        self.ref_level_input.setRange(-130, 10)
        self.ref_level_input.setValue(-60)
        self.ref_level_input.valueChanged.connect(self.update_reference_level)
        
        # Resolution Bandwidth (RBW)
        self.rbw_label = QLabel("Resolution Bandwidth (kHz):")
        self.rbw_input = QDoubleSpinBox()
        self.rbw_input.setRange(1, 1000)
        self.rbw_input.setValue(1)
        self.rbw_input.valueChanged.connect(self.update_rbw)
        
        # Video Bandwidth (VBW)
        self.vbw_label = QLabel("Video Bandwidth (kHz):")
        self.vbw_input = QDoubleSpinBox()
        self.vbw_input.setRange(1, 1000)
        self.vbw_input.setValue(10)
        self.vbw_input.valueChanged.connect(self.update_vbw)
        
        # Trace Length
        self.trace_length_label = QLabel("Trace Length:")
        self.trace_length_input = QSpinBox()
        self.trace_length_input.setRange(101, 801)
        self.trace_length_input.setValue(801)
        self.trace_length_input.valueChanged.connect(self.update_trace_length)
        
        # Window Type
        self.window_label = QLabel("Window Type:")
        self.window_combo = QComboBox()
        self.window_combo.addItems([
            "Hamming",
            "Rectangular",
            "Hanning",
            "Blackman",
            "Kaiser"
        ])
        self.window_combo.currentTextChanged.connect(self.update_window_type)
        
        # Vertical Units
        self.units_label = QLabel("Vertical Units:")
        self.units_combo = QComboBox()
        self.units_combo.addItems([
            "dBm",
            "dBmV",
            "V",
            "W"
        ])
        self.units_combo.currentTextChanged.connect(self.update_vertical_units)
        
        # Add controls to layout
        self.control_layout.addWidget(self.ref_level_label)
        self.control_layout.addWidget(self.ref_level_input)
        self.control_layout.addWidget(self.rbw_label)
        self.control_layout.addWidget(self.rbw_input)
        self.control_layout.addWidget(self.vbw_label)
        self.control_layout.addWidget(self.vbw_input)
        self.control_layout.addWidget(self.trace_length_label)
        self.control_layout.addWidget(self.trace_length_input)
        self.control_layout.addWidget(self.window_label)
        self.control_layout.addWidget(self.window_combo)
        self.control_layout.addWidget(self.units_label)
        self.control_layout.addWidget(self.units_combo)

        # --- Plot Update Handling ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.start_time = None
        self.triggered = False
        
        # Store default settings
        self.default_settings = {
            'ref_level': -60,
            'rbw': 1,
            'vbw': 10,
            'trace_length': 801,
            'window': 'Kaiser',
            'units': 'dBm'
        }
        
        # Default channel settings
        self.current_channel = "2.4GHz"

    def setup_wifi_mask(self):
        """
        Set up WiFi standard mask based on current band.
        """
        if self.current_channel == "2.4GHz":
            mask = self.wifi_masks["2.4GHz"]
        else:
            mask = self.wifi_masks["5GHz"]
        
        # Remove existing mask lines
        if hasattr(self, 'mask_lines'):
            for line in self.mask_lines:
                try:
                    line.remove()
                except Exception:
                    pass  # Already removed or not present
            self.mask_lines = []
        
        # Create new mask lines
        self.mask_lines = []
        
        # Center channel mask
        center_line = self.ax.hlines(mask['mask']['thresholds']['center'],
                                   self.freqs[0] / 1e6, self.freqs[-1] / 1e6,
                                   colors='red', linestyles='dotted', 
                                   label="Center Channel Mask")
        self.mask_lines.append(center_line)
        
        # Adjacent channel mask
        adjacent_line = self.ax.hlines(mask['mask']['thresholds']['adjacent'],
                                     self.freqs[0] / 1e6, self.freqs[-1] / 1e6,
                                     colors='orange', linestyles='dotted',
                                     label="Adjacent Channel Mask")
        self.mask_lines.append(adjacent_line)
        
        # Far channel mask
        far_line = self.ax.hlines(mask['mask']['thresholds']['far'],
                                self.freqs[0] / 1e6, self.freqs[-1] / 1e6,
                                colors='green', linestyles='dotted',
                                label="Far Channel Mask")
        self.mask_lines.append(far_line)
        
        # Add channel markers
        self.channel_markers = []
        for freq in mask['center_freqs']:
            marker = self.ax.axvline(x=freq/1e6, color='purple', linestyle='dotted', alpha=0.5)
            self.channel_markers.append(marker)
        
        self.ax.legend()
        self.canvas.draw()

    def check_wifi_mask_violations(self, trace):
        """
        Check for WiFi mask violations and return violation points.
        """
        violations = {}
        
        if self.current_channel == "2.4GHz":
            mask = self.wifi_masks["2.4GHz"]
        else:
            mask = self.wifi_masks["5GHz"]
        
        # Check each channel
        for freq, power in zip(self.freqs, trace):
            if power > mask['mask']['thresholds']['center']:
                violations[freq] = power
            elif power > mask['mask']['thresholds']['adjacent']:
                violations[freq] = power
            elif power > mask['mask']['thresholds']['far']:
                violations[freq] = power
        
        return violations

    def get_channel_from_freq(self, freq):
        """
        Get WiFi channel number from frequency: always return the closest channel in the correct band.
        Robust against index errors.
        """
        if freq < 3e9:
            centers = self.wifi_masks["2.4GHz"]["center_freqs"]
            channels = self.wifi_masks["2.4GHz"]["channels"]
        else:
            centers = self.wifi_masks["5GHz"]["center_freqs"]
            channels = self.wifi_masks["5GHz"]["channels"]
        if not centers or not channels:
            print("[DEBUG] No channel centers or channel list available!")
            return None
        min_idx = int(np.argmin([abs(freq - cf) for cf in centers]))
        if min_idx >= len(channels):
            print(f"[DEBUG] Channel index {min_idx} out of range for channels list of length {len(channels)}!")
            return None
        return channels[min_idx]



    def update_reference_level(self, value):
        """Update reference level setting."""
        CONFIG_SetReferenceLevel_py(value)
        self.ax.set_ylim(value - 110, value)
        self.canvas.draw()

    def update_rbw(self, value):
        """Update resolution bandwidth setting."""
        SPECTRUM_SetSettings_py(
            rbw=value * 1e3,  # Convert kHz to Hz
            enableVBW=True,
            vbw=self.vbw_input.value() * 1e3,
            traceLength=self.trace_length_input.value(),
            window=self.get_window_type(),
            verticalUnit=self.get_vertical_units()
        )

    def update_vbw(self, value):
        """Update video bandwidth setting."""
        SPECTRUM_SetSettings_py(
            enableVBW=True,
            vbw=value * 1e3,  # Convert kHz to Hz
            traceLength=self.trace_length_input.value(),
            window=self.get_window_type(),
            verticalUnit=self.get_vertical_units()
        )

    def update_trace_length(self, value):
        """Update trace length setting."""
        self.trace_length = value
        self.freqs = np.linspace(
            self.center_input.value() * 1e9 - self.span_input.value() * 1e6 / 2,
            self.center_input.value() * 1e9 + self.span_input.value() * 1e6 / 2,
            value
        )
        SPECTRUM_SetSettings_py(
            traceLength=value,
            window=self.get_window_type(),
            verticalUnit=self.get_vertical_units()
        )
        self.update_plot()

    def update_window_type(self, value):
        """Update window type setting."""
        window_map = {
            "Rectangular": SpectrumWindows.SpectrumWindow_Rectangle,
            "Hamming": SpectrumWindows.SpectrumWindow_Hann,
            "Hanning": SpectrumWindows.SpectrumWindow_Hann,
            "Blackman": SpectrumWindows.SpectrumWindow_BlackmanHarris,
            "Kaiser": SpectrumWindows.SpectrumWindow_Kaiser
        }
        SPECTRUM_SetSettings_py(
            window=window_map[value],
            verticalUnit=self.get_vertical_units()
        )

    def get_vertical_units(self):
        """Return the current vertical unit enum for SPECTRUM_SetSettings_py."""
        units_map = {
            "dBm": SpectrumVerticalUnits.SpectrumVerticalUnit_dBm,
            "dBmV": SpectrumVerticalUnits.SpectrumVerticalUnit_dBmV,
            "V": SpectrumVerticalUnits.SpectrumVerticalUnit_Volt,
            "W": SpectrumVerticalUnits.SpectrumVerticalUnit_Watt
        }
        value = self.units_combo.currentText()
        return units_map.get(value, SpectrumVerticalUnits.SpectrumVerticalUnit_dBm)

    def update_vertical_units(self, value):
        """Update vertical units setting."""
        units_map = {
            "dBm": SpectrumVerticalUnits.SpectrumVerticalUnit_dBm,
            "dBmV": SpectrumVerticalUnits.SpectrumVerticalUnit_dBmV,
            "V": SpectrumVerticalUnits.SpectrumVerticalUnit_Volt,
            "W": SpectrumVerticalUnits.SpectrumVerticalUnit_Watt
        }
        SPECTRUM_SetSettings_py(
            verticalUnit=units_map[value]
        )
        self.ax.set_ylabel(f"Power ({value})")
        self.canvas.draw()

    def update_channel_settings(self, channel):
        """
        Update GUI settings based on selected WiFi channel.
        """
        self.current_channel = channel

        if channel == "2.4GHz":
            # 2.4GHz WiFi band (2.400 - 2.4835 GHz)
            self.center_input.setValue(2.4415)  # Center of 2.4GHz band
            self.span_input.setValue(83.5)     # Full 2.4GHz band
            self.freqs = np.linspace(2.4e9, 2.4835e9, self.trace_length)
        else:  # 5GHz
            # 5GHz WiFi band (5.150 - 5.825 GHz)
            self.center_input.setValue(5.4875)  # Center of 5GHz band
            self.span_input.setValue(675)      # Full 5GHz band
            self.freqs = np.linspace(5.15e9, 5.825e9, self.trace_length)
        
        # Update WiFi mask
        self.setup_wifi_mask()
        
        # Update plot axes
        self.ax.set_xlim(self.freqs[0] / 1e6, self.freqs[-1] / 1e6)
        self.canvas.draw()
        if hasattr(self, 'line_marker') and self.line_marker is not None:
            try:
                self.line_marker.remove()
            except Exception:
                pass  # Already removed or not present
            self.line_marker = None
        self.line_marker = self.ax.axvline(x=0, color='green', linestyle='dashdot', label='Peak Marker')
        
        self.ax.set_xlim(self.freqs[0] / 1e6, self.freqs[-1] / 1e6)
        self.ax.set_title(f"Live Spectrum - {channel} Band")
        self.canvas.draw()

    def start_acquisition(self):
        """
        Start spectrum acquisition with user-defined settings.
        Configures the spectrum analyzer with center frequency, span, and trigger levels.
        Sets up the plot with live trace, max hold, and WiFi standard mask.
        """
        # Convert user inputs to proper frequency units
        self.center_freq = self.center_input.value() * 1e9  # GHz to Hz
        self.span = self.span_input.value() * 1e6  # MHz to Hz
        self.max_duration = self.duration_input.value()  # seconds
        
        # Configure spectrum analyzer
        CONFIG_SetCenterFreq_py(self.center_freq)
        CONFIG_SetReferenceLevel_py(-60)
        SPECTRUM_SetSettings_py(
            span=self.span,
            rbw=1e3,
            enableVBW=True,
            vbw=10e3,
            traceLength=self.trace_length,
            window=SpectrumWindows.SpectrumWindow_Kaiser,
            verticalUnit=SpectrumVerticalUnits.SpectrumVerticalUnit_dBm
        )

        # Always set self.freqs based on selected band, not what the device returns
        if self.current_channel == "2.4GHz":
            self.freqs = np.linspace(2.4e9, 2.4835e9, self.trace_length)
        else:
            self.freqs = np.linspace(5.15e9, 5.825e9, self.trace_length)
        self.max_hold = np.full(self.trace_length, -150.0, dtype=np.float32)
        
        # Initialize plot elements
        self.ax.clear()
        self.line_live, = self.ax.plot(self.freqs / 1e6, np.zeros_like(self.freqs), label="Live Trace")
        self.line_max, = self.ax.plot(self.freqs / 1e6, self.max_hold, label="Max Hold", linestyle='--', color='orange')
        
        # Set up WiFi standard mask
        self.setup_wifi_mask()
        
        self.ax.set_xlim(self.freqs[0] / 1e6, self.freqs[-1] / 1e6)
        self.ax.set_ylim(-130, -20)
        self.ax.set_xlabel("Frequency (MHz)")
        self.ax.set_ylabel("Power (dBm)")
        self.ax.set_title("Live Spectrum with WiFi Mask")
        self.ax.legend()
        self.canvas.draw()
        
        self.start_time = time.time()
        self.timer.start(250)


    def continue_acquisition(self):
        """
        Resume acquisition after pause (mask violation).
        """
        self.timer.start(250)
        self.continue_button.setEnabled(False)

    def stop_acquisition(self):
        """
        Stop the spectrum acquisition.
        """
        self.timer.stop()

    def clear_hold(self):
        """
        Clear the max hold data.
        """
        if self.max_hold is not None:
            self.max_hold = np.full(self.trace_length, -150.0, dtype=np.float32)
            if self.line_max:
                self.line_max.set_ydata(self.max_hold)
            self.canvas.draw()

    def update_plot(self):
        """
        Update the spectrum plot with new trace data.
        Handles live trace, max hold, peak detection, WiFi mask violation checking.
        """
        # Acquire new trace data from the spectrum analyzer
        SPECTRUM_AcquireTrace_py()
        SPECTRUM_WaitForTraceReady_py(100)  # Wait for the trace to be ready
        trace = SPECTRUM_GetTrace_py(trace=SpectrumTraces.SpectrumTrace1, tracePoints=self.trace_length)

        # Update live trace
        self.line_live.set_ydata(trace)
        
        # Update max hold if within duration
        if time.time() - self.start_time <= self.max_duration:
            self.max_hold = np.maximum(self.max_hold, trace)
            self.line_max.set_ydata(self.max_hold)
            
        # Signal analysis
        print(f"[DEBUG] Band: {self.current_channel}, Freq range: {self.freqs[0]/1e6:.1f}-{self.freqs[-1]/1e6:.1f} MHz")
        if np.any(trace > -100):  # Signal is present if any point is above -100 dBm
            self.current_signal_level = np.max(trace)
            peak_index = np.argmax(trace)
            peak_freq = self.freqs[peak_index]
            # Do not overwrite self.current_channel here; use the selected band
            channel_for_title = self.get_channel_from_freq(peak_freq)
            print(f"[DEBUG] Peak freq: {peak_freq/1e6:.2f} MHz, Channel: {channel_for_title}")
            
            # Update title with signal info
            title = f"Live Spectrum - Signal Level: {self.current_signal_level:.1f} dBm"
            if channel_for_title:
                title += f" (Channel {channel_for_title})"
            title_color = 'black'
        else:
            title = "No Signal Detected"
            title_color = 'gray'
            self.current_signal_level = None
            self.current_channel = None
        
        # Check for mask violations
        violations = self.check_wifi_mask_violations(trace)
        if violations:
            self.ax.set_title(f"Live Spectrum with Max Hold & Trigger\nMASK VIOLATION!")
            self.timer.stop()  # Pause acquisition on violation
            self.continue_button.setEnabled(True)
        else:
            self.ax.set_title("Live Spectrum with Max Hold & Trigger")
            self.continue_button.setEnabled(False)

        # --- Add violation markers (red dots) ---
        # Remove previous violation markers if they exist
        if hasattr(self, 'violation_markers'):
            for marker in self.violation_markers:
                marker.remove()
        self.violation_markers = []
        if violations:
            v_freqs = [f/1e6 for f in violations.keys()]
            v_powers = list(violations.values())
            marker = self.ax.scatter(v_freqs, v_powers, color='red', marker='o', label='Mask Violation')
            self.violation_markers.append(marker)
            # Keep legend updated
            handles, labels = self.ax.get_legend_handles_labels()
            if 'Mask Violation' not in labels:
                self.ax.legend()
        else:
            # Remove 'Mask Violation' from legend if no violations
            handles, labels = self.ax.get_legend_handles_labels()
            if 'Mask Violation' in labels:
                idx = labels.index('Mask Violation')
                handles.pop(idx)
                labels.pop(idx)
                self.ax.legend(handles, labels)

        # Update plot
        self.canvas.draw()

        # --- Update per-channel peak table (additional view) ---
        # Determine current band
        if self.freqs[0] < 3e9:
            band = '2.4GHz'
        else:
            band = '5GHz'
        channels = self.wifi_masks[band]['channels']
        centers = self.wifi_masks[band]['center_freqs']
        if band == '2.4GHz':
            channel_width = 22e6
        else:
            channel_width = 20e6
        for i, (ch, cf) in enumerate(zip(channels, centers)):
            # Find indices within channel boundaries (center +/- half channel width)
            ch_min = cf - channel_width / 2
            ch_max = cf + channel_width / 2
            indices = np.where((self.freqs >= ch_min) & (self.freqs <= ch_max))[0]
            if len(indices) > 0:
                peak_val = np.max(trace[indices])
            else:
                peak_val = float('nan')
            self.channel_peak_table.setItem(i, 0, QTableWidgetItem(str(ch)))
            self.channel_peak_table.setItem(i, 1, QTableWidgetItem(f"{cf/1e6:.1f}"))
            self.channel_peak_table.setItem(i, 2, QTableWidgetItem(f"{peak_val:.1f}" if not np.isnan(peak_val) else '-'))
        # Clear remaining rows if fewer than current table rows
        for i in range(len(channels), self.channel_peak_table.rowCount()):
            for col in range(3):
                self.channel_peak_table.setItem(i, col, QTableWidgetItem("-"))

        
        # Update peak information and marker
        if np.any(trace > -100):
            # Find all peaks (local maxima)
            peaks = []
            for i in range(1, len(trace) - 1):
                if trace[i] > trace[i - 1] and trace[i] > trace[i + 1] and trace[i] > -100:
                    peaks.append(i)
            
            if peaks:
                # Sort peaks by power level (strongest first)
                peaks.sort(key=lambda x: trace[x], reverse=True)
                
                # Add up to 20 peaks to the table
                current_time = time.strftime("%H:%M:%S")
                for i, peak_index in enumerate(peaks[:20]):
                    peak_level = trace[peak_index]
                    peak_freq = self.freqs[peak_index]
                    peak_freq_mhz = peak_freq / 1e6
                    channel = self.get_channel_from_freq(peak_freq)
                    
                    # Set background color based on signal strength
                    if peak_level > -40:  # Strong signal
                        color = QColor(255, 200, 200)  # Light red
                    elif peak_level > -60:  # Medium signal
                        color = QColor(255, 255, 200)  # Light yellow
                    else:  # Weak signal
                        color = QColor(200, 255, 200)  # Light green
                    
                    # Update table row
                    self.peak_table.setItem(i, 0, QTableWidgetItem(f"{peak_level:.1f}"))
                    self.peak_table.setItem(i, 1, QTableWidgetItem(f"{peak_freq_mhz:.1f}"))
                    self.peak_table.setItem(i, 2, QTableWidgetItem(f"{channel}" if channel else "-"))
                    self.peak_table.setItem(i, 3, QTableWidgetItem(current_time))
                    
                    # Set background color for entire row
                    for col in range(4):
                        item = self.peak_table.item(i, col)
                        item.setBackground(color)
                
                # Show strongest peak marker
                strongest_peak = peaks[0]
                self.line_marker.set_xdata([self.freqs[strongest_peak] / 1e6])
            else:
                # No valid peaks found
                self.line_marker.set_xdata([0])  # Hide marker if no signal
                
                # Clear table
                for row in range(20):
                    for col in range(4):
                        self.peak_table.setItem(row, col, QTableWidgetItem("-"))
        else:
            self.line_marker.set_xdata([0])  # Hide marker if no signal
            
            # Clear table
            for row in range(20):
                for col in range(4):
                    self.peak_table.setItem(row, col, QTableWidgetItem("-"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpectrumAnalyzerGUI()
    window.show()
    sys.exit(app.exec_())