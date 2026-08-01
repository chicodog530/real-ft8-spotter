# Real FT8 Spotter

Real FT8 Spotter is an intelligent, live DX spotting application that goes beyond simple reporting. It connects directly to the global PSKReporter MQTT firehose and cross-references live propagation data against your actual WSJT-X logbook to calculate personalized physical likelihoods and logbook "Need" values. It will tell you not just who is on the air, but whether you can actually hear them, and whether you need them for a new DXCC, Grid, or Band!

## Features

- **Live Global MQTT Firehose**: Connects seamlessly to `mqtt.pskreporter.info` to instantly stream FT8 spots heard by receivers around the world.
- **Dynamic Propagation Mapping**: Visualizes live propagation paths on an interactive local map.
- **Personalized Likelihood Engine**: Computes the real physical probability of your antenna decoding a station based on nearby receiver consensus, SNR, distance, and bearing.
- **Logbook "Need" Engine**: Import your `wsjtx_log.adi` file! The engine instantly cross-references all incoming spots to identify all-time new DXCC entities, new bands, and new grid squares (VUCC).
- **Opportunity Priority**: Fuses propagation probability and logbook needs into a single unified "Priority" score (0-100), ensuring you only focus on the targets that matter most and are actually reachable.
- **Intelligent Voice Alerts**: Hands-free operation. Automatically announces high-priority DX targets using local text-to-speech.

## Prerequisites & Installation

The application requires Python 3 and the following dependencies:

```bash
pip install PySide6 paho-mqtt folium pyttsx3
```

*(Note: The map visualization utilizes `PySide6.QtWebEngineWidgets`. Ensure your PySide6 installation includes the WebEngine modules.)*

## Quick Start Instructions

1. **Launch the Application**:
   Navigate to the project folder in your terminal and run:
   ```bash
   python main_gui.py
   ```

2. **Configure Your Station**:
   At the top of the application window, you will see settings to configure your station:
   - **My Callsign**: Enter your operating callsign.
   - **Grid**: Enter your 4- or 6-character Maidenhead grid square (e.g., `EM27XO` or `FN21`). The engine uses this to calculate all local propagation distances dynamically!
   - **Nearby Radius**: Select how close a reporting station must be to you (in miles) to be considered "local" for likelihood calculations.
   - **Exclude My Callsign**: Check this to prevent your own TX spots from cluttering the feed.

3. **Import Your Logbook (Crucial!)**:
   To unlock the "Need" scoring:
   - Click the **"Import ADIF"** button in the top toolbar.
   - Navigate to your WSJT-X log file (typically located at `C:\Users\YourUser\AppData\Local\WSJT-X\wsjtx_log.adi`).
   - The engine will ingest the file into the local SQLite database. It calculates a unique fingerprint for every QSO, so you can re-import the same file later without generating duplicates!

4. **Monitor the Live Feed**:
   As spots pour in, the table will populate with real-time DX intelligence:
   - **Likelihood**: The physical probability that you can hear the station right now.
   - **Confidence**: The statistical confidence in the likelihood score (based on the number of local receivers hearing the target).
   - **Need**: A score (0-100) indicating how badly you need this station based on your imported logbook (e.g., "All-Time New DXCC").
   - **Priority**: The final unified score.

5. **Voice Alerts**:
   If the `Voice Alerts` checkbox is enabled, the application will automatically announce any station whose unified Priority score exceeds the alert threshold, preventing you from missing rare DX!

## Architecture

Under the hood, the application is driven by a robust SQLite database (`ft8spotter.db`) that permanently tracks global receiver history, ADIF file states, and calibration logs for future machine learning modeling. The architecture cleanly separates physical propagation math (`likelihood_engine.py`) from arbitrary logbook goals (`need_engine.py`).
