"""
Settings Menu file for Posture Detection Application

This file contains the tkinter-based settings menu GUI.
"""

import cv2
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class ToolTip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text='widget info'):
        self.waittime = 500  # milliseconds
        self.wraplength = 300  # pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        # Try to get widget bbox, fallback to widget position
        try:
            bbox = self.widget.bbox("insert")
            if bbox and len(bbox) >= 4:
                x, y, cx, cy = bbox
                x += self.widget.winfo_rootx() + 25
                y += cy + self.widget.winfo_rooty() + 20
            else:
                # Fallback to widget position
                x = self.widget.winfo_rootx() + 25
                y = self.widget.winfo_rooty() + 20
        except:
            # Fallback to widget position
            try:
                x = self.widget.winfo_rootx() + 25
                y = self.widget.winfo_rooty() + 20
            except:
                # Last resort
                x = 100
                y = 100

        # Creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.attributes('-topmost', True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("Arial", "9", "normal"), wraplength=self.wraplength, padx=5, pady=3)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()

def createToolTip(widget, text):
    """Create a tooltip for a widget."""
    toolTip = ToolTip(widget, text)
    return toolTip

def openSettingsMenu(frame, w, h):
    """Open tkinter settings menu with sidebar navigation and category pages."""
    # Import Posture here to avoid circular import
    import Posture
    
    # Create dimmed background overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    dimmedFrame = cv2.addWeighted(frame, 0.3, overlay, 0.7, 0)
    cv2.imshow("Posture", dimmedFrame)
    cv2.waitKey(1)

    # Create tkinter root window
    root = tk.Tk()
    root.title("Settings")
    root.resizable(False, False)

    # Center the window on screen
    windowWidth = 700
    windowHeight = 600
    screenWidth = root.winfo_screenwidth()
    screenHeight = root.winfo_screenheight()
    x = (screenWidth - windowWidth) // 2
    y = (screenHeight - windowHeight) // 2
    root.geometry(f"{windowWidth}x{windowHeight}+{x}+{y}")

    # Make window stay on top
    root.attributes('-topmost', True)

    # Store original values for cancel/revert
    original_perf_preset = Posture.PERFORMANCE_PRESET
    original_metric_preset = Posture.METRIC_PRESET_NAME
    original_metric_enable_values = {
        'slouching': Posture.METRIC_ENABLE_SLOUCHING,
        'uneven_shoulders': Posture.METRIC_ENABLE_UNEVEN_SHOULDERS,
        'head_tilt': Posture.METRIC_ENABLE_HEAD_TILT,
        'neck_forward': Posture.METRIC_ENABLE_NECK_FORWARD,
        'shoulders_forward': Posture.METRIC_ENABLE_SHOULDERS_FORWARD
    }
    original_perf_values = {
        'processing_fps': Posture.PROCESSING_FPS,
        'display_fps': Posture.DISPLAY_FPS,
        'model_complexity': Posture.MODEL_COMPLEXITY,
        'history_size': Posture.HISTORY_SIZE,
        'outlier_std_deviations': Posture.OUTLIER_STD_DEVIATIONS,
        'show_visual_guides': Posture.SHOW_VISUAL_GUIDES,
        'face_mesh_drawing_enabled': Posture.FACE_MESH_DRAWING_ENABLED,
        'face_landmark_count': len(Posture.FACE_LANDMARK_INDICES)
    }
    original_threshold_values = {
        'slouching': Posture.STATUS_THRESHOLD_SLOUCHING,
        'uneven_shoulders': Posture.STATUS_THRESHOLD_UNEVEN_SHOULDERS,
        'head_tilt': Posture.STATUS_THRESHOLD_HEAD_TILT,
        'neck_forward': Posture.STATUS_THRESHOLD_NECK_FORWARD,
        'shoulders_forward': Posture.STATUS_THRESHOLD_SHOULDERS_FORWARD
    }
    original_visual_values = {
        'show_face_mesh': Posture.VISUAL_SHOW_FACE_MESH,
        'show_metrics': Posture.VISUAL_SHOW_METRICS,
        'show_status': Posture.VISUAL_SHOW_STATUS
    }

    # Create main container
    mainContainer = ttk.Frame(root)
    mainContainer.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Create sidebar
    sidebar = ttk.Frame(mainContainer, width=150)
    sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
    sidebar.pack_propagate(False)

    # Title in sidebar
    titleLabel = ttk.Label(sidebar, text="Options", font=("Arial", 14, "bold"))
    titleLabel.pack(pady=(10, 20))

    # Category buttons
    categories = ["Metrics", "Performance Preset", "Metric Preset", "Visuals", "Notifications"]
    categoryVars = {}
    contentFrames = {}
    currentPage = tk.StringVar(value="Metrics")

    # Create scrollable content area
    scrollContainer = ttk.Frame(mainContainer)
    scrollContainer.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # Create canvas and scrollbar
    contentCanvas = tk.Canvas(scrollContainer, highlightthickness=0)
    scrollbar = ttk.Scrollbar(scrollContainer, orient=tk.VERTICAL, command=contentCanvas.yview)
    contentCanvas.configure(yscrollcommand=scrollbar.set)

    # Pack scrollbar and canvas
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    contentCanvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Create inner frame for content (this is what we scroll)
    contentArea = ttk.Frame(contentCanvas)
    contentWindow = contentCanvas.create_window((0, 0), window=contentArea, anchor=tk.NW)

    # Configure canvas scrolling
    def configureScrollRegion(event=None):
        contentCanvas.update_idletasks()
        contentCanvas.configure(scrollregion=contentCanvas.bbox("all"))

    def configureCanvasWidth(event):
        canvasWidth = event.width
        contentCanvas.itemconfig(contentWindow, width=canvasWidth)

    contentArea.bind('<Configure>', configureScrollRegion)
    contentCanvas.bind('<Configure>', configureCanvasWidth)

    # Enable mouse wheel scrolling
    def onMouseWheel(event):
        contentCanvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    contentCanvas.bind_all("<MouseWheel>", onMouseWheel)

    # Store variables
    metricVars = {}
    perfVars = {}
    metricThresholdVars = {}
    visualVars = {}

    # Description label at bottom (like in screenshot) - define early so switchPage can use it
    descFrame = ttk.Frame(root)
    descSeparator = ttk.Separator(descFrame, orient=tk.HORIZONTAL)
    descSeparator.pack(fill=tk.X, pady=(0, 5))
    descLabel = ttk.Label(descFrame, text="", font=("Arial", 9), foreground="gray")
    descLabel.pack(anchor=tk.W)

    def switchPage(page):
        """Switch to a different settings page."""
        currentPage.set(page)
        # Hide all content frames
        for frame in contentFrames.values():
            frame.pack_forget()
        # Show selected frame
        if page in contentFrames:
            contentFrames[page].pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # Update button states
        for cat, var in categoryVars.items():
            if cat == page:
                var.set(1)
            else:
                var.set(0)

        # Update description text
        descriptions = {
            "Metrics": "Select which posture metrics to track and display",
            "Performance Preset": "Adjust performance settings. Lower presets reduce CPU usage but may affect accuracy.",
            "Metric Preset": "Adjust metric sensitivity thresholds. Lower values = more sensitive (triggers earlier).",
            "Visuals": "Control what visual elements are displayed on the video feed. These settings are independent from performance presets."
        }
        descLabel.config(text=descriptions.get(page, ""))

        # Update scroll region after page switch
        contentCanvas.update_idletasks()
        contentCanvas.configure(scrollregion=contentCanvas.bbox("all"))
        # Scroll to top when switching pages
        contentCanvas.yview_moveto(0)

    # Create category buttons and pages
    for cat in categories:
        var = tk.IntVar(value=1 if cat == "Metrics" else 0)
        categoryVars[cat] = var
        btn = ttk.Radiobutton(sidebar, text=cat, variable=var, value=1,
                             command=lambda c=cat: switchPage(c), width=18)
        btn.pack(anchor=tk.W, pady=2, padx=5)

        # Create content frame for this category
        frame = ttk.Frame(contentArea)
        contentFrames[cat] = frame
        if cat == "Metrics":
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # ========================================================================
    # METRICS PAGE
    # ========================================================================
    metricsFrame = contentFrames["Metrics"]

    enableFrame = ttk.LabelFrame(metricsFrame, text="Enable Metrics", padding="15")
    enableFrame.pack(fill=tk.BOTH, expand=True)

    metricVars['enable_slouching'] = tk.BooleanVar(value=Posture.METRIC_ENABLE_SLOUCHING)
    metricVars['enable_uneven_shoulders'] = tk.BooleanVar(value=Posture.METRIC_ENABLE_UNEVEN_SHOULDERS)
    metricVars['enable_head_tilt'] = tk.BooleanVar(value=Posture.METRIC_ENABLE_HEAD_TILT)
    metricVars['enable_neck_forward'] = tk.BooleanVar(value=Posture.METRIC_ENABLE_NECK_FORWARD)
    metricVars['enable_shoulders_forward'] = tk.BooleanVar(value=Posture.METRIC_ENABLE_SHOULDERS_FORWARD)

    slouchingCB = ttk.Checkbutton(enableFrame, text="Slouching", variable=metricVars['enable_slouching'])
    slouchingCB.pack(anchor=tk.W, pady=8)
    createToolTip(slouchingCB, "Tracks when shoulders are forward or down. Detects slouching posture.")

    unevenShouldersCB = ttk.Checkbutton(enableFrame, text="Uneven Shoulders", variable=metricVars['enable_uneven_shoulders'])
    unevenShouldersCB.pack(anchor=tk.W, pady=8)
    createToolTip(unevenShouldersCB, "Detects when one shoulder is higher than the other. Helps identify shoulder misalignment.")

    headTiltCB = ttk.Checkbutton(enableFrame, text="Head Tilt", variable=metricVars['enable_head_tilt'])
    headTiltCB.pack(anchor=tk.W, pady=8)
    createToolTip(headTiltCB, "Monitors when your head tilts left or right. Useful for detecting neck strain or poor posture habits.")

    neckForwardCB = ttk.Checkbutton(enableFrame, text="Neck Forward", variable=metricVars['enable_neck_forward'])
    neckForwardCB.pack(anchor=tk.W, pady=8)
    createToolTip(neckForwardCB, "Detects forward head posture (text neck). Tracks when your head extends forward beyond your shoulders.")

    shouldersForwardCB = ttk.Checkbutton(enableFrame, text="Shoulders Forward", variable=metricVars['enable_shoulders_forward'])
    shouldersForwardCB.pack(anchor=tk.W, pady=8)
    createToolTip(shouldersForwardCB, "Tracks when shoulders are pushed forward, indicating rounded shoulders or forward posture.")

    # Description will be shown in bottom area

    # ========================================================================
    # PERFORMANCE PRESET PAGE
    # ========================================================================
    perfFrame = contentFrames["Performance Preset"]

    # Preset selection
    perfPresetFrame = ttk.LabelFrame(perfFrame, text="Preset Selection", padding="10")
    perfPresetFrame.pack(fill=tk.X, pady=(0, 10))

    availablePerfPresets = Posture.getAvailablePerformancePresets()
    if "Custom" not in availablePerfPresets:
        availablePerfPresets.append("Custom")
    # Check if current preset exists, otherwise default to Custom
    if Posture.PERFORMANCE_PRESET in ["LOW", "MEDIUM", "HIGH"] or Posture.PERFORMANCE_PRESET in availablePerfPresets:
        currentPerf = Posture.PERFORMANCE_PRESET
    else:
        currentPerf = "Custom"
    perfPresetVar = tk.StringVar(value=currentPerf)

    perfPresetCombo = ttk.Combobox(perfPresetFrame, textvariable=perfPresetVar,
                                   values=availablePerfPresets, state="readonly", width=25)
    perfPresetCombo.pack(anchor=tk.W, pady=5)
    createToolTip(perfPresetCombo, "Select a performance preset or choose 'Custom' to manually configure all settings. LOW: Minimal CPU usage, lower accuracy. MEDIUM: Balanced performance. HIGH: Maximum accuracy, higher CPU usage.")

    # Preset info display frame (for default presets - read-only)
    perfPresetInfoFrame = ttk.LabelFrame(perfFrame, text="Preset Values", padding="10")

    # Custom preset controls container
    perfCustomFrame = ttk.LabelFrame(perfFrame, text="Custom Performance Settings", padding="10")

    # Custom variable entries - initialize with current values (will be updated by preset if needed)
    perfVars['processing_fps'] = tk.DoubleVar(value=Posture.PROCESSING_FPS)
    perfVars['display_fps'] = tk.DoubleVar(value=Posture.DISPLAY_FPS)
    perfVars['model_complexity'] = tk.IntVar(value=Posture.MODEL_COMPLEXITY)
    perfVars['history_size'] = tk.IntVar(value=Posture.HISTORY_SIZE)
    perfVars['outlier_std_deviations'] = tk.DoubleVar(value=Posture.OUTLIER_STD_DEVIATIONS)
    perfVars['show_visual_guides'] = tk.BooleanVar(value=Posture.SHOW_VISUAL_GUIDES)
    perfVars['face_mesh_drawing_enabled'] = tk.BooleanVar(value=Posture.FACE_MESH_DRAWING_ENABLED)
    perfVars['face_landmark_count'] = tk.IntVar(value=len(Posture.FACE_LANDMARK_INDICES))

    # Create custom settings fields
    procFpsLabel = ttk.Label(perfCustomFrame, text="Processing FPS:")
    procFpsLabel.grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(procFpsLabel, "How many times per second the system processes video frames for Posture.pose detection. Lower values reduce CPU usage but may decrease responsiveness. Recommended: 15-30 for balanced performance.")

    procFpsSpinbox = ttk.Spinbox(perfCustomFrame, from_=1, to=60, textvariable=perfVars['processing_fps'], width=15)
    procFpsSpinbox.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(procFpsSpinbox, "How many times per second the system processes video frames for Posture.pose detection. Lower values reduce CPU usage but may decrease responsiveness. Recommended: 15-30 for balanced performance.")

    dispFpsLabel = ttk.Label(perfCustomFrame, text="Display FPS:")
    dispFpsLabel.grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(dispFpsLabel, "The frame rate at which the video feed is displayed. Lower values reduce GPU usage. Should match or be lower than Processing FPS for smooth display.")

    dispFpsSpinbox = ttk.Spinbox(perfCustomFrame, from_=1, to=60, textvariable=perfVars['display_fps'], width=15)
    dispFpsSpinbox.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(dispFpsSpinbox, "The frame rate at which the video feed is displayed. Lower values reduce GPU usage. Should match or be lower than Processing FPS for smooth display.")

    modelComplexityLabel = ttk.Label(perfCustomFrame, text="Model Complexity:")
    modelComplexityLabel.grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(modelComplexityLabel, "MediaPipe model complexity level (0-2). Higher values provide better accuracy but require more processing power. 0=Lightweight, 1=Balanced, 2=Heavy (most accurate).")

    modelComplexitySpinbox = ttk.Spinbox(perfCustomFrame, from_=0, to=2, textvariable=perfVars['model_complexity'], width=15)
    modelComplexitySpinbox.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(modelComplexitySpinbox, "MediaPipe model complexity level (0-2). Higher values provide better accuracy but require more processing power. 0=Lightweight, 1=Balanced, 2=Heavy (most accurate).")

    historySizeLabel = ttk.Label(perfCustomFrame, text="History Size:")
    historySizeLabel.grid(row=3, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(historySizeLabel, "Number of recent measurements stored for outlier detection and smoothing. Higher values provide better smoothing but use more memory. Recommended: 20-30 for good balance.")

    historySizeSpinbox = ttk.Spinbox(perfCustomFrame, from_=5, to=50, textvariable=perfVars['history_size'], width=15)
    historySizeSpinbox.grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(historySizeSpinbox, "Number of recent measurements stored for outlier detection and smoothing. Higher values provide better smoothing but use more memory. Recommended: 20-30 for good balance.")

    outlierStdLabel = ttk.Label(perfCustomFrame, text="Outlier Standard Deviations:")
    outlierStdLabel.grid(row=4, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(outlierStdLabel, "Standard deviation threshold for outlier detection. Values beyond this threshold are filtered out as noise. Higher values (3.0-4.0) are more lenient, lower values (2.0-2.5) filter more aggressively.")

    outlierStdSpinbox = ttk.Spinbox(perfCustomFrame, from_=1.0, to=5.0, increment=0.1, textvariable=perfVars['outlier_std_deviations'], width=15)
    outlierStdSpinbox.grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(outlierStdSpinbox, "Standard deviation threshold for outlier detection. Values beyond this threshold are filtered out as noise. Higher values (3.0-4.0) are more lenient, lower values (2.0-2.5) filter more aggressively.")

    faceLandmarkLabel = ttk.Label(perfCustomFrame, text="Face Landmark Count:")
    faceLandmarkLabel.grid(row=5, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(faceLandmarkLabel, "Number of facial landmarks used for tracking. More landmarks provide better accuracy but increase CPU usage. Range: 5-40. Recommended: 20 for balanced performance, 40 for maximum accuracy.")

    faceLandmarkSpinbox = ttk.Spinbox(perfCustomFrame, from_=5, to=40, textvariable=perfVars['face_landmark_count'], width=15)
    faceLandmarkSpinbox.grid(row=5, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(faceLandmarkSpinbox, "Number of facial landmarks used for tracking. More landmarks provide better accuracy but increase CPU usage. Range: 5-40. Recommended: 20 for balanced performance, 40 for maximum accuracy.")

    visualGuidesCB = ttk.Checkbutton(perfCustomFrame, text="Show Visual Guides", variable=perfVars['show_visual_guides'])
    visualGuidesCB.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=5, padx=5)
    createToolTip(visualGuidesCB, "Shows visual reference lines and guides on the video feed to help you maintain proper posture. Disable for a cleaner view.")

    faceMeshCB = ttk.Checkbutton(perfCustomFrame, text="Draw Face Mesh", variable=perfVars['face_mesh_drawing_enabled'])
    faceMeshCB.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=5, padx=5)
    createToolTip(faceMeshCB, "Draws the Posture.face mesh overlay on the video feed. Useful for debugging but can be distracting. Keep enabled for visual feedback.")

    # Save custom preset button (inside Custom frame)
    perfCustomBtnFrame = ttk.Frame(perfCustomFrame)
    perfCustomBtnFrame.grid(row=8, column=0, columnspan=2, pady=10)

    perfSaveNameVar = tk.StringVar(value="")
    perfSaveNameEntry = ttk.Entry(perfCustomBtnFrame, textvariable=perfSaveNameVar, width=15)
    perfSaveNameEntry.pack(side=tk.LEFT, padx=2)

    perfSaveBtn = ttk.Button(perfCustomBtnFrame, text="Save Preset", width=12)
    perfSaveBtn.pack(side=tk.LEFT, padx=2)

    # Edit/Delete buttons (outside Custom frame - for custom presets only)
    perfEditDeleteFrame = ttk.Frame(perfFrame)
    perfEditDeleteFrame.pack(fill=tk.X, pady=(0, 10))

    perfEditBtn = ttk.Button(perfEditDeleteFrame, text="Edit Preset", width=12, state=tk.DISABLED)
    perfEditBtn.pack(side=tk.LEFT, padx=2)

    perfDeleteBtn = ttk.Button(perfEditDeleteFrame, text="Delete Preset", width=12, state=tk.DISABLED)
    perfDeleteBtn.pack(side=tk.LEFT, padx=2)

    def savePerfCustomPreset():
        name = perfSaveNameVar.get().strip()
        if not name:
            tk.messagebox.showwarning("Warning", "Please enter a preset name")
            return

        if name in ["LOW", "MEDIUM", "HIGH", "Custom"]:
            tk.messagebox.showwarning("Warning", "Cannot use system preset names")
            return

        presetData = {
            "processing_fps": perfVars['processing_fps'].get(),
            "display_fps": perfVars['display_fps'].get(),
            "frame_skip_interval": max(1, int(30 / perfVars['processing_fps'].get())),
            "model_complexity": perfVars['model_complexity'].get(),
            "history_size": perfVars['history_size'].get(),
            "outlier_std_deviations": perfVars['outlier_std_deviations'].get(),
            "show_visual_guides": perfVars['show_visual_guides'].get(),
            "face_mesh_drawing_enabled": perfVars['face_mesh_drawing_enabled'].get(),
            "face_landmark_count": perfVars['face_landmark_count'].get()
        }

        # Check if updating existing preset
        action = "updated" if name in Posture.getAvailablePerformancePresets() else "saved"

        if Posture.saveCustomPerformancePreset(name, presetData):
            # Update combo box - reload list and set selection
            availablePerfPresets = Posture.getAvailablePerformancePresets()
            if "Custom" not in availablePerfPresets:
                availablePerfPresets.append("Custom")
            perfPresetCombo['values'] = availablePerfPresets
            perfPresetVar.set(name)
            perfSaveNameVar.set("")
            # Switch to the saved preset (show info frame) and re-enable buttons
            onPerfPresetChange()
            tk.messagebox.showinfo("Success", f"Preset '{name}' {action}")
        else:
            tk.messagebox.showerror("Error", "Failed to save preset")

    def editPerfCustomPreset():
        current = perfPresetVar.get()
        if current in ["LOW", "MEDIUM", "HIGH", "Custom"]:
            tk.messagebox.showwarning("Warning", "Cannot edit system presets. Select a custom preset first.")
            return

        # Load the preset values into custom frame
        perfPresetVar.set("Custom")
        perfCustomFrame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        perfPresetInfoFrame.pack_forget()
        perfEditBtn.config(state=tk.DISABLED)  # Disable while editing
        perfDeleteBtn.config(state=tk.DISABLED)

        # Load preset values into UI
        presetsData = Posture.loadPerformancePresets()
        if current in presetsData["presets"]:
            preset = presetsData["presets"][current]
            perfUpdatingPreset[0] = True
            perfVars['processing_fps'].set(preset["processing_fps"])
            perfVars['display_fps'].set(preset["display_fps"])
            perfVars['model_complexity'].set(preset["model_complexity"])
            perfVars['history_size'].set(preset["history_size"])
            perfVars['outlier_std_deviations'].set(preset["outlier_std_deviations"])
            perfVars['show_visual_guides'].set(preset["show_visual_guides"])
            perfVars['face_mesh_drawing_enabled'].set(preset["face_mesh_drawing_enabled"])
            perfVars['face_landmark_count'].set(preset["face_landmark_count"])
            perfUpdatingPreset[0] = False
            # Set the name entry to current preset name for editing
            perfSaveNameVar.set(current)

    def deletePerfCustomPreset():
        current = perfPresetVar.get()
        if current in ["LOW", "MEDIUM", "HIGH", "Custom"]:
            tk.messagebox.showwarning("Warning", "Cannot delete system presets")
            return

        if tk.messagebox.askyesno("Confirm", f"Delete preset '{current}'?"):
            if Posture.deletePerformancePreset(current):
                # Reload available presets
                availablePerfPresets = Posture.getAvailablePerformancePresets()
                if "Custom" not in availablePerfPresets:
                    availablePerfPresets.append("Custom")
                perfPresetCombo['values'] = availablePerfPresets
                # Switch to MEDIUM preset
                perfPresetVar.set("MEDIUM")
                onPerfPresetChange()
                tk.messagebox.showinfo("Success", "Preset deleted")
            else:
                tk.messagebox.showerror("Error", "Failed to delete preset")

    perfSaveBtn.config(command=savePerfCustomPreset)
    createToolTip(perfSaveBtn, "Save the current custom performance settings as a new preset. Enter a name in the text field first. If saving with an existing preset name, it will update that preset.")

    perfEditBtn.config(command=editPerfCustomPreset)
    createToolTip(perfEditBtn, "Edit the currently selected custom preset. Only available for user-created presets, not system presets (LOW, MEDIUM, HIGH).")

    perfDeleteBtn.config(command=deletePerfCustomPreset)
    createToolTip(perfDeleteBtn, "Delete the currently selected custom preset. Only available for user-created presets. System presets cannot be deleted.")

    # Flag to prevent infinite loops when updating values (use list for mutable reference)
    perfUpdatingPreset = [False]

    def onPerfVarChange(*args):
        """Called when any performance variable changes - auto-switch to Custom if not matching a preset."""
        if perfUpdatingPreset[0]:
            return
        if perfPresetVar.get() != "Custom":
            perfPresetVar.set("Custom")
            perfCustomFrame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    # Bind change events to auto-switch to Custom
    for varKey in perfVars:
        perfVars[varKey].trace_add('write', lambda *args, vk=varKey: onPerfVarChange())

    # Preset info labels (will be updated dynamically)
    perfInfoLabels = {}

    def updatePerfPresetInfo(presetData):
        """Update the preset info display frame with preset values."""
        # Clear existing labels
        for widget in perfPresetInfoFrame.winfo_children():
            widget.destroy()
        perfInfoLabels.clear()

        row = 0
        perfInfoLabels['processing_fps'] = ttk.Label(perfPresetInfoFrame, text=f"Processing FPS: {presetData['processing_fps']}")
        perfInfoLabels['processing_fps'].grid(row=row, column=0, sticky=tk.W, pady=3, padx=5)
        row += 1

        perfInfoLabels['display_fps'] = ttk.Label(perfPresetInfoFrame, text=f"Display FPS: {presetData['display_fps']}")
        perfInfoLabels['display_fps'].grid(row=row, column=0, sticky=tk.W, pady=3, padx=5)
        row += 1

        perfInfoLabels['model_complexity'] = ttk.Label(perfPresetInfoFrame, text=f"Model Complexity: {presetData['model_complexity']}")
        perfInfoLabels['model_complexity'].grid(row=row, column=0, sticky=tk.W, pady=3, padx=5)
        row += 1

        perfInfoLabels['history_size'] = ttk.Label(perfPresetInfoFrame, text=f"History Size: {presetData['history_size']}")
        perfInfoLabels['history_size'].grid(row=row, column=0, sticky=tk.W, pady=3, padx=5)
        row += 1

        perfInfoLabels['outlier_std_deviations'] = ttk.Label(perfPresetInfoFrame, text=f"Outlier Std Deviations: {presetData['outlier_std_deviations']}")
        perfInfoLabels['outlier_std_deviations'].grid(row=row, column=0, sticky=tk.W, pady=3, padx=5)
        row += 1

        perfInfoLabels['face_landmark_count'] = ttk.Label(perfPresetInfoFrame, text=f"Face Landmark Count: {presetData['face_landmark_count']}")
        perfInfoLabels['face_landmark_count'].grid(row=row, column=0, sticky=tk.W, pady=3, padx=5)
        row += 1

        perfInfoLabels['show_visual_guides'] = ttk.Label(perfPresetInfoFrame, text=f"Show Visual Guides: {'Yes' if presetData['show_visual_guides'] else 'No'}")
        perfInfoLabels['show_visual_guides'].grid(row=row, column=0, sticky=tk.W, pady=3, padx=5)
        row += 1

        perfInfoLabels['face_mesh_drawing_enabled'] = ttk.Label(perfPresetInfoFrame, text=f"Draw Face Mesh: {'Yes' if presetData['face_mesh_drawing_enabled'] else 'No'}")
        perfInfoLabels['face_mesh_drawing_enabled'].grid(row=row, column=0, sticky=tk.W, pady=3, padx=5)

    def onPerfPresetChange(event=None):
        selected = perfPresetVar.get()
        isCustomPreset = selected not in ["LOW", "MEDIUM", "HIGH", "Custom"]

        # Enable/disable Edit and Delete buttons based on preset type
        perfEditBtn.config(state=tk.NORMAL if isCustomPreset else tk.DISABLED)
        perfDeleteBtn.config(state=tk.NORMAL if isCustomPreset else tk.DISABLED)

        if selected == "Custom":
            perfCustomFrame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            perfPresetInfoFrame.pack_forget()
            perfSaveNameVar.set("")
            # If switching to Custom, keep current values in the UI
        elif selected in ["LOW", "MEDIUM", "HIGH"]:
            perfCustomFrame.pack_forget()
            perfPresetInfoFrame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            perfUpdatingPreset[0] = True
            # Use hardcoded preset values and display them
            if selected == "LOW":
                presetData = {
                    "processing_fps": 5,
                    "display_fps": 5,
                    "model_complexity": 0,
                    "history_size": 10,
                    "outlier_std_deviations": 2.5,
                    "show_visual_guides": False,
                    "face_mesh_drawing_enabled": True,
                    "face_landmark_count": 5
                }
            elif selected == "MEDIUM":
                presetData = {
                    "processing_fps": 15,
                    "display_fps": 15,
                    "model_complexity": 1,
                    "history_size": 20,
                    "outlier_std_deviations": 3.0,
                    "show_visual_guides": True,
                    "face_mesh_drawing_enabled": True,
                    "face_landmark_count": 20
                }
            elif selected == "HIGH":
                presetData = {
                    "processing_fps": 30,
                    "display_fps": 30,
                    "model_complexity": 2,
                    "history_size": 30,
                    "outlier_std_deviations": 3.0,
                    "show_visual_guides": True,
                    "face_mesh_drawing_enabled": True,
                    "face_landmark_count": 40
                }
            # Update UI variables and display
            perfVars['processing_fps'].set(presetData["processing_fps"])
            perfVars['display_fps'].set(presetData["display_fps"])
            perfVars['model_complexity'].set(presetData["model_complexity"])
            perfVars['history_size'].set(presetData["history_size"])
            perfVars['outlier_std_deviations'].set(presetData["outlier_std_deviations"])
            perfVars['show_visual_guides'].set(presetData["show_visual_guides"])
            perfVars['face_mesh_drawing_enabled'].set(presetData["face_mesh_drawing_enabled"])
            perfVars['face_landmark_count'].set(presetData["face_landmark_count"])
            updatePerfPresetInfo(presetData)
            perfUpdatingPreset[0] = False
        else:
            # Custom preset selected - show its values in info frame
            perfCustomFrame.pack_forget()
            perfPresetInfoFrame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            perfUpdatingPreset[0] = True
            # Load preset values from file into UI variables
            presetsData = Posture.loadPerformancePresets()
            if selected in presetsData["presets"]:
                preset = presetsData["presets"][selected]
                perfVars['processing_fps'].set(preset["processing_fps"])
                perfVars['display_fps'].set(preset["display_fps"])
                perfVars['model_complexity'].set(preset["model_complexity"])
                perfVars['history_size'].set(preset["history_size"])
                perfVars['outlier_std_deviations'].set(preset["outlier_std_deviations"])
                perfVars['show_visual_guides'].set(preset["show_visual_guides"])
                perfVars['face_mesh_drawing_enabled'].set(preset["face_mesh_drawing_enabled"])
                perfVars['face_landmark_count'].set(preset["face_landmark_count"])
                # Display preset values
                updatePerfPresetInfo(preset)
            perfUpdatingPreset[0] = False

    perfPresetCombo.bind('<<ComboboxSelected>>', onPerfPresetChange)
    # Initial load
    onPerfPresetChange()  # Show/hide Custom frame and load values

    # ========================================================================
    # METRIC PRESET PAGE
    # ========================================================================
    metricPresetFrame = contentFrames["Metric Preset"]

    # Preset selection
    metricPresetSelectFrame = ttk.LabelFrame(metricPresetFrame, text="Preset Selection", padding="10")
    metricPresetSelectFrame.pack(fill=tk.X, pady=(0, 10))

    availableMetricPresets = Posture.getAvailableMetricPresets()
    if "Custom" not in availableMetricPresets:
        availableMetricPresets.append("Custom")
    # Check if current preset exists, otherwise default to Custom
    if Posture.METRIC_PRESET_NAME in availableMetricPresets:
        current_metric = Posture.METRIC_PRESET_NAME
    else:
        current_metric = "Custom"
    metricPresetSelectVar = tk.StringVar(value=current_metric)

    metricPresetSelectCombo = ttk.Combobox(metricPresetSelectFrame, textvariable=metricPresetSelectVar,
                                          values=availableMetricPresets, state="readonly", width=25)
    metricPresetSelectCombo.pack(anchor=tk.W, pady=5)
    createToolTip(metricPresetSelectCombo, "Select a metric sensitivity preset or choose 'Custom' to manually set thresholds. Default: Balanced sensitivity. Sensitive: Triggers alerts more easily. Relaxed: Requires more severe posture issues to trigger.")

    # Preset info display frame (for default presets - read-only)
    metricPresetInfoFrame = ttk.LabelFrame(metricPresetFrame, text="Preset Values", padding="10")

    # Custom threshold controls container
    metricCustomFrame = ttk.LabelFrame(metricPresetFrame, text="Custom Metric Thresholds", padding="10")

    # Custom threshold entries
    metricThresholdVars['slouching'] = tk.DoubleVar(value=Posture.STATUS_THRESHOLD_SLOUCHING)
    metricThresholdVars['uneven_shoulders'] = tk.DoubleVar(value=Posture.STATUS_THRESHOLD_UNEVEN_SHOULDERS)
    metricThresholdVars['head_tilt'] = tk.DoubleVar(value=Posture.STATUS_THRESHOLD_HEAD_TILT)
    metricThresholdVars['neck_forward'] = tk.DoubleVar(value=Posture.STATUS_THRESHOLD_NECK_FORWARD)
    metricThresholdVars['shoulders_forward'] = tk.DoubleVar(value=Posture.STATUS_THRESHOLD_SHOULDERS_FORWARD)

    # Create custom threshold fields
    slouchingLabel = ttk.Label(metricCustomFrame, text="Slouching:")
    slouchingLabel.grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(slouchingLabel, "Threshold for slouching detection. Lower values trigger alerts more easily (more sensitive). Higher values require more severe slouching to trigger. Range: 0-1000. Default: 400. Sensitive: 300. Relaxed: 500.")

    slouchingSpinbox = ttk.Spinbox(metricCustomFrame, from_=0, to=1000, textvariable=metricThresholdVars['slouching'], width=15)
    slouchingSpinbox.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(slouchingSpinbox, "Threshold for slouching detection. Lower values trigger alerts more easily (more sensitive). Higher values require more severe slouching to trigger. Range: 0-1000. Default: 400. Sensitive: 300. Relaxed: 500.")

    unevenShouldersLabel = ttk.Label(metricCustomFrame, text="Uneven Shoulders:")
    unevenShouldersLabel.grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(unevenShouldersLabel, "Threshold for detecting shoulder height difference. Lower values detect smaller differences (more sensitive). Range: 0-500. Default: 150. Sensitive: 100. Relaxed: 200.")

    unevenShouldersSpinbox = ttk.Spinbox(metricCustomFrame, from_=0, to=500, textvariable=metricThresholdVars['uneven_shoulders'], width=15)
    unevenShouldersSpinbox.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(unevenShouldersSpinbox, "Threshold for detecting shoulder height difference. Lower values detect smaller differences (more sensitive). Range: 0-500. Default: 150. Sensitive: 100. Relaxed: 200.")

    headTiltLabel = ttk.Label(metricCustomFrame, text="Head Tilt:")
    headTiltLabel.grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(headTiltLabel, "Maximum head tilt angle (in degrees) before triggering an alert. Lower values detect smaller tilts (more sensitive). Range: 0-90. Default: 10. Sensitive: 5. Relaxed: 15.")

    headTiltSpinbox = ttk.Spinbox(metricCustomFrame, from_=0, to=90, textvariable=metricThresholdVars['head_tilt'], width=15)
    headTiltSpinbox.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(headTiltSpinbox, "Maximum head tilt angle (in degrees) before triggering an alert. Lower values detect smaller tilts (more sensitive). Range: 0-90. Default: 10. Sensitive: 5. Relaxed: 15.")

    neckForwardLabel = ttk.Label(metricCustomFrame, text="Neck Forward:")
    neckForwardLabel.grid(row=3, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(neckForwardLabel, "Threshold for forward head posture (text neck) detection. Lower values trigger sooner (more sensitive). Range: 0-180. Default: 30. Sensitive: 20. Relaxed: 40.")

    neckForwardSpinbox = ttk.Spinbox(metricCustomFrame, from_=0, to=180, textvariable=metricThresholdVars['neck_forward'], width=15)
    neckForwardSpinbox.grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(neckForwardSpinbox, "Threshold for forward head posture (text neck) detection. Lower values trigger sooner (more sensitive). Range: 0-180. Default: 30. Sensitive: 20. Relaxed: 40.")

    shouldersForwardLabel = ttk.Label(metricCustomFrame, text="Shoulders Forward:")
    shouldersForwardLabel.grid(row=4, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(shouldersForwardLabel, "Threshold for detecting forward shoulder posture. Lower values trigger alerts more easily (more sensitive). Range: 0-1000. Default: 400. Sensitive: 300. Relaxed: 500.")

    shouldersForwardSpinbox = ttk.Spinbox(metricCustomFrame, from_=0, to=1000, textvariable=metricThresholdVars['shoulders_forward'], width=15)
    shouldersForwardSpinbox.grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(shouldersForwardSpinbox, "Threshold for detecting forward shoulder posture. Lower values trigger alerts more easily (more sensitive). Range: 0-1000. Default: 400. Sensitive: 300. Relaxed: 500.")

    # Save custom preset button (inside Custom frame)
    metricCustomBtnFrame = ttk.Frame(metricCustomFrame)
    metricCustomBtnFrame.grid(row=5, column=0, columnspan=2, pady=10)

    metricSaveNameVar = tk.StringVar(value="")
    metricSaveNameEntry = ttk.Entry(metricCustomBtnFrame, textvariable=metricSaveNameVar, width=15)
    metricSaveNameEntry.pack(side=tk.LEFT, padx=2)

    metricSaveBtn = ttk.Button(metricCustomBtnFrame, text="Save Preset", width=12)
    metricSaveBtn.pack(side=tk.LEFT, padx=2)

    # Edit/Delete buttons (outside Custom frame - for custom presets only)
    metricEditDeleteFrame = ttk.Frame(metricPresetFrame)
    metricEditDeleteFrame.pack(fill=tk.X, pady=(0, 10))

    metricEditBtn = ttk.Button(metricEditDeleteFrame, text="Edit Preset", width=12, state=tk.DISABLED)
    metricEditBtn.pack(side=tk.LEFT, padx=2)

    metricDeleteBtn = ttk.Button(metricEditDeleteFrame, text="Delete Preset", width=12, state=tk.DISABLED)
    metricDeleteBtn.pack(side=tk.LEFT, padx=2)

    def saveMetricCustomPreset():
        name = metricSaveNameVar.get().strip()
        if not name:
            tk.messagebox.showwarning("Warning", "Please enter a preset name")
            return
        if name in ["Default", "Sensitive", "Relaxed", "Custom"]:
            tk.messagebox.showwarning("Warning", "Cannot use system preset names")
            return

        presetData = {
            "slouching": metricThresholdVars['slouching'].get(),
            "uneven_shoulders": metricThresholdVars['uneven_shoulders'].get(),
            "head_tilt": metricThresholdVars['head_tilt'].get(),
            "neck_forward": metricThresholdVars['neck_forward'].get(),
            "shoulders_forward": metricThresholdVars['shoulders_forward'].get()
        }

        # Check if updating existing preset
        action = "updated" if name in Posture.getAvailableMetricPresets() else "saved"

        if Posture.saveCustomMetricPreset(name, presetData):
            # Update combo box - reload list and set selection
            availableMetricPresets = Posture.getAvailableMetricPresets()
            if "Custom" not in availableMetricPresets:
                availableMetricPresets.append("Custom")
            metricPresetSelectCombo['values'] = availableMetricPresets
            metricPresetSelectVar.set(name)
            metricSaveNameVar.set("")
            # Switch to the saved preset (show info frame) and re-enable buttons
            onMetricPresetChange()
            tk.messagebox.showinfo("Success", f"Preset '{name}' {action}")
        else:
            tk.messagebox.showerror("Error", "Failed to save preset")

    def editMetricCustomPreset():
        current = metricPresetSelectVar.get()
        if current in ["Default", "Sensitive", "Relaxed", "Custom"]:
            tk.messagebox.showwarning("Warning", "Cannot edit system presets. Select a custom preset first.")
            return

        # Load the preset values into custom frame
        metricPresetSelectVar.set("Custom")
        metricCustomFrame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        metricPresetInfoFrame.pack_forget()
        metricEditBtn.config(state=tk.DISABLED)  # Disable while editing
        metricDeleteBtn.config(state=tk.DISABLED)

        # Load preset values into UI
        presetsData = Posture.loadMetricPresets()
        if current in presetsData["presets"]:
            preset = presetsData["presets"][current]
            metricUpdatingPreset[0] = True
            metricThresholdVars['slouching'].set(preset["slouching"])
            metricThresholdVars['uneven_shoulders'].set(preset["uneven_shoulders"])
            metricThresholdVars['head_tilt'].set(preset["head_tilt"])
            metricThresholdVars['neck_forward'].set(preset["neck_forward"])
            metricThresholdVars['shoulders_forward'].set(preset["shoulders_forward"])
            metricUpdatingPreset[0] = False
            # Set the name entry to current preset name for editing
            metricSaveNameVar.set(current)

    def deleteMetricCustomPreset():
        current = metricPresetSelectVar.get()
        if current in ["Default", "Sensitive", "Relaxed", "Custom"]:
            tk.messagebox.showwarning("Warning", "Cannot delete system presets")
            return

        if tk.messagebox.askyesno("Confirm", f"Delete preset '{current}'?"):
            if Posture.deleteMetricPreset(current):
                # Reload available presets
                availableMetricPresets = Posture.getAvailableMetricPresets()
                if "Custom" not in availableMetricPresets:
                    availableMetricPresets.append("Custom")
                metricPresetSelectCombo['values'] = availableMetricPresets
                # Switch to Default preset
                metricPresetSelectVar.set("Default")
                onMetricPresetChange()
                tk.messagebox.showinfo("Success", "Preset deleted")
            else:
                tk.messagebox.showerror("Error", "Failed to delete preset")

    metricSaveBtn.config(command=saveMetricCustomPreset)
    createToolTip(metricSaveBtn, "Save the current custom metric thresholds as a new preset. Enter a name in the text field first. If saving with an existing preset name, it will update that preset.")

    metricEditBtn.config(command=editMetricCustomPreset)
    createToolTip(metricEditBtn, "Edit the currently selected custom preset. Only available for user-created presets, not system presets (Default, Sensitive, Relaxed).")

    metricDeleteBtn.config(command=deleteMetricCustomPreset)
    createToolTip(metricDeleteBtn, "Delete the currently selected custom preset. Only available for user-created presets. System presets cannot be deleted.")

    # Flag to prevent infinite loops when updating values (use list for mutable reference)
    metricUpdatingPreset = [False]

    def onMetricVarChange(*args):
        """Called when any metric threshold variable changes - auto-switch to Custom."""
        if metricUpdatingPreset[0]:
            return
        if metricPresetSelectVar.get() != "Custom":
            metricPresetSelectVar.set("Custom")
            metricCustomFrame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    # Bind change events to auto-switch to Custom
    for varKey in metricThresholdVars:
        metricThresholdVars[varKey].trace_add('write', lambda *args, vk=varKey: onMetricVarChange())

    # Preset info labels (will be updated dynamically)
    metricInfoLabels = {}

    def updateMetricPresetInfo(presetData):
        """Update the metric preset info display frame with preset values."""
        # Clear existing labels
        for widget in metricPresetInfoFrame.winfo_children():
            widget.destroy()
        metricInfoLabels.clear()

        row = 0
        metricInfoLabels['slouching'] = ttk.Label(metricPresetInfoFrame, text=f"Slouching: {presetData['slouching']}")
        metricInfoLabels['slouching'].grid(row=row, column=0, sticky=tk.W, pady=3, padx=5)
        row += 1

        metricInfoLabels['uneven_shoulders'] = ttk.Label(metricPresetInfoFrame, text=f"Uneven Shoulders: {presetData['uneven_shoulders']}")
        metricInfoLabels['uneven_shoulders'].grid(row=row, column=0, sticky=tk.W, pady=3, padx=5)
        row += 1

        metricInfoLabels['head_tilt'] = ttk.Label(metricPresetInfoFrame, text=f"Head Tilt: {presetData['head_tilt']}")
        metricInfoLabels['head_tilt'].grid(row=row, column=0, sticky=tk.W, pady=3, padx=5)
        row += 1

        metricInfoLabels['neck_forward'] = ttk.Label(metricPresetInfoFrame, text=f"Neck Forward: {presetData['neck_forward']}")
        metricInfoLabels['neck_forward'].grid(row=row, column=0, sticky=tk.W, pady=3, padx=5)
        row += 1

        metricInfoLabels['shoulders_forward'] = ttk.Label(metricPresetInfoFrame, text=f"Shoulders Forward: {presetData['shoulders_forward']}")
        metricInfoLabels['shoulders_forward'].grid(row=row, column=0, sticky=tk.W, pady=3, padx=5)

    def onMetricPresetChange(event=None):
        selected = metricPresetSelectVar.get()
        isCustomPreset = selected not in ["Default", "Sensitive", "Relaxed", "Custom"]

        # Enable/disable Edit and Delete buttons based on preset type
        metricEditBtn.config(state=tk.NORMAL if isCustomPreset else tk.DISABLED)
        metricDeleteBtn.config(state=tk.NORMAL if isCustomPreset else tk.DISABLED)

        if selected == "Custom":
            metricCustomFrame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            metricPresetInfoFrame.pack_forget()
            metricSaveNameVar.set("")
            # If switching to Custom, keep current values in the UI
        elif selected in ["Default", "Sensitive", "Relaxed"]:
            metricCustomFrame.pack_forget()
            metricPresetInfoFrame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            metricUpdatingPreset[0] = True
            # Use hardcoded preset values and display them
            if selected == "Default":
                presetData = {
                    "slouching": 400.0,
                    "uneven_shoulders": 150.0,
                    "head_tilt": 10.0,
                    "neck_forward": 30.0,
                    "shoulders_forward": 400.0
                }
            elif selected == "Sensitive":
                presetData = {
                    "slouching": 300.0,
                    "uneven_shoulders": 100.0,
                    "head_tilt": 5.0,
                    "neck_forward": 20.0,
                    "shoulders_forward": 300.0
                }
            elif selected == "Relaxed":
                presetData = {
                    "slouching": 500.0,
                    "uneven_shoulders": 200.0,
                    "head_tilt": 15.0,
                    "neck_forward": 40.0,
                    "shoulders_forward": 500.0
                }
            # Update UI variables and display
            metricThresholdVars['slouching'].set(presetData["slouching"])
            metricThresholdVars['uneven_shoulders'].set(presetData["uneven_shoulders"])
            metricThresholdVars['head_tilt'].set(presetData["head_tilt"])
            metricThresholdVars['neck_forward'].set(presetData["neck_forward"])
            metricThresholdVars['shoulders_forward'].set(presetData["shoulders_forward"])
            updateMetricPresetInfo(presetData)
            metricUpdatingPreset[0] = False
        else:
            # Custom preset selected - show its values in info frame
            metricCustomFrame.pack_forget()
            metricPresetInfoFrame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            metricUpdatingPreset[0] = True
            # Load preset values from file into UI variables
            presetsData = Posture.loadMetricPresets()
            if selected in presetsData["presets"]:
                preset = presetsData["presets"][selected]
                metricThresholdVars['slouching'].set(preset["slouching"])
                metricThresholdVars['uneven_shoulders'].set(preset["uneven_shoulders"])
                metricThresholdVars['head_tilt'].set(preset["head_tilt"])
                metricThresholdVars['neck_forward'].set(preset["neck_forward"])
                metricThresholdVars['shoulders_forward'].set(preset["shoulders_forward"])
                # Display preset values
                updateMetricPresetInfo(preset)
            metricUpdatingPreset[0] = False

    metricPresetSelectCombo.bind('<<ComboboxSelected>>', onMetricPresetChange)
    # Initial load
    onMetricPresetChange()  # Show/hide Custom/Info frame and load values


    # ========================================================================
    # VISUALS PAGE
    # ========================================================================
    visualsFrame = contentFrames["Visuals"]

    visualControlsFrame = ttk.LabelFrame(visualsFrame, text="Visual Display Options", padding="15")
    visualControlsFrame.pack(fill=tk.BOTH, expand=True)

    # Visual settings variables
    visualVars['show_face_mesh'] = tk.BooleanVar(value=Posture.VISUAL_SHOW_FACE_MESH)
    visualVars['show_metrics'] = tk.BooleanVar(value=Posture.VISUAL_SHOW_METRICS)
    visualVars['show_status'] = tk.BooleanVar(value=Posture.VISUAL_SHOW_STATUS)

    # Create visual setting checkboxes with tooltips
    faceMeshCB = ttk.Checkbutton(visualControlsFrame, text="Show Face Mesh", variable=visualVars['show_face_mesh'])
    faceMeshCB.pack(anchor=tk.W, pady=8)
    createToolTip(faceMeshCB, "Display the Posture.face mesh overlay on the video feed. This shows the detected facial landmarks used for tracking.")

    metricsCB = ttk.Checkbutton(visualControlsFrame, text="Show Metrics", variable=visualVars['show_metrics'])
    metricsCB.pack(anchor=tk.W, pady=8)
    createToolTip(metricsCB, "Display metric numeric values on the right side of the screen. Shows the current measurement for each enabled posture metric.")

    statusCB = ttk.Checkbutton(visualControlsFrame, text="Show Status", variable=visualVars['show_status'])
    statusCB.pack(anchor=tk.W, pady=8)
    createToolTip(statusCB, "Display status messages on the left side of the screen. Shows alerts when posture issues are detected (e.g., 'Slouching Detected').")

    # ========================================================================
    # NOTIFICATIONS PAGE
    # ========================================================================
    notificationsFrame = contentFrames["Notifications"]

    # Notification settings variables
    notificationVars = {}
    notificationVars['enabled'] = tk.BooleanVar(value=Posture.NOTIFICATION_ENABLED)
    notificationVars['beep_enabled'] = tk.BooleanVar(value=Posture.NOTIFICATION_BEEP_ENABLED)
    notificationVars['toast_enabled'] = tk.BooleanVar(value=Posture.NOTIFICATION_TOAST_ENABLED)
    notificationVars['min_duration'] = tk.DoubleVar(value=Posture.NOTIFICATION_MIN_DURATION)
    notificationVars['cooldown'] = tk.DoubleVar(value=Posture.NOTIFICATION_COOLDOWN)
    notificationVars['bad_posture_sound_type'] = tk.StringVar(value=Posture.NOTIFICATION_BAD_POSTURE_SOUND_TYPE)
    notificationVars['bad_posture_custom_sound_file'] = tk.StringVar(value=Posture.NOTIFICATION_BAD_POSTURE_CUSTOM_SOUND_FILE)
    notificationVars['revert_sound_type'] = tk.StringVar(value=Posture.NOTIFICATION_REVERT_SOUND_TYPE)
    notificationVars['revert_custom_sound_file'] = tk.StringVar(value=Posture.NOTIFICATION_REVERT_CUSTOM_SOUND_FILE)
    notificationVars['volume'] = tk.DoubleVar(value=Posture.NOTIFICATION_VOLUME)
    notificationVars['message_template'] = tk.StringVar(value=Posture.NOTIFICATION_MESSAGE_TEMPLATE)
    notificationVars['back_to_normal_enabled'] = tk.BooleanVar(value=Posture.NOTIFICATION_BACK_TO_NORMAL_ENABLED)
    notificationVars['back_to_normal_message'] = tk.StringVar(value=Posture.NOTIFICATION_BACK_TO_NORMAL_MESSAGE)

    # Main notification controls
    notificationControlsFrame = ttk.LabelFrame(notificationsFrame, text="Notification Settings", padding="15")
    notificationControlsFrame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    # Enable notifications checkbox
    enableNotificationsCB = ttk.Checkbutton(notificationControlsFrame, text="Enable Notifications", variable=notificationVars['enabled'])
    enableNotificationsCB.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
    createToolTip(enableNotificationsCB, "Enable or disable all posture notifications. When disabled, no alerts will be shown.")

    # Notification type checkboxes
    beepCB = ttk.Checkbutton(notificationControlsFrame, text="Enable Beep Sound", variable=notificationVars['beep_enabled'])
    beepCB.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
    createToolTip(beepCB, "Play a sound when bad posture is detected. You can choose different sound types below.")

    toastCB = ttk.Checkbutton(notificationControlsFrame, text="Enable Toast Notifications", variable=notificationVars['toast_enabled'])
    toastCB.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
    createToolTip(toastCB, "Show Windows toast notifications when bad posture is detected. These appear in the system notification area.")

    backToNormalCB = ttk.Checkbutton(notificationControlsFrame, text="Enable 'Back to Normal' Notifications", variable=notificationVars['back_to_normal_enabled'])
    backToNormalCB.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
    createToolTip(backToNormalCB, "Show a notification and play a pleasant sound when your posture returns to normal after being bad.")

    # Timing settings
    timingFrame = ttk.LabelFrame(notificationsFrame, text="Timing Settings", padding="15")
    timingFrame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    minDurationLabel = ttk.Label(timingFrame, text="Min Duration (seconds):")
    minDurationLabel.grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(minDurationLabel, "How long bad posture must be detected before sending the first notification. Prevents false alarms from brief movements.")

    minDurationSpinbox = ttk.Spinbox(timingFrame, from_=1, to=60, textvariable=notificationVars['min_duration'], width=15)
    minDurationSpinbox.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(minDurationSpinbox, "How long bad posture must be detected before sending the first notification. Prevents false alarms from brief movements.")

    cooldownLabel = ttk.Label(timingFrame, text="Cooldown (seconds):")
    cooldownLabel.grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(cooldownLabel, "Minimum time between notifications for the same issue. Prevents notification spam.")

    cooldownSpinbox = ttk.Spinbox(timingFrame, from_=5, to=300, textvariable=notificationVars['cooldown'], width=15)
    cooldownSpinbox.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(cooldownSpinbox, "Minimum time between notifications for the same issue. Prevents notification spam.")

    # Bad Posture Sound settings
    badPostureSoundFrame = ttk.LabelFrame(notificationsFrame, text="Bad Posture Sound Settings", padding="15")
    badPostureSoundFrame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    badPostureSoundTypeLabel = ttk.Label(badPostureSoundFrame, text="Sound Type:")
    badPostureSoundTypeLabel.grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(badPostureSoundTypeLabel, "Choose the sound to play when bad posture is detected. You can also specify a path to a custom .wav file.")

    badPostureSoundTypeCombo = ttk.Combobox(badPostureSoundFrame, textvariable=notificationVars['bad_posture_sound_type'], width=20, state="readonly")
    badPostureSoundTypeCombo['values'] = ("negative", "positive", "default", "beep", "chime", "alert")
    badPostureSoundTypeCombo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(badPostureSoundTypeCombo, "Choose the sound to play when bad posture is detected. You can also specify a path to a custom .wav file.")

    badPostureCustomSoundLabel = ttk.Label(badPostureSoundFrame, text="Custom Sound File (optional):")
    badPostureCustomSoundLabel.grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(badPostureCustomSoundLabel, "Enter a path to a custom .wav file to use as bad posture notification sound. If specified, this will override the sound type above.")

    badPostureCustomSoundEntry = ttk.Entry(badPostureSoundFrame, textvariable=notificationVars['bad_posture_custom_sound_file'], width=30)
    badPostureCustomSoundEntry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(badPostureCustomSoundEntry, "Enter a path to a custom .wav file to use as bad posture notification sound. If specified, this will override the sound type above.")

    # Revert Sound settings
    revertSoundFrame = ttk.LabelFrame(notificationsFrame, text="Back to Normal Sound Settings", padding="15")
    revertSoundFrame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    revertSoundTypeLabel = ttk.Label(revertSoundFrame, text="Sound Type:")
    revertSoundTypeLabel.grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(revertSoundTypeLabel, "Choose the sound to play when posture returns to normal. You can also specify a path to a custom .wav file.")

    revertSoundTypeCombo = ttk.Combobox(revertSoundFrame, textvariable=notificationVars['revert_sound_type'], width=20, state="readonly")
    revertSoundTypeCombo['values'] = ("negative", "positive", "default", "beep", "chime", "alert")
    revertSoundTypeCombo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(revertSoundTypeCombo, "Choose the sound to play when posture returns to normal. You can also specify a path to a custom .wav file.")

    revertCustomSoundLabel = ttk.Label(revertSoundFrame, text="Custom Sound File (optional):")
    revertCustomSoundLabel.grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(revertCustomSoundLabel, "Enter a path to a custom .wav file to use as back to normal notification sound. If specified, this will override the sound type above.")

    revertCustomSoundEntry = ttk.Entry(revertSoundFrame, textvariable=notificationVars['revert_custom_sound_file'], width=30)
    revertCustomSoundEntry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(revertCustomSoundEntry, "Enter a path to a custom .wav file to use as back to normal notification sound. If specified, this will override the sound type above.")

    # Volume settings
    volumeFrame = ttk.LabelFrame(notificationsFrame, text="Volume Settings", padding="15")
    volumeFrame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    volumeLabel = ttk.Label(volumeFrame, text="Notification Volume:")
    volumeLabel.grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(volumeLabel, "Adjust the volume of notification sounds only. 0.0 = silent, 1.0 = full volume. Works with .wav files (negative.wav, positive.wav, custom files).")

    # Volume value display label (create first)
    volumeValueLabel = ttk.Label(volumeFrame, text=f"{Posture.NOTIFICATION_VOLUME:.1f}")
    volumeValueLabel.grid(row=0, column=2, sticky=tk.W, pady=5, padx=5)

    # Update volume value label when slider changes
    def updateVolumeLabel(value):
        try:
            volumeValueLabel.config(text=f"{float(value):.1f}")
        except (ValueError, tk.TclError, AttributeError):
            pass  # Ignore errors if widget is being destroyed

    # Use tk.Scale instead of ttk.Scale because ttk.Scale doesn't support resolution parameter
    volumeSlider = tk.Scale(volumeFrame, from_=0.0, to=1.0, variable=notificationVars['volume'], orient=tk.HORIZONTAL, length=200, resolution=0.1, command=updateVolumeLabel)
    volumeSlider.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(volumeSlider, "Adjust the volume of notification sounds only. 0.0 = silent, 1.0 = full volume. Works with .wav files (negative.wav, positive.wav, custom files).")

    # Message settings
    messageFrame = ttk.LabelFrame(notificationsFrame, text="Message Settings", padding="15")
    messageFrame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    messageLabel = ttk.Label(messageFrame, text="Alert Message Template:")
    messageLabel.grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(messageLabel, "Customize the notification message. Use {issue} as a placeholder for the posture issue name (e.g., 'Slouching', 'Neck Forward').")

    messageEntry = ttk.Entry(messageFrame, textvariable=notificationVars['message_template'], width=50)
    messageEntry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(messageEntry, "Customize the notification message. Use {issue} as a placeholder for the posture issue name (e.g., 'Slouching', 'Neck Forward').")

    backToNormalLabel = ttk.Label(messageFrame, text="Back to Normal Message:")
    backToNormalLabel.grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
    createToolTip(backToNormalLabel, "Message to display when posture returns to normal. A pleasant chime sound will also play.")

    backToNormalEntry = ttk.Entry(messageFrame, textvariable=notificationVars['back_to_normal_message'], width=50)
    backToNormalEntry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
    createToolTip(backToNormalEntry, "Message to display when posture returns to normal. A pleasant chime sound will also play.")

    # ========================================================================
    # SAVE/CANCEL BUTTONS
    # ========================================================================
    result = {'saved': False}

    def saveSettings():
        """Save all settings."""

        # Save metric enables
        Posture.METRIC_ENABLE_SLOUCHING = metricVars['enable_slouching'].get()
        Posture.METRIC_ENABLE_UNEVEN_SHOULDERS = metricVars['enable_uneven_shoulders'].get()
        Posture.METRIC_ENABLE_HEAD_TILT = metricVars['enable_head_tilt'].get()
        Posture.METRIC_ENABLE_NECK_FORWARD = metricVars['enable_neck_forward'].get()
        Posture.METRIC_ENABLE_SHOULDERS_FORWARD = metricVars['enable_shoulders_forward'].get()

        # Apply performance preset
        selectedPerf = perfPresetVar.get()
        original_model_comp = original_perf_values.get('model_complexity', Posture.MODEL_COMPLEXITY)

        if selectedPerf == "Custom":
            # Apply custom values
            Posture.PROCESSING_FPS = perfVars['processing_fps'].get()
            Posture.DISPLAY_FPS = perfVars['display_fps'].get()
            Posture.FRAME_SKIP_INTERVAL = max(1, int(30 / Posture.PROCESSING_FPS))
            newModelComplexity = perfVars['model_complexity'].get()
            Posture.MODEL_COMPLEXITY = newModelComplexity
            Posture.HISTORY_SIZE = perfVars['history_size'].get()
            Posture.OUTLIER_STD_DEVIATIONS = perfVars['outlier_std_deviations'].get()
            Posture.SHOW_VISUAL_GUIDES = perfVars['show_visual_guides'].get()
            # Posture.FACE_MESH_DRAWING_ENABLED is stored for preset but visual display uses Posture.VISUAL_SHOW_FACE_MESH
            Posture.FACE_MESH_DRAWING_ENABLED = perfVars['face_mesh_drawing_enabled'].get()

            landmarkCount = perfVars['face_landmark_count'].get()
            if landmarkCount <= 5:
                Posture.FACE_LANDMARK_INDICES = Posture.FACE_LANDMARK_INDICES_LOW.copy()
            elif landmarkCount <= 20:
                Posture.FACE_LANDMARK_INDICES = Posture.FACE_LANDMARK_INDICES_MEDIUM.copy()
            else:
                Posture.FACE_LANDMARK_INDICES = Posture.FACE_LANDMARK_INDICES_HIGH.copy()

            Posture.PERFORMANCE_PRESET = "Custom"
        elif selectedPerf in ["LOW", "MEDIUM", "HIGH"]:
            # Use standard preset function
            Posture.PERFORMANCE_PRESET = selectedPerf
            presetConfig = Posture.applyPerformancePreset(selectedPerf)
            newModelComplexity = Posture.MODEL_COMPLEXITY
        else:
            # Custom preset from file
            Posture.PERFORMANCE_PRESET = selectedPerf
            Posture.applyPerformancePresetFromFile(selectedPerf)
            newModelComplexity = Posture.MODEL_COMPLEXITY

        # Reinitialize MediaPipe if model complexity changed from original
        # Only reset Posture.frameCounter and caches if model complexity actually changed
        if newModelComplexity != original_model_comp:
            presetConfig = {'model_complexity': Posture.MODEL_COMPLEXITY}
            Posture.reinitializeMediaPipe(presetConfig)
            # Reset Posture.frameCounter to ensure consistent processing after reinitialization
            # This prevents issues where Posture.frameCounter % Posture.FRAME_SKIP_INTERVAL might cause inconsistent processing
            Posture.frameCounter = 0

        # Apply metric preset
        selectedMetric = metricPresetSelectVar.get()
        if selectedMetric == "Custom":
            # Apply custom threshold values
            Posture.STATUS_THRESHOLD_SLOUCHING = metricThresholdVars['slouching'].get()
            Posture.STATUS_THRESHOLD_UNEVEN_SHOULDERS = metricThresholdVars['uneven_shoulders'].get()
            Posture.STATUS_THRESHOLD_HEAD_TILT = metricThresholdVars['head_tilt'].get()
            Posture.STATUS_THRESHOLD_NECK_FORWARD = metricThresholdVars['neck_forward'].get()
            Posture.STATUS_THRESHOLD_SHOULDERS_FORWARD = metricThresholdVars['shoulders_forward'].get()
            Posture.METRIC_PRESET_NAME = "Custom"
        else:
            Posture.METRIC_PRESET_NAME = selectedMetric
            Posture.applyMetricPreset(selectedMetric)

        # Save visual settings (independent from performance presets)
        Posture.VISUAL_SHOW_FACE_MESH = visualVars['show_face_mesh'].get()
        Posture.VISUAL_SHOW_METRICS = visualVars['show_metrics'].get()
        Posture.VISUAL_SHOW_STATUS = visualVars['show_status'].get()

        # Save notification settings
        Posture.NOTIFICATION_ENABLED = notificationVars['enabled'].get()
        Posture.NOTIFICATION_BEEP_ENABLED = notificationVars['beep_enabled'].get()
        Posture.NOTIFICATION_TOAST_ENABLED = notificationVars['toast_enabled'].get()
        Posture.NOTIFICATION_MIN_DURATION = notificationVars['min_duration'].get()
        Posture.NOTIFICATION_COOLDOWN = notificationVars['cooldown'].get()
        Posture.NOTIFICATION_BAD_POSTURE_SOUND_TYPE = notificationVars['bad_posture_sound_type'].get()
        Posture.NOTIFICATION_BAD_POSTURE_CUSTOM_SOUND_FILE = notificationVars['bad_posture_custom_sound_file'].get()
        Posture.NOTIFICATION_REVERT_SOUND_TYPE = notificationVars['revert_sound_type'].get()
        Posture.NOTIFICATION_REVERT_CUSTOM_SOUND_FILE = notificationVars['revert_custom_sound_file'].get()
        Posture.NOTIFICATION_VOLUME = max(0.0, min(1.0, notificationVars['volume'].get()))  # Clamp between 0.0 and 1.0
        Posture.NOTIFICATION_MESSAGE_TEMPLATE = notificationVars['message_template'].get()
        Posture.NOTIFICATION_BACK_TO_NORMAL_ENABLED = notificationVars['back_to_normal_enabled'].get()
        Posture.NOTIFICATION_BACK_TO_NORMAL_MESSAGE = notificationVars['back_to_normal_message'].get()

        result['saved'] = True
        root.destroy()

    def cancelSettings():
        """Cancel without saving - no changes are made to globals until Save is clicked."""
        root.destroy()

    # Buttons frame at bottom
    buttonFrame = ttk.Frame(root)
    buttonFrame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(10, 0))

    ttk.Button(buttonFrame, text="Save", command=saveSettings, width=15).pack(side=tk.RIGHT, padx=5)
    ttk.Button(buttonFrame, text="Cancel", command=cancelSettings, width=15).pack(side=tk.RIGHT, padx=5)

    # Pack description frame after button frame
    descFrame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 5))

    # Set initial description for Metrics page
    switchPage("Metrics")

    # Run the window
    root.mainloop()

    # Ensure OpenCV window is refreshed and focused after tkinter closes
    # This prevents lag from window focus issues
    cv2.waitKey(1)  # Process any pending OpenCV events

    return result['saved']

