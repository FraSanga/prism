import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math
import json
import copy 
import os           
import datetime     
import prism  # Ensure prism.py is in the same directory

class AdvancedPrismEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Prism Editor PRO")
        self.root.geometry("1200x800")

        # --- WORLD STATE ---
        self.zoom = 5.0 
        self.offset_x = 600 
        self.offset_y = 400
        
        self.start_cfg = {'x': 0, 'y': 0, 'angle': 0}
        self.prisms = []
        self.next_id = 1
        
        # --- MOUSE INTERACTION STATE ---
        self.dragging_prism_idx = None 
        self.dragging_start = False    
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

        # --- GUI LAYOUT ---
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.panel = ttk.Frame(main_frame, padding="10", width=250)
        self.panel.pack(side=tk.LEFT, fill=tk.Y)

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.toolbar = ttk.Frame(right_frame, padding="5")
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.auto_save_var = tk.BooleanVar(value=False)
        self.chk_auto_save = ttk.Checkbutton(self.toolbar, text="Auto-save", variable=self.auto_save_var, command=self.toggle_auto_save)
        self.chk_auto_save.pack(side=tk.LEFT, padx=5)

        ttk.Button(self.toolbar, text="Save State", command=self.save_state).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.toolbar, text="Load State", command=self.load_state).pack(side=tk.LEFT, padx=5)
        
        self.canvas = tk.Canvas(right_frame, bg="#f0f0f0", cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.focus_set()

        # --- SECTION 1: POSITION MODE ---
        ttk.Label(self.panel, text="POSITION MODE", font=("Arial", 10, "bold")).pack(pady=(0,5))
        
        self.mode_var = tk.StringVar(value="GRID")
        ttk.Radiobutton(self.panel, text="GRID (Snap 10px)", variable=self.mode_var, value="GRID", command=self.refresh_ui).pack(anchor="w")
        ttk.Radiobutton(self.panel, text="FREE (Unrestricted)", variable=self.mode_var, value="FREE", command=self.refresh_ui).pack(anchor="w")
        
        ttk.Separator(self.panel, orient='horizontal').pack(fill='x', pady=10)

        # --- SECTION 2: START CONFIG ---
        ttk.Label(self.panel, text="START CONFIG", font=("Arial", 10, "bold")).pack(pady=5)
        f_start = ttk.Frame(self.panel)
        f_start.pack(fill=tk.X)
        ttk.Label(f_start, text="Angle:").pack(side=tk.LEFT)
        self.entry_start = ttk.Entry(f_start, width=6)
        self.entry_start.insert(0, "0")
        self.entry_start.pack(side=tk.LEFT, padx=5)
        ttk.Button(f_start, text="Set", width=4, command=self.update_start_manual).pack(side=tk.LEFT)

        ttk.Separator(self.panel, orient='horizontal').pack(fill='x', pady=10)

        # --- SECTION 3: NEW PRISM ---
        ttk.Label(self.panel, text="NEW PRISM", font=("Arial", 10, "bold")).pack(pady=5)
        
        self.auto_aim_var = tk.BooleanVar(value=False)
        self.chk_aim = ttk.Checkbutton(self.panel, text="Auto-Aim (Active Path)", variable=self.auto_aim_var, command=self.refresh_ui)
        self.chk_aim.pack(anchor="w", pady=2)
        
        self.frame_angle = ttk.Frame(self.panel)
        self.frame_angle.pack(fill=tk.X, pady=2)
        ttk.Label(self.frame_angle, text="Angle:").pack(side=tk.LEFT)
        self.entry_prism_angle = ttk.Entry(self.frame_angle, width=6)
        self.entry_prism_angle.insert(0, "45")
        self.entry_prism_angle.pack(side=tk.LEFT, padx=5)

        ttk.Separator(self.panel, orient='horizontal').pack(fill='x', pady=10)

        # --- SECTION 4: PRISM LIST ---
        ttk.Label(self.panel, text="PRISM LIST", font=("Arial", 10, "bold")).pack(pady=5)
        
        columns = ("id", "x", "y", "ang")
        self.tree = ttk.Treeview(self.panel, columns=columns, show="headings", height=10)
        
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=30, anchor="center")
        self.tree.heading("x", text="X")
        self.tree.column("x", width=55, anchor="center") 
        self.tree.heading("y", text="Y")
        self.tree.column("y", width=55, anchor="center")
        self.tree.heading("ang", text="Deg")
        self.tree.column("ang", width=50, anchor="center")
        
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Separator(self.panel, orient='horizontal').pack(fill='x', pady=10)

        # --- SECTION 5: FINAL ACTIONS ---
        ttk.Button(self.panel, text="SAVE JSON", command=self.save_json_file).pack(fill=tk.X, pady=5)
        ttk.Button(self.panel, text="RESET ALL", command=self.clear_all).pack(fill=tk.X, pady=5)
        
        # --- EVENT BINDINGS ---
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Motion>", self.on_mouse_move) 
        self.canvas.bind("<Button-3>", self.start_pan)   
        self.canvas.bind("<B3-Motion>", self.pan_view)
        
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

    # --- CORE LOGIC ---

    def refresh_ui(self):
        if self.auto_aim_var.get():
            self.entry_prism_angle.configure(state="disabled")
        else:
            self.entry_prism_angle.configure(state="normal")
        self.draw_scene()
        self.refresh_tree() 

    def refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for p in self.prisms:
            if self.mode_var.get() == "GRID":
                x_val = int(p['x'])
                y_val = int(p['y'])
            else:
                x_val = round(p['x'], 3)
                y_val = round(p['y'], 3)
                
            ang_val = round(p['angle'], 3)
            self.tree.insert("", tk.END, values=(p['id'], x_val, y_val, ang_val))

    def get_snapped_coords(self, screen_x, screen_y):
        lx, ly = self.to_logical(screen_x, screen_y)
        if self.mode_var.get() == "GRID":
            lx = round(lx / 10) * 10
            ly = round(ly / 10) * 10
            return int(lx), int(ly)
        else:
            return round(lx, 3), round(ly, 3)

    # --- COPY / PASTE LOGIC ---

    def copy_selection(self, event=None):
        if not self.selected_ids:
            return
        items_to_copy = [p for p in self.prisms if p['id'] in self.selected_ids]
        if not items_to_copy: return
        
        self.clipboard = copy.deepcopy(items_to_copy)
        self.clipboard_is_cut = False 
        
        avg_x = sum(p['x'] for p in self.clipboard) / len(self.clipboard)
        avg_y = sum(p['y'] for p in self.clipboard) / len(self.clipboard)
        self.clipboard_center = (avg_x, avg_y)
        self.draw_scene(show_ghost=True)

    def cut_selection(self, event=None):
        if not self.selected_ids:
            return
        self.copy_selection() 
        self.clipboard_is_cut = True 
        self.cut_ids = self.selected_ids.copy()
        self.draw_scene() 

    def clear_clipboard(self, event=None):
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
        
        prisms_backup = copy.deepcopy(self.prisms)
        next_id_backup = self.next_id
        
        mx_raw, my_raw = self.ghost_cursor_pos
        lx, ly = self.to_logical(mx_raw, my_raw) 
        
        delta_x = lx - self.clipboard_center[0]
        delta_y = ly - self.clipboard_center[1]
        
        if self.mode_var.get() == "GRID":
            delta_x = round(delta_x / 10) * 10
            delta_y = round(delta_y / 10) * 10

        self.selected_ids = []

        for p in self.clipboard:
            new_x = p['x'] + delta_x
            new_y = p['y'] + delta_y
            
            if self.mode_var.get() == "FREE":
                new_x = round(new_x, 3)
                new_y = round(new_y, 3)
            else:
                new_x = int(new_x)
                new_y = int(new_y)

            new_prism = {
                "id": self.next_id,
                "x": new_x,
                "y": new_y,
                "angle": p['angle'] 
            }
            self.prisms.append(new_prism)
            self.selected_ids.append(self.next_id) 
            self.next_id += 1
        
        try:
            if self.clipboard_is_cut:
                self.prisms = [p for p in self.prisms if p['id'] not in self.cut_ids]
                self.cut_ids = []

            prism.calculate_path(self.start_cfg, self.prisms)
            if self.clipboard_is_cut:
                self.clipboard = []
                self.clipboard_is_cut = False
            self.draw_scene()
            self.refresh_tree() 
            self.save_state_for_undo()
            
        except RuntimeError:
            self.prisms = prisms_backup
            self.next_id = next_id_backup
            self.selected_ids = []
            self.draw_scene()
            messagebox.showerror("Loop", "Cannot paste!\nThe configuration creates an infinite loop.")


    def delete_selection(self, event=None, save_state=True):
        if not self.selected_ids: return
        
        prisms_backup = copy.deepcopy(self.prisms)
        
        self.prisms = [p for p in self.prisms if p['id'] not in self.selected_ids]
        self.selected_ids = []
        
        try:
            prism.calculate_path(self.start_cfg, self.prisms)
            self.draw_scene()
            self.refresh_tree()
            if save_state: 
                self.save_state_for_undo()
        except RuntimeError:
            self.prisms = prisms_backup
            self.draw_scene()
            messagebox.showerror("Loop", "Cannot delete!\nRemoving these prisms causes an infinite loop.")

    # --- AUTO AIM LOGIC ---
    
    def get_active_shooter(self, exclude_ids=[]):
        temp_prisms = [p for p in self.prisms if p['id'] not in exclude_ids]
        try:
            seq, _, _ = prism.calculate_path(self.start_cfg, temp_prisms)
        except RuntimeError:
            return self.start_cfg, -1
        except:
            return self.start_cfg, -1
        if not seq:
            return self.start_cfg, -1
        else:
            last_hit_id = seq[-1]
            shooter = next((p for p in self.prisms if p['id'] == last_hit_id), None)
            if shooter:
                return shooter, self.prisms.index(shooter)
            else:
                return self.start_cfg, -1

    def calculate_angle_for_shooter(self, shooter, shooter_idx, target_x, target_y):
        dx = target_x - shooter['x']
        dy = target_y - shooter['y']
        desired_abs_angle = math.degrees(math.atan2(dy, dx))
        if shooter_idx == -1:
            return desired_abs_angle
        else:
            incoming_angle = self.start_cfg['angle']
            try:
                seq, _, _ = prism.calculate_path(self.start_cfg, self.prisms)
                if shooter['id'] in seq:
                    idx_in_seq = seq.index(shooter['id'])
                    prisms_before = seq[:idx_in_seq]
                    for pid in prisms_before:
                        p = next(p for p in self.prisms if p['id'] == pid)
                        incoming_angle += p['angle']
            except: pass 
            deviation = desired_abs_angle - incoming_angle
            deviation = (deviation + 180) % 360 - 180
            return deviation

    # --- MOUSE HANDLING ---

    def on_mouse_down(self, event):
        self.cancel_cut()
        self.canvas.focus_set() 
        lx, ly = self.get_snapped_coords(event.x, event.y)
        
        clicked_prism_idx = None
        for i, p in enumerate(self.prisms):
            dist = math.sqrt((p['x']-lx)**2 + (p['y']-ly)**2)
            threshold = 5 if self.mode_var.get() == "GRID" else 3
            if dist < threshold:
                clicked_prism_idx = i
                break
        
        if clicked_prism_idx is not None:
            self.selected_ids = []
            self.dragging_prism_idx = clicked_prism_idx 
            self.is_dragging = True
            self.draw_scene()
            return

        dist_start = math.sqrt((self.start_cfg['x']-lx)**2 + (self.start_cfg['y']-ly)**2)
        if dist_start < (5 if self.mode_var.get() == "GRID" else 3):
            self.dragging_start = True
            self.is_dragging = True
            self.selected_ids = [] 
            self.draw_scene()
            return

        self.selecting = True
        self.selection_start = (event.x, event.y)
        self.selected_ids = [] 
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
        self.selection_rect = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="magenta", dash=(2,2))


    def on_mouse_drag(self, event):
        lx, ly = self.get_snapped_coords(event.x, event.y)
        
        if self.dragging_prism_idx is not None:
            self.prisms[self.dragging_prism_idx]['x'] = lx
            self.prisms[self.dragging_prism_idx]['y'] = ly
            
            if self.auto_aim_var.get():
                dragged_id = self.prisms[self.dragging_prism_idx]['id']
                shooter, shooter_idx = self.get_active_shooter(exclude_ids=[dragged_id])
                new_angle = self.calculate_angle_for_shooter(shooter, shooter_idx, lx, ly)
                shooter['angle'] = new_angle
                if shooter_idx == -1:
                    self.entry_start.delete(0, tk.END)
                    self.entry_start.insert(0, str(round(new_angle, 3)))
            self.draw_scene()
            
        elif self.dragging_start:
            self.start_cfg['x'] = lx
            self.start_cfg['y'] = ly
            self.draw_scene()

        elif self.selecting:
            cur_x, cur_y = event.x, event.y
            self.canvas.coords(self.selection_rect, self.selection_start[0], self.selection_start[1], cur_x, cur_y)

    def on_mouse_up(self, event):
        if self.is_dragging:
            self.save_state_for_undo()
            self.is_dragging = False

        self.dragging_prism_idx = None
        self.dragging_start = False
        self.refresh_tree() 
        
        if self.selecting:
            self.selecting = False
            if self.selection_rect:
                self.canvas.delete(self.selection_rect)
                self.selection_rect = None
            start_x, start_y = self.selection_start
            end_x, end_y = event.x, event.y
            
            if abs(start_x - end_x) < 3 and abs(start_y - end_y) < 3:
                self.create_new_prism(event.x, event.y)
            else:
                self.finalize_selection(start_x, start_y, end_x, end_y)

    def finalize_selection(self, x1, y1, x2, y2):
        rx1, rx2 = sorted([x1, x2])
        ry1, ry2 = sorted([y1, y2])
        lx1, ly1 = self.to_logical(rx1, ry1) 
        lx2, ly2 = self.to_logical(rx2, ry2)
        ly_min = min(ly1, ly2)
        ly_max = max(ly1, ly2)
        lx_min = min(lx1, lx2)
        lx_max = max(lx1, lx2)

        self.selected_ids = []
        for p in self.prisms:
            if lx_min <= p['x'] <= lx_max and ly_min <= p['y'] <= ly_max:
                self.selected_ids.append(p['id'])
        self.draw_scene()

    def create_new_prism(self, screen_x, screen_y):
        lx, ly = self.get_snapped_coords(screen_x, screen_y)
        angle = 0.0
        backup_shooter = None
        backup_angle = None
        
        if self.auto_aim_var.get():
            shooter, shooter_idx = self.get_active_shooter()
            backup_shooter = shooter
            backup_angle = shooter['angle']
            new_angle = self.calculate_angle_for_shooter(shooter, shooter_idx, lx, ly)
            shooter['angle'] = new_angle
            if shooter_idx == -1:
                self.entry_start.delete(0, tk.END)
                self.entry_start.insert(0, str(round(new_angle, 3)))
        elif not self.auto_aim_var.get():
            try:
                angle = float(self.entry_prism_angle.get())
            except: angle = 0.0

        new_prism = {
            "id": self.next_id,
            "x": lx,
            "y": ly,
            "angle": angle
        }
        self.prisms.append(new_prism)
        
        try:
            prism.calculate_path(self.start_cfg, self.prisms)
            self.next_id += 1
            self.selected_ids = [] 
            self.draw_scene()
            self.refresh_tree()
            self.save_state_for_undo()
        except RuntimeError:
            self.prisms.pop()
            if backup_shooter is not None:
                backup_shooter['angle'] = backup_angle
                if backup_shooter == self.start_cfg:
                    self.entry_start.delete(0, tk.END)
                    self.entry_start.insert(0, str(round(backup_angle, 3)))
            self.draw_scene()
            messagebox.showerror("Loop", "Infinite loop detected!")

    def on_mouse_move(self, event):
        self.ghost_cursor_pos = (event.x, event.y)
        if self.clipboard or (self.dragging_prism_idx is None and not self.dragging_start and not self.selecting):
            self.draw_scene(show_ghost=True)

    # --- DRAWING & GRAPHICS ---

    def to_screen(self, lx, ly):
        sx = self.offset_x + lx * self.zoom
        sy = self.offset_y - ly * self.zoom
        return sx, sy

    def to_logical(self, sx, sy):
        lx = (sx - self.offset_x) / self.zoom
        ly = (self.offset_y - sy) / self.zoom
        return lx, ly

    def draw_grid(self):
        self.canvas.delete("grid")
        ox, oy = self.to_screen(0, 0)
        self.canvas.create_line(0, oy, 2000, oy, fill="#ddd", width=2, tags="grid")
        self.canvas.create_line(ox, 0, ox, 2000, fill="#ddd", width=2, tags="grid")

    def draw_scene(self, show_ghost=False):
        self.canvas.delete("scene")
        path_coords = []
        loop_detected = False

        try:
            seq, path_coords, _ = prism.calculate_path(self.start_cfg, self.prisms)
        except RuntimeError:
            loop_detected = True
        except:
            path_coords = []

        # Green Path
        green_coords_to_draw = []
        clip_extension = False
        if show_ghost and self.auto_aim_var.get():
            clip_extension = True
        if path_coords:
            if clip_extension and len(path_coords) >= 2:
                green_coords_to_draw = path_coords[:-1]
            else:
                green_coords_to_draw = path_coords
        if len(green_coords_to_draw) >= 2:
            screen_coords = [self.to_screen(x, y) for x, y in green_coords_to_draw]
            flat_coords = [val for sublist in screen_coords for val in sublist]
            self.canvas.create_line(flat_coords, fill="#00aa00", width=2, tags="scene")

        if loop_detected:
            self.canvas.create_text(10, 10, anchor="nw", text="⚠️ INFINITE LOOP", fill="red", font=("Arial", 14, "bold"), tags="scene")

        # Paste Preview (Ghost)
        if self.clipboard and show_ghost and not self.selecting and not self.dragging_prism_idx and not self.dragging_start:
            mx_raw, my_raw = self.ghost_cursor_pos
            lx, ly = self.to_logical(mx_raw, my_raw) 
            delta_x = lx - self.clipboard_center[0]
            delta_y = ly - self.clipboard_center[1]
            if self.mode_var.get() == "GRID":
                delta_x = round(delta_x / 10) * 10
                delta_y = round(delta_y / 10) * 10

            for p in self.clipboard:
                pred_x = p['x'] + delta_x
                pred_y = p['y'] + delta_y
                sx, sy = self.to_screen(pred_x, pred_y)
                if self.mode_var.get() == "GRID":
                    r = 6
                    self.canvas.create_rectangle(sx-r, sy-r, sx+r, sy+r, outline="gray", dash=(2,2), tags="scene")
                else:
                    r = 5
                    self.canvas.create_oval(sx-r, sy-r, sx+r, sy+r, outline="gray", dash=(2,2), tags="scene")

        # Ghost Ray
        if show_ghost and not loop_detected:
            shooter, _ = self.get_active_shooter()
            anchor_x, anchor_y = shooter['x'], shooter['y']
            sx_anchor, sy_anchor = self.to_screen(anchor_x, anchor_y)
            mx_raw, my_raw = self.ghost_cursor_pos
            lx_snap, ly_snap = self.get_snapped_coords(mx_raw, my_raw)
            sx_snap, sy_snap = self.to_screen(lx_snap, ly_snap)
            self.canvas.create_line(sx_anchor, sy_anchor, sx_snap, sy_snap, fill="#888", dash=(4, 4), tags="scene")
            if self.auto_aim_var.get():
                self.canvas.create_oval(sx_anchor-4, sy_anchor-4, sx_anchor+4, sy_anchor+4, outline="magenta", width=2, tags="scene")

        # Prisms
        for p in self.prisms:
            sx, sy = self.to_screen(p['x'], p['y'])
            color = "blue" if self.mode_var.get() == "GRID" else "orange"
            
            dash_style = ()
            fill_color = color
            if p['id'] in self.cut_ids:
                dash_style = (4, 4)
                fill_color = ""
            elif p['id'] in self.selected_ids:
                color = "#AA00FF" # Violet
                fill_color = color

            if self.mode_var.get() == "GRID":
                r = 6
                self.canvas.create_rectangle(sx-r, sy-r, sx+r, sy+r, fill=fill_color, outline="black", tags="scene", dash=dash_style)
            else:
                r = 5
                self.canvas.create_oval(sx-r, sy-r, sx+r, sy+r, fill=fill_color, outline="black", tags="scene", dash=dash_style)
            self.canvas.create_text(sx, sy-15, text=f"{p['id']}", font=("Arial", 8, "bold"), tags="scene")

        # Start Point
        sx, sy = self.to_screen(self.start_cfg['x'], self.start_cfg['y'])
        self.canvas.create_oval(sx-5, sy-5, sx+5, sy+5, fill="red", tags="scene")
        rad = math.radians(self.start_cfg['angle'])
        ex = sx + 20 * math.cos(rad)
        ey = sy - 20 * math.sin(rad)
        self.canvas.create_line(sx, sy, ex, ey, arrow=tk.LAST, fill="red", width=2, tags="scene")

    # --- LIST & EXPORT ---

    def clear_all(self):
        self.prisms = []
        self.next_id = 1
        self.start_cfg = {'x': 0, 'y': 0, 'angle': 0}
        self.selected_ids = []
        self.draw_scene()
        self.refresh_tree()
        self.save_state_for_undo()

    def update_start_manual(self):
        try:
            self.start_cfg['angle'] = float(self.entry_start.get())
            self.draw_scene()
            self.save_state_for_undo()
        except: pass

    def save_json_file(self):
        try:
            seq, _, _ = prism.calculate_path(self.start_cfg, self.prisms)
        except: seq = []
        
        # 1. Format Start
        start_clean = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in self.start_cfg.items()}
        start_str = json.dumps(start_clean)
        
        # 2. Format Sequence
        seq_str = json.dumps(seq)
        
        # 3. Format Prisms (Compact List)
        prisms_lines = []
        for p in self.prisms:
            p_clean = {
                "id": p['id'],
                "x": int(p['x']) if self.mode_var.get() == "GRID" else round(p['x'], 3),
                "y": int(p['y']) if self.mode_var.get() == "GRID" else round(p['y'], 3),
                "angle": round(p['angle'], 3)
            }
            p_line = json.dumps(p_clean)
            prisms_lines.append(f"        {p_line}")
        
        if prisms_lines:
            prisms_str = "[\n" + ",\n".join(prisms_lines) + "\n      ]"
        else:
            prisms_str = "[]"

        # 4. Construct Final JSON String
        json_output = f'''{{
  "description": "Exported from Prism Editor",
  "property": "findSequence",
  "input": {{
    "start": {start_str},
    "prisms": {prisms_str}
  }},
  "expected": {{
    "sequence": {seq_str}
  }}
}}'''
        
        # LOGIC TO SAVE FILE
        folder = "json_result"
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_{timestamp}.json"
        filepath = os.path.join(folder, filename)
        
        try:
            with open(filepath, "w") as f:
                f.write(json_output)
            messagebox.showinfo("Saved", f"File saved successfully in:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot save file:\n{e}")

    def save_state(self):
        state = {
            'p': self.prisms,
            's': self.start_cfg,
            'n': self.next_id,
            'z': self.zoom,
            'ox': self.offset_x,
            'oy': self.offset_y
        }
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Editor State"
        )
        
        if not filepath:
            return
            
        try:
            with open(filepath, "w") as f:
                json.dump(state, f, separators=(',', ':'))
            messagebox.showinfo("Saved", f"Editor state saved successfully in:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot save state file:\n{e}")

    def load_state(self):
        filepath = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Editor State"
        )
        
        if not filepath:
            return
            
        try:
            with open(filepath, "r") as f:
                state = json.load(f)
            
            self.prisms = state['p']
            self.start_cfg = state['s']
            self.next_id = state['n']
            self.zoom = state['z']
            self.offset_x = state['ox']
            self.offset_y = state['oy']
            
            self.refresh_ui()
            self.save_state_for_undo()
            messagebox.showinfo("Loaded", "Editor state loaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot load state file:\n{e}")

    def toggle_auto_save(self):
        if self.auto_save_var.get():
            self.auto_save_state()
        else:
            if hasattr(self, 'auto_save_timer'):
                self.root.after_cancel(self.auto_save_timer)
    
    def auto_save_state(self):
        state = {
            'p': self.prisms,
            's': self.start_cfg,
            'n': self.next_id,
            'z': self.zoom,
            'ox': self.offset_x,
            'oy': self.offset_y
        }
        
        try:
            with open("autosave.json", "w") as f:
                json.dump(state, f, separators=(',', ':'))
        except Exception as e:
            print(f"Auto-save failed: {e}")
            
        if self.auto_save_var.get():
            self.auto_save_timer = self.root.after(30000, self.auto_save_state)

    def start_pan(self, event):
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y

    def pan_view(self, event):
        dx = event.x - self.last_mouse_x
        dy = event.y - self.last_mouse_y
        self.offset_x += dx
        self.offset_y += dy
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.draw_grid()
        self.draw_scene()

    def save_state_for_undo(self):
        if self.is_undoredo_op:
            return
            
        # If we are not at the end of the history, truncate it
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]

        state = {
            'prisms': copy.deepcopy(self.prisms),
            'start_cfg': copy.deepcopy(self.start_cfg),
            'next_id': self.next_id
        }
        self.history.append(state)
        self.history_index += 1
        
        # Limit history size to prevent memory issues
        if len(self.history) > 50:
            self.history.pop(0)
            self.history_index -= 1

    def undo_action(self, event=None):
        if self.cut_ids:
            self.cut_ids = []
            self.draw_scene()
            return

        if self.history_index > 0:
            self.is_undoredo_op = True
            self.history_index -= 1
            state = self.history[self.history_index]
            self.prisms = copy.deepcopy(state['prisms'])
            self.start_cfg = copy.deepcopy(state['start_cfg'])
            self.next_id = state['next_id']
            self.refresh_ui()
            self.is_undoredo_op = False

    def redo_action(self, event=None):
        if self.history_index < len(self.history) - 1:
            self.is_undoredo_op = True
            self.history_index += 1
            state = self.history[self.history_index]
            self.prisms = copy.deepcopy(state['prisms'])
            self.start_cfg = copy.deepcopy(state['start_cfg'])
            self.next_id = state['next_id']
            self.refresh_ui()
            self.is_undoredo_op = False

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedPrismEditor(root)
    root.mainloop()