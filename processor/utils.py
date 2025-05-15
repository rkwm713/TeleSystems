"""
Utility functions for the Katapult processor.
"""

import math

def get_nested_value(data_dict, path_keys, default=None):
    """
    Safely retrieves a value from a nested dictionary.
    
    Args:
        data_dict (dict): The dictionary to search
        path_keys (list): List of keys representing the path to the value
        default: Value to return if the path is not found
        
    Returns:
        The value at the specified path, or the default value if not found
    """
    if data_dict is None:
        return default
        
    current_level = data_dict
    for key in path_keys:
        if isinstance(current_level, dict) and key in current_level:
            current_level = current_level[key]
        elif isinstance(current_level, list) and isinstance(key, int) and 0 <= key < len(current_level):
            current_level = current_level[key]
        else:
            return default
    return current_level


def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate the bearing between two points. Returns tuple of (degrees, cardinal_direction)"""
    lat1, lon1, lat2, lon2 = map(lambda x: math.radians(float(x)), [lat1, lon1, lat2, lon2])
    dLon = lon2 - lon1
    y = math.sin(dLon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dLon)
    bearing = (math.degrees(math.atan2(y, x)) + 360) % 360
    directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    cardinal = directions[round(bearing / 45) % 8]
    return (bearing, cardinal)


def compare_scids(scid1, scid2):
    """Compare two SCID numbers, prioritizing base numbers over suffixed ones"""
    scid1, scid2 = str(scid1), str(scid2)
    if scid1 == 'N/A': return 1
    if scid2 == 'N/A': return -1
    scid1_parts, scid2_parts = scid1.split('.'), scid2.split('.')
    try:
        base1, base2 = int(scid1_parts[0].lstrip('0') or '0'), int(scid2_parts[0].lstrip('0') or '0')
        if base1 != base2: return base1 - base2
    except (ValueError, IndexError):
        if scid1_parts[0] != scid2_parts[0]: return -1 if scid1_parts[0] < scid2_parts[0] else 1
    if len(scid1_parts) == 1 and len(scid2_parts) > 1: return -1
    if len(scid1_parts) > 1 and len(scid2_parts) == 1: return 1
    return -1 if scid1 < scid2 else 1
