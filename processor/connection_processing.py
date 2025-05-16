"""
Functions for processing connection-related data from Katapult JSON.
"""

import math
import logging
from .height_utils import format_height_feet_inches
from .photo_data_utils import get_photofirst_data, get_utility_company_names

# Set up logging
logger = logging.getLogger(__name__)

def get_lowest_heights_for_connection(job_data, connection_id):
    """Get the lowest heights for a connection"""
    lowest_com = float('inf')
    lowest_cps = float('inf')
    connection_data = job_data.get("connections", {}).get(connection_id, {})
    if not connection_data: 
        logger.debug(f"Connection ID {connection_id} not found in job_data")
        return "", ""
        
    sections = connection_data.get("sections", {})
    if not sections: 
        logger.debug(f"No sections found in connection {connection_id}")
        return "", ""
        
    trace_data = job_data.get("traces", {}).get("trace_data", {})
    utility_company_names = get_utility_company_names()
    
    for section_id, section_data_entry in sections.items():
        section_photos_dict = section_data_entry.get("photos", {})
        main_photo_id = next((pid for pid, p_entry in section_photos_dict.items() if p_entry.get("association") == "main"), None)
        if not main_photo_id: 
            logger.debug(f"No main photo found in section {section_id} of connection {connection_id}")
            continue
        
        main_photo_entry = section_photos_dict.get(main_photo_id, {})
        photofirst_data = get_photofirst_data(main_photo_id, main_photo_entry, job_data)
        
        for wire_key, wire in photofirst_data.get("wire", {}).items():
            trace_id = wire.get("_trace")
            if not trace_id or trace_id not in trace_data: 
                continue
                
            trace_info = trace_data[trace_id]
            company = trace_info.get("company", "").strip()
            cable_type = trace_info.get("cable_type", "").strip()
            measured_height = wire.get("_measured_height")
            
            if measured_height is not None:
                try:
                    # Convert to float if it's a string
                    if isinstance(measured_height, str):
                        measured_height = float(measured_height)
                    height = float(measured_height)
                    
                    # Check if company is a utility company using flexible matching
                    is_utility = any(company.upper() == util_name.upper() for util_name in utility_company_names)
                    
                    if is_utility and cable_type.upper() in ["NEUTRAL", "STREET LIGHT"]:
                        lowest_cps = min(lowest_cps, height)
                        logger.debug(f"Found CPS wire in section {section_id}: {cable_type}, height: {height}")
                    elif not is_utility: # Assuming any non-CPS is communication for this purpose
                        lowest_com = min(lowest_com, height)
                        logger.debug(f"Found communication wire in section {section_id}: {company} {cable_type}, height: {height}")
                except (ValueError, TypeError) as e:
                    logger.debug(f"Error converting measured_height '{measured_height}' to float: {str(e)}")
                    continue
    
    lowest_com_formatted = format_height_feet_inches(lowest_com) if lowest_com != float('inf') else ""
    lowest_cps_formatted = format_height_feet_inches(lowest_cps) if lowest_cps != float('inf') else ""
    
    logger.debug(f"Connection {connection_id} - Lowest com height: {lowest_com_formatted}, Lowest CPS height: {lowest_cps_formatted}")
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
    if not attacher_name:
        logger.debug(f"Empty attacher name provided for connection {connection_id}")
        return ""
        
    attacher_name = attacher_name.strip()
    
    connection_data = job_data.get("connections", {}).get(connection_id, {})
    if not connection_data: 
        logger.debug(f"Connection ID {connection_id} not found in job_data")
        return ""
        
    sections = connection_data.get("sections", {})
    if not sections: 
        logger.debug(f"No sections found in connection {connection_id}")
        return ""
        
    trace_data = job_data.get("traces", {}).get("trace_data", {})
    
    lowest_height_for_attacher = float('inf')
    # Stores (section_data_entry, wire_annotation, trace_info_for_wire) for the wire with lowest height
    lowest_height_wire_details = None 
    matched_on = ""
    
    for section_id, section_data_entry in sections.items():
        section_photos_dict = section_data_entry.get("photos", {})
        main_photo_id = next((pid for pid, p_entry in section_photos_dict.items() if p_entry.get("association") == "main"), None)
        if not main_photo_id: 
            logger.debug(f"No main photo found in section {section_id} of connection {connection_id}")
            continue
            
        main_photo_entry = section_photos_dict.get(main_photo_id, {})
        photofirst_data = get_photofirst_data(main_photo_id, main_photo_entry, job_data)
        
        for wire_key, wire_annotation in photofirst_data.get("wire", {}).items():
            trace_id = wire_annotation.get("_trace")
            if not trace_id or trace_id not in trace_data: 
                continue
                
            trace_info_for_wire = trace_data[trace_id]
            company = trace_info_for_wire.get("company", "").strip()
            cable_type = trace_info_for_wire.get("cable_type", "").strip()
            
            if cable_type.upper() == "PRIMARY": 
                continue # Skip primary wires
            
            # Build various formats of attacher name for flexible matching
            current_wire_attacher_formats = [
                company.strip(),
                f"{company} {cable_type}".strip(),
                cable_type.strip()
            ]
            
            # Check for a match using flexible pattern matching
            match_found = False
            for fmt in current_wire_attacher_formats:
                if (fmt.upper() == attacher_name.upper() or 
                    fmt.upper() in attacher_name.upper() or 
                    attacher_name.upper() in fmt.upper()):
                    match_found = True
                    matched_on = fmt
                    break
            
            if match_found:
                measured_height_str = wire_annotation.get("_measured_height")
                if measured_height_str is not None:
                    try:
                        if isinstance(measured_height_str, str):
                            measured_height_str = float(measured_height_str)
                        current_measured_height = float(measured_height_str)
                        if current_measured_height < lowest_height_for_attacher:
                            lowest_height_for_attacher = current_measured_height
                            lowest_height_wire_details = (section_data_entry, wire_annotation, trace_info_for_wire)
                            logger.debug(f"Found matching wire for '{attacher_name}' (matched on '{matched_on}') with height {current_measured_height}")
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Error converting measured_height '{measured_height_str}' to float: {str(e)}")
                        continue
    
    if lowest_height_wire_details:
        # Unpack the details for the wire at its lowest point
        _section_data, wire_at_lowest, trace_info_at_lowest = lowest_height_wire_details
        
        # If the wire itself is marked as 'proposed' in traces, its "proposed height" is its measured height
        if trace_info_at_lowest.get("proposed", False):
            logger.debug(f"Wire is marked as proposed, returning existing height for '{attacher_name}'")
            return format_height_feet_inches(lowest_height_for_attacher)
        
        # Check for moves on this specific wire annotation
        mr_move_str = wire_at_lowest.get("mr_move", "0") # Default to "0" if missing
        effective_moves_dict = wire_at_lowest.get("_effective_moves", {})
        
        total_move_inches = 0.0
        try:
            if isinstance(mr_move_str, str):
                mr_move_str = float(mr_move_str)
            total_move_inches += float(mr_move_str)
            logger.debug(f"mr_move for '{attacher_name}': {mr_move_str}")
        except (ValueError, TypeError) as e:
            logger.debug(f"Error converting mr_move '{mr_move_str}' to float: {str(e)}")
            # mr_move might be invalid, treat as 0

        if isinstance(effective_moves_dict, dict):
            for move_key, move_val_str in effective_moves_dict.items():
                try:
                    if isinstance(move_val_str, str):
                        move_val_str = float(move_val_str)
                    move_val_float = float(move_val_str)
                    
                    if move_val_float > 0:
                        move_contribution = math.ceil(move_val_float / 2.0)
                    elif move_val_float < 0:
                        move_contribution = math.floor(move_val_float / 2.0)
                    else:
                        move_contribution = 0
                        
                    total_move_inches += move_contribution
                    logger.debug(f"effective_move for '{attacher_name}' key '{move_key}': {move_val_float} (contribution: {move_contribution})")
                except (ValueError, TypeError) as e:
                    logger.debug(f"Error processing effective_move '{move_val_str}': {str(e)}")
                    continue
        
        # If there's a significant total move, calculate and return proposed height
        if abs(total_move_inches) > 0.01: # Using a small epsilon for float comparison
            proposed_height_val = lowest_height_for_attacher + total_move_inches
            proposed_height_formatted = format_height_feet_inches(proposed_height_val)
            logger.debug(f"Calculated proposed height for '{attacher_name}': {proposed_height_formatted} (base: {lowest_height_for_attacher}, move: {total_move_inches})")
            return proposed_height_formatted
        else:
            # No significant move, so no "proposed height" distinct from existing
            logger.debug(f"No significant moves found for '{attacher_name}', total move: {total_move_inches}")
            return "" 
    else:
        logger.debug(f"No matching wire found for attacher '{attacher_name}' in connection {connection_id}")        
    
    return "" # Attacher not found in any section, or error
