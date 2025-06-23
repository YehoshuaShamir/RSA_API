import pytest
from PyQt5.QtWidgets import QApplication
import numpy as np
import sys
import os

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_rsa_gui import SpectrumAnalyzerGUI

# Mock RSA API constants
SpectrumWindows = type('SpectrumWindows', (), {
    'SpectrumWindow_Rectangular': 0,
    'SpectrumWindow_Hamming': 1,
    'SpectrumWindow_Hanning': 2,
    'SpectrumWindow_Blackman': 3,
    'SpectrumWindow_Kaiser': 4
})

SpectrumVerticalUnits = type('SpectrumVerticalUnits', (), {
    'SpectrumVerticalUnit_dBm': 0,
    'SpectrumVerticalUnit_dBmV': 1,
    'SpectrumVerticalUnit_dBuV': 2,
    'SpectrumVerticalUnit_V': 3,
    'SpectrumVerticalUnit_W': 4
})

# The RSA API is now mocked in the main module itself
# so we don't need to mock it here anymore

@pytest.fixture
def app():
    """Create and return a QApplication instance."""
    test_app = QApplication([])
    window = SpectrumAnalyzerGUI()
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
    app.start_acquisition()
    app.update_plot()
    assert app.line_live is not None
    assert app.line_max is not None
    assert app.line_mask is not None
    assert app.line_marker is not None
    
    # Check if plot limits are set correctly
    xlim = app.ax.get_xlim()
    assert xlim[0] == pytest.approx(2400)
    assert xlim[1] == pytest.approx(2430)
    assert app.ax.get_ylim() == (-130, -20)

def test_center_frequency_range(app):
    """Test center frequency input range."""
    center_input = app.center_input
    assert center_input.minimum() == 0.01
    assert center_input.maximum() == 6.0
    assert center_input.decimals() == 3
    assert center_input.value() == 2.41

def test_span_range(app):
    """Test span input range."""
    span_input = app.span_input
    assert span_input.minimum() == 1
    assert span_input.maximum() == 40
    assert span_input.value() == 30

def test_trigger_level_range(app):
    """Test trigger level input range."""
    trigger_input = app.trigger_input
    assert trigger_input.minimum() == -130
    assert trigger_input.maximum() == 0
    assert trigger_input.value() == -10

def test_start_button_click(app, qtbot):
    """Test start button click functionality."""
    qtbot.mouseClick(app.start_button, Qt.LeftButton)
    assert app.timer.isActive() is True

def test_stop_button_click(app, qtbot):
    """Test stop button click functionality."""
    app.timer.start(100)  # Start timer first
    qtbot.mouseClick(app.stop_button, Qt.LeftButton)
    assert app.timer.isActive() is False

def test_clear_button_click(app, qtbot):
    """Test clear button click functionality."""
    # Set some arbitrary max hold data
    app.max_hold = np.full(801, -50.0, dtype=np.float32)
    qtbot.mouseClick(app.clear_button, Qt.LeftButton)
    assert np.all(app.max_hold == -150.0)  # Default reset value

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
    # Set up mock data that violates the mask
    app.freqs = np.linspace(2.4e9, 2.43e9, 801)
    mock_trace = np.zeros(801)
    mock_trace[400] = -20  # Peak above mask threshold
    app.update_plot()
    assert app.line_mask is not None
    assert app.ax.get_ylim() == (-130, -20)

# Spectrum Control Tests
def test_reference_level_range(app):
    """Test reference level input range."""
    ref_level_input = app.ref_level_input
    assert ref_level_input.minimum() == -130
    assert ref_level_input.maximum() == 10
    assert ref_level_input.value() == -60

def test_rbw_range(app):
    """Test resolution bandwidth input range."""
    rbw_input = app.rbw_input
    assert rbw_input.minimum() == 1
    assert rbw_input.maximum() == 1000
    assert rbw_input.value() == 1

def test_vbw_range(app):
    """Test video bandwidth input range."""
    vbw_input = app.vbw_input
    assert vbw_input.minimum() == 1
    assert vbw_input.maximum() == 1000
    assert vbw_input.value() == 10

def test_trace_length_range(app):
    """Test trace length input range."""
    trace_length_input = app.trace_length_input
    assert trace_length_input.minimum() == 101
    assert trace_length_input.maximum() == 801
    assert trace_length_input.value() == 801

def test_window_type_options(app):
    """Test window type options."""
    window_combo = app.window_combo
    options = ["Rectangular", "Hamming", "Hanning", "Blackman", "Kaiser"]
    assert window_combo.count() == len(options)
    assert all(option in [window_combo.itemText(i) for i in range(window_combo.count())] for option in options)

def test_vertical_units_options(app):
    """Test vertical units options."""
    units_combo = app.units_combo
    options = ["dBm", "dBmV", "dBuV", "V", "W"]
    assert units_combo.count() == len(options)
    assert all(option in [units_combo.itemText(i) for i in range(units_combo.count())] for option in options)

def test_update_reference_level(app, qtbot):
    """Test updating reference level."""
    with qtbot.waitSignal(app.ref_level_input.valueChanged):
        app.ref_level_input.setValue(-50)
    assert app.ref_level_input.value() == -50
    assert app.ax.get_ylim() == (-160, -50)

def test_update_rbw(app, qtbot):
    """Test updating resolution bandwidth."""
    with qtbot.waitSignal(app.rbw_input.valueChanged):
        app.rbw_input.setValue(10)
    assert app.rbw_input.value() == 10

def test_update_vbw(app, qtbot):
    """Test updating video bandwidth."""
    with qtbot.waitSignal(app.vbw_input.valueChanged):
        app.vbw_input.setValue(20)
    assert app.vbw_input.value() == 20

def test_update_trace_length(app, qtbot):
    """Test updating trace length."""
    with qtbot.waitSignal(app.trace_length_input.valueChanged):
        app.trace_length_input.setValue(401)
    assert app.trace_length_input.value() == 401
    assert len(app.freqs) == 401

def test_update_window_type(app, qtbot):
    """Test updating window type."""
    with qtbot.waitSignal(app.window_combo.currentTextChanged):
        app.window_combo.setCurrentText("Hamming")
    assert app.window_combo.currentText() == "Hamming"

def test_update_vertical_units(app, qtbot):
    """Test updating vertical units."""
    with qtbot.waitSignal(app.units_combo.currentTextChanged):
        app.units_combo.setCurrentText("dBmV")
    assert app.units_combo.currentText() == "dBmV"
    assert app.ax.get_ylabel() == "Power (dBmV)"  
    # Check title for mask violation
    assert "MASK VIOLATION" in app.ax.get_title()
