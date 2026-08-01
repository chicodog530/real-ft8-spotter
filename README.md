# Real FT8 Spotter

Real FT8 Spotter is an intelligent, live DX spotting application that goes beyond simple reporting. It connects directly to the global PSKReporter MQTT firehose and cross-references live propagation data against your actual WSJT-X logbook to calculate personalized physical likelihoods and logbook "Need" values. It will tell you not just who is on the air, but whether you can actually hear them, and whether you need them for a new DXCC, Grid, State, or Band!

---

## Prerequisites & Installation

The application runs locally on Windows, macOS, and Linux.

**Windows Users:**
Double-click `install.bat`. It will automatically set up a Python Virtual Environment and install all required dependencies (PySide6, paho-mqtt, folium, pyttsx3, requests).

**Linux / macOS Users:**
Open your terminal inside the project folder and run:
```bash
bash install.sh
```
*(Note for Linux users: Voice alerts require `espeak` and `ffmpeg` to be installed on your system via your package manager).*

## Launching the Application

- **Windows:** Double-click `run.bat`
- **Linux/macOS:** Run `bash run.sh`

---

## Complete User Guide

When you launch the application, you will see a comprehensive control panel at the top. Here is a full breakdown of every button and selection:

### 1. Station Configuration

Before connecting to the live stream, configure your local station parameters:

- **My Callsign**: Enter your operating callsign. (e.g., `W1AW`).
- **Grid**: Enter your 4- or 6-character Maidenhead grid square (e.g., `EM27XO`). 
  *What it does:* The engine calculates propagation likelihoods by looking at what stations near your exact Grid Square are currently hearing. If you move to a new QTH, update this!
- **Exclude My Callsign**: Check this box if you are actively transmitting. 
  *What it does:* It prevents your own outgoing FT8 transmissions from cluttering your incoming DX feed.
- **Nearby Radius**: A dropdown to set the search radius (in miles) around your Grid Square. 
  *What it does:* Tells the math engine how far out to look for "nearby receivers". If you live in a dense area, set it low (50m). If you live in a rural area, set it high (500m) to gather more data points.
- **Import ADIF**: Click this to browse for your WSJT-X logbook (`wsjtx_log.adi`). 
  *What it does:* Securely ingests your logbook into the internal database. The engine instantly cross-references all incoming spots against this logbook to identify All-Time New DXCC entities, new bands, and new grid squares. You can click this anytime you finish a session in WSJT-X to update your internal log.

### 2. Advanced Voice Alert Settings

The application features a powerful, hands-free Voice Alert system powered by text-to-speech.

- **Cooldown Timer**: A dropdown (15s up to 5m). 
  *What it does:* Determines how frequently the Voice Engine is allowed to announce the exact same callsign. If a rare station is camping on a frequency, a 5-minute cooldown ensures the robot doesn't yell at you every 15 seconds.
  
- **Voice Alerts Mode**: A dropdown dictating exactly *what* triggers a voice alert.
  - `Voice Alerts: Off`: Mutes the application entirely and instantly clears the voice queue.
  - `Voice Alerts: Smart Priority`: (Default) Alerts only on stations whose mathematically combined Priority Score is 10 or higher.
  - `Voice Alerts: Any Live POTA`: Dead silence unless a confirmed Parks on the Air activator pops up. (Automatically pings the live POTA API in the background).
  - `Voice Alerts: Any New Country`: Dead silence unless a Country (DXCC) you have never worked before appears.
  - `Voice Alerts: Any New US State`: Dead silence unless an unworked US State is spotted.
  - `Voice Alerts: All Live DX`: Reads off every single station spotted.
  
- **Max Alerts**: A dropdown (1, 3, 5, 10, Unlimited).
  *What it does:* Limits how many stations the voice engine will speak per cycle. Because the engine **sorts the live stations by Priority** before speaking, setting this to `3` guarantees you will only hear the 3 absolute rarest, most achievable stations on the band right now. This prevents the voice engine from getting overwhelmed when the bands are fully open.

### 3. Understanding the Data Feed

As spots pour in, the table will populate with real-time DX intelligence. You can click on any DX Callsign in the table to view its distance and bearing on the map!

- **Likelihood**: The physical probability (0-100%) that you can hear the station right now, calculated by looking at how many of your local neighbors are currently receiving them.
- **Confidence**: The statistical confidence (`Low`, `Med`, `High`) in the likelihood score based on sample size.
- **Need**: A score indicating how badly you need this station based on your imported logbook (e.g., `100 (All-Time New DXCC!)`).
- **Priority**: The final unified score. `Priority = Likelihood × Need`. A high Priority means you desperately need it AND you have a great chance of actually completing the QSO.

## Architecture

Under the hood, the application is driven by a robust SQLite database (`ft8spotter.db`) utilizing Write-Ahead Logging (WAL) for extreme performance. The architecture cleanly separates physical propagation math (`likelihood_engine.py`) from arbitrary logbook goals (`need_engine.py`), and uses multi-threaded queues to ensure the text-to-speech engine never freezes the GUI.
