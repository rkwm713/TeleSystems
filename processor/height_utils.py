"""
Utility functions for working with height measurements.
"""

import math
import logging
from .photo_data_utils import get_photofirst_data, get_utility_company_names

# Set up logging
logger = logging.getLogger(__name__)

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
    
    # Get all possible utility company name formats
    utility_company_names = get_utility_company_names()

    try:
        node_data = job_data.get('nodes', {}).get(node_id, {})
        photos = node_data.get('photos', {})

        for photo_id, photo_details in photos.items():
            # Use the enhanced photofirst_data extraction function
            photofirst_data = get_photofirst_data(photo_id, photo_details, job_data)
            wires = photofirst_data.get('wire', {})
            
            for wire_id, wire_data in wires.items():
                measured_height = wire_data.get('_measured_height')
                trace_id = wire_data.get('_trace')

                if measured_height is None or trace_id is None:
                    continue

                # Try to convert measured_height to float if it's a string
                try:
                    if isinstance(measured_height, str):
                        measured_height = float(measured_height)
                except (ValueError, TypeError):
                    logger.debug(f"Could not convert measured_height '{measured_height}' to float for wire {wire_id}")
                    continue

                trace_details = job_data.get('traces', {}).get('trace_data', {}).get(trace_id, {})
                company = trace_details.get('company', '').strip()
                cable_type = trace_details.get('cable_type', '').strip()

                # Check if company matches any of the utility company name formats
                company_match = any(company.upper() == util_name.upper() for util_name in utility_company_names)
                
                if company_match:
                    if cable_type.upper() == "PRIMARY":
                        min_primary_inches = min(min_primary_inches, measured_height)
                        logger.debug(f"Found primary wire: {trace_id}, height: {measured_height}")
                    elif cable_type.upper() == "NEUTRAL":
                        min_neutral_inches = min(min_neutral_inches, measured_height)
                        logger.debug(f"Found neutral wire: {trace_id}, height: {measured_height}")
    except Exception as e:
        logger.error(f"Error in get_pole_primary_neutral_heights: {str(e)}")

    primary_height_str = format_height_feet_inches(min_primary_inches if min_primary_inches != float('inf') else None)
    neutral_height_str = format_height_feet_inches(min_neutral_inches if min_neutral_inches != float('inf') else None)

    logger.debug(f"Primary height for node {node_id}: {primary_height_str}")
    logger.debug(f"Neutral height for node {node_id}: {neutral_height_str}")

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
    attacher_name = attacher_name.strip() if attacher_name else ""
    
    if not attacher_name:
        return ""

    try:
        node_data = job_data.get('nodes', {}).get(node_id, {})
        photos = node_data.get('photos', {})

        for photo_id, photo_details in photos.items():
            # Use the enhanced photofirst_data extraction function
            photofirst_data = get_photofirst_data(photo_id, photo_details, job_data)
            wires = photofirst_data.get('wire', {})

            for wire_id, wire_data in wires.items():
                measured_height = wire_data.get('_measured_height')
                trace_id = wire_data.get('_trace')

                if measured_height is None or trace_id is None:
                    continue
                
                # Try to convert measured_height to float if it's a string
                try:
                    if isinstance(measured_height, str):
                        measured_height = float(measured_height)
                except (ValueError, TypeError):
                    logger.debug(f"Could not convert measured_height '{measured_height}' to float for wire {wire_id}")
                    continue
                
                trace_details = job_data.get('traces', {}).get('trace_data', {}).get(trace_id, {})
                company = trace_details.get('company', '').strip()
                cable_type = trace_details.get('cable_type', '').strip()
                
                # Create the full attacher name as it would appear in various formats
                full_attacher = company
                if cable_type:
                    full_attacher = f"{company} {cable_type}"
                
                # Do a more flexible matching on attacher name
                attacher_match = False
                if attacher_name.upper() == company.upper():
                    # Match just on company name
                    attacher_match = True
                elif full_attacher.upper() == attacher_name.upper():
                    # Match on full company + cable type
                    attacher_match = True
                elif attacher_name.upper() in full_attacher.upper():
                    # Partial match (attacher name is part of full attacher description)
                    attacher_match = True
                elif company.upper() in attacher_name.upper():
                    # Partial match (company is part of attacher name)
                    attacher_match = True
                
                if attacher_match:
                    min_attacher_height_inches = min(min_attacher_height_inches, measured_height)
                    logger.debug(f"Found attacher wire: {trace_id}, attacher: {full_attacher}, height: {measured_height}")
    except Exception as e:
        logger.error(f"Error in get_attacher_ground_clearance: {str(e)}")
        
    clearance = format_height_feet_inches(min_attacher_height_inches if min_attacher_height_inches != float('inf') else None)
    logger.debug(f"Ground clearance for attacher '{attacher_name}' on node {node_id}: {clearance}")
    
    return clearance
