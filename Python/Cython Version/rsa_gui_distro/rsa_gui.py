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
from PyQt5.QtCore import QTimer

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
            return {
                'actualStartFreq': 2.4e9,
                'actualStopFreq': 2.43e9
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
                'center_freqs': np.arange(2412e6, 2484e6, 5e6),
                'mask': {
                    'channel_width': 22e6,
                    'thresholds': {
                        'center': -40,
                        'adjacent': -50,
                        'far': -60
                    }
                }
            },
            '5GHz': {
                'channels': list(range(36, 64, 4)) + list(range(100, 141, 4)),
                'center_freqs': np.arange(5180e6, 5825e6, 20e6),
                'mask': {
                    'channel_width': 20e6,
                    'thresholds': {
                        'center': -40,
                        'adjacent': -50,
                        'far': -60
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
        
        # Center Frequency
        self.center_label = QLabel("Center Frequency (GHz):")
        self.center_input = QDoubleSpinBox()
        self.center_input.setRange(0, 10)
        self.center_input.setValue(2.4415)
        
        # Span
        self.span_label = QLabel("Span (MHz):")
        self.span_input = QDoubleSpinBox()
        self.span_input.setRange(0, 1000)
        self.span_input.setValue(83.5)
        
        # Duration
        self.duration_label = QLabel("Duration (s):")
        self.duration_input = QDoubleSpinBox()
        self.duration_input.setRange(1, 120)
        self.duration_input.setValue(30)

        # Create scrollable table for peak data
        self.peak_table = QTableWidget(20, 4)
        self.peak_table.setHorizontalHeaderLabels(['Peak Level (dBm)', 'Frequency (MHz)', 'Channel', 'Time'])
        self.peak_table.setVerticalHeaderLabels([str(i) for i in range(1, 21)])
        self.peak_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.peak_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.peak_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.peak_table.setSelectionMode(QTableWidget.NoSelection)
        
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
        
        self.config_layout.addWidget(self.start_button)
        self.config_layout.addWidget(self.stop_button)
        self.config_layout.addWidget(self.clear_button)

        # Create horizontal layout for plot and data display
        plot_layout = QHBoxLayout()
        
        # --- Plot Initialization ---
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        plot_layout.addWidget(self.canvas)
        
        # Set up scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.peak_table)
        plot_layout.addWidget(self.scroll_area)
        
        self.spectrum_layout.addLayout(plot_layout)

        # Initialize plot elements
        self.trace_length = 801
        self.freqs = np.linspace(2.4e9, 2.4835e9, self.trace_length)
        self.max_hold = np.full(self.trace_length, -150.0, dtype=np.float32)
        self.mask_threshold = -40

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
            "Rectangular",
            "Hamming",
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
            "dBuV",
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
        
        # Default settings
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

    def get_channel_from_freq(self, freq):
        """
        Get WiFi channel number from frequency.
        """
        if self.current_channel == "2.4GHz":
            # 2.4GHz channels are 5MHz apart, starting at 2412MHz
            channel = int((freq - 2412e6) / 5e6) + 1
            if 1 <= channel <= 13:
                return channel
        else:  # 5GHz
            # 5GHz channels are 20MHz apart, starting at 5180MHz
            channel = int((freq - 5180e6) / 20e6) + 36
            if 36 <= channel <= 140:
                return channel
        return None

    def update_reference_level(self, value):
        """Update reference level setting."""
        CONFIG_SetReferenceLevel_py(value)
        self.ax.set_ylim(value - 110, value)
        self.canvas.draw()

    def update_rbw(self, value):
        """Update resolution bandwidth setting."""
        SPECTRUM_SetSettings_py(
            rbw=value * 1e3,
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
            vbw=value * 1e3,
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
            "Rectangular": SpectrumWindows.SpectrumWindow_Rectangular,
            "Hamming": SpectrumWindows.SpectrumWindow_Hamming,
            "Hanning": SpectrumWindows.SpectrumWindow_Hanning,
            "Blackman": SpectrumWindows.SpectrumWindow_Blackman,
            "Kaiser": SpectrumWindows.SpectrumWindow_Kaiser
        }
        SPECTRUM_SetSettings_py(
            window=window_map[value],
            verticalUnit=self.get_vertical_units()
        )

    def update_vertical_units(self, value):
        """Update vertical units setting."""
        units_map = {
            "dBm": SpectrumVerticalUnits.SpectrumVerticalUnit_dBm,
            "dBmV": SpectrumVerticalUnits.SpectrumVerticalUnit_dBmV,
            "dBuV": SpectrumVerticalUnits.SpectrumVerticalUnit_dBuV,
            "V": SpectrumVerticalUnits.SpectrumVerticalUnit_V,
            "W": SpectrumVerticalUnits.SpectrumVerticalUnit_W
        }
        SPECTRUM_SetSettings_py(
            verticalUnit=units_map[value]
        )
        self.ax.set_ylabel(f"Power ({value})")
        self.canvas.draw()

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
                line.remove()
        
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
        
        self.ax.legend()
        self.canvas.draw()

    def check_wifi_mask_violations(self, trace):
        """
        Check for WiFi mask violations and return violation points.
        """
        if self.current_channel == "2.4GHz":
            mask = self.wifi_masks["2.4GHz"]
        else:
            mask = self.wifi_masks["5GHz"]
        
        violations = []
        for i, power in enumerate(trace):
            freq = self.freqs[i]
            channel = self.get_channel_from_freq(freq)
            
            if channel:
                if power > mask['mask']['thresholds']['center']:
                    violations.append((freq, power, 'center'))
                elif power > mask['mask']['thresholds']['adjacent']:
                    violations.append((freq, power, 'adjacent'))
                elif power > mask['mask']['thresholds']['far']:
                    violations.append((freq, power, 'far'))
        
        return violations

    def update_channel_settings(self, channel):
        """
        Update GUI settings based on selected WiFi channel.
        """
        self.current_channel = channel
        
        if channel == "2.4GHz":
            self.center_input.setValue(2.4415)
            self.span_input.setValue(83.5)
            self.freqs = np.linspace(2.4e9, 2.4835e9, self.trace_length)
        else:  # 5GHz
            self.center_input.setValue(5.250)
            self.span_input.setValue(400)
            self.freqs = np.linspace(5.180e9, 5.580e9, self.trace_length)
        
        self.ax.set_xlim(self.freqs[0] / 1e6, self.freqs[-1] / 1e6)
        self.setup_wifi_mask()
        self.canvas.draw()

    def start_acquisition(self):
        """
        Start spectrum acquisition with user-defined settings.
        Configures the spectrum analyzer with center frequency, span, and trigger levels.
        Sets up the plot with live trace, max hold, and WiFi standard mask.
        """
        center_freq = self.center_input.value() * 1e9
        span = self.span_input.value() * 1e6
        
        CONFIG_SetCenterFreq_py(center_freq)
        SPECTRUM_SetSettings_py(
            startFreq=center_freq - span/2,
            stopFreq=center_freq + span/2,
            rbw=self.rbw_input.value() * 1e3,
            enableVBW=True,
            vbw=self.vbw_input.value() * 1e3,
            traceLength=self.trace_length_input.value(),
            window=self.get_window_type(),
            verticalUnit=self.get_vertical_units()
        )
        
        self.max_hold = np.full(self.trace_length, -150.0, dtype=np.float32)
        self.line_max.set_ydata(self.max_hold)
        self.timer.start(100)  # Update every 100ms

    def stop_acquisition(self):
        """
        Stop the spectrum acquisition.
        """
        self.timer.stop()

    def clear_hold(self):
        """
        Clear the max hold data.
        """
        self.max_hold = np.full(self.trace_length, -150.0, dtype=np.float32)
        self.line_max.set_ydata(self.max_hold)
        self.canvas.draw()

    def update_plot(self):
        """
        Update the spectrum plot with new trace data.
        Handles live trace, max hold, peak detection, WiFi mask violation checking.
        """
        # Acquire new trace data
        SPECTRUM_AcquireTrace_py()
        SPECTRUM_WaitForTraceReady_py(1000)
        trace = SPECTRUM_GetTrace_py()

        # Update live trace
        self.line_live.set_ydata(trace)

        # Update max hold
        self.max_hold = np.maximum(self.max_hold, trace)
        self.line_max.set_ydata(self.max_hold)

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

        # Check for mask violations
        violations = self.check_wifi_mask_violations(trace)
        if violations:
            self.ax.set_title(f"Live Spectrum with Max Hold & Trigger\nMASK VIOLATION!")
        else:
            self.ax.set_title("Live Spectrum with Max Hold & Trigger")

        # Update plot
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpectrumAnalyzerGUI()
    window.show()
    sys.exit(app.exec_())
