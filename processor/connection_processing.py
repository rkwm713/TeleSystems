"""
Functions for processing connection-related data from Katapult JSON.
"""

import math
from .height_utils import format_height_feet_inches

def get_lowest_heights_for_connection(job_data, connection_id):
    """Get the lowest heights for a connection"""
    lowest_com = float('inf')
    lowest_cps = float('inf')
    connection_data = job_data.get("connections", {}).get(connection_id, {})
    if not connection_data: return "", ""
    sections = connection_data.get("sections", {})
    if not sections: return "", ""
    trace_data = job_data.get("traces", {}).get("trace_data", {})
    
    for section_id, section_data in sections.items():
        photos = section_data.get("photos", {})
        main_photo_id = next((pid for pid, pdata in photos.items() if pdata.get("association") == "main"), None)
        if not main_photo_id: continue
        photo_data = job_data.get("photos", {}).get(main_photo_id, {})
        photofirst_data = photo_data.get("photofirst_data", {})
        
        for wire_key, wire in photofirst_data.get("wire", {}).items():
            trace_id = wire.get("_trace")
            if not trace_id or trace_id not in trace_data: continue
            trace_info = trace_data[trace_id]
            company = trace_info.get("company", "").strip()
            cable_type = trace_info.get("cable_type", "").strip()
            measured_height = wire.get("_measured_height")
            
            if measured_height is not None:
                try:
                    height = float(measured_height)
                    if company.lower() == "cps energy" and cable_type.lower() in ["neutral", "street light"]:
                        lowest_cps = min(lowest_cps, height)
                    elif company.lower() != "cps energy":
                        lowest_com = min(lowest_com, height)
                except (ValueError, TypeError):
                    continue
    
    lowest_com_formatted = format_height_feet_inches(lowest_com) if lowest_com != float('inf') else ""
    lowest_cps_formatted = format_height_feet_inches(lowest_cps) if lowest_cps != float('inf') else ""
    return lowest_com_formatted, lowest_cps_formatted

def get_midspan_proposed_heights(job_data, connection_id, attacher_name):
    """
    Get the proposed height for a specific attacher in the connection's span.
    
    For each wire:
    1. Find the section with the lowest measured height
    2. Use that section to check for mr_move or effective_moves
    3. If there are moves (nonzero), calculate and return the proposed height
    4. If no moves, return empty string
    
    Args:
        job_data (dict): The Katapult JSON data
        connection_id (str): The connection ID to analyze
        attacher_name (str): The attacher name to find
        
    Returns:
        str: Formatted proposed height or empty string if no changes
    """
    # Get the connection data
    connection_data = job_data.get("connections", {}).get(connection_id, {})
    if not connection_data:
        return ""
        
    # Get sections from the connection
    sections = connection_data.get("sections", {})
    if not sections:
        return ""
        
    # Get trace_data
    trace_data = job_data.get("traces", {}).get("trace_data", {})
    
    # Store the lowest height section for this attacher
    lowest_height = float('inf')
    lowest_section = None
    
    # First pass: find the section with the lowest measured height for this attacher
    for section_id, section_data in sections.items():
        photos = section_data.get("photos", {})
        main_photo_id = next((pid for pid, pdata in photos.items() if pdata.get("association") == "main"), None)
        if not main_photo_id:
            continue
            
        # Get photofirst_data
        photo_data = job_data.get("photos", {}).get(main_photo_id, {})
        photofirst_data = photo_data.get("photofirst_data", {})
        
        # Process wire data
        for wire_key, wire in photofirst_data.get("wire", {}).items():
            trace_id = wire.get("_trace")
            if not trace_id or trace_id not in trace_data:
                continue
                
            trace_info = trace_data[trace_id]
            company = trace_info.get("company", "").strip()
            cable_type = trace_info.get("cable_type", "").strip()
            
            # Skip if cable_type is "Primary"
            if cable_type.lower() == "primary":
                continue
            
            # Construct the attacher name the same way as in the main list
            current_attacher = f"{company} {cable_type}"
            
            if current_attacher.strip() == attacher_name.strip():
                measured_height = wire.get("_measured_height")
                if measured_height is not None:
                    try:
                        measured_height = float(measured_height)
                        if measured_height < lowest_height:
                            lowest_height = measured_height
                            lowest_section = (section_data, wire, trace_info)
                    except (ValueError, TypeError):
                        continue
    
    # If we found a section with this attacher
    if lowest_section:
        section_data, wire, trace_info = lowest_section
        
        # Check if this is a proposed wire
        is_proposed = trace_info.get("proposed", False)
        if is_proposed:
            return format_height_feet_inches(lowest_height)
        
        # Check for moves
        mr_move = wire.get("mr_move", 0)
        effective_moves = wire.get("_effective_moves", {})
        
        # Only consider nonzero moves
        has_mr_move = False
        try:
            has_mr_move = abs(float(mr_move)) > 0.01
        except (ValueError, TypeError):
            has_mr_move = False
            
        has_effective_move = any(abs(float(mv)) > 0.01 for mv in effective_moves.values() 
                               if _is_number(mv))
        
        if not has_mr_move and not has_effective_move:
            return ""
        
        # Calculate total move
        total_move = float(mr_move) if has_mr_move else 0.0
        if has_effective_move:
            for move in effective_moves.values():
                try:
                    move_value = float(move)
                    # Only add if nonzero
                    if abs(move_value) > 0.01:
                        # Round up half of the move
                        half_move = -(-move_value // 2) if move_value > 0 else (move_value // 2)
                        total_move += half_move
                except (ValueError, TypeError):
                    continue
                    
        # Calculate proposed height
        proposed_height = lowest_height + total_move
        return format_height_feet_inches(proposed_height)
    
    return ""  # Return empty string if no section found or if there was an error

def _is_number(value):
    """Helper function to check if a value can be converted to a float"""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False
