import os
import time
import sys

rsa_dll_path = r"C:\Tektronix\RSA_API\lib\x64"
os.add_dll_directory(rsa_dll_path)
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.animation import FuncAnimation
from rsa_api import * 

"""

# --- Initialize Device ---
DEVICE_Connect_py()
print(DEVICE_GetSerialNumber_py())
print(DEVICE_GetInfo_py())
print(DEVICE_Search_py())

# DEVICE_Reset_py(0)


DEVICE_Run_py()

# --- Configure Spectrum ---
SPECTRUM_SetEnable_py(True)
SPECTRUM_SetDefault_py()
detector = SpectrumDetectors.SpectrumDetector_AverageVRMS
SPECTRUM_SetTraceType_py(0, TraceType.TraceTypeAverage,detector)     
# SPECTRUM_SetDetectorType_py(DetectorType.RMS)
# SPECTRUM_SetWindow_py(Window.Kaiser)
SPECTRUM_SetSettings_py(span=20e6, rbw=300e3, enableVBW=False, vbw=100e3,
                            traceLength=801, window=SpectrumWindows.SpectrumWindow_Kaiser,
                            verticalUnit=SpectrumVerticalUnits.SpectrumVerticalUnit_dBm)
# SPECTRUM_SetSpan_py(20e6)
SPECTRUM_SetCenterFreq_py(2.437e9)  # Wi-Fi channel 6 center freq
# SPECTRUM_SetRBW_py(300e3)
# SPECTRUM_SetVBW_py(100e3)

# --- Prepare Trace ---
SPECTRUM_SetTraceCount_py(1)
SPECTRUM_SetTraceEnabled_py(0, True)
SPECTRUM_SetTraceType_py(0, TraceType.TraceTypeAverage)

# Get spectrum settings
settings = SPECTRUM_GetSettings_py()
trace_length = settings['traceLength']
freqs = np.linspace(settings['actualStartFreq'], settings['actualStopFreq'], trace_length)

# --- Capture & Plot ---
SPECTRUM_AcquireTrace_py()
SPECTRUM_WaitForDataReady_py(1000)

data = SPECTRUM_GetTrace_py(0)
SPECTRUM_SetEnable_py(False)
DEVICE_Stop_py()

# --- Plot ---
plt.figure(figsize=(10, 5))
plt.plot(freqs / 1e6, data)
plt.title('2.4 GHz Wi-Fi Spectrum - RSA306B')
plt.xlabel('Frequency (MHz)')
plt.ylabel('Power (dBm)')
plt.grid(True)
plt.tight_layout()
plt.show()




# --- Initialize Device ---
DEVICE_Connect_py()
print("Serial Number:", DEVICE_GetSerialNumber_py())
print("Device Info:", DEVICE_GetInfo_py())
print("Search Results:", DEVICE_Search_py())

# Optional hardware reset — requires modifying your wrapper to drop the deviceID param
# DEVICE_Reset_py()  

DEVICE_Run_py()

# --- Spectrum Configuration ---
SPECTRUM_SetEnable_py(True)
SPECTRUM_SetDefault_py()

# Trace config: Trace 1, Enabled, RMS detector
SPECTRUM_SetTraceType_py(
    trace=SpectrumTraces.SpectrumTrace1,
    enable=True,
    detector=SpectrumDetectors.SpectrumDetector_AverageVRMS
)

# Spectrum sweep settings for 2.4GHz Wi-Fi band (channel 6)
SPECTRUM_SetSettings_py(
    span=20e6,
    rbw=300e3,
    enableVBW=True,
    vbw=100e3,
    traceLength=801,
    window=SpectrumWindows.SpectrumWindow_Kaiser,
    verticalUnit=SpectrumVerticalUnits.SpectrumVerticalUnit_dBm
)

CONFIG_SetCenterFreq_py(2.437e9)  # Center frequency in Hz

# --- Acquire and Plot Trace ---
SPECTRUM_AcquireTrace_py()
SPECTRUM_WaitForTraceReady_py(timeoutMsec=1000)

settings = SPECTRUM_GetSettings_py()
trace_length = settings['traceLength']
freqs = np.linspace(settings['actualStartFreq'], settings['actualStopFreq'], trace_length)

trace = SPECTRUM_GetTrace_py(trace=SpectrumTraces.SpectrumTrace1, tracePoints=trace_length)

# --- Cleanup ---
SPECTRUM_SetEnable_py(False)
DEVICE_Stop_py()

# --- Plot ---
plt.figure(figsize=(10, 5))
plt.plot(freqs / 1e6, trace)
plt.title('2.4 GHz Wi-Fi Spectrum - RSA306B')
plt.xlabel('Frequency (MHz)')
plt.ylabel('Power (dBm)')
plt.grid(True)
plt.tight_layout()
plt.show()

"""
# --- Spectrum Sweep Configuration ---
SPAN = 40e6                   # Max span per sweep (RSA306B limit)
STEP = 30e6                   # Overlapping step to avoid gaps
START_FREQ = 2.4e9            # Start of sweep (2.4 GHz)
STOP_FREQ = 5.6e9             # End of sweep (5.6 GHz)
TRACE_LEN = 801               # Trace resolution
MAX_HOLD_SEC = 30             # Duration of max hold
SWEEP_INTERVAL_MS = 50       # Delay between updates

# --- Generate Band Sweep Plan ---
bands = [{"cf": f, "label": f"{f/1e9:.3f} GHz"} for f in np.arange(START_FREQ, STOP_FREQ, STEP)]

num_bands = len(bands)

# --- RSA306B Setup ---
DEVICE_Connect_py()
DEVICE_Run_py()
SPECTRUM_SetEnable_py(True)
SPECTRUM_SetDefault_py()

SPECTRUM_SetTraceType_py(
    trace=SpectrumTraces.SpectrumTrace1,
    enable=True,
    detector=SpectrumDetectors.SpectrumDetector_AverageVRMS
)

# --- Compute Full Composite Frequency Range ---
full_freq_start = START_FREQ - SPAN / 2
full_freq_stop = STOP_FREQ + SPAN / 2
full_freqs = np.linspace(full_freq_start, full_freq_stop, TRACE_LEN * num_bands)

# --- Allocate Buffers ---
live_combined = np.full_like(full_freqs, -150.0, dtype=np.float32)
max_combined = np.full_like(full_freqs, -150.0, dtype=np.float32)

# --- Plot Setup ---
fig, ax = plt.subplots(figsize=(14, 6))
line_live, = ax.plot(full_freqs / 1e6, live_combined, label="Live Trace")
line_max, = ax.plot(full_freqs / 1e6, max_combined, label="Max Hold", linestyle='--', color='orange')

ax.set_ylim(-130, 0)
ax.set_xlim(full_freqs[0] / 1e6, full_freqs[-1] / 1e6)
ax.set_xlabel("Frequency (MHz)")
ax.set_ylabel("Power (dBm)")
ax.set_title("2.4–5.6 GHz Wi-Fi Sweep with Max Hold (RSA306B)")
ax.grid(True)
ax.legend()

# --- State ---
start_time = time.time()
band_index = 0

# --- Update Loop ---
def update(frame):
    global band_index, start_time

    # Select band
    band = bands[band_index]
    CONFIG_SetCenterFreq_py(band["cf"])

    # Apply sweep settings
    SPECTRUM_SetSettings_py(
        span=SPAN,
        rbw=300e3,
        enableVBW=True,
        vbw=100e3,
        traceLength=TRACE_LEN,
        window=SpectrumWindows.SpectrumWindow_Kaiser,
        verticalUnit=SpectrumVerticalUnits.SpectrumVerticalUnit_dBm
    )

    # Acquire trace
    SPECTRUM_AcquireTrace_py()
    SPECTRUM_WaitForTraceReady_py(100)
    trace = SPECTRUM_GetTrace_py(trace=SpectrumTraces.SpectrumTrace1, tracePoints=TRACE_LEN)

    # Get actual frequencies
    settings = SPECTRUM_GetSettings_py()
    freqs = np.linspace(settings['actualStartFreq'], settings['actualStopFreq'], TRACE_LEN)

    # Merge into full buffers
    for i, f in enumerate(freqs):
        idx = np.argmin(np.abs(full_freqs - f))
        live_combined[idx] = trace[i]
        if time.time() - start_time <= MAX_HOLD_SEC:
            max_combined[idx] = max(max_combined[idx], trace[i])

    # Update plot
    line_live.set_ydata(live_combined)
    line_max.set_ydata(max_combined)

    # Rotate to next band
    band_index = (band_index + 1) % num_bands
    return line_live, line_max

# --- Animate Plot ---
ani = FuncAnimation(fig, update, interval=SWEEP_INTERVAL_MS)
plt.tight_layout()
plt.show()

# --- Cleanup ---
SPECTRUM_SetEnable_py(False)
DEVICE_Stop_py()