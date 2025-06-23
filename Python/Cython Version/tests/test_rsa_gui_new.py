import pytest
import numpy as np
import sys
import os

# Set testing environment variable
os.environ['RSA_API_TESTING'] = '1'

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock matplotlib imports
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Mock pyplot
plt = type('plt', (), {
    'subplots': lambda: (Figure(), Figure().add_subplot(111)),
    'show': lambda: None
})

# Mock PyQt5 imports
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QPushButton, QSpinBox, QTabWidget
)
from PyQt5.QtCore import QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

# Mock rsa_api module
rsa_api = type('rsa_api', (), {
    'DEVICE_Connect_py': lambda: True,
    'DEVICE_Run_py': lambda: True,
    'SPECTRUM_SetEnable_py': lambda enable: True,
    'SPECTRUM_SetDefault_py': lambda: True,
    'CONFIG_SetCenterFreq_py': lambda freq: True,
    'CONFIG_SetReferenceLevel_py': lambda level: True,
    'SPECTRUM_SetSettings_py': lambda **kwargs: True,
    'SPECTRUM_GetSettings_py': lambda: {
        'actualStartFreq': 2.4e9,
        'actualStopFreq': 2.43e9
    },
    'SPECTRUM_AcquireTrace_py': lambda: True,
    'SPECTRUM_WaitForTraceReady_py': lambda timeout: True,
    'SPECTRUM_GetTrace_py': lambda **kwargs: np.zeros(801)
})

# Add rsa_api to sys.modules to prevent import error
sys.modules['rsa_api'] = rsa_api

# Mock QApplication for testing
class MockQApplication(QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__([])

class MockQWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.setWindowTitle("RSA306B Spectrum Analyzer")
        self.setGeometry(100, 100, 1000, 600)

QApplication = MockQApplication
QWidget = MockQWidget

# Mock QtBot for testing
class MockQtBot:
    def mouseClick(self, widget, button):
        widget.click()
    def addWidget(self, widget):
        pass

qtbot = MockQtBot()

# Import the main module after setting up mocks
from rsa_gui import SpectrumAnalyzerGUI

@pytest.fixture
def app():
    """Create and return a properly initialized GUI instance."""
    # Create QApplication instance
    test_app = QApplication([])
    
    # Create and initialize GUI
    window = SpectrumAnalyzerGUI()
    
    # Initialize GUI components with default values
    window.center_input.setValue(2.41)
    window.span_input.setValue(30)
    window.duration_input.setValue(30)
    window.trigger_input.setValue(-10)
    
    # Initialize plot components
    window.fig, window.ax = plt.subplots()
    window.canvas = FigureCanvas(window.fig)
    window.spectrum_layout.addWidget(window.canvas)
    
    # Initialize plot lines
    window.line_live, = window.ax.plot([], [])
    window.line_max, = window.ax.plot([], [])
    window.line_mask = window.ax.axhline(-40, color='r', linestyle='--')
    window.line_marker = window.ax.axvline(0, color='r', linestyle='--')
    
    # Set plot limits
    window.ax.set_xlim(2400, 2430)
    window.ax.set_ylim(-130, -20)
    
    return window

def test_initial_state(app):
    """Test the initial state of the GUI."""
    assert app.windowTitle() == "RSA306B Spectrum Analyzer"
    assert app.geometry().width() == 1000
    assert app.geometry().height() == 600
    assert app.tabs.count() == 2
    assert app.tabs.tabText(0) == "Live Spectrum"
    assert app.tabs.tabText(1) == "Spectrum Control"

def test_start_acquisition(app):
    """Test starting acquisition."""
    app.start_acquisition()
    assert app.timer.isActive() is True
    assert app.center_freq == 2.41e9
    assert app.span == 30e6
    assert app.max_duration == 30
    assert app.trigger_level == -10

def test_update_plot(app):
    """Test plot update functionality."""
    # Set up mock trace data
    app.freqs = np.linspace(2.4e9, 2.43e9, 801)
    app.update_plot()
    
    # Check if plot lines exist
    assert app.line_live is not None
    assert app.line_max is not None
    assert app.line_mask is not None
    assert app.line_marker is not None
    
    # Check if plot limits are set correctly
    xlim = app.ax.get_xlim()
    assert xlim[0] == pytest.approx(2400)
    assert xlim[1] == pytest.approx(2430)
    assert app.ax.get_ylim() == (-130, -20)

def test_peak_detection(app):
    """Test peak detection functionality."""
    # Set up mock data with a peak
    app.freqs = np.linspace(2.4e9, 2.43e9, 801)
    mock_trace = np.zeros(801)
    mock_trace[400] = -30  # Peak at index 400
    
    # Update plot with mock data
    app.update_plot()
    
    # Check if peak marker is at correct position
    peak_freq = app.freqs[400] / 1e6  # Convert to MHz
    assert app.line_marker.get_xdata()[0] == pytest.approx(peak_freq, abs=1e-6)

def test_mask_violation(app):
    """Test mask violation detection."""
    # Set up mock data that violates mask
    app.freqs = np.linspace(2.4e9, 2.43e9, 801)
    mock_trace = np.full(801, -35)  # Above -40dBm mask threshold
    
    # Update plot with mock data
    app.update_plot()
    
    # Check title for mask violation
    assert "MASK VIOLATION" in app.ax.get_title()

def test_clear_button_click(app):
    """Test clear button click functionality."""
    # Set some arbitrary max hold data
    app.max_hold = np.full(801, -50.0, dtype=np.float32)
    
    # Call clear_hold method directly
    app.clear_hold()
    
    # Verify max hold data is reset to default
    assert np.all(app.max_hold == -150.0)  # Default reset value

def test_stop_acquisition(app):
    """Test stopping acquisition."""
    # Start acquisition first
    app.start_acquisition()
    assert app.timer.isActive() is True
    
    # Stop acquisition
    app.stop_acquisition()
    assert app.timer.isActive() is False

def test_input_ranges(app):
    """Test input control value ranges."""
    # Test center frequency range (0.01-6.0 GHz)
    app.center_input.setValue(0.009)  # Below min
    assert app.center_input.value() == 0.01
    app.center_input.setValue(6.1)    # Above max
    assert app.center_input.value() == 6.0
    
    # Test span range (1-40 MHz)
    app.span_input.setValue(0.9)      # Below min
    assert app.span_input.value() == 1
    app.span_input.setValue(41)       # Above max
    assert app.span_input.value() == 40
    
    # Test duration range (1-120 seconds)
    app.duration_input.setValue(0)    # Below min
    assert app.duration_input.value() == 1
    app.duration_input.setValue(121)  # Above max
    assert app.duration_input.value() == 120
    
    # Test trigger level range (-130 to 0 dBm)
    app.trigger_input.setValue(-131)  # Below min
    assert app.trigger_input.value() == -130
    app.trigger_input.setValue(1)     # Above max
    assert app.trigger_input.value() == 0

def test_gui_layout(app):
    """Test GUI layout structure."""
    # Check if spectrum tab has the correct layout
    assert isinstance(app.spectrum_layout, QVBoxLayout)
    assert isinstance(app.config_layout, QHBoxLayout)
    
    # Check if all input controls are present in config layout
    assert app.center_input in app.config_layout.children()
    assert app.span_input in app.config_layout.children()
    assert app.duration_input in app.config_layout.children()
    assert app.trigger_input in app.config_layout.children()
    
    # Check if all buttons are present and enabled
    assert app.start_button.isEnabled()
    assert app.stop_button.isEnabled()
    assert app.clear_button.isEnabled()
    
    # Check if plot canvas is present in spectrum layout
    assert app.canvas in app.spectrum_layout.children()

def test_plot_labels_and_axes(app):
    """Test plot labels and axes configuration."""
    # Initialize plot with default values
    app.start_acquisition()
    
    # Check axis labels
    assert app.ax.get_xlabel() == "Frequency (MHz)"
    assert app.ax.get_ylabel() == "Power (dBm)"
    
    # Check axis limits
    xlim = app.ax.get_xlim()
    assert xlim[0] == pytest.approx(2400)
    assert xlim[1] == pytest.approx(2430)
    assert app.ax.get_ylim() == (-130, -20)
    
    # Check title
    assert "Live Spectrum" in app.ax.get_title()
    
    # Check legend
    legend = app.ax.get_legend()
    assert legend is not None
    labels = [text.get_text() for text in legend.get_texts()]
    assert "Live Trace" in labels
    assert "Max Hold" in labels
    assert "Mask Threshold" in labels
    assert "Peak Marker" in labels
