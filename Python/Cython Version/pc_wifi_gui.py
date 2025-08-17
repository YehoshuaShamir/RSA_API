import sys
import subprocess
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QTabWidget
)
from PyQt5.QtCore import QTimer
from bleak import BleakScanner
import asyncio
from PyQt5.QtCore import QTimer, QThread, pyqtSignal

class PCWiFiSpectrumGUI(QWidget):
    """
    A GUI application for visualizing the WiFi spectrum using the PC's WiFi adapter.
    Scans for WiFi networks and displays their signal strength across channels.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PC WiFi Spectrum Analyzer')
        self.setGeometry(100, 100, 800, 400)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # --- Tabs for WiFi and Bluetooth ---
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # WiFi Tab
        self.wifi_tab = QWidget()
        from PyQt5.QtWidgets import QHBoxLayout, QComboBox
        # Change WiFi tab layout to horizontal
        self.wifi_tab_layout = QHBoxLayout()
        self.wifi_tab.setLayout(self.wifi_tab_layout)
        # Left: Table, Right: Plot and controls
        self.left_panel = QVBoxLayout()
        self.right_panel = QVBoxLayout()
        self.info_label = QLabel('Scanning for WiFi networks...')
        self.left_panel.addWidget(self.info_label)
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels([
            'Channel', 'WiFi Name', 'Signal Level', 'BSSID', 'Authentication', 'Encryption'])
        self.left_panel.addWidget(self.table_widget)
        self.wifi_tab_layout.addLayout(self.left_panel)
        # Controls for mode selection
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(['dBm', 'Percent'])
        self.mode_combo.currentIndexChanged.connect(self.update_spectrum)
        self.right_panel.addWidget(self.mode_combo)
        self.canvas = FigureCanvas(plt.Figure(figsize=(8, 6)))
        self.ax_24, self.ax_5 = self.canvas.figure.subplots(2, 1, sharex=False)
        self.canvas.figure.tight_layout(pad=3)
        self.right_panel.addWidget(self.canvas)
        self.refresh_button = QPushButton('Refresh Scan')
        self.refresh_button.clicked.connect(self.update_spectrum)
        self.right_panel.addWidget(self.refresh_button)
        self.wifi_tab_layout.addLayout(self.right_panel)
        self.tabs.addTab(self.wifi_tab, "WiFi")

        self.display_mode = 'dBm'
        self.mode_combo.setCurrentIndex(0)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_change)

        self.timer = QTimer(self)
        self.timer.setInterval(5000)  # Refresh every 5 seconds
        self.timer.timeout.connect(self.update_spectrum)
        self.timer.start()

        self.update_spectrum()

        # Bluetooth Tab
        self.bt_tab = QWidget()
        self.bt_tab_layout = QVBoxLayout()
        self.bt_tab.setLayout(self.bt_tab_layout)
        self.bt_table = QTableWidget()
        self.bt_table.setColumnCount(3)
        self.bt_table.setHorizontalHeaderLabels(['Bluetooth Name', 'MAC Address', 'Signal Strength (RSSI)'])
        self.bt_tab_layout.addWidget(self.bt_table)
        self.bt_refresh_button = QPushButton('Refresh Bluetooth Scan')
        self.bt_refresh_button.clicked.connect(self.update_bluetooth)
        self.bt_tab_layout.addWidget(self.bt_refresh_button)
        self.tabs.addTab(self.bt_tab, "Bluetooth")

        self.update_bluetooth()

    def _on_mode_change(self):
        self.display_mode = self.mode_combo.currentText()
        self.update_spectrum()

    def update_spectrum(self):
        # Prevent overlapping scans
        self.refresh_button.setEnabled(False)
        self.timer.stop()
        try:
            scan_output = self.scan_wifi_networks()
            if scan_output.startswith('ERROR'):
                self.info_label.setText(scan_output)
                self.table_widget.setRowCount(0)
                self.ax_24.clear()
                self.ax_5.clear()
                self.canvas.draw()
                return
            networks = self.parse_wifi_scan(scan_output)
            self.update_table(networks)
            self.info_label.setText(f'Found {len(networks)} WiFi networks.')
            # Separate into 2.4 GHz and 5 GHz
            networks_24 = [n for n in networks if 1 <= n['channel'] <= 14]
            networks_5 = [n for n in networks if n['channel'] >= 36]
            # 2.4 GHz plot
            self.ax_24.clear()
            if networks_24:
                channels_24 = [net['channel'] for net in networks_24]
                if self.display_mode == 'Percent':
                    signals_24 = [int(round((net['signal'] + 100) * 2)) for net in networks_24]  # dBm to %
                else:
                    signals_24 = [net['signal'] for net in networks_24]
                labels_24 = [net['ssid'] for net in networks_24]
                self.ax_24.bar(channels_24, signals_24, tick_label=channels_24, color='lightgreen')
                for i, txt in enumerate(labels_24):
                    yval = signals_24[i] + 2 if self.display_mode == 'Percent' else signals_24[i] + 1
                    self.ax_24.text(channels_24[i], yval, txt, ha='center', fontsize=8, rotation=45)
            self.ax_24.set_xlabel('WiFi Channel (2.4 GHz)')
            self.ax_24.set_ylabel(f"Signal Strength ({'%' if self.display_mode == 'Percent' else 'dBm'})")
            self.ax_24.set_title('2.4 GHz WiFi Spectrum')
            if self.display_mode == 'Percent':
                self.ax_24.set_ylim(0, 100)
            else:
                self.ax_24.set_ylim(-100, 0)
            # 5 GHz plot
            self.ax_5.clear()
            if networks_5:
                channels_5 = [net['channel'] for net in networks_5]
                if self.display_mode == 'Percent':
                    signals_5 = [int(round((net['signal'] + 100) * 2)) for net in networks_5]
                else:
                    signals_5 = [net['signal'] for net in networks_5]
                labels_5 = [net['ssid'] for net in networks_5]
                self.ax_5.bar(channels_5, signals_5, tick_label=channels_5, color='skyblue')
                for i, txt in enumerate(labels_5):
                    yval = signals_5[i] + 2 if self.display_mode == 'Percent' else signals_5[i] + 1
                    self.ax_5.text(channels_5[i], yval, txt, ha='center', fontsize=8, rotation=45)
            self.ax_5.set_xlabel('WiFi Channel (5 GHz)')
            self.ax_5.set_ylabel(f"Signal Strength ({'%' if self.display_mode == 'Percent' else 'dBm'})")
            self.ax_5.set_title('5 GHz WiFi Spectrum')
            if self.display_mode == 'Percent':
                self.ax_5.set_ylim(0, 100)
            else:
                self.ax_5.set_ylim(-100, 0)
            self.canvas.draw()
        except Exception as e:
            self.info_label.setText(f'Exception: {str(e)}')
            self.ax_24.clear()
            self.ax_5.clear()
            self.table_widget.setRowCount(0)
            self.canvas.draw()
        finally:
            self.refresh_button.setEnabled(True)
            self.timer.start()
            
    def parse_wifi_scan(self, scan_output):
        # Extract SSID, Channel, Signal, BSSID, Authentication, Encryption
        networks = []
        ssid = None
        channel = None
        signal = None
        bssid = None
        auth = None
        encryption = None
        for line in scan_output.splitlines():
            ssid_match = re.match(r'\s*SSID \d+ : (.*)', line)
            if ssid_match:
                ssid = ssid_match.group(1).strip()
                continue
            channel_match = re.match(r'\s*Channel *: (\d+)', line)
            if channel_match:
                channel = int(channel_match.group(1))
                continue
            signal_match = re.match(r'\s*Signal *: (\d+)%', line)
            if signal_match:
                signal_percent = int(signal_match.group(1))
                # Convert percent to dBm: dBm = (percent / 2) - 100
                signal = (signal_percent / 2) - 100
                continue
            bssid_match = re.match(r'\s*BSSID \d+ *: ([0-9A-Fa-f:]+)', line)
            if bssid_match:
                bssid = bssid_match.group(1).strip()
                continue
            auth_match = re.match(r'\s*Authentication *: (.+)', line)
            if auth_match:
                auth = auth_match.group(1).strip()
                continue
            encryption_match = re.match(r'\s*Encryption *: (.+)', line)
            if encryption_match:
                encryption = encryption_match.group(1).strip()
                continue
            # When all are found, append
            if (ssid is not None and channel is not None and signal is not None and
                bssid is not None and auth is not None and encryption is not None):
                networks.append({
                    'ssid': ssid,
                    'channel': channel,
                    'signal': signal,
                    'bssid': bssid,
                    'auth': auth,
                    'encryption': encryption
                })
                bssid = None
                auth = None
                encryption = None
        return networks

    def scan_wifi_networks(self):
        """
        Scan for WiFi networks using netsh command.
        """
        try:
            output = subprocess.check_output(
                ['netsh', 'wlan', 'show', 'networks', 'mode=bssid'],
                shell=True, encoding='utf-8', errors='replace', timeout=3
            )
            return output
        except subprocess.TimeoutExpired:
            return 'ERROR: WiFi scan timed out.'
        except Exception as e:
            return f'ERROR: {str(e)}'

    def update_table(self, networks):
        self.table_widget.setRowCount(len(networks))
        for row, net in enumerate(networks):
            ch = net.get('channel', '')
            ssid = net.get('ssid', '')
            sig = net.get('signal', '')
            if self.display_mode == 'Percent' and isinstance(sig, (int, float)):
                sig_disp = int(round((sig + 100) * 2))
            elif isinstance(sig, float):
                sig_disp = f"{sig:.1f}"
            else:
                sig_disp = sig
            bssid = net.get('bssid', '')
            auth = net.get('auth', '')
            encryption = net.get('encryption', '')
            display_ssid = ssid if ssid else 'Hidden Network'
            self.table_widget.setItem(row, 0, QTableWidgetItem(str(ch)))
            self.table_widget.setItem(row, 1, QTableWidgetItem(display_ssid))
            self.table_widget.setItem(row, 2, QTableWidgetItem(str(sig_disp)))
            self.table_widget.setItem(row, 3, QTableWidgetItem(bssid))
            self.table_widget.setItem(row, 4, QTableWidgetItem(auth))
            self.table_widget.setItem(row, 5, QTableWidgetItem(encryption))

    def update_bluetooth(self):
        print('[DEBUG] update_bluetooth called')
        self.bt_refresh_button.setEnabled(False)
        self.bt_table.setRowCount(0)
        self.bt_table.setRowCount(1)
        self.bt_table.setItem(0, 0, QTableWidgetItem('Scanning...'))
        self.bt_table.setItem(0, 1, QTableWidgetItem(''))
        self.bt_table.setItem(0, 2, QTableWidgetItem(''))
        # Start BLE scan in a thread
        self._ble_thread = BLEScanThread()
        self._ble_thread.scan_results.connect(self._on_ble_scan_results)
        self._ble_thread.start()

    def _on_ble_scan_results(self, devices):
        print(f'[DEBUG] _on_ble_scan_results called with: {devices}')
        self.bt_table.setRowCount(0)
        if isinstance(devices, Exception):
            self.bt_table.setRowCount(1)
            self.bt_table.setItem(0, 0, QTableWidgetItem('Scan Error'))
            self.bt_table.setItem(0, 1, QTableWidgetItem(str(devices)))
            self.bt_table.setItem(0, 2, QTableWidgetItem(''))
        elif not devices:
            self.bt_table.setRowCount(1)
            self.bt_table.setItem(0, 0, QTableWidgetItem('No BLE devices found'))
            self.bt_table.setItem(0, 1, QTableWidgetItem(''))
            self.bt_table.setItem(0, 2, QTableWidgetItem(''))
        else:
            self.bt_table.setRowCount(len(devices))
            for row, dev in enumerate(devices):
                name = getattr(dev, 'name', 'Unknown')
                addr = getattr(dev, 'address', 'Unknown')
                rssi = getattr(dev, 'rssi', '')
                self.bt_table.setItem(row, 0, QTableWidgetItem(str(name)))
                self.bt_table.setItem(row, 1, QTableWidgetItem(str(addr)))
                self.bt_table.setItem(row, 2, QTableWidgetItem(str(rssi)))
        self.timer.stop()
        try:
            scan_output = self.scan_wifi_networks()
            if scan_output.startswith('ERROR'):
                self.info_label.setText(scan_output)
                self.table_widget.setRowCount(0)
                self.ax_24.clear()
                self.ax_5.clear()
                self.canvas.draw()
                return
            networks = self.parse_wifi_scan(scan_output)
            self.update_table(networks)
            self.info_label.setText(f'Found {len(networks)} WiFi networks.')
            # Separate into 2.4 GHz and 5 GHz
            networks_24 = [n for n in networks if 1 <= n['channel'] <= 14]
            networks_5 = [n for n in networks if n['channel'] >= 36]
            # 2.4 GHz plot
            self.ax_24.clear()
            if networks_24:
                channels_24 = [net['channel'] for net in networks_24]
                signals_24 = [net['signal'] for net in networks_24]
                labels_24 = [net['ssid'] for net in networks_24]
                self.ax_24.bar(channels_24, signals_24, tick_label=channels_24, color='lightgreen')
                for i, txt in enumerate(labels_24):
                    self.ax_24.text(channels_24[i], signals_24[i]+2, txt, ha='center', fontsize=8, rotation=45)
            self.ax_24.set_xlabel('WiFi Channel (2.4 GHz)')
            self.ax_24.set_ylabel('Signal Strength (%)')
            self.ax_24.set_title('2.4 GHz WiFi Spectrum')
            self.ax_24.set_ylim(0, 100)
            # 5 GHz plot
            self.ax_5.clear()
            if networks_5:
                channels_5 = [net['channel'] for net in networks_5]
                signals_5 = [net['signal'] for net in networks_5]
                labels_5 = [net['ssid'] for net in networks_5]
                self.ax_5.bar(channels_5, signals_5, tick_label=channels_5, color='skyblue')
                for i, txt in enumerate(labels_5):
                    self.ax_5.text(channels_5[i], signals_5[i]+2, txt, ha='center', fontsize=8, rotation=45)
            self.ax_5.set_xlabel('WiFi Channel (5 GHz)')
            self.ax_5.set_ylabel('Signal Strength (%)')
            self.ax_5.set_title('5 GHz WiFi Spectrum')
            self.ax_5.set_ylim(0, 100)
            self.canvas.draw()
        except Exception as e:
            self.info_label.setText(f'Exception: {str(e)}')
            self.ax_24.clear()
            self.ax_5.clear()
            self.table_widget.setRowCount(0)
            self.canvas.draw()
        finally:
            self.refresh_button.setEnabled(True)
            self.timer.start()

class BLEScanThread(QThread):
    scan_results = pyqtSignal(object)

    def run(self):
        try:
            devices = asyncio.run(BleakScanner.discover(timeout=8.0))
            self.scan_results.emit(devices)
        except Exception as e:
            self.scan_results.emit(e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PCWiFiSpectrumGUI()
    window.show()
    sys.exit(app.exec_())
