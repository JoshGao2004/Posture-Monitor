"""
Posture Detection and Analysis Application
==========================================

A real-time posture monitoring application that uses computer vision to detect
and analyze body posture through a webcam feed. The application tracks various
posture metrics including slouching, head tilt, neck forward position, shoulder
alignment, and more.

Features:
- Real-time face and pose landmark detection using MediaPipe Pose and Face Mesh
- Configurable performance presets (LOW, MEDIUM, HIGH) for different hardware
- Custom metric threshold presets for personalized sensitivity settings
- Visual feedback with face mesh overlay, metric displays, and alignment guides
- Settings menu for customizing metrics, performance, and visual options
- Calibration system for establishing baseline posture reference

Author: Joshua Gao
Date: 01/26
"""

import cv2
import mediapipe as mp
import math
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
import os
import time
from SettingsMenu import openSettingsMenu

# ============================================================================
# CONFIGURATION - USER ADJUSTABLE SETTINGS
# ============================================================================

# Smoothing Parameters (Exponential Moving Average)
# Lower values = more smoothing (less responsive), Higher values = less smoothing (more responsive)
alpha = 0.25          # General smoothing factor (0-1)
alphaZ = 0.2          # Z-axis smoothing (more aggressive for depth stability)

# Noise Filtering
deadZoneZ = 0.0006    # Threshold to filter small Z-axis fluctuations (prevents jitter)

# Neck Angle Calculation
headYWeight = 0.8     # Weight of head Y position in neck angle (0.0 = ignore Y, 1.0 = full weight)
                      # 0.5 = Y is half as important as Z (reduces impact of looking up/down)

# MediaPipe Detection Settings
MIN_DETECTION_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.6
MODEL_COMPLEXITY = 2  # 0, 1, or 2 (higher = more accurate but slower)

# Visibility and Quality Settings
MIN_VISIBILITY = 0.7  # Minimum visibility score for landmarks (0.0-1.0, higher = more strict)
MIN_PRESENCE = 0.7   # Minimum presence score for landmarks (0.0-1.0, higher = more strict)
OUTLIER_STD_DEVIATIONS = 3.0  # Number of standard deviations for outlier detection
HISTORY_SIZE = 30  # Number of recent values to keep for outlier detection

# Display Settings
WELCOME_FONT_SCALE = 0.7
WELCOME_OVERLAY_OPACITY = 0.7  # 0.0 = transparent, 1.0 = opaque

# Metric Toggles - Set to True to enable tracking and display, False to disable
METRIC_ENABLE_SLOUCHING = True
METRIC_ENABLE_UNEVEN_SHOULDERS = True
METRIC_ENABLE_HEAD_TILT = True
METRIC_ENABLE_NECK_FORWARD = True
METRIC_ENABLE_SHOULDERS_FORWARD = True

# Status Thresholds (in scaled 0-500 range, adjust to change sensitivity)
# Lower values = more sensitive (triggers earlier), Higher values = less sensitive
STATUS_THRESHOLD_SLOUCHING = 350.0         # Shoulders forward/down (shoulderForward or negative relativeShoulderY)
STATUS_THRESHOLD_UNEVEN_SHOULDERS = 150.0  # Shoulder height asymmetry
STATUS_THRESHOLD_HEAD_TILT = 10.0        # Head tilt angle (degrees, absolute value)
STATUS_THRESHOLD_NECK_FORWARD = 30.0      # Neck forward lean (neckAngle) - combines head and neck forward posture
STATUS_THRESHOLD_SHOULDERS_FORWARD = 350.0 # Shoulder protraction (shoulderForward)

# Metric Preset Settings
METRIC_PRESET_NAME = "Default"  # Current metric preset name
METRIC_PRESETS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Presets", "metric_presets.json")

# Performance Preset File
PERFORMANCE_PRESETS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Presets", "performance_presets.json")

# Window Settings
WINDOW_SCALE_FACTOR = 1.5  # Scale factor for window size (1.0 = original, 1.5 = 50% larger)

# Visual Guides Settings
SHOW_VISUAL_GUIDES = True  # Show alignment lines and guides
GUIDE_COLOR_GOOD = (0, 255, 0)    # Green for good alignment
GUIDE_COLOR_BAD = (0, 0, 255)     # Red for poor alignment
GUIDE_LINE_THICKNESS = 2

# Performance Preset Settings
# Options: "LOW", "MEDIUM", "HIGH"
PERFORMANCE_PRESET = "MEDIUM"  # Default to medium

# Performance settings (will be adjusted by preset)
PROCESSING_FPS = 30  # Target FPS for processing (lower = less CPU)
DISPLAY_FPS = 30  # Target FPS for display (limits how fast window updates)
FACE_MESH_DRAWING_ENABLED = True  # Draw face mesh overlay (performance preset setting - overridden by visual settings)

# Visual Display Settings (independent from performance presets)
VISUAL_SHOW_FACE_MESH = True  # Show/hide face mesh overlay
VISUAL_SHOW_METRICS = True  # Show/hide metric numbers
VISUAL_SHOW_STATUS = True  # Show/hide status text

# Notification Settings
NOTIFICATION_ENABLED = True  # Enable/disable notifications
NOTIFICATION_BEEP_ENABLED = True  # Enable/disable beep sound
NOTIFICATION_TOAST_ENABLED = True  # Enable/disable Windows toast notifications
NOTIFICATION_MIN_DURATION = 5.0  # Seconds of bad posture before first notification
NOTIFICATION_COOLDOWN = 30.0  # Seconds between notifications for same issue
NOTIFICATION_BAD_POSTURE_SOUND_TYPE = "negative"  # "negative", "positive", "default", "beep", "chime", "alert"
NOTIFICATION_BAD_POSTURE_CUSTOM_SOUND_FILE = ""  # Path to custom .wav file for bad posture (overrides sound type if specified)
NOTIFICATION_REVERT_SOUND_TYPE = "positive"  # "negative", "positive", "default", "beep", "chime", "alert"
NOTIFICATION_REVERT_CUSTOM_SOUND_FILE = ""  # Path to custom .wav file for revert (overrides sound type if specified)
NOTIFICATION_VOLUME = 0.5  # Volume level (0.0 to 1.0, where 1.0 is 100%)
NOTIFICATION_MESSAGE_TEMPLATE = "Posture Alert: {issue}"  # Customizable message template
NOTIFICATION_BACK_TO_NORMAL_ENABLED = True  # Enable/disable "back to normal" notifications
NOTIFICATION_BACK_TO_NORMAL_MESSAGE = "Posture is back to normal!"  # Message when posture improves

# ============================================================================
# CONSTANTS
# ============================================================================

# Face landmark indices for stable face position calculation
# Using many points across the face for better stability and noise reduction
# HIGH preset - 40 most suitable landmarks (strategically selected for stability and coverage)
FACE_LANDMARK_INDICES_HIGH = [
    # Core facial structure (nose, eyes, mouth area) - 15 points
    1, 2, 4, 5, 6, 9, 10, 19, 20, 21,  # Nose area (most stable)
    33, 36, 39, 42, 45, 48,  # Eye corners and cheekbones (critical for alignment)

    # Symmetrical face points for tilt detection - 12 points
    234, 236, 238, 241, 244, 250,  # Right side temple and cheek
    151, 168, 172, 175, 197,  # Left side temple and forehead

    # Jawline and chin for stability - 8 points
    283, 284, 288, 291, 296, 297, 298, 300,  # Chin and lower jaw

    # Additional stable points for depth calculation - 5 points
    103, 107, 109,  # Forehead center
    332, 338,  # Upper face regions
]

# Medium preset (subset of landmarks)
FACE_LANDMARK_INDICES_MEDIUM = [
    1, 2, 4, 9, 10,  # Nose area
    33, 36, 39, 42, 45, 48,  # Cheek and jawline
    103, 109, 151, 168, 172, 175,  # Forehead and temples
    234, 236, 238, 241, 244, 250,  # Additional facial features
    283, 284, 288, 296, 297, 300  # Chin and lower face
]

# Low preset (minimal landmarks - 5 key points)
FACE_LANDMARK_INDICES_LOW = [1, 33, 168, 234, 283]  # Nose tip, left cheek, forehead, right temple, chin

# Current active face landmark indices (will be set by preset)
FACE_LANDMARK_INDICES = FACE_LANDMARK_INDICES_MEDIUM.copy()

# ============================================================================
# PERFORMANCE PRESET FUNCTIONS
# ============================================================================

def applyPerformancePreset(preset):
    """Apply performance preset settings and return updated configuration."""
    global MODEL_COMPLEXITY, HISTORY_SIZE, OUTLIER_STD_DEVIATIONS
    global SHOW_VISUAL_GUIDES, FACE_MESH_DRAWING_ENABLED, PROCESSING_FPS, DISPLAY_FPS
    global FACE_LANDMARK_INDICES, FRAME_SKIP_INTERVAL

    if preset == "LOW":
        # Low performance - minimal processing
        PROCESSING_FPS = 5  # Process 5 frames per second
        DISPLAY_FPS = 5  # Limit display FPS to 5 (mesh only updates when processing)
        FRAME_SKIP_INTERVAL = 6  # Skip 5 frames, process every 6th (30fps / 5fps = 6)
        MODEL_COMPLEXITY = 0  # Lowest complexity
        HISTORY_SIZE = 10  # Smaller history
        OUTLIER_STD_DEVIATIONS = 2.5  # Less strict outlier detection
        SHOW_VISUAL_GUIDES = False  # Disable visual guides
        FACE_MESH_DRAWING_ENABLED = True  # Still draw mesh when processing
        FACE_LANDMARK_INDICES = FACE_LANDMARK_INDICES_LOW.copy()  # Only 5 landmarks
    elif preset == "MEDIUM":
        # Medium performance - balanced
        PROCESSING_FPS = 15  # Process 15 frames per second
        DISPLAY_FPS = 15  # Limit display FPS to 15 (mesh only updates when processing)
        FRAME_SKIP_INTERVAL = 2  # Skip 1 frame, process every 2nd (30fps / 15fps = 2)
        MODEL_COMPLEXITY = 1  # Medium complexity
        HISTORY_SIZE = 20  # Medium history
        OUTLIER_STD_DEVIATIONS = 3.0  # Standard outlier detection
        SHOW_VISUAL_GUIDES = True  # Enable visual guides
        FACE_MESH_DRAWING_ENABLED = True  # Draw face mesh
        FACE_LANDMARK_INDICES = FACE_LANDMARK_INDICES_MEDIUM.copy()  # ~20 landmarks
    elif preset == "HIGH":
        # High performance - maximum quality
        PROCESSING_FPS = 30  # Process all frames (30 FPS target)
        DISPLAY_FPS = 30  # Full display FPS
        FRAME_SKIP_INTERVAL = 1  # Process every frame
        MODEL_COMPLEXITY = 2  # Highest complexity
        HISTORY_SIZE = 30  # Full history
        OUTLIER_STD_DEVIATIONS = 3.0  # Standard outlier detection
        SHOW_VISUAL_GUIDES = True  # Enable visual guides
        FACE_MESH_DRAWING_ENABLED = True  # Draw face mesh
        FACE_LANDMARK_INDICES = FACE_LANDMARK_INDICES_HIGH.copy()  # 40 landmarks

    return {
        'model_complexity': MODEL_COMPLEXITY,
        'processing_fps': PROCESSING_FPS,
        'face_landmark_indices': FACE_LANDMARK_INDICES
    }

def reinitializeMediaPipe(config):
    """Reinitialize MediaPipe with new configuration."""
    global face, pose, cachedFaceResults, cachedPoseResults, cachedCurrShoulderZ
    global cachedCurrShoulderY, cachedCurrChestZ, cachedLeftShoulder, cachedRightShoulder

    # Close old instances
    try:
        face.close()
    except:
        pass
    try:
        pose.close()
    except:
        pass

    # Clear cached results
    cachedFaceResults = None
    cachedPoseResults = None
    cachedCurrShoulderZ = None
    cachedCurrShoulderY = None
    cachedCurrChestZ = None
    cachedLeftShoulder = None
    cachedRightShoulder = None

    # Reinitialize with new settings
    face = mpFace.FaceMesh(
        refine_landmarks=True,
        max_num_faces=1,
        min_detection_confidence=MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
        static_image_mode=False
    )

    pose = mpPose.Pose(
        model_complexity=config['model_complexity'],
        smooth_landmarks=True,
        min_detection_confidence=MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
        static_image_mode=False,
        enable_segmentation=False,
        smooth_segmentation=False
    )

# ============================================================================
# METRIC PRESET FUNCTIONS
# ============================================================================

def _loadPresetsFromFile(filePath, defaultPresets, saveFunction):
    """Helper function to load presets from JSON file with error handling."""
    if os.path.exists(filePath):
        try:
            with open(filePath, 'r') as f:
                presetsData = json.load(f)
                # Validate structure
                if "presets" in presetsData and isinstance(presetsData["presets"], dict):
                    return presetsData
                else:
                    print(f"Warning: Invalid presets file structure. Using defaults.")
                    return defaultPresets
        except json.JSONDecodeError as e:
            print(f"Warning: Error reading presets file: {e}. Using defaults.")
            return defaultPresets
        except Exception as e:
            print(f"Warning: Error loading presets: {e}. Using defaults.")
            return defaultPresets
    else:
        # Create default file
        saveFunction(defaultPresets)
        return defaultPresets

def loadMetricPresets():
    """Load metric presets from JSON file. Create default file if it doesn't exist."""
    defaultPresets = {
        "version": "1.0",
        "default_preset": "Default",
        "presets": {
            "Default": {
                "slouching": 400.0,
                "uneven_shoulders": 150.0,
                "head_tilt": 10.0,
                "neck_forward": 30.0,
                "shoulders_forward": 400.0
            },
            "Sensitive": {
                "slouching": 300.0,
                "uneven_shoulders": 100.0,
                "head_tilt": 5.0,
                "neck_forward": 20.0,
                "shoulders_forward": 300.0
            },
            "Relaxed": {
                "slouching": 500.0,
                "uneven_shoulders": 200.0,
                "head_tilt": 15.0,
                "neck_forward": 40.0,
                "shoulders_forward": 500.0
            }
        }
    }
    return _loadPresetsFromFile(METRIC_PRESETS_FILE, defaultPresets, saveMetricPresets)

def saveMetricPresets(presetsData):
    """Save metric presets to JSON file."""
    try:
        with open(METRIC_PRESETS_FILE, 'w') as f:
            json.dump(presetsData, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving metric presets: {e}")
        return False

def applyMetricPreset(presetName):
    """Apply a metric preset by name."""
    global STATUS_THRESHOLD_SLOUCHING, STATUS_THRESHOLD_UNEVEN_SHOULDERS
    global STATUS_THRESHOLD_HEAD_TILT, STATUS_THRESHOLD_NECK_FORWARD, STATUS_THRESHOLD_SHOULDERS_FORWARD

    presetsData = loadMetricPresets()

    if presetName in presetsData["presets"]:
        preset = presetsData["presets"][presetName]
        STATUS_THRESHOLD_SLOUCHING = preset["slouching"]
        STATUS_THRESHOLD_UNEVEN_SHOULDERS = preset["uneven_shoulders"]
        STATUS_THRESHOLD_HEAD_TILT = preset["head_tilt"]
        STATUS_THRESHOLD_NECK_FORWARD = preset["neck_forward"]
        STATUS_THRESHOLD_SHOULDERS_FORWARD = preset["shoulders_forward"]
        return True
    else:
        print(f"Warning: Preset '{presetName}' not found. Using current values.")
        return False

def getAvailableMetricPresets():
    """Get list of available metric preset names."""
    presetsData = loadMetricPresets()
    return list(presetsData["presets"].keys())

def loadPerformancePresets():
    """Load performance presets from JSON file. Create default file if it doesn't exist."""
    defaultPresets = {
        "version": "1.0",
        "default_preset": "MEDIUM",
        "presets": {
            "LOW": {
                "processing_fps": 5,
                "display_fps": 5,
                "frame_skip_interval": 6,
                "model_complexity": 0,
                "history_size": 10,
                "outlier_std_deviations": 2.5,
                "show_visual_guides": False,
                "face_mesh_drawing_enabled": True,
                "face_landmark_count": 5
            },
            "MEDIUM": {
                "processing_fps": 15,
                "display_fps": 15,
                "frame_skip_interval": 2,
                "model_complexity": 1,
                "history_size": 20,
                "outlier_std_deviations": 3.0,
                "show_visual_guides": True,
                "face_mesh_drawing_enabled": True,
                "face_landmark_count": 20
            },
            "HIGH": {
                "processing_fps": 30,
                "display_fps": 30,
                "frame_skip_interval": 1,
                "model_complexity": 2,
                "history_size": 30,
                "outlier_std_deviations": 3.0,
                "show_visual_guides": True,
                "face_mesh_drawing_enabled": True,
                "face_landmark_count": 40
            }
        }
    }
    return _loadPresetsFromFile(PERFORMANCE_PRESETS_FILE, defaultPresets, savePerformancePresets)

def savePerformancePresets(presetsData):
    """Save performance presets to JSON file."""
    try:
        with open(PERFORMANCE_PRESETS_FILE, 'w') as f:
            json.dump(presetsData, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving performance presets: {e}")
        return False

def getAvailablePerformancePresets():
    """Get list of available performance preset names (excluding system presets)."""
    presetsData = loadPerformancePresets()
    # Return all presets (including custom ones)
    return list(presetsData["presets"].keys())

def applyPerformancePresetFromFile(presetName):
    """Apply a performance preset by name from file, including custom presets."""
    global PROCESSING_FPS, DISPLAY_FPS, FRAME_SKIP_INTERVAL, MODEL_COMPLEXITY
    global HISTORY_SIZE, OUTLIER_STD_DEVIATIONS, SHOW_VISUAL_GUIDES
    global FACE_MESH_DRAWING_ENABLED, FACE_LANDMARK_INDICES

    presetsData = loadPerformancePresets()

    if presetName in presetsData["presets"]:
        preset = presetsData["presets"][presetName]

        PROCESSING_FPS = preset["processing_fps"]
        DISPLAY_FPS = preset["display_fps"]
        FRAME_SKIP_INTERVAL = preset["frame_skip_interval"]
        MODEL_COMPLEXITY = preset["model_complexity"]
        HISTORY_SIZE = preset["history_size"]
        OUTLIER_STD_DEVIATIONS = preset["outlier_std_deviations"]
        SHOW_VISUAL_GUIDES = preset["show_visual_guides"]
        FACE_MESH_DRAWING_ENABLED = preset["face_mesh_drawing_enabled"]

        # Set face landmark indices based on count
        landmarkCount = preset["face_landmark_count"]
        if landmarkCount <= 5:
            FACE_LANDMARK_INDICES = FACE_LANDMARK_INDICES_LOW.copy()
        elif landmarkCount <= 20:
            FACE_LANDMARK_INDICES = FACE_LANDMARK_INDICES_MEDIUM.copy()
        else:
            FACE_LANDMARK_INDICES = FACE_LANDMARK_INDICES_HIGH.copy()

        return True
    else:
        print(f"Warning: Performance preset '{presetName}' not found.")
        return False

def saveCustomPerformancePreset(presetName, presetData):
    """Save a custom performance preset."""
    presetsData = loadPerformancePresets()
    presetsData["presets"][presetName] = presetData
    return savePerformancePresets(presetsData)

def deletePerformancePreset(presetName):
    """Delete a custom performance preset (cannot delete LOW, MEDIUM, HIGH)."""
    if presetName in ["LOW", "MEDIUM", "HIGH"]:
        return False  # Cannot delete system presets

    presetsData = loadPerformancePresets()
    if presetName in presetsData["presets"]:
        del presetsData["presets"][presetName]
        return savePerformancePresets(presetsData)
    return False

def saveCustomMetricPreset(presetName, presetData):
    """Save a custom metric preset."""
    presetsData = loadMetricPresets()
    presetsData["presets"][presetName] = presetData
    return saveMetricPresets(presetsData)

def deleteMetricPreset(presetName):
    """Delete a custom metric preset (cannot delete Default, Sensitive, Relaxed)."""
    if presetName in ["Default", "Sensitive", "Relaxed"]:
        return False  # Cannot delete system presets

    presetsData = loadMetricPresets()
    if presetName in presetsData["presets"]:
        del presetsData["presets"][presetName]
        return saveMetricPresets(presetsData)
    return False

# ============================================================================
# INITIALIZATION
# ============================================================================

# Initialize webcam
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Initialize MediaPipe
mpFace = mp.solutions.face_mesh
mpPose = mp.solutions.pose
mpDraw = mp.solutions.drawing_utils

# Apply default preset (MEDIUM)
presetConfig = applyPerformancePreset(PERFORMANCE_PRESET)
face = mpFace.FaceMesh(
    refine_landmarks=True,
    max_num_faces=1,
    min_detection_confidence=MIN_DETECTION_CONFIDENCE,
    min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
    static_image_mode=False
)

pose = mpPose.Pose(
    model_complexity=presetConfig['model_complexity'],
    smooth_landmarks=True,
    min_detection_confidence=MIN_DETECTION_CONFIDENCE,
    min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
    static_image_mode=False,
    enable_segmentation=False,
    smooth_segmentation=False
)

# Load and apply default metric preset
def initializeMetricPreset():
    """Initialize and apply the default metric preset."""
    global METRIC_PRESET_NAME

    presetsData = loadMetricPresets()
    # Use default preset from file if available, otherwise use "Default"
    if "default_preset" in presetsData and presetsData["default_preset"] in presetsData["presets"]:
        presetName = presetsData["default_preset"]
    elif METRIC_PRESET_NAME in presetsData["presets"]:
        presetName = METRIC_PRESET_NAME
    else:
        # Fallback to first available preset
        available = list(presetsData["presets"].keys())
        presetName = available[0] if available else "Default"

    METRIC_PRESET_NAME = presetName
    applyMetricPreset(presetName)

initializeMetricPreset()

# ============================================================================
# STATE VARIABLES
# ============================================================================

# Saved reference positions (calibration baseline)
savedFaceZPos = None
savedFaceYPos = None
savedShoulderZPos = None
savedShoulderYPos = None
savedChestZPos = None
savedShoulderAsymmetry = None
savedNeckAngle = None
savedShoulderForward = None

# Smoothed metric values (Exponential Moving Average)
smoothedFaceToShoulderZ = 0.0
smoothedFaceToShoulderY = 0.0
smoothedRelativeShoulderZ = 0.0
smoothedRelativeShoulderY = 0.0
smoothedShoulderAsymmetry = 0.0
smoothedHeadTilt = 0.0
smoothedNeckAngle = 0.0
smoothedShoulderForward = 0.0

# Outlier detection - store recent values for statistical analysis
metricHistory = {
    'faceToShoulderZ': [],
    'relativeShoulderZ': [],
    'relativeShoulderY': [],
    'shoulderAsymmetry': [],
    'headTilt': [],
    'neckAngle': [],
    'shoulderForward': []
}

# Frame skipping for performance
frameCounter = 0
FRAME_SKIP_INTERVAL = 1  # Process every Nth frame (will be set by preset)

# Cached results for display continuity (prevents flashing)
cachedFaceResults = None
cachedPoseResults = None
cachedCurrShoulderZ = None
cachedCurrShoulderY = None
cachedCurrChestZ = None
cachedLeftShoulder = None
cachedRightShoulder = None
DISPLAY_FPS = 30  # Will be set by preset

# Notification tracking
BAD_POSTURE_START_TIME = {}  # Track when each issue started {issue_name: timestamp}
LAST_NOTIFICATION_TIME = 0  # Global last notification time (single cooldown for all issues)
TOTAL_BAD_POSTURE_TIME = {}  # Track total time per issue for statistics {issue_name: seconds}
HAD_BAD_POSTURE = False  # Track if we had bad posture in previous check
NEGATIVE_NOTIFICATION_SENT = False  # Track if a negative notification was sent (needed for positive notification)

# ============================================================================
# HELPER FUNCTIONS - LANDMARK & POSITION CALCULATION
# ============================================================================

def isLandmarkVisible(landmark):
    """Check if landmark has sufficient visibility and presence."""
    return (hasattr(landmark, 'visibility') and landmark.visibility >= MIN_VISIBILITY and
            hasattr(landmark, 'presence') and landmark.presence >= MIN_PRESENCE)

def calculateFacePosition(faceLandmarks):
    """Calculate average face position using multiple landmarks for stability with visibility filtering."""
    faceZValues = []
    faceYValues = []

    for idx in FACE_LANDMARK_INDICES:
        if len(faceLandmarks.landmark) > idx:
            landmark = faceLandmarks.landmark[idx]
            # Only use visible landmarks
            if isLandmarkVisible(landmark):
                faceZValues.append(landmark.z)
                faceYValues.append(landmark.y)

    if faceZValues:
        faceZ = sum(faceZValues) / len(faceZValues)
        faceY = sum(faceYValues) / len(faceYValues)
    else:
        # Fallback to nose tip if no visible landmarks found
        noseTip = faceLandmarks.landmark[1]
        faceZ = noseTip.z
        faceY = noseTip.y

    return faceZ, faceY

def calculateStableShoulderPosition(leftShoulder, rightShoulder, leftEar, rightEar,
                                   leftElbow, rightElbow):
    """Calculate stable shoulder position using multi-point estimation with visibility weighting."""
    positions = []
    weights = []

    # Use actual shoulder landmarks if visible
    if leftShoulder and isLandmarkVisible(leftShoulder):
        positions.append((leftShoulder.x, leftShoulder.y, leftShoulder.z))
        weights.append(leftShoulder.visibility)

    if rightShoulder and isLandmarkVisible(rightShoulder):
        positions.append((rightShoulder.x, rightShoulder.y, rightShoulder.z))
        weights.append(rightShoulder.visibility)

    # Use ear-to-elbow midpoint estimation if available
    if leftEar and leftElbow and isLandmarkVisible(leftEar) and isLandmarkVisible(leftElbow):
        estX = (leftEar.x + leftElbow.x) / 2
        estY = (leftEar.y + leftElbow.y) / 2
        estZ = (leftEar.z + leftElbow.z) / 2
        positions.append((estX, estY, estZ))
        weights.append((leftEar.visibility + leftElbow.visibility) / 2)

    if rightEar and rightElbow and isLandmarkVisible(rightEar) and isLandmarkVisible(rightElbow):
        estX = (rightEar.x + rightElbow.x) / 2
        estY = (rightEar.y + rightElbow.y) / 2
        estZ = (rightEar.z + rightElbow.z) / 2
        positions.append((estX, estY, estZ))
        weights.append((rightEar.visibility + rightElbow.visibility) / 2)

    if not positions:
        # Fallback to direct shoulder average if no valid estimates
        if leftShoulder and rightShoulder:
            return ((leftShoulder.x + rightShoulder.x) / 2,
                    (leftShoulder.y + rightShoulder.y) / 2,
                    (leftShoulder.z + rightShoulder.z) / 2)
        return None

    # Weighted average
    totalWeight = sum(weights)
    if totalWeight == 0:
        return None

    avgX = sum(p[0] * w for p, w in zip(positions, weights)) / totalWeight
    avgY = sum(p[1] * w for p, w in zip(positions, weights)) / totalWeight
    avgZ = sum(p[2] * w for p, w in zip(positions, weights)) / totalWeight

    return (avgX, avgY, avgZ)

# ============================================================================
# HELPER FUNCTIONS - QUALITY & VALIDATION
# ============================================================================

def detectOutlier(value, metricName):
    """Detect if a value is an outlier (>3 standard deviations from recent history)."""
    history = metricHistory[metricName]

    if len(history) < 5:  # Need at least 5 values for statistical analysis
        history.append(value)
        return value

    # Calculate mean and standard deviation
    mean = sum(history) / len(history)
    variance = sum((x - mean) ** 2 for x in history) / len(history)
    stdDev = math.sqrt(variance) if variance > 0 else 0.001

    # Check if value is an outlier
    isOutlier = abs(value - mean) > OUTLIER_STD_DEVIATIONS * stdDev

    # Add to history (maintain size)
    history.append(value)
    if len(history) > HISTORY_SIZE:
        history.pop(0)

    # Return previous value if outlier detected
    if isOutlier:
        return history[-2] if len(history) > 1 else mean

    return value

def validateCalibrationQuality(faceResults, poseResults):
    """Validate calibration quality by checking landmark visibility."""
    qualityIssues = []
    qualityScore = 100.0

    # Check face landmarks visibility
    if faceResults.multi_face_landmarks:
        visibleFaceLandmarks = 0
        totalFaceLandmarks = 0
        for fl in faceResults.multi_face_landmarks:
            for idx in FACE_LANDMARK_INDICES[:10]:  # Check first 10 key landmarks
                if len(fl.landmark) > idx:
                    totalFaceLandmarks += 1
                    if isLandmarkVisible(fl.landmark[idx]):
                        visibleFaceLandmarks += 1

        faceVisibility = (visibleFaceLandmarks / totalFaceLandmarks * 100) if totalFaceLandmarks > 0 else 0
        if faceVisibility < 70:
            qualityIssues.append(f"Low face visibility: {faceVisibility:.0f}%")
            qualityScore -= 20

    # Check pose landmarks visibility
    if poseResults and poseResults.pose_landmarks:
        lm = poseResults.pose_landmarks.landmark
        requiredLandmarks = {
            'Left Shoulder': lm[11],
            'Right Shoulder': lm[12],
            'Left Ear': lm[7],
            'Right Ear': lm[8],
            'Left Elbow': lm[13],
            'Right Elbow': lm[14],
            'Left Hip': lm[23],
            'Right Hip': lm[24]
        }

        missingLandmarks = []
        for name, landmark in requiredLandmarks.items():
            if not isLandmarkVisible(landmark):
                missingLandmarks.append(name)
                qualityScore -= 10

        if missingLandmarks:
            qualityIssues.append(f"Low visibility: {', '.join(missingLandmarks)}")

    return max(0, qualityScore), qualityIssues

# ============================================================================
# HELPER FUNCTIONS - METRIC CALCULATION
# ============================================================================

def calculatePostureMetrics(currFaceZ, currFaceY, currShoulderZ, currShoulderY,
                           currChestZ, leftShoulder, rightShoulder, faceLandmarks):
    """Calculate all posture metrics from current positions."""
    metrics = {}

    # Relative shoulder positions (standardized: forward/bad = positive)
    metrics['relativeShoulderZ'] = savedShoulderZPos - currShoulderZ  # Forward = positive
    metrics['relativeShoulderY'] = savedShoulderYPos - currShoulderY  # Up = positive (intuitive)

    # Face position relative to shoulders (removes whole-body movement)
    faceMovementZ = currFaceZ - savedFaceZPos
    shoulderMovementZ = currShoulderZ - savedShoulderZPos
    metrics['faceToShoulderZ'] = shoulderMovementZ - faceMovementZ  # Forward head = positive

    faceMovementY = currFaceY - savedFaceYPos
    shoulderMovementY = currShoulderY - savedShoulderYPos
    metrics['faceToShoulderY'] = shoulderMovementY - faceMovementY  # Down = negative (intuitive)

    # Shoulder Asymmetry
    if leftShoulder is not None and rightShoulder is not None:
        shoulderAsymmetryRaw = abs(leftShoulder.y - rightShoulder.y)
        if savedShoulderAsymmetry is not None:
            metrics['shoulderAsymmetry'] = shoulderAsymmetryRaw - savedShoulderAsymmetry
        else:
            metrics['shoulderAsymmetry'] = shoulderAsymmetryRaw
    else:
        metrics['shoulderAsymmetry'] = 0.0

    # Head Tilt (directional: left = negative, right = positive)
    if len(faceLandmarks.landmark) > 454:
        leftTemple = faceLandmarks.landmark[234]
        rightTemple = faceLandmarks.landmark[454]
        tiltDy = leftTemple.y - rightTemple.y
        tiltDx = abs(leftTemple.x - rightTemple.x) + 0.001
        metrics['headTilt'] = max(-90.0, min(90.0, math.atan2(tiltDy, tiltDx) * (180 / math.pi)))
    else:
        metrics['headTilt'] = 0.0

    # Neck Angle (forward lean, weighted Y component)
    neckDy = (currFaceY - currShoulderY) * headYWeight
    neckDz = abs(currFaceZ - currShoulderZ) + 0.001
    neckAngleRaw = math.atan2(neckDy, neckDz) * (180 / math.pi)
    if savedNeckAngle is not None:
        metrics['neckAngle'] = neckAngleRaw - savedNeckAngle  # Forward lean = positive
    else:
        metrics['neckAngle'] = neckAngleRaw

    # Shoulder Forward Position (relative to chest, removes whole-body movement)
    if currChestZ is not None and savedChestZPos is not None:
        shoulderMovementZ = currShoulderZ - savedShoulderZPos
        chestMovementZ = currChestZ - savedChestZPos
        # Relative shoulder forward = shoulder movement minus chest movement
        # Forward (shoulder moves forward relative to chest) = positive (bad)
        metrics['shoulderForward'] = chestMovementZ - shoulderMovementZ  # Forward = positive
    else:
        metrics['shoulderForward'] = 0.0

    return metrics

def applyDeadZone(value, threshold):
    """Filter out small fluctuations below threshold."""
    if abs(value) < threshold:
        return 0.0
    return value

def scaleAndSmoothMetrics(metrics):
    """Scale metrics to 0-500 range and apply exponential moving average smoothing with outlier detection."""
    # Scale factors
    zScaleFactor = 500 / 0.0599
    yScaleFactor = 500 / 1.0
    asymmetryScale = 500 / 0.1
    neckAngleScale = 500 / 90.0
    shoulderForwardScale = 500 / 0.0599

    # Apply dead zone to Z metrics
    metrics['faceToShoulderZ'] = applyDeadZone(metrics['faceToShoulderZ'], deadZoneZ)
    metrics['relativeShoulderZ'] = applyDeadZone(metrics['relativeShoulderZ'], deadZoneZ)

    # Apply outlier detection before scaling
    metrics['faceToShoulderZ'] = detectOutlier(metrics['faceToShoulderZ'], 'faceToShoulderZ')
    metrics['relativeShoulderZ'] = detectOutlier(metrics['relativeShoulderZ'], 'relativeShoulderZ')
    metrics['relativeShoulderY'] = detectOutlier(metrics['relativeShoulderY'], 'relativeShoulderY')
    metrics['shoulderAsymmetry'] = detectOutlier(metrics['shoulderAsymmetry'], 'shoulderAsymmetry')
    metrics['headTilt'] = detectOutlier(metrics['headTilt'], 'headTilt')
    metrics['neckAngle'] = detectOutlier(metrics['neckAngle'], 'neckAngle')
    metrics['shoulderForward'] = detectOutlier(metrics['shoulderForward'], 'shoulderForward')

    # Scale and smooth
    global smoothedFaceToShoulderZ, smoothedFaceToShoulderY
    global smoothedRelativeShoulderZ, smoothedRelativeShoulderY
    global smoothedShoulderAsymmetry, smoothedHeadTilt
    global smoothedNeckAngle, smoothedShoulderForward

    smoothedRelativeShoulderZ = alphaZ * (metrics['relativeShoulderZ'] * zScaleFactor) + (1 - alphaZ) * smoothedRelativeShoulderZ
    smoothedFaceToShoulderZ = alphaZ * (metrics['faceToShoulderZ'] * zScaleFactor) + (1 - alphaZ) * smoothedFaceToShoulderZ
    smoothedRelativeShoulderY = alpha * (metrics['relativeShoulderY'] * yScaleFactor) + (1 - alpha) * smoothedRelativeShoulderY
    smoothedFaceToShoulderY = alpha * (metrics['faceToShoulderY'] * yScaleFactor) + (1 - alpha) * smoothedFaceToShoulderY
    smoothedShoulderAsymmetry = alpha * (metrics['shoulderAsymmetry'] * asymmetryScale) + (1 - alpha) * smoothedShoulderAsymmetry
    smoothedHeadTilt = alpha * metrics['headTilt'] + (1 - alpha) * smoothedHeadTilt
    smoothedNeckAngle = alpha * (metrics['neckAngle'] * neckAngleScale) + (1 - alpha) * smoothedNeckAngle
    smoothedShoulderForward = alphaZ * (metrics['shoulderForward'] * shoulderForwardScale) + (1 - alphaZ) * smoothedShoulderForward

# ============================================================================
# HELPER FUNCTIONS - STATUS & DISPLAY
# ============================================================================

def getPostureStatus():
    """Check all enabled metrics against thresholds and return list of active status issues."""
    statuses = []

    # Slouching (shoulders forward relative to chest OR shoulders dropped)
    if METRIC_ENABLE_SLOUCHING and (smoothedShoulderForward > STATUS_THRESHOLD_SLOUCHING or smoothedRelativeShoulderY < -STATUS_THRESHOLD_SLOUCHING):
        statuses.append("Slouching")

    # Uneven Shoulders
    if METRIC_ENABLE_UNEVEN_SHOULDERS and smoothedShoulderAsymmetry > STATUS_THRESHOLD_UNEVEN_SHOULDERS:
        statuses.append("Uneven Shoulders")

    # Head Tilted
    if METRIC_ENABLE_HEAD_TILT and abs(smoothedHeadTilt) > STATUS_THRESHOLD_HEAD_TILT:
        statuses.append("Head Tilted")

    # Neck Forward (forward lean - combines head and neck forward posture)
    if METRIC_ENABLE_NECK_FORWARD and smoothedNeckAngle > STATUS_THRESHOLD_NECK_FORWARD:
        statuses.append("Neck Forward")

    # Shoulders Forward (protraction)
    if METRIC_ENABLE_SHOULDERS_FORWARD and smoothedShoulderForward > STATUS_THRESHOLD_SHOULDERS_FORWARD:
        statuses.append("Shoulders Forward")

    return statuses

def isMetricTriggered(metricName, metricValue):
    """Check if a metric exceeds its threshold (triggered)."""
    if metricName == "Slouching":
        return (smoothedShoulderForward > STATUS_THRESHOLD_SLOUCHING or
                smoothedRelativeShoulderY < -STATUS_THRESHOLD_SLOUCHING)
    elif metricName == "Uneven Shoulders":
        return metricValue > STATUS_THRESHOLD_UNEVEN_SHOULDERS
    elif metricName == "Head Tilt":
        return abs(metricValue) > STATUS_THRESHOLD_HEAD_TILT
    elif metricName == "Neck Forward":
        return metricValue > STATUS_THRESHOLD_NECK_FORWARD
    elif metricName == "Shoulders Forward":
        return metricValue > STATUS_THRESHOLD_SHOULDERS_FORWARD
    return False

def displayStatus(frame):
    """Display individual metrics stacked vertically, only showing enabled ones."""
    statuses = getPostureStatus()

    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 0.8
    thickness = 2
    lineSpacing = 35  # Vertical spacing between lines
    startY = 30

    yPos = startY

    if statuses:
        # Display each status on its own line
        for status in statuses:
            cv2.putText(frame, status, (10, yPos), font, fontScale, (0, 0, 255), thickness)  # Red
            yPos += lineSpacing
    else:
        # Good posture - no issues detected
        cv2.putText(frame, "Good Posture", (10, yPos), font, fontScale, (0, 255, 0), thickness)  # Green

def displayMetricNumbers(frame, w):
    """Display metric names and numeric values on the right side, only showing enabled ones."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 0.8
    thickness = 2
    lineSpacing = 35  # Vertical spacing between lines (should match displayStatus)
    startY = 30
    rightMargin = 20  # Margin from right edge

    yPos = startY
    metrics = []

    # Collect enabled metrics with their values
    if METRIC_ENABLE_SLOUCHING:
        # Show the higher of the two slouching indicators
        slouchValue = max(smoothedShoulderForward, -smoothedRelativeShoulderY if smoothedRelativeShoulderY < 0 else 0)
        metrics.append(("Slouching", slouchValue))

    if METRIC_ENABLE_UNEVEN_SHOULDERS:
        metrics.append(("Uneven Shoulders", smoothedShoulderAsymmetry))

    if METRIC_ENABLE_HEAD_TILT:
        metrics.append(("Head Tilt", smoothedHeadTilt))

    if METRIC_ENABLE_NECK_FORWARD:
        metrics.append(("Neck Forward", smoothedNeckAngle))

    if METRIC_ENABLE_SHOULDERS_FORWARD:
        metrics.append(("Shoulders Forward", smoothedShoulderForward))

    # Display each metric name and value on the right side
    for metricName, metricValue in metrics:
        # Format the value (use 1 decimal place)
        valueText = f"{metricValue:.1f}"

        # Create full text with metric name
        fullText = f"{metricName}: {valueText}"

        # Check if metric is triggered to determine color
        isTriggered = isMetricTriggered(metricName, metricValue)
        color = (0, 0, 255) if isTriggered else (0, 255, 0)  # Red if triggered, green otherwise

        # Get text width for right alignment
        (textWidth, textHeight), _ = cv2.getTextSize(fullText, font, fontScale, thickness)
        xPos = w - textWidth - rightMargin

        # Display metric name and value
        cv2.putText(frame, fullText, (xPos, yPos), font, fontScale, color, thickness)
        yPos += lineSpacing

# ============================================================================
# HELPER FUNCTIONS - NOTIFICATIONS
# ============================================================================

def playNotificationSound(soundType="default", customSoundFile="", isGoodPosture=False):
    """Play a notification sound based on the sound type with volume control."""
    if not NOTIFICATION_BEEP_ENABLED:
        return

    scriptDir = os.path.dirname(os.path.abspath(__file__))
    soundsDir = os.path.join(scriptDir, "Sounds")
    
    try:
        volume = max(0.0, min(1.0, NOTIFICATION_VOLUME))  # Clamp volume between 0.0 and 1.0

        # Try using pygame.mixer for volume control (supports .wav files)
        try:
            import pygame
            pygame.mixer.init()
            soundObj = None

            # Pleasant sound for good posture - use positive.wav
            if isGoodPosture:
                positivePath = os.path.join(scriptDir, "positive.wav")
                if os.path.exists(positivePath):
                    soundObj = pygame.mixer.Sound(positivePath)
                else:
                    # Fallback to soft pleasant chime if file doesn't exist
                    winsound.Beep(800, 100)
                    time.sleep(0.03)
                    winsound.Beep(1000, 100)
                    time.sleep(0.03)
                    winsound.Beep(1200, 150)
                    return
            # Check for custom sound file first
            elif customSoundFile and os.path.exists(customSoundFile):
                soundObj = pygame.mixer.Sound(customSoundFile)
            # Use predefined sound types
            elif soundType == "negative":
                # Negative.wav file
                negativePath = os.path.join(soundsDir, "negative.wav")
                if os.path.exists(negativePath):
                    soundObj = pygame.mixer.Sound(negativePath)
            elif soundType == "positive":
                # Positive.wav file
                positivePath = os.path.join(soundsDir, "positive.wav")
                if os.path.exists(positivePath):
                    soundObj = pygame.mixer.Sound(positivePath)
            elif os.path.exists(soundType):
                # Custom sound file specified directly in soundType
                soundObj = pygame.mixer.Sound(soundType)

            # Play sound with volume control if we have a sound object
            if soundObj:
                soundObj.set_volume(volume)
                soundObj.play()
                return
        except ImportError:
            pass  # pygame not available, fall back to winsound
        except Exception as e:
            print(f"Error with pygame.mixer: {e}")
            # Fall back to winsound

        # Fallback to winsound (no volume control, but works without pygame)
        import winsound

        # Pleasant sound for good posture - use positive.wav
        if isGoodPosture:
            positivePath = os.path.join(soundsDir, "positive.wav")
            if os.path.exists(positivePath):
                winsound.PlaySound(positivePath, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                # Fallback to soft pleasant chime if file doesn't exist
                winsound.Beep(800, 100)
                time.sleep(0.03)
                winsound.Beep(1000, 100)
                time.sleep(0.03)
                winsound.Beep(1200, 150)
            return

        # Check for custom sound file first
        if customSoundFile and os.path.exists(customSoundFile):
            winsound.PlaySound(customSoundFile, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return

        # Use predefined sound types
        if soundType == "negative":
            # Negative.wav file
            negativePath = os.path.join(soundsDir, "negative.wav")
            if os.path.exists(negativePath):
                winsound.PlaySound(negativePath, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                # Fallback to default beep if file doesn't exist
                winsound.Beep(1000, 200)
        elif soundType == "positive":
            # Positive.wav file
            positivePath = os.path.join(soundsDir, "positive.wav")
            if os.path.exists(positivePath):
                winsound.PlaySound(positivePath, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                # Fallback to chime if file doesn't exist
                winsound.Beep(1500, 200)
        elif soundType == "default" or soundType == "beep":
            # Standard Windows beep (single beep) - volume control not available
            winsound.Beep(1000, 200)  # 1000 Hz for 200ms
        elif soundType == "chime":
            # Single pleasant chime - volume control not available
            winsound.Beep(1500, 200)
        elif soundType == "alert":
            # Single alert sound - volume control not available
            winsound.Beep(800, 300)
        elif os.path.exists(soundType):
            # Custom sound file specified directly in soundType
            winsound.PlaySound(soundType, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        print(f"Error playing notification sound: {e}")

def showNotificationToast(message):
    """Show a Windows toast notification."""
    if not NOTIFICATION_TOAST_ENABLED:
        return

    try:
        import winotify
        toast = winotify.Notification(
            app_id="Posture Monitor",
            title="Posture Alert",
            msg=message,
            duration="short"
        )
        toast.show()
    except ImportError as e:
        print(f"winotify ImportError: {e}")
        print(f"NOTIFICATION: {message}")
    except Exception as e:
        print(f"Error with winotify: {type(e).__name__}: {e}")
        print(f"NOTIFICATION: {message}")

def sendNotification(issue, customSoundFile=""):
    """Send notification for a posture issue (beep + toast)."""
    if not NOTIFICATION_ENABLED:
        return

    # Format message
    message = NOTIFICATION_MESSAGE_TEMPLATE.format(issue=issue)

    # Play sound using bad posture sound settings
    soundFile = customSoundFile if customSoundFile else NOTIFICATION_BAD_POSTURE_CUSTOM_SOUND_FILE
    playNotificationSound(NOTIFICATION_BAD_POSTURE_SOUND_TYPE, soundFile, isGoodPosture=False)

    # Show toast
    showNotificationToast(message)

def sendBackToNormalNotification():
    """Send notification when posture returns to normal."""
    if not NOTIFICATION_ENABLED or not NOTIFICATION_BACK_TO_NORMAL_ENABLED:
        return

    # Play sound using revert sound settings
    playNotificationSound(NOTIFICATION_REVERT_SOUND_TYPE, NOTIFICATION_REVERT_CUSTOM_SOUND_FILE, isGoodPosture=True)

    # Show toast
    showNotificationToast(NOTIFICATION_BACK_TO_NORMAL_MESSAGE)

def checkAndNotifyPosture(statuses, currentTime):
    """Check posture statuses and send notifications if needed."""
    global BAD_POSTURE_START_TIME, LAST_NOTIFICATION_TIME, TOTAL_BAD_POSTURE_TIME, HAD_BAD_POSTURE, NEGATIVE_NOTIFICATION_SENT

    if not isCalibrated():
        return

    hasBadPosture = len(statuses) > 0

    # Check if posture returned to normal
    if HAD_BAD_POSTURE and not hasBadPosture:
        # Posture just returned to normal - send positive notification only if negative was sent
        if NEGATIVE_NOTIFICATION_SENT:
            sendBackToNormalNotification()
            NEGATIVE_NOTIFICATION_SENT = False  # Reset flag after sending positive notification
        HAD_BAD_POSTURE = False
        # Reset tracking for all resolved issues
        for issue in list(BAD_POSTURE_START_TIME.keys()):
            if issue not in statuses:
                # Issue resolved - track total time
                if issue in BAD_POSTURE_START_TIME:
                    duration = currentTime - BAD_POSTURE_START_TIME[issue]
                    if issue not in TOTAL_BAD_POSTURE_TIME:
                        TOTAL_BAD_POSTURE_TIME[issue] = 0
                    TOTAL_BAD_POSTURE_TIME[issue] += duration
                # Clean up tracking
                BAD_POSTURE_START_TIME.pop(issue, None)
        return

    # Update HAD_BAD_POSTURE flag
    if hasBadPosture:
        HAD_BAD_POSTURE = True

    # Reset tracking for issues that are no longer present
    currentIssues = set(statuses)
    for issue in list(BAD_POSTURE_START_TIME.keys()):
        if issue not in currentIssues:
            # Issue resolved - track total time
            if issue in BAD_POSTURE_START_TIME:
                duration = currentTime - BAD_POSTURE_START_TIME[issue]
                if issue not in TOTAL_BAD_POSTURE_TIME:
                    TOTAL_BAD_POSTURE_TIME[issue] = 0
                TOTAL_BAD_POSTURE_TIME[issue] += duration
            # Clean up tracking
            BAD_POSTURE_START_TIME.pop(issue, None)

    # Check if we should send a notification (global cooldown, not per-issue)
    timeSinceLastNotification = currentTime - LAST_NOTIFICATION_TIME

    # Check each current issue
    for issue in statuses:
        # Initialize tracking if this is a new issue
        if issue not in BAD_POSTURE_START_TIME:
            BAD_POSTURE_START_TIME[issue] = currentTime

        # Calculate how long this issue has been present
        duration = currentTime - BAD_POSTURE_START_TIME[issue]

        # Send notification if duration is met and global cooldown has passed
        if (duration >= NOTIFICATION_MIN_DURATION and
            timeSinceLastNotification >= NOTIFICATION_COOLDOWN):
            sendNotification(issue, NOTIFICATION_BAD_POSTURE_CUSTOM_SOUND_FILE)
            LAST_NOTIFICATION_TIME = currentTime
            NEGATIVE_NOTIFICATION_SENT = True  # Mark that a negative notification was sent
            break  # Only send one notification per check (global cooldown)

def displayWelcomeScreen(frame, h, w):
    """Display welcome screen with calibration instructions."""
    welcomeText1 = "Welcome to Posture Monitor"
    welcomeText2 = "Please sit up straight with good posture, then"
    welcomeText3 = "Press 'C' to calibrate your baseline position"
    welcomeText4 = "Press 'ESC' to exit"

    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 2
    color = (255, 255, 255)

    # Calculate centered positions
    textY1 = h // 2 - 60
    textY2 = h // 2 - 20
    textY3 = h // 2 + 20
    textY4 = h // 2 + 60

    textSizes = [cv2.getTextSize(text, font, WELCOME_FONT_SCALE, thickness)[0]
                 for text in [welcomeText1, welcomeText2, welcomeText3, welcomeText4]]
    textX = [(w - size[0]) // 2 for size in textSizes]

    # Draw semi-transparent overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, WELCOME_OVERLAY_OPACITY, frame, 1 - WELCOME_OVERLAY_OPACITY, 0, frame)

    # Draw text
    cv2.putText(frame, welcomeText1, (textX[0], textY1), font, WELCOME_FONT_SCALE, color, thickness)
    cv2.putText(frame, welcomeText2, (textX[1], textY2), font, WELCOME_FONT_SCALE, color, thickness)
    cv2.putText(frame, welcomeText3, (textX[2], textY3), font, WELCOME_FONT_SCALE, (0, 255, 255), thickness)
    cv2.putText(frame, welcomeText4, (textX[3], textY4), font, WELCOME_FONT_SCALE, color, thickness)

def drawVisualGuides(frame, w, h, leftShoulder, rightShoulder, leftHip, rightHip,
                     leftEar, rightEar, leftElbow, rightElbow):
    """Draw visual alignment guides showing ideal vs current posture."""
    if not (leftShoulder and rightShoulder and leftHip and rightHip):
        return

    # Convert normalized coordinates to pixel coordinates
    def toPixel(landmark):
        return (int(landmark.x * w), int(landmark.y * h))

    ls = toPixel(leftShoulder)
    rs = toPixel(rightShoulder)
    lh = toPixel(leftHip)
    rh = toPixel(rightHip)

    # Draw shoulder line
    shoulderColor = GUIDE_COLOR_GOOD if abs(leftShoulder.y - rightShoulder.y) < 0.02 else GUIDE_COLOR_BAD
    cv2.line(frame, ls, rs, shoulderColor, GUIDE_LINE_THICKNESS)

    # Draw hip line
    hipColor = GUIDE_COLOR_GOOD if abs(leftHip.y - rightHip.y) < 0.02 else GUIDE_COLOR_BAD
    cv2.line(frame, lh, rh, hipColor, GUIDE_LINE_THICKNESS)

    # Draw vertical alignment lines (shoulder to hip)
    shoulderCenterX = (ls[0] + rs[0]) // 2
    hipCenterX = (lh[0] + rh[0]) // 2

    # Check if shoulders and hips are aligned vertically
    alignmentGood = abs(shoulderCenterX - hipCenterX) < w * 0.05  # 5% of frame width tolerance
    alignmentColor = GUIDE_COLOR_GOOD if alignmentGood else GUIDE_COLOR_BAD

    shoulderCenterY = (ls[1] + rs[1]) // 2
    hipCenterY = (lh[1] + rh[1]) // 2

    cv2.line(frame, (shoulderCenterX, shoulderCenterY),
             (hipCenterX, hipCenterY), alignmentColor, GUIDE_LINE_THICKNESS)

    # Draw head alignment if ears are visible
    if leftEar and rightEar and isLandmarkVisible(leftEar) and isLandmarkVisible(rightEar):
        le = toPixel(leftEar)
        re = toPixel(rightEar)
        earCenterX = (le[0] + re[0]) // 2
        earCenterY = (le[1] + re[1]) // 2

        # Check head alignment with shoulders
        headAlignmentGood = abs(earCenterX - shoulderCenterX) < w * 0.05
        headColor = GUIDE_COLOR_GOOD if headAlignmentGood else GUIDE_COLOR_BAD

        cv2.line(frame, (earCenterX, earCenterY),
                 (shoulderCenterX, shoulderCenterY), headColor, GUIDE_LINE_THICKNESS)

        # Draw ear line
        earTilt = abs(leftEar.y - rightEar.y)
        earLineColor = GUIDE_COLOR_GOOD if earTilt < 0.02 else GUIDE_COLOR_BAD
        cv2.line(frame, le, re, earLineColor, GUIDE_LINE_THICKNESS)

def drawSettingsButton(frame, w, h):
    """Draw settings button in bottom-left corner and return button coordinates."""
    buttonWidth = 120
    buttonHeight = 35
    margin = 10
    x = margin
    y = h - buttonHeight - margin

    # Draw button background
    cv2.rectangle(frame, (x, y), (x + buttonWidth, y + buttonHeight), (50, 50, 50), -1)
    cv2.rectangle(frame, (x, y), (x + buttonWidth, y + buttonHeight), (200, 200, 200), 2)

    # Draw button text
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 0.6
    thickness = 2
    text = "Settings"
    (textWidth, textHeight), baseline = cv2.getTextSize(text, font, fontScale, thickness)
    textX = x + (buttonWidth - textWidth) // 2
    textY = y + (buttonHeight + textHeight) // 2
    cv2.putText(frame, text, (textX, textY), font, fontScale, (255, 255, 255), thickness)

    return (x, y, x + buttonWidth, y + buttonHeight)

def isPointInButton(x, y, buttonCoords):
    """Check if a point is within the button coordinates."""
    if buttonCoords is None:
        return False
    btnX1, btnY1, btnX2, btnY2 = buttonCoords
    return btnX1 <= x <= btnX2 and btnY1 <= y <= btnY2

# ============================================================================
# HELPER FUNCTIONS - CALIBRATION
# ============================================================================

def isCalibrated():
    """Check if system has been calibrated."""
    return (savedFaceZPos is not None and savedFaceYPos is not None and
            savedShoulderZPos is not None and savedShoulderYPos is not None and
            savedChestZPos is not None)

def calibrate(faceResults, poseResults):
    """Save current positions as calibration baseline with quality validation."""
    global savedFaceZPos, savedFaceYPos
    global savedShoulderZPos, savedShoulderYPos, savedChestZPos
    global savedShoulderAsymmetry, savedNeckAngle, savedShoulderForward
    global smoothedFaceToShoulderZ, smoothedFaceToShoulderY
    global smoothedRelativeShoulderZ, smoothedRelativeShoulderY
    global smoothedShoulderAsymmetry, smoothedHeadTilt, smoothedNeckAngle, smoothedShoulderForward

    # Validate calibration quality
    qualityScore, qualityIssues = validateCalibrationQuality(faceResults, poseResults)

    if qualityScore < 50:
        print(f"WARNING: Poor calibration quality ({qualityScore:.0f}%). Please ensure:")
        print("  - Face is fully visible")
        print("  - Shoulders are clearly visible")
        print("  - Good lighting conditions")
        for issue in qualityIssues:
            print(f"  - {issue}")
        print("Calibration may be inaccurate. Consider recalibrating.")
    elif qualityScore < 80:
        print(f"Calibration quality: {qualityScore:.0f}% (acceptable)")
        if qualityIssues:
            for issue in qualityIssues:
                print(f"  - {issue}")
    else:
        print(f"Calibration quality: {qualityScore:.0f}% (excellent)")

    # Save face reference position
    for fl in faceResults.multi_face_landmarks:
        if len(fl.landmark) > 1:
            savedFaceZPos, savedFaceYPos = calculateFacePosition(fl)
            break

    # Save shoulder and chest reference positions using multi-point estimation
    lm = poseResults.pose_landmarks.landmark
    leftShoulder = lm[11]
    rightShoulder = lm[12]
    leftEar = lm[7]
    rightEar = lm[8]
    leftElbow = lm[13]
    rightElbow = lm[14]
    leftHip = lm[23]
    rightHip = lm[24]

    # Use multi-point shoulder estimation
    shoulderPos = calculateStableShoulderPosition(
        leftShoulder, rightShoulder, leftEar, rightEar, leftElbow, rightElbow
    )

    if shoulderPos:
        savedShoulderZPos = shoulderPos[2]
        savedShoulderYPos = shoulderPos[1]
    else:
        # Fallback to direct average
        savedShoulderZPos = (leftShoulder.z + rightShoulder.z) / 2
        savedShoulderYPos = (leftShoulder.y + rightShoulder.y) / 2

    savedChestZPos = ((leftShoulder.z + rightShoulder.z) / 2 + (leftHip.z + rightHip.z) / 2) / 2

    # Save reference values for metrics
    savedShoulderAsymmetry = abs(leftShoulder.y - rightShoulder.y)

    # Save neck angle reference (using weighted Y component)
    if savedFaceYPos is not None and savedShoulderYPos is not None:
        neckDy = (savedFaceYPos - savedShoulderYPos) * headYWeight
        neckDz = abs(savedFaceZPos - savedShoulderZPos) + 0.001
        savedNeckAngle = math.atan2(neckDy, neckDz) * (180 / math.pi)

    # Shoulder forward now uses relative movement (no baseline needed)
    savedShoulderForward = None

    # Reset all smoothed values and history
    smoothedFaceToShoulderZ = 0.0
    smoothedFaceToShoulderY = 0.0
    smoothedRelativeShoulderZ = 0.0
    smoothedRelativeShoulderY = 0.0
    smoothedShoulderAsymmetry = 0.0
    smoothedHeadTilt = 0.0
    smoothedNeckAngle = 0.0
    smoothedShoulderForward = 0.0

    # Clear metric history for fresh start
    for key in metricHistory:
        metricHistory[key].clear()

    print(f"Reference positions saved (Quality: {qualityScore:.0f}%)")

# ============================================================================
# MOUSE CALLBACK FOR SETTINGS BUTTON
# ============================================================================

settingsButtonCoords = None
settingsMenuRequested = False

def mouseCallback(event, x, y, flags, param):
    """Handle mouse clicks for settings button."""
    global settingsButtonCoords, settingsMenuRequested

    if event == cv2.EVENT_LBUTTONDOWN:
        if isPointInButton(x, y, settingsButtonCoords):
            settingsMenuRequested = True

# ============================================================================
# MAIN LOOP
# ============================================================================

# Set up mouse callback
cv2.namedWindow("Posture")
cv2.setMouseCallback("Posture", mouseCallback, (0, 0))  # Will update with actual dimensions

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Frame skipping for performance - only process every Nth frame
    frameCounter += 1
    shouldProcess = (frameCounter % FRAME_SKIP_INTERVAL == 0)

    # Flip frame horizontally for mirror effect
    frame = cv2.flip(frame, 1)

    # Resize frame to increase window size (keep text size the same)
    h, w, _ = frame.shape
    newW = int(w * WINDOW_SCALE_FACTOR)
    newH = int(h * WINDOW_SCALE_FACTOR)
    frame = cv2.resize(frame, (newW, newH), interpolation=cv2.INTER_LINEAR)
    h, w = newH, newW

    # Process frame with MediaPipe (only if should process)

    faceResults = None
    poseResults = None

    if shouldProcess:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faceResults = face.process(rgb)
        poseResults = pose.process(rgb)
        # Cache results for display on skipped frames
        if faceResults:
            cachedFaceResults = faceResults
        if poseResults:
            cachedPoseResults = poseResults
    else:
        # Use cached results if not processing this frame (for display continuity)
        faceResults = cachedFaceResults
        poseResults = cachedPoseResults

    # ========================================================================
    # VISUALIZATION: Draw landmarks and guides
    # ========================================================================

    # Draw face mesh (green) - only if enabled in visual settings and we have results (prevents flashing)
    if VISUAL_SHOW_FACE_MESH and faceResults and faceResults.multi_face_landmarks:
        for fl in faceResults.multi_face_landmarks:
            mpDraw.draw_landmarks(
                frame, fl, mpFace.FACEMESH_CONTOURS,
                mpDraw.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1),
                mpDraw.DrawingSpec(color=(0, 255, 0), thickness=1)
            )

    # Extract and calculate pose landmarks
    # Use cached values if not processing this frame, otherwise calculate fresh
    if shouldProcess:
        currShoulderZ = None
        currShoulderY = None
        currChestZ = None
        leftShoulder = None
        rightShoulder = None
        leftEar = None
        rightEar = None
        leftElbow = None
        rightElbow = None
        leftHip = None
        rightHip = None
    else:
        # Use cached values when not processing
        currShoulderZ = cachedCurrShoulderZ
        currShoulderY = cachedCurrShoulderY
        currChestZ = cachedCurrChestZ
        leftShoulder = cachedLeftShoulder
        rightShoulder = cachedRightShoulder
        leftEar = None
        rightEar = None
        leftElbow = None
        rightElbow = None
        leftHip = None
        rightHip = None

    # Extract landmarks from results (either fresh or cached) - only when processing
    if shouldProcess and poseResults and poseResults.pose_landmarks:
        lm = poseResults.pose_landmarks.landmark
        leftShoulder = lm[11]
        rightShoulder = lm[12]
        leftEar = lm[7]
        rightEar = lm[8]
        leftElbow = lm[13]
        rightElbow = lm[14]
        leftHip = lm[23]
        rightHip = lm[24]

        # Calculate current positions using multi-point estimation
        shoulderPos = calculateStableShoulderPosition(
            leftShoulder, rightShoulder, leftEar, rightEar, leftElbow, rightElbow
        )

        if shoulderPos:
            currShoulderZ = shoulderPos[2]
            currShoulderY = shoulderPos[1]
        else:
            # Fallback to direct average
            currShoulderZ = (leftShoulder.z + rightShoulder.z) / 2
            currShoulderY = (leftShoulder.y + rightShoulder.y) / 2

        currChestZ = ((leftShoulder.z + rightShoulder.z) / 2 + (leftHip.z + rightHip.z) / 2) / 2

        # Cache pose data for display continuity
        cachedCurrShoulderZ = currShoulderZ
        cachedCurrShoulderY = currShoulderY
        cachedCurrChestZ = currChestZ
        cachedLeftShoulder = leftShoulder
        cachedRightShoulder = rightShoulder

        # Draw visual guides if enabled
        if SHOW_VISUAL_GUIDES and isCalibrated() and leftShoulder and rightShoulder:
            drawVisualGuides(frame, w, h, leftShoulder, rightShoulder, leftHip, rightHip,
                           leftEar, rightEar, leftElbow, rightElbow)

    # Draw shoulder visualization - unified logic for both processing and cached frames
    # Only draw if mesh is enabled and we have shoulder data
    if VISUAL_SHOW_FACE_MESH:
        drawShoulder = False
        drawLeftShoulder = None
        drawRightShoulder = None

        if shouldProcess and leftShoulder and rightShoulder:
            # Use fresh data from processing frame
            drawShoulder = True
            drawLeftShoulder = leftShoulder
            drawRightShoulder = rightShoulder
        elif not shouldProcess and cachedLeftShoulder and cachedRightShoulder:
            # Use cached data for non-processing frames
            drawShoulder = True
            drawLeftShoulder = cachedLeftShoulder
            drawRightShoulder = cachedRightShoulder

        if drawShoulder:
            lx, ly = int(drawLeftShoulder.x * w), int(drawLeftShoulder.y * h)
            rx, ry = int(drawRightShoulder.x * w), int(drawRightShoulder.y * h)
            cv2.circle(frame, (lx, ly), 8, (0, 0, 255), -1)
            cv2.circle(frame, (rx, ry), 8, (0, 0, 255), -1)
            cv2.line(frame, (lx, ly), (rx, ry), (0, 0, 255), 2)

    # ========================================================================
    # WELCOME SCREEN: Show if not calibrated
    # ========================================================================

    if not isCalibrated():
        displayWelcomeScreen(frame, h, w)

    # ========================================================================
    # POSTURE ANALYSIS: Calculate and display metrics
    # ========================================================================

    # Calculate metrics only when processing new frame
    if (shouldProcess and isCalibrated() and faceResults and faceResults.multi_face_landmarks and
        currShoulderZ is not None and currShoulderY is not None and currChestZ is not None):

        for fl in faceResults.multi_face_landmarks:
            if len(fl.landmark) > 1:
                # Calculate current face position
                currFaceZ, currFaceY = calculateFacePosition(fl)

                # Calculate all posture metrics
                metrics = calculatePostureMetrics(
                    currFaceZ, currFaceY, currShoulderZ, currShoulderY,
                    currChestZ, leftShoulder, rightShoulder, fl
                )

                # Scale, smooth, and display status and metric numbers
                scaleAndSmoothMetrics(metrics)
                break

    # Always display metrics (using cached/smoothed values) regardless of processing frame
    # Only show if enabled in visual settings
    if isCalibrated():
        if VISUAL_SHOW_STATUS:
            displayStatus(frame)
        if VISUAL_SHOW_METRICS:
            displayMetricNumbers(frame, w)

        # Check and send notifications for bad posture
        statuses = getPostureStatus()
        currentTime = time.time()
        checkAndNotifyPosture(statuses, currentTime)

    # ========================================================================
    # SETTINGS BUTTON
    # ========================================================================

    # Draw settings button
    settingsButtonCoords = drawSettingsButton(frame, w, h)

    # Check if settings menu should be opened
    if settingsMenuRequested:
        settingsMenuRequested = False
        # Store current frame for dimmed background and open settings menu
        currentFrameForSettings = frame.copy()
        settingsSaved = openSettingsMenu(currentFrameForSettings, w, h)
        # After settings menu closes, skip the stale frame and continue to next iteration
        # This prevents processing a frame that was captured before settings opened
        if settingsSaved:
            # Only reset frameCounter if settings were saved (to trigger fresh processing)
            # But skip the current stale frame first
            frameCounter = FRAME_SKIP_INTERVAL - 1  # Will trigger processing on next frame
        # Skip displaying the stale frame - continue to next loop iteration
        continue  # This skips the rest of the loop and gets a fresh frame

    # ========================================================================
    # DISPLAY AND INPUT HANDLING
    # ========================================================================

    cv2.imshow("Posture", frame)

    # Limit FPS for LOW and MEDIUM presets using waitKey timing
    # waitKey returns time in milliseconds, calculate delay needed
    if DISPLAY_FPS < 30:
        delay_ms = int(1000 / DISPLAY_FPS)  # Milliseconds per frame
        key = cv2.waitKey(delay_ms) & 0xFF
    else:
        key = cv2.waitKey(1) & 0xFF

    if key == 27:  # ESC key
        break
    elif key == ord('c') or key == ord('C'):  # Calibrate
        if faceResults and faceResults.multi_face_landmarks and poseResults and poseResults.pose_landmarks:
            calibrate(faceResults, poseResults)

# ============================================================================
# CLEANUP
# ============================================================================

cap.release()
cv2.destroyAllWindows()

