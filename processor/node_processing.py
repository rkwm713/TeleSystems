"""
Functions for processing node-related data from Katapult JSON.
"""

from .height_utils import format_height_feet_inches
from .utils import calculate_bearing

def get_neutral_wire_height(job_data, node_id):
    """Find the height of the neutral wire for a given node"""
    node_photos = job_data.get("nodes", {}).get(node_id, {}).get("photos", {})
    main_photo_id = next((pid for pid, pdata in node_photos.items() if pdata.get("association") == "main"), None)
    
    if main_photo_id:
        photo_data = job_data.get("photos", {}).get(main_photo_id, {})
        photofirst_data = photo_data.get("photofirst_data", {})
        trace_data = job_data.get("traces", {}).get("trace_data", {})
        
        for wire_key, wire in photofirst_data.get("wire", {}).items():
            trace_id = wire.get("_trace")
            if trace_id and trace_id in trace_data:
                trace_info = trace_data[trace_id]
                company = trace_info.get("company", "").strip()
                cable_type = trace_info.get("cable_type", "").strip()
                
                if company.lower() == "cps energy" and cable_type.lower() == "neutral":
                    measured_height = wire.get("_measured_height")
                    if measured_height is not None:
                        try:
                            return float(measured_height)
                        except (ValueError, TypeError):
                            continue
    return None


def get_attachers_from_node_trace(job_data, node_id):
    """Extract attachers from node trace data"""
    attachers = {}
    node_info = job_data.get("nodes", {}).get(node_id, {})
    photo_ids = node_info.get("photos", {})
    main_photo_id = next((pid for pid, pdata in photo_ids.items() if pdata.get("association") == "main"), None)
    if not main_photo_id:
        return {}
    photo_data = job_data.get("photos", {}).get(main_photo_id, {})
    photofirst_data = photo_data.get("photofirst_data", {})
    trace_data = job_data.get("traces", {}).get("trace_data", {})
    
    # First pass: collect all power wires to find the lowest one
    power_wires = {}
    for category in ["wire", "equipment", "guying"]:
        for item_key, item in photofirst_data.get(category, {}).items():
            trace_id = item.get("_trace")
            if not trace_id or trace_id not in trace_data:
                continue
            trace_entry = trace_data[trace_id]
            company = trace_entry.get("company", "").strip()
            type_label = trace_entry.get("cable_type", "") if category in ["wire", "guying"] else trace_entry.get("equipment_type", "")
            if not type_label:
                continue
            
            if company.lower() == "cps energy" and type_label.lower() in ["primary", "neutral", "street light"]:
                measured = item.get("_measured_height")
                if measured is not None:
                    try:
                        measured = float(measured)
                        power_wires[type_label] = (measured, trace_id)
                    except (ValueError, TypeError):
                        continue
    
    lowest_power_wire = None
    lowest_height = float('inf')
    for wire_type, (height, trace_id) in power_wires.items():
        if height < lowest_height:
            lowest_height = height
            lowest_power_wire = (wire_type, trace_id)
    
    for category in ["wire", "equipment", "guying"]:
        for item_key, item in photofirst_data.get(category, {}).items():
            trace_id = item.get("_trace")
            if not trace_id or trace_id not in trace_data:
                continue
            trace_entry = trace_data[trace_id]
            company = trace_entry.get("company", "").strip()
            type_label = trace_entry.get("cable_type", "") if category in ["wire", "guying"] else trace_entry.get("equipment_type", "")
            if not type_label:
                continue
            
            if company.lower() == "cps energy" and type_label.lower() in ["primary", "neutral", "street light"]:
                if not lowest_power_wire or trace_id != lowest_power_wire[1]:
                    continue
            
            attacher_name = type_label if company.lower() == "cps energy" else f"{company} {type_label}"
            attachers[attacher_name] = trace_id
    return attachers


def get_heights_for_node_trace_attachers(job_data, node_id, attacher_trace_map):
    """Get attachment heights for a specific node's attachers"""
    heights = {}
    photo_ids = job_data.get("nodes", {}).get(node_id, {}).get("photos", {})
    main_photo_id = next((pid for pid, pdata in photo_ids.items() if pdata.get("association") == "main"), None)
    if not main_photo_id:
        return heights
    photofirst_data = job_data.get("photos", {}).get(main_photo_id, {}).get("photofirst_data", {})
    all_sections = {**photofirst_data.get("wire", {}), **photofirst_data.get("equipment", {}), **photofirst_data.get("guying", {})}
    for attacher_name, trace_id in attacher_trace_map.items():
        for item_key, item in all_sections.items():
            if item.get("_trace") != trace_id:
                continue
            measured = item.get("_measured_height")
            mr_move = item.get("mr_move", 0)
            if measured is not None:
                try:
                    measured = float(measured)
                    mr_move = float(mr_move) if mr_move else 0.0
                    proposed = measured + mr_move
                    existing_fmt = format_height_feet_inches(measured)
                    proposed_fmt = "" if abs(proposed - measured) < 0.01 else format_height_feet_inches(proposed)
                    heights[attacher_name] = (existing_fmt, proposed_fmt)
                    break
                except Exception as e:
                    print(f"Height parse error for {attacher_name} on node {node_id}: {str(e)}")
    return heights


def get_attachers_for_node(job_data, node_id):
    """Get all attachers for a node including guying and drip loops"""
    main_attacher_data = []
    neutral_height = get_neutral_wire_height(job_data, node_id)
    node_photos = job_data.get("nodes", {}).get(node_id, {}).get("photos", {})
    main_photo_id = next((pid for pid, pdata in node_photos.items() if pdata.get("association") == "main"), None)
    
    if main_photo_id:
        photo_data = job_data.get("photos", {}).get(main_photo_id, {})
        photofirst_data = photo_data.get("photofirst_data", {})
        trace_data = job_data.get("traces", {}).get("trace_data", {})
        
        for wire_key, wire in photofirst_data.get("wire", {}).items():
            trace_id = wire.get("_trace")
            if trace_id and trace_id in trace_data:
                trace_info = trace_data[trace_id]
                company = trace_info.get("company", "").strip()
                cable_type = trace_info.get("cable_type", "").strip()
                
                if cable_type.lower() == "primary":
                    continue
                    
                measured_height = wire.get("_measured_height")
                mr_move = wire.get("mr_move")
                
                if company and cable_type:
                    attacher_name = f"{company} {cable_type}"
                    existing_height = ""
                    proposed_height = ""
                    raw_height = None
                    
                    if measured_height is not None:
                        try:
                            measured_height_float = float(measured_height)
                            raw_height = measured_height_float
                            existing_height = format_height_feet_inches(measured_height_float)
                            
                            if mr_move is not None:
                                try:
                                    mr_move_float = float(mr_move)
                                    proposed_height_value = measured_height_float + mr_move_float
                                    proposed_height = format_height_feet_inches(proposed_height_value)
                                except (ValueError, TypeError):
                                    proposed_height = "" # Keep existing if mr_move is invalid
                        except (ValueError, TypeError):
                            existing_height = ""
                            proposed_height = ""
                            raw_height = 0.0 # Default to 0 if parsing fails
                    
                    main_attacher_data.append({
                        'name': attacher_name,
                        'existing_height': existing_height,
                        'proposed_height': proposed_height,
                        'raw_height': raw_height if raw_height is not None else 0.0,
                        'is_proposed': trace_info.get("proposed", False)
                    })
        
        for guy_key, guy in photofirst_data.get("guying", {}).items():
            trace_id = guy.get("_trace")
            if trace_id and trace_id in trace_data:
                trace_info = trace_data[trace_id]
                company = trace_info.get("company", "").strip()
                cable_type = trace_info.get("cable_type", "").strip()
                measured_height = guy.get("_measured_height")
                mr_move = guy.get("mr_move")
                
                if company and cable_type:
                    is_down_guy = False
                    raw_height_guy = None
                    if measured_height is not None and neutral_height is not None:
                        try:
                            guy_height_float = float(measured_height)
                            raw_height_guy = guy_height_float
                            if guy_height_float < neutral_height:
                                is_down_guy = True
                        except (ValueError, TypeError):
                            pass # Keep is_down_guy as False
                    
                    if is_down_guy:
                        attacher_name = f"{company} {cable_type} (Down Guy)"
                        existing_height = ""
                        proposed_height = ""
                        
                        if raw_height_guy is not None:
                            existing_height = format_height_feet_inches(raw_height_guy)
                            if mr_move is not None:
                                try:
                                    mr_move_float = float(mr_move)
                                    proposed_height_value = raw_height_guy + mr_move_float
                                    proposed_height = format_height_feet_inches(proposed_height_value)
                                except (ValueError, TypeError):
                                    proposed_height = ""
                        
                        main_attacher_data.append({
                            'name': attacher_name,
                            'existing_height': existing_height,
                            'proposed_height': proposed_height,
                            'raw_height': raw_height_guy if raw_height_guy is not None else 0.0,
                            'is_proposed': trace_info.get("proposed", False)
                        })
    
    main_attacher_data.sort(key=lambda x: x['raw_height'], reverse=True)
    reference_spans = get_reference_attachers(job_data, node_id)
    backspan_data, backspan_bearing = get_backspan_attachers(job_data, node_id)
    
    return {
        'main_attachers': main_attacher_data,
        'reference_spans': reference_spans,
        'backspan': {
            'data': backspan_data,
            'bearing': backspan_bearing
        }
    }


def get_reference_attachers(job_data, node_id):
    """Find reference span attachers by finding connections where node_id matches either node_id_1 or node_id_2"""
    reference_info = []
    neutral_height = get_neutral_wire_height(job_data, node_id)
    
    for conn_id, conn_data in job_data.get("connections", {}).items():
        connection_type = conn_data.get("attributes", {}).get("connection_type", {})
        connection_type_value = next(iter(connection_type.values()), "") if isinstance(connection_type, dict) else connection_type.get("button_added", "")
        
        if "reference" in str(connection_type_value).lower() and \
           (conn_data.get("node_id_1") == node_id or conn_data.get("node_id_2") == node_id):
            bearing_str = ""
            sections = conn_data.get("sections", {})
            if sections:
                section_ids = list(sections.keys())
                mid_section_id = section_ids[len(section_ids) // 2]
                mid_section = sections[mid_section_id]
                lat, lon = mid_section.get("latitude"), mid_section.get("longitude")
                
                if lat and lon:
                    from_node = job_data.get("nodes", {}).get(node_id, {})
                    from_photos = from_node.get("photos", {})
                    if from_photos:
                        main_photo_id_from = next((pid for pid, pdata in from_photos.items() if pdata.get("association") == "main"), None)
                        if main_photo_id_from:
                            photo_data_from = job_data.get("photos", {}).get(main_photo_id_from, {})
                            if photo_data_from and "latitude" in photo_data_from and "longitude" in photo_data_from:
                                from_lat, from_lon = photo_data_from["latitude"], photo_data_from["longitude"]
                                degrees, cardinal = calculate_bearing(from_lat, from_lon, lat, lon)
                                bearing_str = f"{cardinal} ({int(degrees)}°)"
                
                photos_mid = mid_section.get("photos", {})
                main_photo_id_mid = next((pid for pid, pdata in photos_mid.items() if pdata.get("association") == "main"), None)
                if main_photo_id_mid:
                    photo_data_mid = job_data.get("photos", {}).get(main_photo_id_mid, {})
                    if not photo_data_mid: continue
                    photofirst_data_mid = photo_data_mid.get("photofirst_data", {})
                    if not photofirst_data_mid: continue
                    
                    span_data = []
                    trace_data = job_data.get("traces", {}).get("trace_data", {})
                    
                    for wire_key, wire in photofirst_data_mid.get("wire", {}).items():
                        trace_id = wire.get("_trace")
                        if not trace_id or trace_id not in trace_data: continue
                        trace_info = trace_data[trace_id]
                        company, cable_type = trace_info.get("company", "").strip(), trace_info.get("cable_type", "").strip()
                        if cable_type.lower() == "primary": continue
                        
                        measured_height = wire.get("_measured_height")
                        mr_move = wire.get("mr_move", 0)
                        effective_moves = wire.get("_effective_moves", {})
                        
                        if company and cable_type and measured_height is not None:
                            try:
                                measured_height_float = float(measured_height)
                                attacher_name = f"{company} {cable_type}"
                                existing_height = format_height_feet_inches(measured_height_float)
                                proposed_height = ""
                                total_move = float(mr_move) if mr_move else 0.0
                                for move_val in (effective_moves or {}).values(): # Ensure effective_moves is not None
                                    try: total_move += float(move_val)
                                    except (ValueError, TypeError): continue
                                if abs(total_move) > 0.001: # Check for significant move
                                    proposed_height_value = measured_height_float + total_move
                                    proposed_height = format_height_feet_inches(proposed_height_value)
                                span_data.append({'name': attacher_name, 'existing_height': existing_height, 'proposed_height': proposed_height, 'raw_height': measured_height_float, 'is_reference': True})
                            except (ValueError, TypeError): continue
                    
                    for guy_key, guy in photofirst_data_mid.get("guying", {}).items():
                        trace_id = guy.get("_trace")
                        if not trace_id or trace_id not in trace_data: continue
                        trace_info = trace_data[trace_id]
                        company, cable_type = trace_info.get("company", "").strip(), trace_info.get("cable_type", "").strip()
                        measured_height = guy.get("_measured_height")
                        mr_move = guy.get("mr_move", 0)
                        effective_moves = guy.get("_effective_moves", {})
                        
                        if company and cable_type and measured_height is not None and neutral_height is not None:
                            try:
                                guy_height_float = float(measured_height)
                                if guy_height_float < neutral_height:
                                    attacher_name = f"{company} {cable_type} (Down Guy)"
                                    existing_height = format_height_feet_inches(guy_height_float)
                                    proposed_height = ""
                                    total_move = float(mr_move) if mr_move else 0.0
                                    for move_val in (effective_moves or {}).values(): # Ensure effective_moves is not None
                                        try: total_move += float(move_val)
                                        except (ValueError, TypeError): continue
                                    if abs(total_move) > 0.001: # Check for significant move
                                        proposed_height_value = guy_height_float + total_move
                                        proposed_height = format_height_feet_inches(proposed_height_value)
                                    span_data.append({'name': attacher_name, 'existing_height': existing_height, 'proposed_height': proposed_height, 'raw_height': guy_height_float, 'is_reference': True})
                            except (ValueError, TypeError): continue
                    
                    span_data.sort(key=lambda x: x['raw_height'], reverse=True)
                    if span_data:
                        reference_info.append({'bearing': bearing_str, 'data': span_data})
    return reference_info


def get_backspan_attachers(job_data, node_id):
    """
    Get backspan attachers information for a node.
    
    Args:
        job_data (dict): The Katapult JSON data
        node_id (str): The node ID to find backspan attachers for
        
    Returns:
        tuple: (list_of_attacher_data, bearing_string)
    """
    backspan_data = []
    bearing_str = ""
    
    neutral_height = get_neutral_wire_height(job_data, node_id)
    
    # Determine what connections could be considered "backspan"
    # Generally we look for overhead connections from this pole to another pole
    # and consider the direction with most connections or a specific designation
    node_photos = job_data.get("nodes", {}).get(node_id, {}).get("photos", {})
    node_lat, node_lon = None, None
    
    # Get node location
    main_photo_id = next((pid for pid, pdata in node_photos.items() 
                         if pdata.get("association") == "main"), None)
    if main_photo_id:
        photo_data = job_data.get("photos", {}).get(main_photo_id, {})
        if photo_data:
            node_lat, node_lon = photo_data.get("latitude"), photo_data.get("longitude")
    
    if not node_lat or not node_lon:
        return backspan_data, bearing_str
    
    # Find connections that match criteria for backspan
    potential_backspans = []
    
    for conn_id, conn_data in job_data.get("connections", {}).items():
        # Skip if this isn't a connection from our node
        if conn_data.get("node_id_1") != node_id and conn_data.get("node_id_2") != node_id:
            continue
            
        # Skip certain connection types that can't be backspans
        conn_button = conn_data.get("button", "").lower()
        if conn_button in ["anchor", "ug_poly_path"]:  # Skip anchors and underground connections
            continue
            
        # Get the other node in this connection
        other_node_id = conn_data.get("node_id_2") if conn_data.get("node_id_1") == node_id else conn_data.get("node_id_1")
        if not other_node_id or other_node_id not in job_data.get("nodes", {}):
            continue
            
        # Check if this connection is marked as a backspan in attributes
        is_backspan = False
        connection_type = conn_data.get("attributes", {}).get("connection_type", {})
        
        if isinstance(connection_type, dict):
            for type_val in connection_type.values():
                if isinstance(type_val, str) and "back" in type_val.lower():
                    is_backspan = True
                    break
        elif isinstance(connection_type, str) and "back" in connection_type.lower():
            is_backspan = True
            
        # Find midpoint section to calculate bearing
        sections = conn_data.get("sections", {})
        mid_section_id = None
        mid_lat, mid_lon = None, None
        
        if sections:
            section_ids = list(sections.keys())
            # Use the middle section for most accurate midpoint
            mid_section_id = section_ids[len(section_ids) // 2]
            mid_section = sections[mid_section_id]
            mid_lat, mid_lon = mid_section.get("latitude"), mid_section.get("longitude")
            
        if mid_lat and mid_lon:
            # Calculate bearing from our node to the midpoint
            bearing_tuple = calculate_bearing(node_lat, node_lon, mid_lat, mid_lon)
            
            # Add to potential backspans
            potential_backspans.append({
                'conn_id': conn_id,
                'other_node_id': other_node_id,
                'is_backspan_marked': is_backspan,
                'bearing': bearing_tuple[0],  # Numeric bearing
                'cardinal': bearing_tuple[1],  # Cardinal direction
                'mid_section_id': mid_section_id
            })
    
    # Choose the backspan based on priority:
    # 1. Connection explicitly marked as a backspan
    # 2. If no marked backspan, choose the one most directly behind the pole
    
    chosen_backspan = None
    
    # First try to find a connection explicitly marked as backspan
    marked_backspans = [bs for bs in potential_backspans if bs['is_backspan_marked']]
    if marked_backspans:
        chosen_backspan = marked_backspans[0]
    elif potential_backspans:
        # If no marked backspan, find the one that's most in the opposite direction
        # from the majority of connections - this is typically the backspan
        
        # Calculate the average bearing of all connections
        all_bearings = [bs['bearing'] for bs in potential_backspans]
        if not all_bearings:
            return backspan_data, bearing_str
            
        # Calculate the average bearing (considering the circular nature of bearings)
        avg_sin = sum(math.sin(math.radians(b)) for b in all_bearings) / len(all_bearings)
        avg_cos = sum(math.cos(math.radians(b)) for b in all_bearings) / len(all_bearings)
        avg_bearing = (math.degrees(math.atan2(avg_sin, avg_cos)) + 360) % 360
        
        # Find the connection most opposite to the average bearing (about 180 degrees difference)
        # This is likely the backspan
        chosen_backspan = min(potential_backspans, 
                              key=lambda bs: abs(((bs['bearing'] - avg_bearing + 180) % 360) - 180))
    
    # If we found a backspan, extract the attachment data
    if chosen_backspan:
        # Set the bearing string
        bearing_str = f"{chosen_backspan['cardinal']} ({int(chosen_backspan['bearing'])}°)"
        
        # Get the midpoint section data
        conn_data = job_data.get("connections", {}).get(chosen_backspan['conn_id'], {})
        sections = conn_data.get("sections", {})
        mid_section_id = chosen_backspan['mid_section_id']
        
        if sections and mid_section_id and mid_section_id in sections:
            mid_section = sections[mid_section_id]
            photos = mid_section.get("photos", {})
            main_photo_id = next((pid for pid, pdata in photos.items() 
                                 if pdata.get("association") == "main"), None)
            
            if main_photo_id:
                photo_data = job_data.get("photos", {}).get(main_photo_id, {})
                if not photo_data: 
                    return backspan_data, bearing_str
                    
                photofirst_data = photo_data.get("photofirst_data", {})
                if not photofirst_data: 
                    return backspan_data, bearing_str
                
                trace_data = job_data.get("traces", {}).get("trace_data", {})
                
                # Extract wire attachments
                for wire_key, wire in photofirst_data.get("wire", {}).items():
                    trace_id = wire.get("_trace")
                    if not trace_id or trace_id not in trace_data: 
                        continue
                        
                    trace_info = trace_data[trace_id]
                    company = trace_info.get("company", "").strip()
                    cable_type = trace_info.get("cable_type", "").strip()
                    
                    # Skip primary
                    if cable_type.lower() == "primary":
                        continue
                    
                    measured_height = wire.get("_measured_height")
                    mr_move = wire.get("mr_move", 0)
                    effective_moves = wire.get("_effective_moves", {})
                    
                    if company and cable_type and measured_height is not None:
                        try:
                            measured_height_float = float(measured_height)
                            attacher_name = f"{company} {cable_type}"
                            existing_height = format_height_feet_inches(measured_height_float)
                            proposed_height = ""
                            
                            # Calculate total movement from MR moves and effective moves
                            total_move = float(mr_move) if mr_move else 0.0
                            if effective_moves:
                                for move_val in effective_moves.values():
                                    try:
                                        total_move += float(move_val)
                                    except (ValueError, TypeError):
                                        continue
                            
                            # If there's a significant move, calculate proposed height
                            if abs(total_move) > 0.001:
                                proposed_height_value = measured_height_float + total_move
                                proposed_height = format_height_feet_inches(proposed_height_value)
                                
                            backspan_data.append({
                                'name': attacher_name,
                                'existing_height': existing_height,
                                'proposed_height': proposed_height,
                                'raw_height': measured_height_float,
                                'is_backspan': True
                            })
                        except (ValueError, TypeError):
                            continue
                
                # Extract guy attachments
                for guy_key, guy in photofirst_data.get("guying", {}).items():
                    trace_id = guy.get("_trace")
                    if not trace_id or trace_id not in trace_data:
                        continue
                        
                    trace_info = trace_data[trace_id]
                    company = trace_info.get("company", "").strip()
                    cable_type = trace_info.get("cable_type", "").strip()
                    measured_height = guy.get("_measured_height")
                    mr_move = guy.get("mr_move", 0)
                    effective_moves = guy.get("_effective_moves", {})
                    
                    # Only include down guys (below neutral)
                    if company and cable_type and measured_height is not None and neutral_height is not None:
                        try:
                            guy_height_float = float(measured_height)
                            if guy_height_float < neutral_height:  # It's a down guy
                                attacher_name = f"{company} {cable_type} (Down Guy)"
                                existing_height = format_height_feet_inches(guy_height_float)
                                proposed_height = ""
                                
                                # Calculate total movement
                                total_move = float(mr_move) if mr_move else 0.0
                                if effective_moves:
                                    for move_val in effective_moves.values():
                                        try:
                                            total_move += float(move_val)
                                        except (ValueError, TypeError):
                                            continue
                                
                                # If there's a significant move, calculate proposed height
                                if abs(total_move) > 0.001:
                                    proposed_height_value = guy_height_float + total_move
                                    proposed_height = format_height_feet_inches(proposed_height_value)
                                
                                backspan_data.append({
                                    'name': attacher_name,
                                    'existing_height': existing_height,
                                    'proposed_height': proposed_height,
                                    'raw_height': guy_height_float,
                                    'is_backspan': True
                                })
                        except (ValueError, TypeError):
                            continue
                
                # Sort by height descending
                backspan_data.sort(key=lambda x: x['raw_height'], reverse=True)
    
    return backspan_data, bearing_str
