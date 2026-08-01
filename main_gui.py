import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QSystemTrayIcon, QMenu, QFileDialog, QLineEdit, QComboBox, QCheckBox, QDialog, QSlider)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
from mqtt_worker import MqttWorker
from background_service import BackgroundAlertService
from pota_integration import PotaIntegration
import time

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    WEB_ENGINE_AVAILABLE = False

class AdvancedFilterDialog(QDialog):
    def __init__(self, parent=None, current_includes="", current_excludes=""):
        super().__init__(parent)
        self.setWindowTitle("Advanced Country Filters")
        self.resize(350, 150)
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Only Include Countries (comma separated):"))
        self.include_input = QLineEdit(current_includes)
        self.include_input.setPlaceholderText("e.g. Bulgaria, Spain, France")
        layout.addWidget(self.include_input)
        
        layout.addWidget(QLabel("Exclude Countries (comma separated):"))
        self.exclude_input = QLineEdit(current_excludes)
        self.exclude_input.setPlaceholderText("e.g. United States, Canada")
        layout.addWidget(self.exclude_input)
        
        save_btn = QPushButton("Save Filters")
        save_btn.clicked.connect(self.accept)
        layout.addWidget(save_btn)
        
    def get_filters(self):
        return self.include_input.text(), self.exclude_input.text()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FT8 Local DX Spotter (LIVE)")
        self.resize(1100, 600)
        self.alert_service = BackgroundAlertService()
        self.worker = None
        self.last_alert_times = {} # Track when we last alerted for a DX
        self.current_spots = [] # Store live spots for popup lookups
        self.advanced_includes = ""
        self.advanced_excludes = ""
        self.setup_ui()
        self.apply_theme()
        self.setup_system_tray()
        
    def setup_system_tray(self):
        # We need an icon for the tray. We'll use a default fallback if not found.
        self.tray_icon = QSystemTrayIcon(self)
        
        # Avoid relying on style() enum that may cause a crash
        # For prototype, we can use an empty QIcon or attempt to grab a generic one safely
        self.tray_icon.setIcon(QIcon())
        
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
    def closeEvent(self, event):
        # Minimize to tray instead of exiting
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "FT8 Spotter",
            "Application minimized to system tray. Still monitoring in background.",
            QSystemTrayIcon.Information,
            2000
        )

        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header_label = QLabel("YWD STATION HUB (FT8 DX SPOTTER)")
        header_label.setObjectName("header")
        main_layout.addWidget(header_label)
        
        # Settings Layout (Radius)
        settings_layout = QHBoxLayout()
        
        from PySide6.QtWidgets import QComboBox, QLineEdit, QCheckBox
        
        # My Callsign
        callsign_label = QLabel("My Callsign:")
        settings_layout.addWidget(callsign_label)
        self.callsign_input = QLineEdit("KE0CGB")
        self.callsign_input.setMaximumWidth(60)
        settings_layout.addWidget(self.callsign_input)
        
        grid_label = QLabel("Grid:")
        settings_layout.addWidget(grid_label)
        self.grid_input = QLineEdit("EM27XO")
        self.grid_input.setMaximumWidth(60)
        settings_layout.addWidget(self.grid_input)
        
        # Exclude Checkbox
        self.exclude_cb = QCheckBox("Exclude My Callsign")
        self.exclude_cb.setChecked(True)
        settings_layout.addWidget(self.exclude_cb)
        
        self.radius_label = QLabel("   Nearby Radius: 100 miles")
        settings_layout.addWidget(self.radius_label)
        
        self.radius_slider = QSlider(Qt.Horizontal)
        self.radius_slider.setMinimum(25)
        self.radius_slider.setMaximum(500)
        self.radius_slider.setSingleStep(5)
        self.radius_slider.setTickInterval(25)
        self.radius_slider.setValue(100)
        self.radius_slider.setMaximumWidth(150)
        settings_layout.addWidget(self.radius_slider)
        
        cooldown_label = QLabel("   Alert Cooldown:")
        settings_layout.addWidget(cooldown_label)
        self.cooldown_combo = QComboBox()
        # 15s up to 5m in 30s increments
        self.cooldown_options = {
            "15 sec": 15, "45 sec": 45, "1m 15s": 75, "1m 45s": 105, 
            "2m 15s": 135, "2m 45s": 165, "3m 15s": 195, "3m 45s": 225, 
            "4m 15s": 255, "4m 45s": 285, "5m 00s": 300
        }
        self.cooldown_combo.addItems(list(self.cooldown_options.keys()))
        self.cooldown_combo.setCurrentText("5m 00s")
        settings_layout.addWidget(self.cooldown_combo)
        
        self.pota_engine = PotaIntegration()
        self.pota_engine.start()
        
        self.voice_combo = QComboBox()
        self.voice_combo.addItems([
            "Voice Alerts: Off",
            "Voice Alerts: Smart Priority",
            "Voice Alerts: Any Live POTA",
            "Voice Alerts: Any New Country",
            "Voice Alerts: Any New US State",
            "Voice Alerts: All Live DX"
        ])
        self.voice_combo.setCurrentText("Voice Alerts: Smart Priority")
        self.voice_combo.currentTextChanged.connect(self.on_voice_toggled)
        settings_layout.addWidget(self.voice_combo)
        
        self.max_alerts_combo = QComboBox()
        self.max_alerts_combo.addItems([
            "Max Alerts: 1",
            "Max Alerts: 3",
            "Max Alerts: 5",
            "Max Alerts: 10",
            "Max Alerts: Unlimited"
        ])
        self.max_alerts_combo.setCurrentText("Max Alerts: 5")
        settings_layout.addWidget(self.max_alerts_combo)
        
        self.last_batch_alert_time = 0
        
        # Connect inputs to update worker filters dynamically
        self.radius_slider.valueChanged.connect(self.on_radius_changed)
        self.exclude_cb.toggled.connect(self.update_filters)
        self.callsign_input.textChanged.connect(self.update_filters)
        self.grid_input.textChanged.connect(self.update_filters)
        
        self.import_btn = QPushButton("Import ADIF")
        self.import_btn.clicked.connect(self.import_adif)
        settings_layout.addWidget(self.import_btn)
        
        self.adv_filter_btn = QPushButton("Advanced Filters")
        self.adv_filter_btn.clicked.connect(self.open_advanced_filters)
        settings_layout.addWidget(self.adv_filter_btn)
        
        settings_layout.addStretch()
        main_layout.addLayout(settings_layout)
        
        # Summary Area
        self.summary_label = QLabel("100 miles: Good opening to Europe on 20m")
        self.summary_label.setObjectName("summary")
        main_layout.addWidget(self.summary_label)
        
        # Table
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Time", "Band", "DX Callsign", "Likelihood", "Confidence", "Need", "Priority", "Reported By"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellClicked.connect(self.on_cell_clicked)
        
        # We wrap the table and map in a splitter or just VBox. For now, VBox.
        main_layout.addWidget(self.table)
        
        # Map Area
        if WEB_ENGINE_AVAILABLE:
            self.map_view = QWebEngineView()
            self.map_view.setMinimumHeight(200)
            main_layout.addWidget(self.map_view)
            self.initialize_map()
        else:
            self.map_label = QLabel("Map requires PySide6-WebEngineWidgets installed.")
            self.map_label.setStyleSheet("color: red; padding: 20px;")
            main_layout.addWidget(self.map_label)
            
        # Status footer
        self.status_label = QLabel("Ready.")
        self.status_label.setObjectName("status")
        main_layout.addWidget(self.status_label)
        
        # We start the map centered roughly in the US with dark mode.
        # We also create a LayerGroup for markers so we can easily clear them.
        self.map_html = """
        <!DOCTYPE html><html><head>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style> body { margin:0; padding:0; background-color:#151c24; } #map { width:100%; height:100vh; } </style>
        </head><body><div id="map"></div><script>
            var map = L.map('map').setView([37.6, -94.0], 3);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 }).addTo(map);
            var markerGroup = L.layerGroup().addTo(map);
            
            // Expose a global function to update markers
            window.updateMarkers = function(js_code) {
                markerGroup.clearLayers();
                eval(js_code); // Execute the Python-generated marker script inside the group
            };
        </script></body></html>
        """
        
        if WEB_ENGINE_AVAILABLE:
            self.map_view.setHtml(self.map_html)
            self.map_view.page().renderProcessTerminated.connect(self.on_render_process_terminated)
        
        # Start MQTT Stream
        self.start_stream()

    def on_voice_toggled(self, text):
        if text == "Voice Alerts: Off":
            self.alert_service.clear()
            self.status_label.setText("Voice alerts muted and queue cleared.")
        else:
            self.last_alert_times.clear()
            self.last_batch_alert_time = 0
            self.status_label.setText(f"Alert mode changed to {text.replace('Voice Alerts: ', '')}.")

    def on_radius_changed(self, value):
        # Snap to 5-mile increments
        snapped_value = round(value / 5) * 5
        if self.radius_slider.value() != snapped_value:
            self.radius_slider.setValue(snapped_value)
            return
            
        self.radius_label.setText(f"   Nearby Radius: {snapped_value} miles")
        self.update_filters()

    def update_filters(self):
        if self.worker:
            self.worker.exclude_callsign = self.callsign_input.text().upper() if self.exclude_cb.isChecked() else ""
            self.worker.radius = self.radius_slider.value()
            self.worker.my_callsign = self.callsign_input.text().upper()
            
            # Update Country Filters
            self.worker.include_countries = [c.strip().lower() for c in self.advanced_includes.split(",") if c.strip()]
            self.worker.exclude_countries = [c.strip().lower() for c in self.advanced_excludes.split(",") if c.strip()]
            
            new_grid = self.grid_input.text().upper()
            if len(new_grid) >= 4 and new_grid != self.worker.my_grid:
                self.worker.my_grid = new_grid
                from phase1_poc import grid_to_latlon
                loc = grid_to_latlon(new_grid)
                if loc:
                    self.worker.my_loc = loc

    def start_stream(self):
        if self.worker and self.worker.isRunning():
            return
            
        exclude = self.callsign_input.text().upper() if self.exclude_cb.isChecked() else ""
        radius = self.radius_slider.value()
        my_call = self.callsign_input.text().upper() or "KE0CGB"
        my_grid = self.grid_input.text().upper() or "EM27XO"
        
        self.status_label.setText("Starting MQTT Live Stream...")
        self.worker = MqttWorker(my_call, my_grid, exclude, radius, min_dx=1000, pota_engine=self.pota_engine)
        self.worker.data_ready.connect(self.on_data_ready)
        self.worker.status_update.connect(self.status_label.setText)
        self.worker.start()

    def import_adif(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open ADIF Log", "", "ADIF Files (*.adi *.adif);;All Files (*)")
        if file_name:
            self.status_label.setText(f"Importing {file_name}...")
            # We run this synchronously for now, it's fast enough or we could put it in a thread.
            from database import Database
            from adif_parser import AdifParser
            
            # If the worker is running, use its db connection to avoid locks, otherwise make a new one
            db = self.worker.db if self.worker else Database()
            parser = AdifParser(db)
            
            try:
                new_qsos = parser.import_incremental(file_name)
                QMessageBox.information(self, "Import Complete", f"Successfully imported {new_qsos} new QSOs!")
                self.status_label.setText("Import Complete.")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import ADIF:\n{e}")
                self.status_label.setText("Import Failed.")

    def open_advanced_filters(self):
        dialog = AdvancedFilterDialog(self, self.advanced_includes, self.advanced_excludes)
        if dialog.exec():
            self.advanced_includes, self.advanced_excludes = dialog.get_filters()
            self.update_filters()
            self.status_label.setText(f"Advanced Country Filters updated.")

    def on_render_process_terminated(self, termination_status, exit_code):
        print(f"WebEngine render process crashed ({termination_status}). Reloading map...")
        self.map_view.setHtml(self.map_html)

    def initialize_map(self):
        pass
        
    def on_data_ready(self, scored_dx, map_data):
        self.current_spots = map_data['spots']
        self.table.setRowCount(len(scored_dx))
        current_time = time.strftime("%H:%M:%S")
        
        cooldown_secs = self.cooldown_options[self.cooldown_combo.currentText()]
        now = time.time()
        
        # Rebuild table
        self.table.setRowCount(0)
        
        # Sort by priority descending so best stations are evaluated/spoken first
        scored_dx.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        # Limit rows to 100 for performance
        display_spots = scored_dx[:100]
        
        max_alerts_text = self.max_alerts_combo.currentText()
        if "Unlimited" in max_alerts_text:
            max_alerts = float('inf')
        else:
            max_alerts = int(max_alerts_text.split(": ")[1])
            
        alerts_sent_this_cycle = 0
        can_alert_batch = (now - self.last_batch_alert_time >= cooldown_secs)
        
        for idx, dx in enumerate(display_spots):
            self.table.insertRow(idx)
            
            # Formatting values from new engines
            # dx['spots'] is available if needed
            latest_spot_time = time.strftime('%H:%M:%S', time.localtime()) # mock time
            
            self.table.setItem(idx, 0, QTableWidgetItem(latest_spot_time))
            self.table.setItem(idx, 1, QTableWidgetItem(dx['band']))
            self.table.setItem(idx, 2, QTableWidgetItem(dx['tx_call']))
            self.table.setItem(idx, 3, QTableWidgetItem(str(dx.get('likelihood', 'N/A'))))
            self.table.setItem(idx, 4, QTableWidgetItem(str(dx.get('confidence', 'Low'))))
            
            need_str = f"{dx.get('need_val', 0)} ({dx.get('need_exp', '')})"
            self.table.setItem(idx, 5, QTableWidgetItem(need_str))
            
            self.table.setItem(idx, 6, QTableWidgetItem(str(dx.get('priority', 0))))
            
            rx_count = str(dx.get('rx_count', len(dx.get('receivers', []))))
            self.table.setItem(idx, 7, QTableWidgetItem(f"{rx_count} rx"))
                
            # Cooldown check for voice alert
            voice_mode = self.voice_combo.currentText()
            should_alert = False
            
            if voice_mode == "Voice Alerts: Smart Priority" and dx.get('priority', 0) >= 10:
                should_alert = True
                msg = f"Live DX Alert! {dx.get('rx_count', 0)} nearby stations are hearing {dx.get('tx_call', '')} on {dx.get('band', '')}. Priority is {dx.get('priority', 0)}."
            elif voice_mode == "Voice Alerts: Any Live POTA" and dx.get('is_pota', False):
                should_alert = True
                msg = f"POTA Alert! Active park activator {dx.get('tx_call', '')} spotted on {dx.get('band', '')}."
            elif voice_mode == "Voice Alerts: Any New Country" and dx.get('is_new_country', False):
                should_alert = True
                msg = f"New Country Alert! {dx.get('country', 'Unknown')} spotted: {dx.get('tx_call', '')} on {dx.get('band', '')}."
            elif voice_mode == "Voice Alerts: Any New US State" and dx.get('is_new_state', False):
                should_alert = True
                msg = f"New State Alert! {dx.get('state', 'Unknown')} spotted: {dx.get('tx_call', '')} on {dx.get('band', '')}."
            elif voice_mode == "Voice Alerts: All Live DX":
                should_alert = True
                msg = f"Live DX: {dx.get('tx_call', '')} on {dx.get('band', '')}."
                
            if should_alert and can_alert_batch:
                dx_key = f"{dx['tx_call']}_{dx['band']}"
                last_alert = self.last_alert_times.get(dx_key, 0)
                if now - last_alert >= cooldown_secs:
                    if alerts_sent_this_cycle < max_alerts:
                        self.last_alert_times[dx_key] = now
                        self.alert_service.announce(msg)
                        alerts_sent_this_cycle += 1
                        self.last_batch_alert_time = now
        
        # Update map without flashing
        if WEB_ENGINE_AVAILABLE:
            markers_js = ""
            for s in map_data['spots']:
                markers_js += f"L.circleMarker([{s['rx_loc'][0]}, {s['rx_loc'][1]}], {{color: 'red', radius: 4}}).bindPopup('RX: {s['rx_call']}').addTo(markerGroup);\n"
                markers_js += f"L.circleMarker([{s['tx_loc'][0]}, {s['tx_loc'][1]}], {{color: 'green', radius: 4}}).bindPopup('TX: {s['tx_call']}').addTo(markerGroup);\n"
                markers_js += f"L.polyline([[{s['rx_loc'][0]}, {s['rx_loc'][1]}], [{s['tx_loc'][0]}, {s['tx_loc'][1]}]], {{color: 'gray', weight: 1, dashArray: '5, 5'}}).addTo(markerGroup);\n"
            
            # Pass the javascript commands to our global window function
            script = f"window.updateMarkers(`{markers_js}`);"
            self.map_view.page().runJavaScript(script)

    def on_cell_clicked(self, row, col):
        # Trigger on "DX Callsign" (col 2)
        if col == 2:
            cell_text = self.table.item(row, col).text()
            callsigns = [c.strip() for c in cell_text.split(',') if c.strip()]
            
            info_html = ""
            for call in callsigns:
                # Find this callsign in our live spots buffer
                grid = "Unknown"
                dist = "Unknown mi"
                country = "Unknown" # In a full app, map callsign prefix to DXCC
                
                for s in self.current_spots:
                    if s['tx_call'] == call:
                        grid = s['tx_grid']
                        dist = f"{s['dist_to_tx']:,.0f} mi"
                        break
                        
                info_html += f"<b>Callsign:</b> {call}<br>"
                info_html += f"<b>Locator:</b> {grid}<br>"
                info_html += f"<b>Country:</b> {country}<br>"
                info_html += f"<b>Distance:</b> {dist}<hr>"
            
            msg = QMessageBox(self)
            msg.setWindowTitle("Station Info")
            msg.setStyleSheet(self.styleSheet()) # apply dark theme
            msg.setText(info_html)
            msg.exec()

    def apply_theme(self):
        # Dark theme based on the user's provided screenshot
        style = """
        QMainWindow {
            background-color: #0f151b;
        }
        QWidget {
            background-color: #0f151b;
            color: #a4b4c4;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10pt;
        }
        QLabel#header {
            font-size: 16pt;
            font-weight: bold;
            color: #ffffff;
            padding: 10px 0;
        }
        QLabel#summary {
            color: #00d284;
            font-weight: bold;
        }
        QTableWidget {
            background-color: #151c24;
            color: #ffffff;
            gridline-color: #2b3a4a;
            border: 1px solid #2b3a4a;
        }
        QHeaderView::section {
            background-color: #1a232d;
            color: #8a9ba8;
            padding: 4px;
            border: 1px solid #2b3a4a;
            font-weight: bold;
        }
        QLabel#status {
            color: #8a9ba8;
            padding: 5px 0;
        }
        QLineEdit, QComboBox {
            background-color: #1a232d;
            border: 1px solid #2b3a4a;
            color: #ffffff;
            padding: 3px;
        }
        QCheckBox {
            color: #a4b4c4;
            spacing: 5px;
        }
        QCheckBox::indicator {
            width: 13px;
            height: 13px;
        }
        QPushButton {
            background-color: #1a232d;
            border: 1px solid #2b3a4a;
            color: #ffffff;
            padding: 4px 10px;
        }
        QPushButton:hover {
            background-color: #2b3a4a;
        }
        """
        self.setStyleSheet(style)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
