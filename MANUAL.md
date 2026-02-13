# User Manual - Prism Editor PRO

Prism Editor PRO is a graphical interface for creating and simulating optical configurations using prisms.

## Startup
Run the main file via terminal:
`python editor.py`

Note: This editor uses the `prism.py` library for its core optical calculations.

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

## Laser Sources
The editor now supports multiple laser sources. You can manage them using the "LASER SOURCES" panel.

*   **Add:** Adds a new laser source to the scene. The new laser will be placed at the current mouse position.
*   **Remove:** Removes the currently selected laser source.
*   **Laser List:** The list shows all laser sources with their ID, position, and angle. Click on a laser to make it the "active" laser. The active laser's path is drawn in a brighter color, and it is the one affected by the "Auto-Aim" feature.
*   **Angle Tolerance:** This field controls the tolerance for a laser beam to hit a prism. A smaller value means the beam has to be more accurately aimed. You can set the value by typing in the box and pressing Enter or clicking "Set".
*   **Max Iterations:** This is a safeguard against performance issues with very complex scenes. It sets the maximum number of steps for each laser path calculation. You can set the value by typing in the box and pressing Enter or clicking "Set".

## Interface Controls

### Mouse Controls
- **Left Click (on empty space):** Deselect all.
- **Left Drag (on empty space):** Create a multiple selection box.
- **Left Drag (on a prism):** Move the selected prism.
- **Left Drag (on Start/Red Dot):** Move the laser origin point.
- **Right Drag (anywhere):** Pan the view (move the workspace).
- **Mouse Wheel:** Zoom in and out, centered on the mouse cursor.

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

### Auto-Aim & Manual Angle Control
Located in the side panel under "NEW PRISM".
- **Auto-Aim Enabled:** When creating or moving a prism, the previous element in the optical chain (or the Start point) automatically rotates to target the newly placed prism.
- **Manual Angle Setting:** You can manually set or update the rotation of prisms using the **Angle reflection** field and the **Set** button (or by pressing Enter).
    - **Single Prism:** Select a prism on the canvas or in the list, enter the desired angle, and click "Set".
    - **Group of Prisms:** Use box selection (Left Drag on empty space) or select multiple prisms in the list, then enter an angle and click "Set" to update all selected prisms at once.
    - **Last Placed:** If no selection is active, clicking "Set" will update the angle of the most recently placed prism.
- **Auto-Aim Disabled:** Prisms maintain their fixed angle when being moved. New prisms are created using the angle currently in the text field.

### Infinite Loop Detection & Visualization
The software calculates the beam path in real-time. If a laser beam enters an infinite loop (e.g., between two parallel mirrors), the editor will detect this and visualize the loop.

*   The path segment that forms the loop will be drawn in **red**.
*   The non-looping part of the path will be drawn in the standard green color.
*   A warning message will also be displayed on the canvas for the affected laser.

### Prism List
The side table displays in real-time:
- **ID:** Unique identifier of the prism.
- **X / Y:** Spatial coordinates.
- **Deg:** Rotation angle in degrees.

## Saving and Loading State

The editor allows you to save and load the entire state of the editor. This includes the position of all prisms, all laser start configurations, the angle tolerance, and the max iterations setting.

- **Save:** Click the "Save" button to save the current state of the editor to a file.
- **Load:** Click the "Load" button to load a previously saved editor state from a file. The editor will automatically center and zoom to fit the loaded content.
- **Auto-save:** The "Auto-save" checkbox enables or disables the auto-save feature. When enabled, the editor will automatically save the complete current state to a file named `autosave.json` every 30 seconds.
