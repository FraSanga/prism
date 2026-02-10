import math
from matplotlib import pyplot as plt
import json
import os

# --- CONFIGURATION ---
VISUALIZATION_MODE = 'NONE' # Options: PNG, SHOW, NONE
ANGLE_TOLERANCE = 0.001
MAX_ITERATIONS = 1000

# Console colors
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

def calculate_path(start_config, prisms_list):
    """
    Calculates the sequence of prisms hit by the ray.
    Raises RuntimeError if an infinite loop creates more than MAX_ITERATIONS hits.
    """
    current_x = start_config['x']
    current_y = start_config['y']
    current_angle = start_config['angle']
    
    sequence = []
    path_coords = [(current_x, current_y)]
    error_lines = [] 
    iteration = 0
    
    while True:
        iteration += 1
        if iteration > MAX_ITERATIONS:
            raise RuntimeError("Infinite Loop Detected")
        
        rad_angle = math.radians(current_angle)
        candidates = []
        
        for p in prisms_list:
            dx = p['x'] - current_x
            dy = p['y'] - current_y
            
            dist = math.sqrt(dx*dx + dy*dy)
            
            # Avoid self-intersection (ray getting stuck on the prism it just hit)
            if dist == 0: 
                continue 
            
            angle_to_point = math.degrees(math.atan2(dy, dx))
            diff = (angle_to_point - current_angle + 180) % 360 - 180
            
            # Check if point is in the direction of the ray
            if abs(diff) < ANGLE_TOLERANCE:
                candidates.append((dist, p))

        if not candidates:
            # Ray goes to infinity (draw a final segment)
            final_len = 15
            end_x = current_x + final_len * math.cos(rad_angle)
            end_y = current_y + final_len * math.sin(rad_angle)
            path_coords.append((end_x, end_y))
            
            # Calculate final error rays
            err_rad = math.radians(ANGLE_TOLERANCE)
            ex_pos = current_x + final_len * math.cos(rad_angle + err_rad)
            ey_pos = current_y + final_len * math.sin(rad_angle + err_rad)
            ex_neg = current_x + final_len * math.cos(rad_angle - err_rad)
            ey_neg = current_y + final_len * math.sin(rad_angle - err_rad)
            error_lines.append(((current_x, current_y), (ex_pos, ey_pos), (ex_neg, ey_neg)))
            break

        # Sort by distance and pick the closest one
        candidates.sort(key=lambda x: x[0])
        dist, best_prism = candidates[0]
        
        sequence.append(best_prism['id'])
        path_coords.append((best_prism['x'], best_prism['y']))
        
        # Calculate error rays for this segment
        err_rad = math.radians(ANGLE_TOLERANCE)
        ex_pos = current_x + dist * math.cos(rad_angle + err_rad)
        ey_pos = current_y + dist * math.sin(rad_angle + err_rad)
        ex_neg = current_x + dist * math.cos(rad_angle - err_rad)
        ey_neg = current_y + dist * math.sin(rad_angle - err_rad)
        error_lines.append(((current_x, current_y), (ex_pos, ey_pos), (ex_neg, ey_neg)))

        # Update state
        current_x = best_prism['x']
        current_y = best_prism['y']
        current_angle += best_prism['angle'] 

    return sequence, path_coords, error_lines

def generate_plot(case_name, start_cfg, prisms, sequence, path_coords, error_lines, passed):
    if VISUALIZATION_MODE == 'PNG':
        plt.switch_backend('Agg')
        
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Draw Prisms
    if prisms:
        px = [p['x'] for p in prisms]
        py = [p['y'] for p in prisms]
        ids = [p['id'] for p in prisms]
        ax.scatter(px, py, c='blue', s=80, label='Prisms', zorder=5)
        for i, txt in enumerate(ids):
            ax.annotate(f"{txt}\n({prisms[i]['angle']}°)", (px[i], py[i]), 
                        xytext=(0, 10), textcoords='offset points', ha='center', fontsize=8)
    
    # Draw Path
    path_x = [p[0] for p in path_coords]
    path_y = [p[1] for p in path_coords]
    ax.plot(path_x, path_y, c='green', linewidth=1.5, label='Path', zorder=4)
    
    # Draw Start Point
    ax.scatter(start_cfg['x'], start_cfg['y'], c='red', marker='x', s=100, label='Start')
    start_rad = math.radians(start_cfg['angle'])
    ax.arrow(start_cfg['x'], start_cfg['y'], math.cos(start_rad)*2, math.sin(start_rad)*2, 
             head_width=0.5, head_length=0.5, fc='red', ec='red', alpha=0.5)

    # Draw Error Lines
    first_err = True
    for start, end_pos, end_neg in error_lines:
        lbl = rf'$\pm${ANGLE_TOLERANCE}°' if first_err else ""
        ax.plot([start[0], end_pos[0]], [start[1], end_pos[1]], c='orange', linestyle=':', alpha=0.8, label=lbl)
        ax.plot([start[0], end_neg[0]], [start[1], end_neg[1]], c='orange', linestyle=':', alpha=0.8)
        first_err = False

    status_color = 'green' if passed else 'red'
    status_text = "PASS" if passed else "FAIL"
    
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.5)
    
    seq_str = str(sequence) if len(str(sequence)) < 50 else str(sequence)[:47] + "..."
    ax.set_title(f"Test: {case_name} | Seq: {seq_str} | {status_text}", color=status_color, fontweight='bold')
    ax.legend(loc='upper right')
    
    if VISUALIZATION_MODE == 'PNG':
        # Create 'png_result' directory if it doesn't exist
        png_result_dir = 'png_result'
        os.makedirs(png_result_dir, exist_ok=True)
        
        safe_name = "".join([c if c.isalnum() else "_" for c in case_name])
        # Join path safely
        filename = os.path.join(png_result_dir, f"test_{safe_name}.png")
        
        plt.savefig(filename)
        plt.close(fig)
        
    elif VISUALIZATION_MODE == 'SHOW':
        plt.show()

def run_tests():
    filename = 'canonical-data.json'
    
    if not os.path.exists(filename):
        print(f"{RED}Error: File '{filename}' not found.{RESET}")
        return

    try:
        with open(filename, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"{RED}Error: Invalid JSON.{RESET}")
        return

    cases = data.get('cases', [])
    print(f"Running {len(cases)} tests...\n")
    
    passed_count = 0

    for case in cases:
        desc = case['description']
        inp = case['input']
        expected = case['expected']['sequence']
        
        start_cfg = inp['start']
        prisms = inp.get('prisms', [])
        
        actual_seq, path, errs = calculate_path(start_cfg, prisms)
        
        is_correct = (actual_seq == expected)
        
        if is_correct:
            print(f"[{GREEN}PASS{RESET}] {desc}")
            passed_count += 1
        else:
            print(f"[{RED}FAIL{RESET}] {desc}")
            print(f"       Expected: {expected}")
            print(f"       Got:      {actual_seq}")

        if VISUALIZATION_MODE != 'NONE':
            generate_plot(desc, start_cfg, prisms, actual_seq, path, errs, is_correct)

    print(f"\nFinal Results: {passed_count}/{len(cases)} tests passed.")
    if VISUALIZATION_MODE == 'PNG':
        print(f"Graphs saved in the 'png_result' folder.")

if __name__ == "__main__":
    run_tests()