"""
Functions for extracting data from Katapult JSON structures.
"""

from .utils import get_nested_value
from .height_utils import format_height_feet_inches

def extract_pole_tag(node_data):
    """Extract pole tag from node data"""
    if not node_data:
        return "N/A"
    
    # Check multiple possible locations for pole tag
    pole_tag = get_nested_value(node_data, ['attributes', 'pole_tag', '-Imported', 'tagtext'])
    if not pole_tag:
        pole_tag = get_nested_value(node_data, ['attributes', 'pole_tag', 'tagtext'])
    if not pole_tag:
        pole_tag = get_nested_value(node_data, ['attributes', 'PoleNumber', '-Imported'])
    if not pole_tag:
        pole_tag = get_nested_value(node_data, ['attributes', 'PoleNumber', 'assessment'])
    if not pole_tag:
        pole_tag = get_nested_value(node_data, ['attributes', 'PL_number', '-Imported'])
        
    return str(pole_tag) if pole_tag else "N/A"


def extract_scid(node_data):
    """Extract SCID or operation number from node data"""
    if not node_data:
        return "N/A"
    
    scid = get_nested_value(node_data, ['attributes', 'scid', '-Imported'])
    if not scid:
        scid = get_nested_value(node_data, ['attributes', 'OP_number', '-Imported'])
    
    return str(scid) if scid else "N/A"


def extract_location(node_data):
    """Extract latitude and longitude from node data"""
    if not node_data:
        return None, None
    
    # First try to get coordinates from the main photo
    node_photos = node_data.get('photos', {})
    main_photo_id = next((pid for pid, pdata in node_photos.items() 
                         if pdata.get('association') == 'main'), None)
    
    if main_photo_id:
        photo_data = get_nested_value(node_data, ['photos', main_photo_id], {})
        lat = photo_data.get('latitude')
        lon = photo_data.get('longitude')
        if lat and lon:
            return lat, lon
    
    # Fallback to node attributes if available
    lat = get_nested_value(node_data, ['attributes', 'latitude'])
    lon = get_nested_value(node_data, ['attributes', 'longitude'])
    
    return lat, lon


def extract_span_length(conn_data):
    """Extract span length from connection data"""
    if not conn_data:
        return None
    
    span_length = get_nested_value(conn_data, ['attributes', 'span_length', 'value'])
    if not span_length:
        # Try alternate locations
        span_length = get_nested_value(conn_data, ['attributes', 'length', 'value'])
        if not span_length:
            span_length = get_nested_value(conn_data, ['length'])
    
    try:
        return float(span_length) if span_length else None
    except (ValueError, TypeError):
        return None


def extract_connection_type(conn_data):
    """Extract connection type from connection data"""
    if not conn_data:
        return ""
    
    conn_type = get_nested_value(conn_data, ['attributes', 'connection_type', 'button_added'])
    if not conn_type and isinstance(get_nested_value(conn_data, ['attributes', 'connection_type']), dict):
        # Try to get the first value if it's a dictionary with dynamic keys
        conn_type_dict = get_nested_value(conn_data, ['attributes', 'connection_type'])
        if conn_type_dict:
            first_key = next(iter(conn_type_dict), None)
            if first_key:
                conn_type = conn_type_dict[first_key]
    
    # Fallback to the connection button type
    if not conn_type:
        conn_type = get_nested_value(conn_data, ['button'])
    
    return str(conn_type) if conn_type else ""


def extract_mr_status(node_data):
    """Extract make-ready status from node data"""
    if not node_data:
        return ""
    
    # Check for make-ready status in different possible locations
    mr_status = get_nested_value(node_data, ['attributes', 'mr_state', 'button_added'])
    if not mr_status:
        mr_status = get_nested_value(node_data, ['attributes', 'kat_MR_state', 'button_added'])
    if not mr_status:
        # Check for work type which might indicate MR status
        work_type = get_nested_value(node_data, ['attributes', 'kat_work_type'])
        if isinstance(work_type, dict):
            first_key = next(iter(work_type), None)
            if first_key:
                work_type_val = work_type[first_key]
                if 'make ready' in str(work_type_val).lower():
                    mr_status = work_type_val
    
    return str(mr_status) if mr_status else ""


def extract_pole_owner(node_data):
    """Extract pole owner from node data"""
    if not node_data:
        return ""
    
    owner = get_nested_value(node_data, ['attributes', 'pole_owner', 'multi_added'])
    if not owner:
        owner = get_nested_value(node_data, ['attributes', 'pole_owner', 'button_added'])
    
    # Handle if it's a list
    if isinstance(owner, list) and owner:
        owner = owner[0]
    
    return str(owner) if owner else ""


def extract_pole_structure(node_data):
    """
    Extract comprehensive pole structure information with improved fallback logic.
    
    Args:
        node_data (dict): Node data from Katapult JSON
        
    Returns:
        str: Formatted pole structure string (e.g., "45-3 Southern Pine")
    """
    if not node_data:
        return ""
    
    attrs = get_nested_value(node_data, ['attributes'], {})
    
    # First try proposed_pole_spec if available
    proposed_spec = None
    proposed_spec_data = attrs.get("proposed_pole_spec", {})
    if proposed_spec_data:
        # Get the first non-empty value from the dynamic keys
        for key, value in proposed_spec_data.items():
            if isinstance(value, dict):
                proposed_spec = value.get("value")  # If it's in a value field
            else:
                proposed_spec = value  # If it's direct
            if proposed_spec and proposed_spec != "N/A":
                break
    
    if proposed_spec:
        return proposed_spec
    
    # Fall back to pole_height and pole_class
    height = None
    height_data = attrs.get("pole_height", {}) or attrs.get("height", {})
    if height_data:
        if "one" in height_data:
            height = height_data.get("one")
        else:
            # Try first non-empty value from dynamic keys
            for key, value in height_data.items():
                if value and value != "N/A":
                    height = value
                    break
    
    pole_class = None
    class_data = attrs.get("pole_class", {})
    if class_data:
        if "one" in class_data:
            pole_class = class_data.get("one")
        else:
            # Try first non-empty value from dynamic keys
            for key, value in class_data.items():
                if value and value != "N/A":
                    pole_class = value
                    break
    
    species = ""
    
    # Check birthmark brand for more details
    birthmark_brand = attrs.get('birthmark_brand', {})
    if birthmark_brand and isinstance(birthmark_brand, dict):
        # Get the first key for birthmark details
        first_key = next(iter(birthmark_brand), None)
        if first_key:
            brand_details = birthmark_brand[first_key]
            if not height: 
                height = get_nested_value(brand_details, ['pole_height'])
            if not pole_class: 
                pole_class = get_nested_value(brand_details, ['pole_class'])
            species_code = get_nested_value(brand_details, ['pole_species*'])
            
            # Map species code to full name
            species_map = {"SPC": "Southern Pine", "WRC": "Western Red Cedar", 
                           "DF": "Douglas Fir", "LP": "Lodgepole Pine"}
            species = species_map.get(species_code, species_code if species_code else "")
    
    # Fallback for species
    if not species:
        species_data = attrs.get('pole_species', {})
        if species_data:
            if "one" in species_data:
                species = species_data.get("one")
            else:
                # Try first non-empty value from dynamic keys
                for key, value in species_data.items():
                    if value and value != "N/A":
                        species = value
                        break
    
    # Construct the structure string
    parts = []
    if height: 
        parts.append(str(height))
    if pole_class: 
        parts.append(str(pole_class))
    
    structure_str = "-".join(parts)
    if species:
        structure_str = f"{structure_str} {species}".strip()
    
    return structure_str if structure_str else ""


def extract_pla_percentage(node_data):
    """Extract PLA (Percent Loading Allowance) percentage from node data"""
    if not node_data:
        return ""
    
    # Try different possible paths for PLA data
    pla_val = get_nested_value(node_data, ['attributes', 'final_passing_capacity_%'])
    
    if pla_val and isinstance(pla_val, dict): 
        # It's an object with a dynamic key
        val_key = next(iter(pla_val), None)
        if val_key:
            num_str = pla_val[val_key]
            try:
                return f"{float(num_str):.2f}%"
            except (ValueError, TypeError):
                pass
    
    # Try direct string value
    if isinstance(pla_val, str):
        try:
            return f"{float(pla_val):.2f}%"
        except (ValueError, TypeError):
            pass
    
    # Try alternate paths
    alternate_paths = [
        ['attributes', 'final_passing_capacity_p'],
        ['attributes', 'passing_capacity_%'],
        ['attributes', 'passing_capacity_p']
    ]
    
    for path in alternate_paths:
        alt_val = get_nested_value(node_data, path)
        if alt_val:
            if isinstance(alt_val, dict):
                val_key = next(iter(alt_val), None)
                if val_key:
                    try:
                        return f"{float(alt_val[val_key]):.2f}%"
                    except (ValueError, TypeError):
                        continue
            elif isinstance(alt_val, str):
                try:
                    return f"{float(alt_val):.2f}%"
                except (ValueError, TypeError):
                    continue
    
    return ""


def extract_construction_grade(node_data):
    """Extract construction grade from node data"""
    if not node_data:
        return ""
    
    # Get pole class to map to grade
    pole_class = get_nested_value(node_data, ['attributes', 'pole_class', 'one'])
    
    # Fallback to birthmark data
    if not pole_class:
        birthmark_brand = get_nested_value(node_data, ['attributes', 'birthmark_brand'])
        if birthmark_brand and isinstance(birthmark_brand, dict):
            first_key = next(iter(birthmark_brand), None)
            if first_key:
                brand_details = birthmark_brand[first_key]
                pole_class = get_nested_value(brand_details, ['pole_class'])
    
    if pole_class:
        # Standard mapping from pole class to construction grade
        class_to_grade_map = {
            "1": "B", "2": "C", "3": "C", "4": "D", "5": "D/E",
            "H1": "B", "H2": "C", "H3": "C", "H4": "D", "H5": "D/E"
        }
        return class_to_grade_map.get(str(pole_class), "")
    
    return ""


def extract_proposed_riser(node_data):
    """Extract proposed riser information from node data"""
    if not node_data:
        return "NO"
    
    # Check for riser attribute
    riser_val = get_nested_value(node_data, ['attributes', 'riser', 'button_added'])
    
    # If riser attribute exists and is not explicitly "No", assume YES
    if riser_val and str(riser_val).lower() != 'no':
        return "YES (1)"
    
    # Check for riser in MR notes
    mr_notes = get_nested_value(node_data, ['attributes', 'kat_MR_notes'])
    if mr_notes and isinstance(mr_notes, dict):
        for note_val in mr_notes.values():
            note_text = str(note_val).lower()
            if "riser" in note_text and any(term in note_text for term in ["install", "add", "new", "proposed"]):
                return "YES (1)"
    
    return "NO"


def extract_proposed_guy(node_id, job_data):
    """Extract proposed guy information for a node"""
    if not node_id or not job_data:
        return "NO"
    
    count = 0
    connections = job_data.get('connections', {})
    nodes = job_data.get('nodes', {})
    
    # Check connections for anchor/guy connections
    for conn_data in connections.values():
        if conn_data.get('button') == 'anchor':
            # Check if this connection is connected to our node
            if conn_data.get('node_id_1') == node_id or conn_data.get('node_id_2') == node_id:
                # Identify the anchor node
                anchor_node_id = conn_data.get('node_id_1') if conn_data.get('node_id_1') != node_id else conn_data.get('node_id_2')
                
                if not anchor_node_id or anchor_node_id not in nodes:
                    continue
                
                # Check if anchor is new/proposed
                anchor_node_data = nodes[anchor_node_id]
                anchor_type = get_nested_value(anchor_node_data, ['attributes', 'node_type', 'button_added'])
                
                if anchor_type and 'new' in str(anchor_type).lower():
                    count += 1
    
    # Check MR notes for guy mentions
    node_data = nodes.get(node_id, {})
    mr_notes = get_nested_value(node_data, ['attributes', 'kat_MR_notes'])
    if mr_notes and isinstance(mr_notes, dict):
        for note_val in mr_notes.values():
            note_text = str(note_val).lower()
            if "guy" in note_text and any(term in note_text for term in ["install", "add", "new", "proposed"]):
                count += 1
    
    return f"YES ({count})" if count > 0 else "NO"


def determine_attachment_action(node_data, job_data):
    """Determine the attachment action (Installing/Removing/Existing)"""
    if not node_data:
        return "(E)xisting"
    
    # Default to existing
    action = "(E)xisting"
    
    # Check work type for indications of new installations
    work_type = get_nested_value(node_data, ['attributes', 'kat_work_type'])
    if work_type:
        work_type_val = ""
        if isinstance(work_type, dict):
            first_key = next(iter(work_type), None)
            if first_key:
                work_type_val = str(work_type[first_key]).lower()
        else:
            work_type_val = str(work_type).lower()
        
        if any(term in work_type_val for term in ["make ready", "upgrade", "new", "install"]):
            action = "(I)nstalling"
    
    # Check MR violations/notes for installation indications
    mr_violations = get_nested_value(node_data, ['attributes', 'kat_MR_violations'])
    if mr_violations:
        violation_text = str(mr_violations).lower()
        if "proposed" in violation_text:
            action = "(I)nstalling"
    
    # Check if the node has any proposed attachments in photofirst data
    node_id = node_data.get('id')
    if node_id:
        node_photos = node_data.get('photos', {})
        main_photo_id = next((pid for pid, pdata in node_photos.items() 
                             if pdata.get('association') == 'main'), None)
        
        if main_photo_id:
            photo_data = get_nested_value(job_data, ['photos', main_photo_id], {})
            photofirst_data = photo_data.get('photofirst_data', {})
            
            # Check wire data for proposed flags
            for wire in photofirst_data.get('wire', {}).values():
                trace_id = wire.get('_trace')
                if trace_id:
                    trace_data = get_nested_value(job_data, ['traces', 'trace_data', trace_id], {})
                    if trace_data.get('proposed', False):
                        action = "(I)nstalling"
                        break
    
    return action
