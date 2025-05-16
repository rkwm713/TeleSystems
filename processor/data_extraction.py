"""
Functions for extracting data from Katapult JSON structures.
"""

from .utils import get_nested_value
from .height_utils import format_height_feet_inches

def extract_pole_tag(node_data):
    """Extract pole tag from node data, prioritizing documented fields."""
    if not node_data:
        return "N/A"
    
    attributes = node_data.get('attributes', {})
    if not attributes:
        return "N/A"

    # Priority 1: PoleNumber (assessment or -Imported)
    pole_tag = get_nested_value(attributes, ['PoleNumber', 'assessment'])
    if not pole_tag:
        pole_tag = get_nested_value(attributes, ['PoleNumber', '-Imported'])
    
    # Priority 2: PL_number (assessment or -Imported)
    if not pole_tag:
        pole_tag = get_nested_value(attributes, ['PL_number', 'assessment'])
    if not pole_tag:
        pole_tag = get_nested_value(attributes, ['PL_number', '-Imported'])

    # Priority 3: electric_pole_tag (assessment or -Imported)
    if not pole_tag:
        pole_tag = get_nested_value(attributes, ['electric_pole_tag', 'assessment'])
    if not pole_tag:
        pole_tag = get_nested_value(attributes, ['electric_pole_tag', '-Imported'])

    # Priority 4: DLOC_number (assessment or -Imported) - from work-flow.md
    if not pole_tag:
        pole_tag = get_nested_value(attributes, ['DLOC_number', 'assessment'])
    if not pole_tag:
        pole_tag = get_nested_value(attributes, ['DLOC_number', '-Imported'])

    # Fallback to older 'pole_tag' attribute if others are not found
    if not pole_tag:
        pole_tag = get_nested_value(attributes, ['pole_tag', 'tagtext'])
    if not pole_tag:
         pole_tag = get_nested_value(attributes, ['pole_tag', '-Imported', 'tagtext']) # Less common variant

    return str(pole_tag) if pole_tag else "N/A"


def extract_scid(node_data):
    """Extract SCID or operation number from node data"""
    if not node_data:
        return "N/A"
    
    scid = get_nested_value(node_data, ['attributes', 'scid', '-Imported'])
    if not scid:
        scid = get_nested_value(node_data, ['attributes', 'OP_number', '-Imported']) # OP_number seems like a reasonable fallback
    
    return str(scid) if scid else "N/A"


def extract_location(node_data):
    """Extract latitude and longitude from node data"""
    if not node_data:
        return None, None
    
    # Priority 1: Direct latitude/longitude on the node object (as per Katapult JSON Guide Snippet A)
    lat = node_data.get('latitude')
    lon = node_data.get('longitude')
    if lat is not None and lon is not None: # Check for not None, as 0 is a valid coordinate
        return lat, lon

    # Priority 2: Coordinates from the main photo associated with the node
    node_photos = node_data.get('photos', {})
    main_photo_id = next((pid for pid, pdata in node_photos.items() 
                         if pdata.get('association') == 'main'), None)
    
    if main_photo_id:
        # The photo entry itself under node_data.photos might contain lat/lon
        photo_entry = node_photos.get(main_photo_id, {})
        lat = photo_entry.get('latitude')
        lon = photo_entry.get('longitude')
        if lat is not None and lon is not None:
            return lat, lon
        
        # Fallback: Check top-level 'photos' or 'photo_summary' if node's photo entry doesn't have it
        # This part is more complex as get_photofirst_data utility is for 'photofirst_data', not direct lat/lon
        # For now, we assume if it's in a photo, it's in the photo_entry under the node.
        # If Katapult JSONs store main photo lat/lon *only* in a top-level photos/photo_summary, this might need adjustment.

    # Priority 3: Fallback to node attributes (less common for primary coordinates)
    lat = get_nested_value(node_data, ['attributes', 'latitude'])
    lon = get_nested_value(node_data, ['attributes', 'longitude'])
    if lat is not None and lon is not None:
        return lat, lon
    
    return None, None # Return None, None if not found


def extract_span_length(conn_data):
    """Extract span length from connection data"""
    if not conn_data:
        return None
    
    # Primary documented path for span length seems to be under attributes
    span_length = get_nested_value(conn_data, ['attributes', 'span_length', 'value']) 
    if not span_length:
        # Alternative from observation
        span_length = get_nested_value(conn_data, ['attributes', 'length', 'value'])
    if not span_length:
        # Direct length if not in attributes (less common for structured data)
        span_length = conn_data.get('length')

    try:
        return float(span_length) if span_length is not None else None
    except (ValueError, TypeError):
        return None


def extract_connection_type(conn_data):
    """Extract connection type from connection data"""
    if not conn_data:
        return ""
    
    # Katapult JSON Guide Snippet F suggests 'button' or 'attributes.connection_type.button_added'
    conn_type = get_nested_value(conn_data, ['attributes', 'connection_type', 'button_added'])
    
    if not conn_type: # If not found, try the direct 'button' attribute on the connection
        conn_type = conn_data.get('button')

    # Fallback for dynamic keys if 'button_added' wasn't present but 'connection_type' is a dict
    if not conn_type and isinstance(get_nested_value(conn_data, ['attributes', 'connection_type']), dict):
        conn_type_dict = get_nested_value(conn_data, ['attributes', 'connection_type'])
        if conn_type_dict: # Get the first value from the dynamic keys
            first_key = next(iter(conn_type_dict), None)
            if first_key and isinstance(conn_type_dict[first_key], str): # Ensure it's a string value
                conn_type = conn_type_dict[first_key]
    
    return str(conn_type) if conn_type else ""


def extract_mr_status(node_data):
    """Extract make-ready status from node data"""
    if not node_data:
        return ""
    attributes = node_data.get('attributes', {})
    
    # Katapult JSON Guide Snippet B mentions 'mr_state.button_added'
    mr_status = get_nested_value(attributes, ['mr_state', 'button_added'])
    
    # Fallback to observed 'kat_MR_state'
    if not mr_status:
        mr_status = get_nested_value(attributes, ['kat_MR_state', 'button_added'])
    
    # Fallback to 'kat_work_type' if it indicates make_ready
    if not mr_status:
        work_type_obj = attributes.get('kat_work_type', {})
        if isinstance(work_type_obj, dict):
            # It can be under 'button_added' or a dynamic key
            work_type_val = work_type_obj.get('button_added')
            if not work_type_val:
                 # Try first value from dynamic keys
                first_key = next(iter(work_type_obj), None)
                if first_key:
                    work_type_val = work_type_obj[first_key]

            if work_type_val and 'make_ready' in str(work_type_val).lower(): # Changed 'make ready' to 'make_ready'
                mr_status = work_type_val
    
    return str(mr_status) if mr_status else ""


def extract_pole_owner(node_data):
    """Extract pole owner from node data"""
    if not node_data:
        return ""
    attributes = node_data.get('attributes', {})

    # Katapult JSON Guide Snippet B: PoleOwner.assessment
    owner = get_nested_value(attributes, ['PoleOwner', 'assessment'])
    
    # Fallback to observed 'pole_owner' with 'multi_added' or 'button_added'
    if not owner:
        owner_val = get_nested_value(attributes, ['pole_owner', 'multi_added'])
        if not owner_val:
            owner_val = get_nested_value(attributes, ['pole_owner', 'button_added'])
        
        if isinstance(owner_val, list) and owner_val:
            owner = owner_val[0] # Take the first if it's a list
        elif isinstance(owner_val, str):
            owner = owner_val

    return str(owner) if owner else ""


def extract_pole_structure(node_data):
    """
    Extract comprehensive pole structure information (Height-Class Species).
    Prioritizes documented paths from Katapult JSON Guide Snippet B.
    """
    if not node_data:
        return ""
    
    attrs = node_data.get('attributes', {})
    if not attrs:
        return ""

    height = None
    pole_class = None
    species = None

    # Priority 1: Documented paths (PoleHeight.assessment, PoleClass.assessment, PoleSpecies.assessment)
    height = get_nested_value(attrs, ['PoleHeight', 'assessment'])
    pole_class = get_nested_value(attrs, ['PoleClass', 'assessment'])
    species = get_nested_value(attrs, ['PoleSpecies', 'assessment'])

    # Fallback: 'proposed_pole_spec' (if it contains the full string)
    if not (height and pole_class and species): # If any primary part is missing, check proposed_spec
        proposed_spec_val = None
        proposed_spec_data = attrs.get("proposed_pole_spec", {})
        if proposed_spec_data and isinstance(proposed_spec_data, dict):
            # Iterate through dynamic keys if present
            for key, value_obj in proposed_spec_data.items():
                if isinstance(value_obj, dict):
                    val = value_obj.get("value")
                else: # Direct value
                    val = value_obj
                if val and val != "N/A":
                    proposed_spec_val = val
                    break # Take the first valid one
        if proposed_spec_val:
             # If proposed_spec_val seems to be a full "Height-Class Species" string, return it.
             # This is a heuristic; might need refinement if format varies.
            if isinstance(proposed_spec_val, str) and '-' in proposed_spec_val:
                return proposed_spec_val


    # Fallback: lowercase versions or 'one' key (observed in existing code)
    if not height:
        height_data = attrs.get("pole_height", {}) or attrs.get("height", {})
        if isinstance(height_data, dict):
            height = height_data.get("one")
            if not height: # Try first dynamic key's value
                height = next((str(v) for v in height_data.values() if v and v != "N/A"), None)
    
    if not pole_class:
        class_data = attrs.get("pole_class", {})
        if isinstance(class_data, dict):
            pole_class = class_data.get("one")
            if not pole_class:
                pole_class = next((str(v) for v in class_data.values() if v and v != "N/A"), None)

    if not species:
        species_data = attrs.get("pole_species", {})
        if isinstance(species_data, dict):
            species = species_data.get("one")
            if not species:
                species = next((str(v) for v in species_data.values() if v and v != "N/A"), None)

    # Fallback: birthmark_brand for missing parts
    if not height or not pole_class or not species:
        birthmark_brand = attrs.get('birthmark_brand', {})
        if birthmark_brand and isinstance(birthmark_brand, dict):
            first_key = next(iter(birthmark_brand), None)
            if first_key:
                brand_details = birthmark_brand[first_key]
                if not height: height = get_nested_value(brand_details, ['pole_height'])
                if not pole_class: pole_class = get_nested_value(brand_details, ['pole_class'])
                if not species:
                    species_code = get_nested_value(brand_details, ['pole_species*']) # Note: '*' in key
                    species_map = {"SPC": "Southern Pine", "WRC": "Western Red Cedar", 
                                   "DF": "Douglas Fir", "LP": "Lodgepole Pine"}
                    species = species_map.get(str(species_code), str(species_code) if species_code else "")
    
    parts = []
    if height: parts.append(str(height))
    if pole_class: parts.append(str(pole_class))
    
    structure_str = "-".join(parts)
    if species:
        structure_str = f"{structure_str} {species}".strip()
    
    return structure_str if structure_str else ""


def extract_pla_percentage(node_data):
    """Extract PLA (Percent Loading Allowance) percentage from node data."""
    if not node_data:
        return ""
    attrs = node_data.get('attributes', {})
    if not attrs:
        return ""

    # Katapult JSON Guide Snippet B: 'final_passing_capacity_%' or 'existing_capacity_%'
    # Both can have a dynamic key for the value.
    
    pla_value_str = None
    
    # Try 'final_passing_capacity_%'
    final_cap_data = attrs.get('final_passing_capacity_%')
    if isinstance(final_cap_data, dict):
        # Get value from dynamic key
        pla_value_str = next((str(v) for v in final_cap_data.values()), None)
    elif isinstance(final_cap_data, str): # Direct string value
        pla_value_str = final_cap_data

    # Try 'existing_capacity_%' if final not found or invalid
    if not pla_value_str:
        existing_cap_data = attrs.get('existing_capacity_%')
        if isinstance(existing_cap_data, dict):
            pla_value_str = next((str(v) for v in existing_cap_data.values()), None)
        elif isinstance(existing_cap_data, str):
            pla_value_str = existing_cap_data
            
    # Fallbacks from original code if primary paths fail
    if not pla_value_str:
        alternate_paths_keys = [
            'final_passing_capacity_p', # Note: _p instead of _%
            'passing_capacity_%',
            'passing_capacity_p'
        ]
        for key in alternate_paths_keys:
            alt_val_data = attrs.get(key)
            if isinstance(alt_val_data, dict):
                pla_value_str = next((str(v) for v in alt_val_data.values()), None)
            elif isinstance(alt_val_data, str):
                pla_value_str = alt_val_data
            if pla_value_str:
                break
                
    if pla_value_str:
        try:
            return f"{float(pla_value_str):.2f}%"
        except (ValueError, TypeError):
            pass # Failed to convert, will return ""
            
    return ""


def extract_construction_grade(node_data):
    """Extract construction grade from node data."""
    if not node_data:
        return ""
    attrs = node_data.get('attributes', {})
    if not attrs:
        return ""

    # Katapult JSON Guide Snippet B: 'construction_grade_analysis.assessment'
    grade = get_nested_value(attrs, ['construction_grade_analysis', 'assessment'])
    if grade:
        return str(grade)

    # Fallback: Infer from pole_class (as in original code)
    # For pole_class, use the logic from extract_pole_structure or a simplified version
    pole_class_val = get_nested_value(attrs, ['PoleClass', 'assessment'])
    if not pole_class_val: # Try lowercase fallback
        class_data = attrs.get("pole_class", {})
        if isinstance(class_data, dict):
            pole_class_val = class_data.get("one")
            if not pole_class_val:
                pole_class_val = next((str(v) for v in class_data.values() if v and v != "N/A"), None)
    
    if not pole_class_val: # Try birthmark
        birthmark_brand = attrs.get('birthmark_brand', {})
        if birthmark_brand and isinstance(birthmark_brand, dict):
            first_key = next(iter(birthmark_brand), None)
            if first_key:
                brand_details = birthmark_brand[first_key]
                pole_class_val = get_nested_value(brand_details, ['pole_class'])

    if pole_class_val:
        class_to_grade_map = {
            "1": "B", "2": "C", "3": "C", "4": "D", "5": "D/E",
            "H1": "B", "H2": "C", "H3": "C", "H4": "D", "H5": "D/E"
        }
        # Ensure pole_class_val is a string for map lookup
        return class_to_grade_map.get(str(pole_class_val), "")
        
    return ""


def extract_proposed_riser(node_data):
    """Extract proposed riser information from node data"""
    if not node_data:
        return "NO"
    attrs = node_data.get('attributes', {})
    
    # Check for riser attribute (e.g., a button_added field)
    riser_val = get_nested_value(attrs, ['riser', 'button_added'])
    
    # If riser attribute exists and is not explicitly "No" or empty, assume YES
    if riser_val and str(riser_val).lower() not in ['no', 'none', '']:
        return "YES (1)" # Assuming 1 if present, count might need more logic if available
    
    # Check for riser in MR notes (kat_MR_notes)
    # This is heuristic and depends on note content.
    mr_notes_data = attrs.get('kat_MR_notes')
    if mr_notes_data and isinstance(mr_notes_data, dict):
        for note_key, note_content in mr_notes_data.items():
            note_text = str(note_content).lower()
            if "riser" in note_text and any(term in note_text for term in ["install", "add", "new", "proposed"]):
                return "YES (1)" # Assuming 1 if mentioned as new/proposed
    
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
