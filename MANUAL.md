# User Manual - Prism Editor PRO

Prism Editor PRO is a graphical interface designed for creating optical configurations and generating JSON configuration files for the Prism Ray Tracer simulator.

## Startup
Run the main file via terminal:
`python editor.py`

Note: The `prism.py` file must be present in the same directory.

## Positioning Modes
The software operates in two distinct modes, selectable from the side panel:

1. **GRID**
   - Coordinates are snapped to the nearest multiple of 10.
   - Ideal for standard geometric configurations and alignment tests.
   - X and Y values are saved as integers.

2. **FREE**
   - No positioning constraints.
   - Coordinates are saved with 3-decimal precision (e.g., 10.125).
   - Ideal for testing complex reflections, specific angles, or physical limits.

## Interface Controls

### Mouse Controls
- **Left Click (on empty space):** Deselect all.
- **Left Drag (on empty space):** Create a multiple selection box.
- **Left Drag (on a prism):** Move the selected prism.
- **Left Drag (on Start/Red Dot):** Move the laser origin point.
- **Right Drag (anywhere):** Pan the view (move the workspace).

### Keyboard Shortcuts
- **Ctrl + Z:** Undo the last action.
- **Ctrl + Y:** Redo the last undone action.
- **Ctrl + C:** Copy selected prisms.
- **Ctrl + X:** Cut selected prisms (paste once).
- **Ctrl + V:** Activate paste mode. A "ghost" preview will follow the cursor. Click to confirm the position.
- **Esc:** Cancel the current paste operation and clear the clipboard.
- **Del / Backspace:** Delete selected prisms.

*Note: On macOS, use Cmd instead of Ctrl.*

## Advanced Features

### Auto-Aim
Located in the side panel under "NEW PRISM".
- **Enabled:** When creating or moving a prism, the previous element in the optical chain (or the Start point) automatically rotates to target the newly placed prism.
- **Disabled:** Prisms maintain their fixed angle. You can manually enter the angle in the dedicated text field.

### Infinite Loop Detection
The software calculates the beam path in real-time. If an operation (move, create, paste) creates an infinite loop (e.g., two parallel mirrors), the action is blocked, and an error message is displayed to prevent the software from freezing.

### Prism List
The side table displays in real-time:
- **ID:** Unique identifier of the prism.
- **X / Y:** Spatial coordinates.
- **Deg:** Rotation angle in degrees.

## Data Export

### Saving JSON
Clicking the **SAVE JSON** button:
1. Creates a `json_result` folder in the program directory (if it does not exist).
2. Generates a timestamped file (e.g., `test_20260210_043000.json`).
3. The file contains the complete configuration (Start + Prisms + Expected Sequence) in a compact format.

### JSON Format
The generated file follows this structure:
- `input`: Contains the `start` object and the `prisms` list.
- `expected`: Contains the `sequence` of IDs hit by the laser.
- Decimal numbers are rounded to the third decimal place.

## Saving and Loading State

The editor allows you to save and load the entire state of the editor, including the position of the prisms, the start configuration, and the zoom level.

- **Save State:** Click the "Save State" button to save the current state of the editor to a file.
- **Load State:** Click the "Load State" button to load a previously saved editor state from a file.
- **Auto-save:** The "Auto-save" checkbox enables or disables the auto-save feature. When enabled, the editor will automatically save the current state to a file named `autosave.json` every 30 seconds.