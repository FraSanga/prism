import math

def calculate_all_paths(starts, prisms_list, angle_tolerance, max_iterations, attenuation_factor=0, attenuation_threshold=0.01):
    """
    Calculates the paths for multiple laser beams with intensity and branching.
    """
    queue = []
    for i, s in enumerate(starts):
        queue.append({
            'x': s['x'], 'y': s['y'], 'angle': s['angle'], 
            'intensity': 1.0, 
            'start_idx': i,
            'path_coords': [(s['x'], s['y'])],
            'visited': {}
        })
    
    combiner_hits = {}
    
    all_segments = [[] for _ in range(len(starts))]
    all_sequences = [[] for _ in range(len(starts))]
    all_loop_coords = [None] * len(starts)
    
    segments_count = 0
    while queue and segments_count < max_iterations:
        ray = queue.pop(0)
        cx, cy, c_angle = ray['x'], ray['y'], ray['angle']
        c_intensity = ray['intensity']
        s_idx = ray['start_idx']
        
        # Loop detection
        rounded_angle = round(c_angle % 360, 3)
        state = (cx, cy, rounded_angle)
        if state in ray['visited']:
            if all_loop_coords[s_idx] is None: # Only handle the first loop detected for a given start
                loop_start_index = ray['visited'][state]
                all_loop_coords[s_idx] = ray['path_coords'][loop_start_index:]
            continue # Stop processing this looped path

        ray['visited'][state] = len(ray['path_coords']) - 1
        
        dist, prism = find_next_hit(cx, cy, c_angle, prisms_list, angle_tolerance)
        
        if prism:
            new_path_coords = ray['path_coords'] + [(prism['x'], prism['y'])]
            
            # Apply attenuation
            new_intensity = c_intensity * ((1.0 - attenuation_factor) ** dist)
            
            if new_intensity < attenuation_threshold:
                # Truncate if needed
                continue

            all_segments[s_idx].append((cx, cy, prism['x'], prism['y'], c_intensity, new_intensity))
            all_sequences[s_idx].append(prism['id'])
            segments_count += 1
            
            p_type = prism.get('type', 'normal')
            p_factor = prism.get('intensity_factor', 1.0)
            p_angle = prism['angle']
            
            # Common properties for next rays in the queue
            next_ray_props = {
                'x': prism['x'], 'y': prism['y'],
                'start_idx': s_idx,
                'path_coords': new_path_coords,
                'visited': ray['visited'].copy()
            }

            if p_type == 'combiner':
                pid = prism['id']
                if pid not in combiner_hits: combiner_hits[pid] = []
                combiner_hits[pid].append({'angle': c_angle, 'intensity': new_intensity, 'props': next_ray_props})
                
                if len(combiner_hits[pid]) >= 2:
                    h1 = combiner_hits[pid].pop(0)
                    h2 = combiner_hits[pid].pop(0)
                    
                    a1 = math.radians(h1['angle']); a2 = math.radians(h2['angle'])
                    avg_angle = math.degrees(math.atan2(math.sin(a1) + math.sin(a2), math.cos(a1) + math.cos(a2)))
                    
                    combined_intensity = min(1.0, (h1['intensity'] + h2['intensity']) * p_factor)
                    
                    if combined_intensity >= attenuation_threshold:
                        queue.append({**h2['props'], 'angle': avg_angle + p_angle, 'intensity': combined_intensity})
                continue
            
            # Other types
            new_rays = []
            if p_type == 'normal':
                new_rays.append({'angle': c_angle + p_angle, 'intensity': new_intensity})
            elif p_type == 'splitter':
                split_intensity = (new_intensity / 2.0) * p_factor
                new_rays.append({'angle': c_angle + p_angle, 'intensity': split_intensity})
                new_rays.append({'angle': c_angle - p_angle, 'intensity': split_intensity})
            elif p_type == 'reducer' or p_type == 'amplifier':
                mod_intensity = min(1.0, new_intensity * p_factor)
                new_rays.append({'angle': c_angle + p_angle, 'intensity': mod_intensity})

            for r in new_rays:
                if r['intensity'] >= attenuation_threshold:
                    queue.append({**next_ray_props, **r})
        else:
            # Final segment logic
            final_len = 1000
            dist = final_len
            if attenuation_factor > 0 and attenuation_factor < 1 and c_intensity > attenuation_threshold:
                 death_dist = math.log(attenuation_threshold / c_intensity) / math.log(1.0 - attenuation_factor)
                 dist = min(final_len, max(0, death_dist))
            elif attenuation_factor >= 1:
                dist = 0
            
            if dist > 0:
                ex = cx + dist * math.cos(math.radians(c_angle))
                ey = cy + dist * math.sin(math.radians(c_angle))
                all_segments[s_idx].append((cx, cy, ex, ey, c_intensity, c_intensity * ((1.0 - attenuation_factor)**dist)))

    results = []
    for i in range(len(starts)):
        results.append({
            "segments": all_segments[i],
            "sequence": all_sequences[i],
            "error": None,
            "path_coords": [], # Kept for compatibility, but segments are primary
            "loop_coords": all_loop_coords[i],
            "error_lines": []
        })
    return results

def calculate_path(start_config, prisms_list, angle_tolerance, max_iterations):
    """
    Simplified calculate_path for backward compatibility in internal calculations (like auto-aim).
    Only follows the first path and ignores intensity/attenuation for simple logic.
    """
    results = calculate_all_paths([start_config], prisms_list, angle_tolerance, max_iterations)
    res = results[0]
    # Reconstruct path_coords from segments for compatibility
    path_coords = []
    if res['segments']:
        path_coords.append((res['segments'][0][0], res['segments'][0][1]))
        for seg in res['segments']:
            path_coords.append((seg[2], seg[3]))
    return res['sequence'], path_coords, None, []

def find_next_hit(current_x, current_y, current_angle, prisms_list, angle_tolerance):
    rad_angle = math.radians(current_angle)
    candidates = []
    for p in prisms_list:
        dx = p['x'] - current_x
        dy = p['y'] - current_y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist < 0.1: continue 
        
        angle_to_point = math.degrees(math.atan2(dy, dx))
        diff = (angle_to_point - current_angle + 180) % 360 - 180
        if abs(diff) < angle_tolerance:
            candidates.append((dist, p))
    
    if not candidates:
        return None, None
    
    candidates.sort(key=lambda x: x[0])
    return candidates[0]
