import os
import sys
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QPushButton, QSpinBox, QTabWidget
)
from PyQt5.QtCore import QTimer

rsa_dll_path = r"C:\Tektronix\RSA_API\lib\x64"
os.add_dll_directory(rsa_dll_path)
from rsa_api import *

class SpectrumAnalyzerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RSA306B Spectrum Analyzer")
        self.setGeometry(100, 100, 1000, 600)

        # --- Init RSA device ---
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

        self.center_label = QLabel("Center Freq (GHz):")
        self.center_input = QDoubleSpinBox()
        self.center_input.setRange(0.01, 6.0)
        self.center_input.setDecimals(3)
        self.center_input.setValue(2.41)

        self.span_label = QLabel("Span (MHz):")
        self.span_input = QDoubleSpinBox()
        self.span_input.setRange(1, 40)
        self.span_input.setValue(30)

        self.duration_label = QLabel("Max Hold (sec):")
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 120)
        self.duration_input.setValue(30)

        self.trigger_label = QLabel("Trigger Level (dBm):")
        self.trigger_input = QDoubleSpinBox()
        self.trigger_input.setRange(-130, 0)
        self.trigger_input.setValue(-100)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_acquisition)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_acquisition)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_hold)

        self.config_layout.addWidget(self.center_label)
        self.config_layout.addWidget(self.center_input)
        self.config_layout.addWidget(self.span_label)
        self.config_layout.addWidget(self.span_input)
        self.config_layout.addWidget(self.duration_label)
        self.config_layout.addWidget(self.duration_input)
        self.config_layout.addWidget(self.trigger_label)
        self.config_layout.addWidget(self.trigger_input)
        self.config_layout.addWidget(self.start_button)
        self.config_layout.addWidget(self.stop_button)
        self.config_layout.addWidget(self.clear_button)

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        self.spectrum_layout.addWidget(self.canvas)

        # --- Control Tab Layout ---
        self.control_layout = QVBoxLayout()
        self.control_tab.setLayout(self.control_layout)

        self.control_label = QLabel("Spectrum Module Ready. Adjust settings in main tab.")
        self.control_layout.addWidget(self.control_label)

        # --- Plot Update Handling ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.max_hold = None
        self.freqs = None
        self.trace_length = 801
        self.start_time = None
        self.line_live = None
        self.line_max = None
        self.line_mask = None
        self.line_marker = None
        self.triggered = False

    def start_acquisition(self):
        self.center_freq = self.center_input.value() * 1e9
        self.span = self.span_input.value() * 1e6
        self.max_duration = self.duration_input.value()
        self.trigger_level = self.trigger_input.value()

        CONFIG_SetCenterFreq_py(self.center_freq)
        CONFIG_SetReferenceLevel_py(-60)
        SPECTRUM_SetSettings_py(
            span=self.span,
            rbw=100e3,
            enableVBW=True,
            vbw=50e3,
            traceLength=self.trace_length,
            window=SpectrumWindows.SpectrumWindow_Kaiser,
            verticalUnit=SpectrumVerticalUnits.SpectrumVerticalUnit_dBm
        )

        TRIG_SetTriggerMode_py(TriggerMode.triggered)
        TRIG_SetIFPowerTriggerLevel_py(self.trigger_level)

        settings = SPECTRUM_GetSettings_py()
        self.freqs = np.linspace(settings['actualStartFreq'], settings['actualStopFreq'], self.trace_length)
        self.max_hold = np.full(self.trace_length, -150.0, dtype=np.float32)
        self.mask_threshold = -40

        self.ax.clear()
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

        self.start_time = time.time()
        self.timer.start(250)

    def stop_acquisition(self):
        self.timer.stop()

    def clear_hold(self):
        if self.max_hold is not None:
            self.max_hold = np.full(self.trace_length, -150.0, dtype=np.float32)
            if self.line_max:
                self.line_max.set_ydata(self.max_hold)
            self.canvas.draw()

    def update_plot(self):
        SPECTRUM_AcquireTrace_py()
        SPECTRUM_WaitForTraceReady_py(100)
        trace = SPECTRUM_GetTrace_py(trace=SpectrumTraces.SpectrumTrace1, tracePoints=self.trace_length)

        self.line_live.set_ydata(trace)
        if time.time() - self.start_time <= self.max_duration:
            self.max_hold = np.maximum(self.max_hold, trace)
            self.line_max.set_ydata(self.max_hold)

        peak_index = np.argmax(trace)
        peak_freq_mhz = self.freqs[peak_index] / 1e6
        self.line_marker.set_xdata([peak_freq_mhz])

        if np.any(trace > self.mask_threshold):
            self.ax.set_title("Live Spectrum - MASK VIOLATION!", color='red')
        else:
            self.ax.set_title("Live Spectrum with Max Hold & Trigger")

        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpectrumAnalyzerGUI()
    window.show()
    sys.exit(app.exec_())