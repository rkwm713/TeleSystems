"""
Functions for processing and describing movements of attachers.
"""

def get_movement_summary(attacher_data, cps_only=False):
    """
    Generate a movement summary for all attachers that have moves, proposed wires, and guying.
    
    Args:
        attacher_data (list): List of attacher data dictionaries
        cps_only (bool): If True, only include CPS Energy movements
        
    Returns:
        str: Formatted movement summary with one movement per line
    """
    summaries = []
    
    # First handle movements of existing attachments
    for attacher in attacher_data:
        name = attacher['name']
        existing = attacher['existing_height']
        proposed = attacher['proposed_height']
        is_proposed = attacher.get('is_proposed', False)
        is_guy = '(Down Guy)' in name
        
        # Skip if cps_only is True and this is not a CPS attachment
        if cps_only and not name.lower().startswith("cps energy"):
            continue
        
        # Handle proposed new attachments (including guys)
        if is_proposed:
            if is_guy:
                summaries.append(f"Add {name} at {existing}")
            else:
                summaries.append(f"Install proposed {name} at {existing}")
            continue
            
        # Handle movements of existing attachments
        if proposed and existing:
            try:
                existing_parts = existing.replace('"', '').split("'")
                proposed_parts = proposed.replace('"', '').split("'")
                
                existing_inches = int(existing_parts[0]) * 12 + int(existing_parts[1])
                proposed_inches = int(proposed_parts[0]) * 12 + int(proposed_parts[1])
                
                # Calculate movement
                movement = proposed_inches - existing_inches
                
                if movement != 0:
                    # Determine if raising or lowering
                    action = "Raise" if movement > 0 else "Lower"
                    # Get absolute movement in inches
                    inches_moved = abs(movement)
                    
                    summary = f"{action} {name} {inches_moved}\" from {existing} to {proposed}"
                    summaries.append(summary)
            except (ValueError, IndexError):
                continue
    
    return "\n".join(summaries) if summaries else ""

def generate_remedy_description(attacher_data, is_underground=False):
    """
    Generate a remedy description including installations and movements.
    
    Args:
        attacher_data (list): List of attacher data dictionaries
        is_underground (bool): Whether this is for an underground connection
        
    Returns:
        str: Formatted remedy description
    """
    install_lines = []
    riser_lines = set()
    
    # Find all proposed attachments and generate descriptions
    for attacher in attacher_data:
        if attacher.get('is_proposed'):
            company = attacher['name'].split()[0]
            height = attacher.get('proposed_height') or attacher.get('existing_height') or ""
            
            install_line = f"Install proposed {attacher['name']} at {height}" if height else f"Install proposed {attacher['name']}"
            install_lines.append(install_line)
            
            # Add riser description if it's an underground connection
            if is_underground:
                riser_lines.add(f"Install proposed {company} Riser @ {height} to UG connection" if height else f"Install proposed {company} Riser to UG connection")
    
    # If no explicit proposed attachments, use the first attacher info (fallback)
    if not install_lines and attacher_data:
        attacher = attacher_data[0]
        company = attacher['name'].split()[0]
        height = attacher.get('proposed_height') or attacher.get('existing_height') or ""
        
        install_lines.append(f"Install proposed {attacher['name']} at {height}" if height else f"Install proposed {attacher['name']}")
        
        if is_underground:
            riser_lines.add(f"Install proposed {company} Riser @ {height} to UG connection" if height else f"Install proposed {company} Riser to UG connection")
    
    # Add movement summary for height adjustments
    movement_summary = get_movement_summary(attacher_data)
    
    # Combine everything into a complete remedy description
    remedy_lines = install_lines + list(riser_lines)
    if movement_summary:
        remedy_lines.append(movement_summary)
    
    return "\n".join(remedy_lines)
