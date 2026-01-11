# Posture Detection Application

A real-time posture monitoring application that uses computer vision to detect and analyze body posture through a webcam feed. The application tracks various posture metrics including slouching, head tilt, neck forward position, shoulder alignment, and more.

## Features

### Real-time Posture Detection
- **Face and Pose Landmark Detection**: Uses MediaPipe Pose and Face Mesh for accurate real-time tracking
- **Multiple Posture Metrics**:
  - Slouching detection (tracks when shoulders are forward or down)
  - Uneven shoulders (detects shoulder height differences)
  - Head tilt (monitors left/right head tilt)
  - Neck forward (detects forward head posture / "text neck")
  - Shoulders forward (tracks rounded shoulders)

### Performance Optimization
- **Configurable Performance Presets**: LOW, MEDIUM, and HIGH presets for different hardware capabilities
- **Custom Performance Settings**: Fine-tune processing FPS, model complexity, history size, and more
- **Frame Skipping**: Intelligent frame skipping to reduce CPU usage while maintaining responsiveness

### Customizable Settings
- **Metric Presets**: Default, Sensitive, and Relaxed sensitivity presets
- **Custom Metric Thresholds**: Adjustable thresholds for each posture metric
- **Visual Controls**: Toggle face mesh overlay, metric displays, and status messages
- **Settings Menu**: Easy-to-use GUI for configuring all settings

### Notifications
- **Sound Notifications**: Customizable sound alerts for bad posture (negative.wav, positive.wav, or custom files)
- **Toast Notifications**: Windows toast notifications for posture alerts
- **Back to Normal Alerts**: Pleasant notifications when posture returns to normal
- **Volume Control**: Adjustable notification volume (0.0 to 1.0)
- **Timing Controls**: Configurable minimum duration and cooldown periods

### Calibration System
- Interactive calibration to establish baseline posture reference
- Quality validation to ensure accurate calibration

## Quick Start

**Download and run the executable**

1. Go to the **Releases** page on GitHub
2. Download the latest `Posture.zip` file
3. Extract and run `Posture.exe`

---

### Prerequisites
- Python 3.12 or higher
- Webcam/camera
- Windows OS (for toast notifications)

### Setup from Source

1. **Clone or download the repository**

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Or install individually:
   ```bash
   pip install opencv-python mediapipe numpy pygame winotify
   ```
   
   Note: `tkinter` is included with Python and doesn't need to be installed separately.

## Usage

### Running the Application

**Option 1: Run the standalone executable** (Recommended for end users)
   - Double-click `Posture.exe` (download from GitHub Releases)
   - No Python installation required - just run and go!

**Option 2: Run from source** (For developers)
   ```bash
   python Posture.py
   ```

### Getting Started

1. **Launch the application** - The video feed will start automatically

2. **Calibration** (first time):
   - Position yourself comfortably in front of the camera
   - Press `C` to calibrate when you're in a good posture
   - Wait for the calibration to complete (you'll see quality feedback)

3. **Settings Menu**:
   - Click the "Settings" button in the top-right corner of the video window
   - Configure metrics, performance presets, visual options, and notifications
   - Click "Save" to apply changes or "Cancel" to discard

4. **Keyboard Controls**:
   - `C` - Calibrate (recalibrate your baseline posture)
   - `ESC` - Exit the application

### Basic Workflow

1. **Launch the application** - The video feed will start
2. **Calibrate** - Press `C` when you're sitting in your ideal posture
3. **Work normally** - The application will monitor your posture in real-time
4. **Receive alerts** - You'll get notifications when bad posture is detected
5. **Adjust settings** - Use the settings menu to customize detection sensitivity and notifications

## Project Structure

```
Posture/
├── Posture.py              # Main application file
├── SettingsMenu.py         # Settings menu GUI module
├── Posture.spec            # PyInstaller configuration file
├── Presets/                # Preset configuration files
│   ├── metric_presets.json
│   └── performance_presets.json
├── Sounds/                 # Notification sound files
│   ├── negative.wav        # Bad posture alert sound
│   └── positive.wav        # Good posture notification sound
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Configuration

### Performance Presets

- **LOW**: Minimal CPU usage (5 FPS, model complexity 0, 5 face landmarks)
- **MEDIUM**: Balanced performance (15 FPS, model complexity 1, 20 face landmarks)
- **HIGH**: Maximum accuracy (30 FPS, model complexity 2, 40 face landmarks)
- **Custom**: Create and save your own performance presets

### Metric Presets

- **Default**: Balanced sensitivity thresholds
- **Sensitive**: Triggers alerts more easily (lower thresholds)
- **Relaxed**: Requires more severe posture issues to trigger (higher thresholds)
- **Custom**: Create and save your own metric threshold presets

### Notification Settings

- **Sound Types**: negative, positive, default, beep, chime, alert, or custom .wav file
- **Volume**: Adjustable from 0.0 (silent) to 1.0 (full volume)
- **Min Duration**: How long bad posture must be detected before alerting (prevents false alarms)
- **Cooldown**: Minimum time between notifications (prevents spam)

## Tips for Best Results

1. **Good Lighting**: Ensure your face and upper body are well-lit
2. **Clear View**: Keep your face and shoulders visible to the camera
3. **Calibrate Properly**: Take time to calibrate when you're in your ideal working posture
4. **Adjust Sensitivity**: If you get too many or too few alerts, adjust the metric preset sensitivity
5. **Performance**: Use LOW preset if you experience lag; use HIGH for maximum accuracy
6. **Notifications**: Adjust volume and timing to match your preferences and work environment

## Troubleshooting

- **No video feed**: Check that your camera is connected and not in use by another application
- **Low FPS**: Try the LOW performance preset or reduce camera resolution
- **Inaccurate detection**: Recalibrate when in your ideal posture position
- **Notifications not working**: 
  - Verify notification settings are enabled in the settings menu
  - If running from source, check that `winotify` is installed: `pip install winotify`
- **Executable won't run**:
  - Some antivirus software may flag PyInstaller executables (this is a false positive)
  - Try adding an exception for `Posture.exe` in your antivirus settings
  - First startup may take a few seconds as files are extracted (this is normal)
- **Import errors** (when running from source): Ensure all dependencies are installed in your virtual environment

## Requirements

### For End Users (Using Executable)
- ✅ **Nothing!** Just download and run `Posture.exe` - all dependencies are included

### For Developers (Running from Source)
- Python 3.12+
- Dependencies listed in `requirements.txt`:
  - OpenCV (opencv-python) - Computer vision library
  - MediaPipe - Pose and face landmark detection
  - NumPy - Numerical operations
  - Pygame - Volume-controlled sound notifications
  - Winotify - Windows toast notifications
  - Tkinter - GUI library (included with Python, no installation needed)
  - PyInstaller (optional) - For building standalone executables

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**For building executables:**
```bash
pip install pyinstaller
```

## License

This project is provided as-is for personal use.

## Author

Joshua Gao







