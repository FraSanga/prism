import math

# --- CONFIGURATION ---
ANGLE_TOLERANCE = 0.01
MAX_ITERATIONS = 1000

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
