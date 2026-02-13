import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math
import json
import copy
import os
import datetime
import prism

class AdvancedPrismEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Prism Editor PRO - Multi-Laser")
        self.root.geometry("1200x800")

        # --- WORLD STATE ---
        self.zoom = 5.0
        self.offset_x = 600
        self.offset_y = 400
        
        self.start_configs = [{'x': 0, 'y': 0, 'angle': 0, 'id': 1}]
        self.next_start_id = 2
        self.active_start_idx = 0
        
        self.prisms = []
        self.next_id = 1
        self.angle_tolerance = 0.01
        self.max_iterations = 1000
        
        # --- MOUSE INTERACTION STATE ---
        self.dragging_prism_idx = None
        self.dragging_start_idx = None
        self.selecting = False
        self.selection_start = (0, 0)
        self.selection_rect = None
        
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.ghost_cursor_pos = (0,0)

        # --- SELECTION & CLIPBOARD STATE ---
        self.selected_ids = []
        self.clipboard = []
        self.clipboard_center = (0,0)
        self.clipboard_is_cut = False

        # --- HISTORY (UNDO/REDO) ---
        self.history = []
        self.history_index = -1
        self.is_undoredo_op = False
        self.is_dragging = False
        self.cut_ids = []
        self.placing_laser = False
        self.last_placed_prism_id = None

        # --- GUI LAYOUT ---
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.panel = ttk.Frame(main_frame, padding="10", width=300)
        self.panel.pack(side=tk.LEFT, fill=tk.Y)

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.toolbar = ttk.Frame(right_frame, padding="5")
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.auto_save_var = tk.BooleanVar(value=False)
        self.chk_auto_save = ttk.Checkbutton(self.toolbar, text="Auto-save", variable=self.auto_save_var, command=self.toggle_auto_save)
        self.chk_auto_save.pack(side=tk.LEFT, padx=5)

        ttk.Button(self.toolbar, text="Save", command=self.save_state).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.toolbar, text="Load", command=self.load_state).pack(side=tk.LEFT, padx=5)
        
        self.canvas = tk.Canvas(right_frame, bg="#f0f0f0", cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.focus_set()

        # --- PANEL SECTIONS ---
        self.create_position_mode_section()
        self.create_laser_sources_section()
        self.create_new_prism_section()
        self.create_prism_list_section()
        self.create_final_actions_section()

        # --- EVENT BINDINGS ---
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.pan_view)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)
        
        # Shortcuts
        self.root.bind("<Control-z>", self.undo_action)
        self.root.bind("<Control-y>", self.redo_action)
        self.root.bind("<Control-c>", self.copy_selection)
        self.root.bind("<Control-x>", self.cut_selection)
        self.root.bind("<Control-v>", self.paste_selection)
        self.root.bind("<Delete>", self.delete_selection)
        self.root.bind("<Escape>", self.clear_clipboard)
        
        # Mac Support
        self.root.bind("<Command-z>", self.undo_action)
        self.root.bind("<Command-y>", self.redo_action)
        self.root.bind("<Command-c>", self.copy_selection)
        self.root.bind("<Command-x>", self.cut_selection)
        self.root.bind("<Command-v>", self.paste_selection)
        self.root.bind("<BackSpace>", self.delete_selection)

        self.draw_grid()
        self.draw_scene()
        self.save_state_for_undo()

    def create_position_mode_section(self):
        ttk.Label(self.panel, text="POSITION MODE", font=("Arial", 10, "bold")).pack(pady=(0,5))
        self.mode_var = tk.StringVar(value="GRID")
        ttk.Radiobutton(self.panel, text="GRID (Snap 10px)", variable=self.mode_var, value="GRID", command=self.refresh_ui).pack(anchor="w")
        ttk.Radiobutton(self.panel, text="FREE (Unrestricted)", variable=self.mode_var, value="FREE", command=self.refresh_ui).pack(anchor="w")
        ttk.Separator(self.panel, orient='horizontal').pack(fill='x', pady=10)

    def create_laser_sources_section(self):
        ttk.Label(self.panel, text="LASER SOURCES", font=("Arial", 10, "bold")).pack(pady=5)
        
        f_laser_tree = ttk.Frame(self.panel)
        f_laser_tree.pack(fill=tk.X, pady=2)
        
        cols = ("id", "x", "y", "ang")
        self.laser_tree = ttk.Treeview(f_laser_tree, columns=cols, show="headings", height=4)
        self.laser_tree.heading("id", text="ID")
        self.laser_tree.column("id", width=30, anchor="center")
        self.laser_tree.heading("x", text="X")
        self.laser_tree.column("x", width=55, anchor="center")
        self.laser_tree.heading("y", text="Y")
        self.laser_tree.column("y", width=55, anchor="center")
        self.laser_tree.heading("ang", text="Deg")
        self.laser_tree.column("ang", width=50, anchor="center")
        self.laser_tree.pack(fill=tk.X, expand=True)
        self.laser_tree.bind("<<TreeviewSelect>>", self.on_laser_select)

        f_laser_buttons = ttk.Frame(self.panel)
        f_laser_buttons.pack(fill=tk.X, pady=2)
        ttk.Button(f_laser_buttons, text="Add", command=self.add_laser).pack(side=tk.LEFT)
        ttk.Button(f_laser_buttons, text="Remove", command=self.remove_laser).pack(side=tk.LEFT, padx=5)

        # Angle Tolerance
        f_angle_tolerance = ttk.Frame(self.panel)
        f_angle_tolerance.pack(fill=tk.X, pady=5)
        ttk.Label(f_angle_tolerance, text="Angle Tolerance:").grid(row=0, column=0, sticky="w")
        self.entry_angle_tolerance = ttk.Entry(f_angle_tolerance, width=6)
        self.entry_angle_tolerance.grid(row=0, column=1, sticky="ew", padx=5)
        self.entry_angle_tolerance.insert(0, str(self.angle_tolerance))
        self.entry_angle_tolerance.bind("<Return>", lambda event: self.update_angle_tolerance())
        ttk.Button(f_angle_tolerance, text="Set", width=4, command=self.update_angle_tolerance).grid(row=0, column=2, sticky="e")
        f_angle_tolerance.grid_columnconfigure(1, weight=1) # Make entry expand

        # Max Iterations
        f_max_iterations = ttk.Frame(self.panel)
        f_max_iterations.pack(fill=tk.X, pady=5)
        ttk.Label(f_max_iterations, text="Max Iterations:").grid(row=0, column=0, sticky="w")
        self.entry_max_iterations = ttk.Entry(f_max_iterations, width=6)
        self.entry_max_iterations.grid(row=0, column=1, sticky="ew", padx=5)
        self.entry_max_iterations.insert(0, str(self.max_iterations))
        self.entry_max_iterations.bind("<Return>", lambda event: self.update_max_iterations())
        ttk.Button(f_max_iterations, text="Set", width=4, command=self.update_max_iterations).grid(row=0, column=2, sticky="e")
        f_max_iterations.grid_columnconfigure(1, weight=1) # Make entry expand

        ttk.Separator(self.panel, orient='horizontal').pack(fill='x', pady=10)

    def update_angle_tolerance(self):
        try:
            self.angle_tolerance = float(self.entry_angle_tolerance.get())
            self.refresh_ui()
        except ValueError:
            messagebox.showerror("Invalid Input", "Angle tolerance must be a valid number.")

    def update_max_iterations(self):
        try:
            self.max_iterations = int(self.entry_max_iterations.get())
            self.refresh_ui()
        except ValueError:
            messagebox.showerror("Invalid Input", "Max iterations must be a valid integer.")

    def create_new_prism_section(self):
        ttk.Label(self.panel, text="NEW PRISM", font=("Arial", 10, "bold")).pack(pady=5)
        self.auto_aim_var = tk.BooleanVar(value=False)
        self.chk_aim = ttk.Checkbutton(self.panel, text="Auto-Aim (Active Path)", variable=self.auto_aim_var, command=self.refresh_ui)
        self.chk_aim.pack(anchor="w", pady=2)
        
        f_angle_reflection = ttk.Frame(self.panel)
        f_angle_reflection.pack(fill=tk.X, pady=2)
        ttk.Label(f_angle_reflection, text="Angle reflection:").grid(row=0, column=0, sticky="w")
        self.entry_prism_angle = ttk.Entry(f_angle_reflection, width=6)
        self.entry_prism_angle.grid(row=0, column=1, sticky="ew", padx=5)
        self.entry_prism_angle.insert(0, "45")
        self.entry_prism_angle.bind("<Return>", lambda event: self.update_prism_angle())
        ttk.Button(f_angle_reflection, text="Set", width=4, command=self.update_prism_angle).grid(row=0, column=2, sticky="e")
        f_angle_reflection.grid_columnconfigure(1, weight=1) # Make entry expand

        ttk.Separator(self.panel, orient='horizontal').pack(fill='x', pady=10)

    def update_prism_angle(self):
        try:
            new_angle = float(self.entry_prism_angle.get())
            if self.selected_ids:
                for p in self.prisms:
                    if p['id'] in self.selected_ids:
                        p['angle'] = new_angle
            elif self.last_placed_prism_id is not None:
                for p in self.prisms:
                    if p['id'] == self.last_placed_prism_id:
                        p['angle'] = new_angle
                        break
                self.last_placed_prism_id = None
            
            self.refresh_ui()
            self.save_state_for_undo()
        except ValueError:
            messagebox.showerror("Invalid Input", "Angle must be a valid number.")

    def create_prism_list_section(self):
        ttk.Label(self.panel, text="PRISM LIST", font=("Arial", 10, "bold")).pack(pady=5)
        columns = ("id", "x", "y", "ang")
        self.tree = ttk.Treeview(self.panel, columns=columns, show="headings", height=10)
        self.tree.heading("id", text="ID"); self.tree.column("id", width=30, anchor="center")
        self.tree.heading("x", text="X"); self.tree.column("x", width=55, anchor="center")
        self.tree.heading("y", text="Y"); self.tree.column("y", width=55, anchor="center")
        self.tree.heading("ang", text="Deg"); self.tree.column("ang", width=50, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.on_prism_select)
        ttk.Separator(self.panel, orient='horizontal').pack(fill='x', pady=10)

    def on_prism_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items: return
        
        self.selected_ids = []
        for item_id in selected_items:
            # In Python 3, keys are strings.
            values = self.tree.item(item_id)['values']
            if values:
                self.selected_ids.append(values[0])
        
        self.draw_scene()

    def create_final_actions_section(self):
        ttk.Button(self.panel, text="Clean", command=self.clear_all).pack(fill=tk.X, pady=5)

    def on_laser_select(self, event):
        selected_item = self.laser_tree.focus()
        if not selected_item: return
        
        if selected_item:
            item_values = self.laser_tree.item(selected_item)['values']
            if item_values:
                selected_id = item_values[0]
                for i, cfg in enumerate(self.start_configs):
                    if cfg['id'] == selected_id:
                        self.active_start_idx = i
                        self.draw_scene()
                        break

    def add_laser(self):
        self.placing_laser = True
        self.canvas.config(cursor="tcross")

    def cancel_placing_laser(self):
        if self.placing_laser:
            self.placing_laser = False
            self.canvas.config(cursor="crosshair")

    def remove_laser(self):
        if len(self.start_configs) > 1:
            self.start_configs.pop(self.active_start_idx)
            self.active_start_idx = min(self.active_start_idx, len(self.start_configs) - 1)
            self.refresh_ui()
            self.save_state_for_undo()

    def refresh_ui(self):
        self.entry_prism_angle.configure(state="disabled" if self.auto_aim_var.get() else "normal")
        self.draw_scene()
        self.refresh_prism_tree()
        self.refresh_laser_tree()

    def refresh_prism_tree(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for p in self.prisms:
            x_val = int(p['x']) if self.mode_var.get() == "GRID" else round(p['x'], 3)
            y_val = int(p['y']) if self.mode_var.get() == "GRID" else round(p['y'], 3)
            self.tree.insert("", tk.END, iid=str(p['id']), values=(p['id'], x_val, y_val, round(p['angle'], 3)))
        
        # Restore selection
        if self.selected_ids:
            # Filter IDs that actually exist in the tree
            valid_ids = [str(pid) for pid in self.selected_ids if self.tree.exists(str(pid))]
            if valid_ids:
                self.tree.selection_set(valid_ids)
                self.tree.see(valid_ids[0])
            
    def refresh_laser_tree(self):
        for item in self.laser_tree.get_children(): self.laser_tree.delete(item)
        for i, cfg in enumerate(self.start_configs):
            x_val = int(cfg['x']) if self.mode_var.get() == "GRID" else round(cfg['x'], 3)
            y_val = int(cfg['y']) if self.mode_var.get() == "GRID" else round(cfg['y'], 3)
            item = self.laser_tree.insert("", tk.END, iid=str(cfg['id']), values=(cfg['id'], x_val, y_val, round(cfg['angle'], 3)))
            if i == self.active_start_idx:
                self.laser_tree.selection_set(item)
                self.laser_tree.focus(item)

    def get_snapped_coords(self, screen_x, screen_y):
        lx, ly = self.to_logical(screen_x, screen_y)
        if self.mode_var.get() == "GRID":
            return round(lx / 10) * 10, round(ly / 10) * 10
        return round(lx, 3), round(ly, 3)

    def copy_selection(self, event=None):
        if not self.selected_ids: return
        self.clipboard = copy.deepcopy([p for p in self.prisms if p['id'] in self.selected_ids])
        if not self.clipboard: return
        self.clipboard_is_cut = False
        self.clipboard_center = (sum(p['x'] for p in self.clipboard)/len(self.clipboard), sum(p['y'] for p in self.clipboard)/len(self.clipboard))
        self.draw_scene(show_ghost=True)

    def cut_selection(self, event=None):
        if not self.selected_ids: return
        self.copy_selection()
        self.clipboard_is_cut = True
        self.cut_ids = self.selected_ids.copy()
        self.draw_scene()

    def clear_clipboard(self, event=None):
        self.cancel_placing_laser()
        self.clipboard = []
        self.clipboard_is_cut = False
        self.draw_scene()

    def cancel_cut(self):
        if self.cut_ids:
            self.cut_ids = []
            self.clipboard = []
            self.clipboard_is_cut = False
            self.draw_scene()

    def paste_selection(self, event=None):
        if not self.clipboard: return
        
        lx, ly = self.to_logical(*self.ghost_cursor_pos)
        delta_x, delta_y = lx - self.clipboard_center[0], ly - self.clipboard_center[1]
        if self.mode_var.get() == "GRID":
            delta_x, delta_y = round(delta_x / 10) * 10, round(delta_y / 10) * 10

        self.selected_ids = []
        for p in self.clipboard:
            new_prism = {"id": self.next_id, "x": p['x'] + delta_x, "y": p['y'] + delta_y, "angle": p['angle']}
            self.prisms.append(new_prism)
            self.selected_ids.append(self.next_id)
            self.next_id += 1
        
        if self.clipboard_is_cut:
            self.prisms = [p for p in self.prisms if p['id'] not in self.cut_ids]
            self.cut_ids = []

        if self.clipboard_is_cut: self.clipboard, self.clipboard_is_cut = [], False
        self.save_state_for_undo()
        self.refresh_ui()

    def delete_selection(self, event=None):
        if not self.selected_ids: return
        self.prisms = [p for p in self.prisms if p['id'] not in self.selected_ids]
        self.selected_ids = []
        self.save_state_for_undo()
        self.refresh_ui()

    def get_active_shooter(self, exclude_ids=[]):
        if not self.start_configs: return {'x':0,'y':0,'angle':0}, -1
        active_start_cfg = self.start_configs[self.active_start_idx]
        temp_prisms = [p for p in self.prisms if p['id'] not in exclude_ids]
        try:
            seq, _, _, _ = prism.calculate_path(active_start_cfg, temp_prisms, self.angle_tolerance, self.max_iterations)
        except RuntimeError:
            return active_start_cfg, -1
        
        if not seq: return active_start_cfg, -1
        
        last_hit_id = seq[-1]
        shooter = next((p for p in self.prisms if p['id'] == last_hit_id), None)
        return (shooter, self.prisms.index(shooter)) if shooter else (active_start_cfg, -1)

    def calculate_angle_for_shooter(self, shooter, shooter_idx, target_x, target_y):
        dx, dy = target_x - shooter['x'], target_y - shooter['y']
        desired_abs_angle = math.degrees(math.atan2(dy, dx))
        
        if shooter_idx == -1: return desired_abs_angle

        active_start_cfg = self.start_configs[self.active_start_idx]
        incoming_angle = active_start_cfg['angle']
        try:
            seq, _, _, _ = prism.calculate_path(active_start_cfg, self.prisms, self.angle_tolerance, self.max_iterations)
            if shooter['id'] in seq:
                prisms_before = seq[:seq.index(shooter['id'])]
                for pid in prisms_before:
                    p = next(p for p in self.prisms if p['id'] == pid)
                    incoming_angle += p['angle']
        except: pass
        deviation = desired_abs_angle - incoming_angle
        return (deviation + 180) % 360 - 180

    def on_mouse_down(self, event):
        self.cancel_cut()
        self.canvas.focus_set()
        self.selecting = False
        lx, ly = self.get_snapped_coords(event.x, event.y)

        if self.placing_laser:
            new_id = self.next_start_id
            self.start_configs.append({'x': lx, 'y': ly, 'angle': 0, 'id': new_id})
            self.next_start_id += 1
            self.active_start_idx = len(self.start_configs) - 1
            self.cancel_placing_laser()
            self.refresh_ui()
            self.save_state_for_undo()
            self.laser_tree.see(str(new_id))
            self.laser_tree.selection_set(str(new_id))
            self.laser_tree.focus(str(new_id))
            return
        
        # Check for dragging start point
        for i, cfg in enumerate(self.start_configs):
            if math.sqrt((cfg['x'] - lx)**2 + (cfg['y'] - ly)**2) < (5 if self.mode_var.get() == "GRID" else 3):
                self.dragging_start_idx = i
                self.is_dragging = True
                self.selected_ids = []
                self.draw_scene()
                return

        # Check for dragging prism
        for i, p in enumerate(self.prisms):
            if math.sqrt((p['x']-lx)**2 + (p['y']-ly)**2) < (5 if self.mode_var.get() == "GRID" else 3):
                self.dragging_prism_idx = i
                self.is_dragging = True
                self.selected_ids = [p['id']]
                self.tree.selection_set(str(p['id']))
                self.tree.focus(str(p['id']))
                self.tree.see(str(p['id']))
                self.draw_scene()
                return

        self.selecting, self.selection_start, self.selected_ids = True, (event.x, event.y), []
        if self.selection_rect: self.canvas.delete(self.selection_rect)
        self.selection_rect = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="magenta", dash=(2,2))

    def on_mouse_drag(self, event):
        lx, ly = self.get_snapped_coords(event.x, event.y)
        
        if self.dragging_start_idx is not None:
            self.start_configs[self.dragging_start_idx]['x'], self.start_configs[self.dragging_start_idx]['y'] = lx, ly
        elif self.dragging_prism_idx is not None:
            self.prisms[self.dragging_prism_idx]['x'], self.prisms[self.dragging_prism_idx]['y'] = lx, ly
            if self.auto_aim_var.get():
                dragged_id = self.prisms[self.dragging_prism_idx]['id']
                shooter, shooter_idx = self.get_active_shooter(exclude_ids=[dragged_id])
                new_angle = self.calculate_angle_for_shooter(shooter, shooter_idx, lx, ly)
                shooter['angle'] = new_angle
                if shooter_idx == -1: self.refresh_laser_tree()
        elif self.selecting:
            self.canvas.coords(self.selection_rect, self.selection_start[0], self.selection_start[1], event.x, event.y)
        self.draw_scene()

    def on_mouse_up(self, event):
        need_refresh = False
        if self.is_dragging: 
            self.save_state_for_undo()
            need_refresh = True
        self.is_dragging = self.dragging_prism_idx = self.dragging_start_idx = None
        self.cancel_placing_laser()
        
        if self.selecting:
            self.selecting = False
            if self.selection_rect: self.canvas.delete(self.selection_rect); self.selection_rect = None
            if abs(self.selection_start[0] - event.x) < 3 and abs(self.selection_start[1] - event.y) < 3:
                self.create_new_prism(event.x, event.y)
            else:
                self.finalize_selection(*self.selection_start, event.x, event.y)
        elif need_refresh:
            self.refresh_ui()

    def finalize_selection(self, x1, y1, x2, y2):
        rx1, rx2 = sorted([x1, x2]); ry1, ry2 = sorted([y1, y2])
        lx1, ly1 = self.to_logical(rx1, ry1); lx2, ly2 = self.to_logical(rx2, ry2)
        self.selected_ids = [p['id'] for p in self.prisms if min(lx1,lx2) <= p['x'] <= max(lx1,lx2) and min(ly1,ly2) <= p['y'] <= max(ly1,ly2)]
        self.tree.selection_set([str(pid) for pid in self.selected_ids])
        if self.selected_ids:
            self.tree.see(str(self.selected_ids[0]))
        self.draw_scene()

    def create_new_prism(self, screen_x, screen_y):
        lx, ly = self.get_snapped_coords(screen_x, screen_y)
        try:
            angle = float(self.entry_prism_angle.get()) if not self.auto_aim_var.get() else 0.0
        except ValueError:
            angle = 0.0
        
        if self.auto_aim_var.get():
            shooter, shooter_idx = self.get_active_shooter()
            new_angle = self.calculate_angle_for_shooter(shooter, shooter_idx, lx, ly)
            shooter['angle'] = new_angle
            if shooter_idx == -1: self.refresh_laser_tree()

        self.prisms.append({"id": self.next_id, "x": lx, "y": ly, "angle": angle})
        self.last_placed_prism_id = self.next_id
        newly_added_prism_id = self.next_id # Store the ID for scrolling
        
        self.next_id += 1
        self.selected_ids = []
        self.save_state_for_undo()
        self.refresh_ui()

        # Scroll to the newly added prism
        self.tree.see(str(newly_added_prism_id))
        self.tree.selection_set(str(newly_added_prism_id))
        self.tree.focus(str(newly_added_prism_id))

    def on_mouse_move(self, event):
        self.ghost_cursor_pos = (event.x, event.y)
        if self.placing_laser or self.clipboard or (self.dragging_prism_idx is None and self.dragging_start_idx is None and not self.selecting):
            self.draw_scene(show_ghost=True)

    def start_pan(self, event):
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        
    def draw_ghost_laser(self):
        if self.placing_laser:
            lx, ly = self.get_snapped_coords(*self.ghost_cursor_pos)
            sx, sy = self.to_screen(lx, ly)
            
            self.canvas.create_oval(sx-5, sy-5, sx+5, sy+5, fill="gray", dash=(2,2), tags="scene")
            
            rad = math.radians(0) # Default angle
            ex, ey = sx + 20 * math.cos(rad), sy - 20 * math.sin(rad)
            self.canvas.create_line(sx, sy, ex, ey, arrow=tk.LAST, fill="gray", width=2, dash=(2,2), tags="scene")

    def pan_view(self, event):
        dx = event.x - self.last_mouse_x
        dy = event.y - self.last_mouse_y
        self.offset_x += dx
        self.offset_y += dy
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.draw_grid()
        self.draw_scene()

    def on_mouse_wheel(self, event):
        lx_before, ly_before = self.to_logical(event.x, event.y)
        
        if event.num == 4 or event.delta > 0:
            self.zoom *= 1.1
        elif event.num == 5 or event.delta < 0:
            self.zoom *= 0.9
            
        lx_after, ly_after = self.to_logical(event.x, event.y)
        
        self.offset_x += (lx_after - lx_before) * self.zoom
        self.offset_y -= (ly_after - ly_before) * self.zoom

        self.draw_grid()
        self.draw_scene()

    def to_screen(self, lx, ly): return self.offset_x + lx * self.zoom, self.offset_y - ly * self.zoom
    def to_logical(self, sx, sy): return (sx - self.offset_x) / self.zoom, (self.offset_y - sy) / self.zoom

    def draw_grid(self):
        self.canvas.delete("grid")
        ox, oy = self.to_screen(0, 0)
        self.canvas.create_line(0, oy, 2000, oy, fill="#ddd", width=2, tags="grid")
        self.canvas.create_line(ox, 0, ox, 2000, fill="#ddd", width=2, tags="grid")

    def draw_scene(self, show_ghost=False):
        self.canvas.delete("scene")
        results = prism.calculate_all_paths(self.start_configs, self.prisms, self.angle_tolerance, self.max_iterations)

        error_messages = []
        for i, res in enumerate(results):
            if res['error']:
                error_messages.append(f"⚠️ LASER {self.start_configs[i]['id']}: {res['error']}")

            color = "#00aa00" if i == self.active_start_idx else "#88ff88"
            
            if res['path_coords']:
                path = res['path_coords']
                if len(path) >= 2:
                    flat_coords = [c for p in path for c in self.to_screen(*p)]
                    self.canvas.create_line(flat_coords, fill=color, width=2, tags="scene")

            if res['loop_coords']:
                loop_path = res['loop_coords']
                loop_path.append(loop_path[0])
                if len(loop_path) >= 2:
                    flat_coords = [c for p in loop_path for c in self.to_screen(*p)]
                    self.canvas.create_line(flat_coords, fill="red", width=2, tags="scene")
            
            if res['error_lines']:
                for error_line_segment in res['error_lines']:
                    start_point, pos_point, neg_point = error_line_segment
                    
                    flat_coords_pos = [c for p in [start_point, pos_point] for c in self.to_screen(*p)]
                    self.canvas.create_line(flat_coords_pos, fill="orange", width=1, dash=(2,2), tags="scene")
                    
                    flat_coords_neg = [c for p in [start_point, neg_point] for c in self.to_screen(*p)]
                    self.canvas.create_line(flat_coords_neg, fill="orange", width=1, dash=(2,2), tags="scene")
        
        for i, msg in enumerate(error_messages):
            self.canvas.create_text(10, 10 + i*20, anchor="nw", text=msg, fill="red", font=("Arial", 14, "bold"), tags="scene")

        self.draw_ghost_paste()
        self.draw_ghost_ray(show_ghost, results)
        if show_ghost:
            self.draw_ghost_laser()
        self.draw_prisms()
        self.draw_start_points()

    def draw_ghost_paste(self):
        if self.clipboard and not self.selecting and self.dragging_prism_idx is None and self.dragging_start_idx is None:
            lx, ly = self.to_logical(*self.ghost_cursor_pos)
            delta_x, delta_y = lx - self.clipboard_center[0], ly - self.clipboard_center[1]
            if self.mode_var.get() == "GRID":
                delta_x, delta_y = round(delta_x/10)*10, round(delta_y/10)*10
            for p in self.clipboard:
                sx, sy = self.to_screen(p['x']+delta_x, p['y']+delta_y)
                r = 6 if self.mode_var.get() == "GRID" else 5
                self.canvas.create_rectangle(sx-r, sy-r, sx+r, sy+r, outline="gray", dash=(2,2), tags="scene") if self.mode_var.get() == "GRID" else self.canvas.create_oval(sx-r, sy-r, sx+r, sy+r, outline="gray", dash=(2,2), tags="scene")

    def draw_ghost_ray(self, show_ghost, results):
        if show_ghost and all(not r['error'] for r in results):
            shooter, _ = self.get_active_shooter()
            sx_anchor, sy_anchor = self.to_screen(shooter['x'], shooter['y'])
            lx_snap, ly_snap = self.get_snapped_coords(*self.ghost_cursor_pos)
            sx_snap, sy_snap = self.to_screen(lx_snap, ly_snap)
            self.canvas.create_line(sx_anchor, sy_anchor, sx_snap, sy_snap, fill="#888", dash=(4, 4), tags="scene")
            if self.auto_aim_var.get():
                self.canvas.create_oval(sx_anchor-4, sy_anchor-4, sx_anchor+4, sy_anchor+4, outline="magenta", width=2, tags="scene")

    def draw_prisms(self):
        for p in self.prisms:
            sx, sy = self.to_screen(p['x'], p['y'])
            color = "blue" if self.mode_var.get() == "GRID" else "orange"
            fill_color, dash_style = color, ()
            if p['id'] in self.cut_ids: fill_color, dash_style = "", (4, 4)
            elif p['id'] in self.selected_ids: fill_color = "#AA00FF"
            r = 6 if self.mode_var.get() == "GRID" else 5
            self.canvas.create_rectangle(sx-r, sy-r, sx+r, sy+r, fill=fill_color, outline="black", tags="scene", dash=dash_style) if self.mode_var.get() == "GRID" else self.canvas.create_oval(sx-r, sy-r, sx+r, sy+r, fill=fill_color, outline="black", tags="scene", dash=dash_style)
            self.canvas.create_text(sx, sy-15, text=f"{p['id']}", font=("Arial", 8, "bold"), tags="scene")

    def draw_start_points(self):
        for i, cfg in enumerate(self.start_configs):
            sx, sy = self.to_screen(cfg['x'], cfg['y'])
            fill_color = "red" if i == self.active_start_idx else "pink"
            self.canvas.create_oval(sx-5, sy-5, sx+5, sy+5, fill=fill_color, tags="scene")
            rad = math.radians(cfg['angle'])
            ex, ey = sx + 20 * math.cos(rad), sy - 20 * math.sin(rad)
            self.canvas.create_line(sx, sy, ex, ey, arrow=tk.LAST, fill=fill_color, width=2, tags="scene")
            self.canvas.create_text(sx, sy+15, text=f"L{cfg['id']}", font=("Arial", 8, "bold"), fill="red", tags="scene")

    def clear_all(self):
        self.prisms, self.start_configs = [], [{'x': 0, 'y': 0, 'angle': 0, 'id': 1}]
        self.next_id, self.next_start_id, self.active_start_idx, self.selected_ids = 1, 2, 0, []
        self.refresh_ui(); self.save_state_for_undo()

    def save_state(self):
        data = {
            'prisms': self.prisms, 
            'start_configs': self.start_configs,
            'angle_tolerance': self.angle_tolerance,
            'max_iterations': self.max_iterations
        }
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"prism_data_{timestamp}.json"
        
        filepath = filedialog.asksaveasfilename(
            initialdir="prisms_data", 
            defaultextension=".json", 
            filetypes=[("JSON", "*.json")], 
            title="Save State",
            initialfile=default_filename
        )
        
        if filepath:
            if not os.path.exists("prisms_data"):
                os.makedirs("prisms_data")
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Saved", f"State saved to {filepath}")

    def load_state(self):
        filepath = filedialog.askopenfilename(initialdir="prisms_data", defaultextension=".json", filetypes=[("JSON", "*.json")], title="Load State")
        if filepath:
            with open(filepath, "r") as f: data = json.load(f)
            self.prisms = data.get('prisms', [])
            self.start_configs = data.get('start_configs', [{'x':0,'y':0,'angle':0,'id':1}])
            self.angle_tolerance = data.get('angle_tolerance', 0.01)
            self.max_iterations = data.get('max_iterations', 1000)
            self.entry_angle_tolerance.delete(0, tk.END)
            self.entry_angle_tolerance.insert(0, str(self.angle_tolerance))
            self.entry_max_iterations.delete(0, tk.END)
            self.entry_max_iterations.insert(0, str(self.max_iterations))

            if 'start_cfg' in data: # Legacy support
                self.start_configs = [{'id':1, **data['start_cfg']}]

            self.next_id = max([p['id'] for p in self.prisms] + [0]) + 1
            self.next_start_id = max([s['id'] for s in self.start_configs] + [0]) + 1
            self.active_start_idx = 0
            
            self.root.update_idletasks() # Ensure canvas dimensions are available
            self.center_and_zoom_on_content()
            
            self.save_state_for_undo()
            self.refresh_ui()

    def center_and_zoom_on_content(self):
        if not self.prisms and not self.start_configs:
            return

        all_points = []
        for p in self.prisms:
            all_points.append((p['x'], p['y']))
        for s in self.start_configs:
            all_points.append((s['x'], s['y']))

        if not all_points:
            return

        min_x = min(p[0] for p in all_points)
        max_x = max(p[0] for p in all_points)
        min_y = min(p[1] for p in all_points)
        max_y = max(p[1] for p in all_points)

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        box_width = max_x - min_x
        box_height = max_y - min_y
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if box_width == 0 and box_height == 0:
            self.zoom = 5.0
        else:
            padding = 50 
            
            zoom_x = (canvas_width - 2 * padding) / box_width if box_width > 0 else float('inf')
            zoom_y = (canvas_height - 2 * padding) / box_height if box_height > 0 else float('inf')

            self.zoom = min(zoom_x, zoom_y)

        self.offset_x = canvas_width / 2 - center_x * self.zoom
        self.offset_y = canvas_height / 2 + center_y * self.zoom


    def save_state_for_undo(self):
        if self.is_undoredo_op: return
        if self.history_index < len(self.history) - 1: self.history = self.history[:self.history_index + 1]
        state = {'prisms': copy.deepcopy(self.prisms), 'start_configs': copy.deepcopy(self.start_configs), 'next_id': self.next_id, 'next_start_id': self.next_start_id, 'active_start_idx': self.active_start_idx}
        self.history.append(state)
        self.history_index += 1
        if len(self.history) > 50: self.history.pop(0); self.history_index -= 1
        
    def restore_from_history(self, state):
        self.prisms = copy.deepcopy(state['prisms'])
        self.start_configs = copy.deepcopy(state['start_configs'])
        self.next_id = state['next_id']
        self.next_start_id = state['next_start_id']
        self.active_start_idx = state['active_start_idx']
        self.is_undoredo_op = False
        self.refresh_ui()

    def undo_action(self, event=None):
        if self.cut_ids: self.cut_ids = []; self.draw_scene(); return
        if self.history_index > 0:
            self.is_undoredo_op = True
            self.history_index -= 1
            self.restore_from_history(self.history[self.history_index])

    def redo_action(self, event=None):
        if self.history_index < len(self.history) - 1:
            self.is_undoredo_op = True
            self.history_index += 1
            self.restore_from_history(self.history[self.history_index])
            
    def toggle_auto_save(self):
        if self.auto_save_var.get():
            self.auto_save_state()
        else:
            if hasattr(self, 'auto_save_timer'):
                self.root.after_cancel(self.auto_save_timer)

    def auto_save_state(self):
        data = {
            'prisms': self.prisms, 
            'start_configs': self.start_configs,
            'angle_tolerance': self.angle_tolerance,
            'max_iterations': self.max_iterations
        }
        save_directory = "prisms_data"
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
        autosave_filepath = os.path.join(save_directory, "autosave.json")
        
        try:
            with open(autosave_filepath, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Auto-save failed: {e}")
            
        if self.auto_save_var.get():
            self.auto_save_timer = self.root.after(30000, self.auto_save_state)

        
if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedPrismEditor(root)
    root.mainloop()