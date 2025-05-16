"""
Functions for processing connection-related data from Katapult JSON.
"""

import math
from .height_utils import format_height_feet_inches
from .photo_data_utils import get_photofirst_data # Added import

def get_lowest_heights_for_connection(job_data, connection_id):
    """Get the lowest heights for a connection"""
    lowest_com = float('inf')
    lowest_cps = float('inf')
    connection_data = job_data.get("connections", {}).get(connection_id, {})
    if not connection_data: return "", ""
    sections = connection_data.get("sections", {})
    if not sections: return "", ""
    trace_data = job_data.get("traces", {}).get("trace_data", {})
    
    for section_id, section_data_entry in sections.items(): # Renamed section_data to section_data_entry
        section_photos_dict = section_data_entry.get("photos", {}) # Renamed photos
        main_photo_id = next((pid for pid, p_entry in section_photos_dict.items() if p_entry.get("association") == "main"), None)
        if not main_photo_id: continue
        
        main_photo_entry = section_photos_dict.get(main_photo_id, {})
        photofirst_data = get_photofirst_data(main_photo_id, main_photo_entry, job_data)
        
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
                    elif company.lower() != "cps energy": # Assuming any non-CPS is communication for this purpose
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
    1. Find the section with the lowest measured height for the attacher
    2. Use that section's wire data to check for mr_move or effective_moves
    3. If there are moves (nonzero), calculate and return the proposed height
    4. If no moves, or if the wire is marked 'proposed', return existing height or empty.
    
    Args:
        job_data (dict): The Katapult JSON data
        connection_id (str): The connection ID to analyze
        attacher_name (str): The attacher name to find (e.g., "ATT Fiber")
        
    Returns:
        str: Formatted proposed height or empty string if no changes / not applicable
    """
    connection_data = job_data.get("connections", {}).get(connection_id, {})
    if not connection_data: return ""
        
    sections = connection_data.get("sections", {})
    if not sections: return ""
        
    trace_data = job_data.get("traces", {}).get("trace_data", {})
    
    lowest_height_for_attacher = float('inf')
    # Stores (section_data_entry, wire_annotation, trace_info_for_wire) for the wire with lowest height
    lowest_height_wire_details = None 
    
    for section_id, section_data_entry in sections.items():
        section_photos_dict = section_data_entry.get("photos", {})
        main_photo_id = next((pid for pid, p_entry in section_photos_dict.items() if p_entry.get("association") == "main"), None)
        if not main_photo_id: continue
            
        main_photo_entry = section_photos_dict.get(main_photo_id, {})
        photofirst_data = get_photofirst_data(main_photo_id, main_photo_entry, job_data)
        
        for wire_key, wire_annotation in photofirst_data.get("wire", {}).items():
            trace_id = wire_annotation.get("_trace")
            if not trace_id or trace_id not in trace_data: continue
                
            trace_info_for_wire = trace_data[trace_id]
            company = trace_info_for_wire.get("company", "").strip()
            cable_type = trace_info_for_wire.get("cable_type", "").strip()
            
            if cable_type.lower() == "primary": continue # Skip primary wires
            
            current_wire_attacher_name = f"{company} {cable_type}".strip()
            
            if current_wire_attacher_name == attacher_name.strip():
                measured_height_str = wire_annotation.get("_measured_height")
                if measured_height_str is not None:
                    try:
                        current_measured_height = float(measured_height_str)
                        if current_measured_height < lowest_height_for_attacher:
                            lowest_height_for_attacher = current_measured_height
                            lowest_height_wire_details = (section_data_entry, wire_annotation, trace_info_for_wire)
                    except (ValueError, TypeError):
                        continue
    
    if lowest_height_wire_details:
        # Unpack the details for the wire at its lowest point
        _section_data, wire_at_lowest, trace_info_at_lowest = lowest_height_wire_details
        
        # If the wire itself is marked as 'proposed' in traces, its "proposed height" is its measured height
        if trace_info_at_lowest.get("proposed", False):
            return format_height_feet_inches(lowest_height_for_attacher)
        
        # Check for moves on this specific wire annotation
        mr_move_str = wire_at_lowest.get("mr_move", "0") # Default to "0" if missing
        effective_moves_dict = wire_at_lowest.get("_effective_moves", {})
        
        total_move_inches = 0.0
        try:
            total_move_inches += float(mr_move_str)
        except (ValueError, TypeError):
            pass # mr_move might be invalid, treat as 0

        if isinstance(effective_moves_dict, dict):
            for move_val_str in effective_moves_dict.values():
                try:
                    # As per original logic: "Round up half of the move" - this seems specific.
                    # Replicating: -(-val // 2) for positive, (val // 2) for negative.
                    # This is effectively math.ceil(val / 2) for positive and math.floor(val / 2) for negative.
                    # Or more simply, if we assume moves are integers:
                    move_val_float = float(move_val_str)
                    if move_val_float > 0:
                        total_move_inches += math.ceil(move_val_float / 2.0)
                    elif move_val_float < 0:
                         total_move_inches += math.floor(move_val_float / 2.0)
                    # If move_val_float is 0, it adds 0.
                except (ValueError, TypeError):
                    continue
        
        # If there's a significant total move, calculate and return proposed height
        if abs(total_move_inches) > 0.01: # Using a small epsilon for float comparison
            proposed_height_val = lowest_height_for_attacher + total_move_inches
            return format_height_feet_inches(proposed_height_val)
        else:
            # No significant move, so no "proposed height" distinct from existing
            return "" 
            
    return "" # Attacher not found in any section, or error

# _is_number helper is not strictly needed with try-except blocks for float conversion,
# but can be kept if used elsewhere or for explicit pre-checks.
# For now, removing it as direct float conversions with try-except are used.
