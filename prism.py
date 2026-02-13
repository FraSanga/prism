import math

def calculate_all_paths(starts, prisms_list, angle_tolerance, max_iterations):
    """
    Calculates the paths for multiple laser beams.
    """
    all_results = []

    for start_config in starts:
        try:
            sequence, path_coords, loop_coords, error_lines = calculate_path(start_config, prisms_list, angle_tolerance, max_iterations)
            all_results.append({
                "sequence": sequence,
                "path_coords": path_coords,
                "loop_coords": loop_coords,
                "error_lines": error_lines,
                "error": None
            })
        except RuntimeError as e:
            all_results.append({
                "sequence": [],
                "path_coords": [],
                "loop_coords": None,
                "error_lines": [],
                "error": str(e)
            })

    return all_results

def calculate_path(start_config, prisms_list, angle_tolerance, max_iterations):
    """
    Calculates the sequence of prisms hit by the ray.
    Returns the path and a boolean indicating if a loop was detected.
    """
    current_x = start_config['x']
    current_y = start_config['y']
    current_angle = start_config['angle']
    
    sequence = []
    path_coords = [(current_x, current_y)]
    error_lines = [] 
    visited_states = {} # state -> index
    iteration = 0
    
    while True:
        iteration += 1
        if iteration > max_iterations:
            raise RuntimeError("Max iterations reached")

        rounded_angle = round(current_angle % 360, 3)
        state = (current_x, current_y, rounded_angle)
        
        if state in visited_states:
            loop_start_index = visited_states[state]
            non_loop_coords = path_coords[:loop_start_index+1]
            loop_coords = path_coords[loop_start_index:]
            return sequence, non_loop_coords, loop_coords, error_lines

        visited_states[state] = len(path_coords) - 1
        
        rad_angle = math.radians(current_angle)
        candidates = []
        
        for p in prisms_list:
            dx = p['x'] - current_x
            dy = p['y'] - current_y
            
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist == 0: 
                continue 
            
            angle_to_point = math.degrees(math.atan2(dy, dx))
            diff = (angle_to_point - current_angle + 180) % 360 - 180
            
            if abs(diff) < angle_tolerance:
                candidates.append((dist, p))

        if not candidates:
            final_len = 15
            end_x = current_x + final_len * math.cos(rad_angle)
            end_y = current_y + final_len * math.sin(rad_angle)
            path_coords.append((end_x, end_y))
            
            err_rad = math.radians(angle_tolerance)
            ex_pos = current_x + final_len * math.cos(rad_angle + err_rad)
            ey_pos = current_y + final_len * math.sin(rad_angle + err_rad)
            ex_neg = current_x + final_len * math.cos(rad_angle - err_rad)
            ey_neg = current_y + final_len * math.sin(rad_angle - err_rad)
            error_lines.append(((current_x, current_y), (ex_pos, ey_pos), (ex_neg, ey_neg)))
            break

        candidates.sort(key=lambda x: x[0])
        dist, best_prism = candidates[0]
        
        sequence.append(best_prism['id'])
        path_coords.append((best_prism['x'], best_prism['y']))
        
        err_rad = math.radians(angle_tolerance)
        ex_pos = current_x + dist * math.cos(rad_angle + err_rad)
        ey_pos = current_y + dist * math.sin(rad_angle + err_rad)
        ex_neg = current_x + dist * math.cos(rad_angle - err_rad)
        ey_neg = current_y + dist * math.sin(rad_angle - err_rad)
        error_lines.append(((current_x, current_y), (ex_pos, ey_pos), (ex_neg, ey_neg)))

        current_x = best_prism['x']
        current_y = best_prism['y']
        current_angle += best_prism['angle'] 

    return sequence, path_coords, None, error_lines

