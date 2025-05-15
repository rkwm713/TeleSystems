"""
Utility functions for working with height measurements.
"""

import math

def format_height_feet_inches(height_float):
    """
    Convert height from inches to feet-inches format.
    
    Args:
        height_float (float): Height in inches
        
    Returns:
        str: Formatted height in feet-inches format (e.g., "10'-6\"")
    """
    if not isinstance(height_float, (int, float)) or height_float is None or math.isnan(height_float):
        return ""
    total_inches = round(height_float)
    feet = total_inches // 12
    inches = total_inches % 12
    return f"{feet}'-{inches}\""

def get_pole_primary_neutral_heights(node_id, job_data, utility_company_name="CPS ENERGY"):
    """
    Extracts the lowest "Primary" and "Neutral" wire heights for a given pole.

    Args:
        node_id (str): The ID of the pole (node).
        job_data (dict): The full JSON data.
        utility_company_name (str, optional): The name of the utility company. Defaults to "CPS ENERGY".

    Returns:
        dict: {'primary_height': "X'-Y\"", 'neutral_height': "X'-Y\""}
              Values are formatted strings or empty if not found.
    """
    min_primary_inches = float('inf')
    min_neutral_inches = float('inf')

    try:
        node_data = job_data.get('nodes', {}).get(node_id, {})
        photos = node_data.get('photos', {})

        for photo_id, photo_details in photos.items():
            photofirst_data = photo_details.get('photofirst_data', {})
            wires = photofirst_data.get('wire', {})
            
            for wire_id, wire_data in wires.items():
                measured_height = wire_data.get('_measured_height')
                trace_id = wire_data.get('_trace')

                if measured_height is None or trace_id is None:
                    continue

                trace_details = job_data.get('traces', {}).get('trace_data', {}).get(trace_id, {})
                company = trace_details.get('company')
                cable_type = trace_details.get('cable_type')

                if company == utility_company_name:
                    if cable_type == "Primary":
                        min_primary_inches = min(min_primary_inches, measured_height)
                    elif cable_type == "Neutral":
                        min_neutral_inches = min(min_neutral_inches, measured_height)
    except Exception:
        # Log error or handle as needed, for now, pass to return defaults
        pass

    primary_height_str = format_height_feet_inches(min_primary_inches if min_primary_inches != float('inf') else None)
    neutral_height_str = format_height_feet_inches(min_neutral_inches if min_neutral_inches != float('inf') else None)

    return {'primary_height': primary_height_str, 'neutral_height': neutral_height_str}

def get_attacher_ground_clearance(node_id, attacher_name, job_data):
    """
    Extracts the lowest wire height for a specific attacher on a given pole.
    This is reported as "Ground Clearance" for that attacher on the pole.

    Args:
        node_id (str): The ID of the pole.
        attacher_name (str): The name of the attacher company.
        job_data (dict): The full JSON data.

    Returns:
        str: "X'-Y\"" representing the attacher's lowest height, or empty string if not found.
    """
    min_attacher_height_inches = float('inf')

    try:
        node_data = job_data.get('nodes', {}).get(node_id, {})
        photos = node_data.get('photos', {})

        for photo_id, photo_details in photos.items():
            photofirst_data = photo_details.get('photofirst_data', {})
            wires = photofirst_data.get('wire', {})

            for wire_id, wire_data in wires.items():
                measured_height = wire_data.get('_measured_height')
                trace_id = wire_data.get('_trace')

                if measured_height is None or trace_id is None:
                    continue
                
                trace_details = job_data.get('traces', {}).get('trace_data', {}).get(trace_id, {})
                company = trace_details.get('company')

                if company == attacher_name:
                    min_attacher_height_inches = min(min_attacher_height_inches, measured_height)
    except Exception:
        # Log error or handle as needed, for now, pass to return default
        pass
        
    return format_height_feet_inches(min_attacher_height_inches if min_attacher_height_inches != float('inf') else None)
