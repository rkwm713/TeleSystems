"""
Core processing functions for Katapult JSON data.
"""

import json
import time
import pandas as pd

from .data_extraction import (
    extract_pole_tag, extract_scid, extract_location, extract_span_length,
    extract_connection_type, extract_mr_status, extract_pole_owner,
    extract_pole_structure, extract_pla_percentage, extract_construction_grade,
    extract_proposed_riser, extract_proposed_guy, determine_attachment_action
)
from .node_processing import get_attachers_for_node
from .connection_processing import get_lowest_heights_for_connection, get_midspan_proposed_heights
from .movement_processing import get_movement_summary, generate_remedy_description
from .excel_generator import create_output_excel


def process_katapult_json(json_path, output_excel_path):
    """
    Main function to process a Katapult JSON file and generate an Excel report.
    
    Args:
        json_path (str): Path to the Katapult JSON file
        output_excel_path (str): Path where the Excel report will be saved
        
    Returns:
        dict: Statistics about the processing
    """
    start_time = time.time()
    
    try:
        # Load the JSON file
        print(f"Loading JSON file from {json_path}...")
        with open(json_path, 'r', encoding='utf-8') as file:
            job_data = json.load(file)
        print(f"JSON file loaded successfully.")
            
        # Process the data
        print("Processing data...")
        df = process_data(job_data, None)  # No GeoJSON for now
        
        if df.empty:
            print("ERROR: No data could be extracted from the JSON file.")
            return {
                "status": "error",
                "message": "No data could be extracted from the JSON file."
            }
        
        print(f"Data processed successfully. Generated {len(df)} records.")
            
        # Create Excel file
        print(f"Creating Excel file at {output_excel_path}...")
        create_output_excel(output_excel_path, df, job_data)
        print(f"Excel file created successfully at {output_excel_path}.")
        
        # Gather statistics
        processing_time = round(time.time() - start_time, 2)
        
        # Count unique poles, connections, and attachers
        pole_count = 0
        if 'node_id_1' in df.columns and not df['node_id_1'].empty:
            pole_count = len(set(df['node_id_1'].tolist()))
        connection_count = len(df)
        
        # Count attachers and proposed attachments
        attacher_count = 0
        proposed_count = 0
        
        # Gather all attachers for statistics
        if 'node_id_1' in df.columns:
            for _, record in df.iterrows():
                node_id = record['node_id_1']
                if node_id: # Ensure node_id is not None or empty
                    attachers = get_attachers_for_node(job_data, node_id)
                    main_attachers = attachers.get('main_attachers', [])
                    
                    attacher_count += len(main_attachers)
                    for attacher in main_attachers:
                        if attacher.get('is_proposed', False):
                            proposed_count += 1
        
        return {
            "status": "success",
            "processing_time": processing_time,
            "pole_count": pole_count,
            "connection_count": connection_count,
            "attacher_count": attacher_count,
            "proposed_count": proposed_count
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def process_data(job_data, geojson_path):
    """
    Process Katapult job data and optionally geojson into a DataFrame with comprehensive pole and connection information.
    Structures data to match the required Excel output format.
    
    Args:
        job_data (dict): The loaded Katapult JSON data
        geojson_path (str): Optional path to a GeoJSON file with additional data
        
    Returns:
        pd.DataFrame: Processed data with all relevant connection and pole information
    """
    columns = [
        'operation_number', 'attachment_action', 'pole_owner', 'pole_number', 
        'pole_structure', 'proposed_riser', 'proposed_guy', 'pla_percentage',
        'construction_grade', 'node_id_1', 'node_id_2', 'connection_id', 
        'span_length', 'pole_tag_1', 'pole_tag_2', 'latitude_1', 'longitude_1', 
        'latitude_2', 'longitude_2', 'lowest_com_height', 'lowest_cps_height'
    ]
    
    processed_records = []
    operation_counter = 1
    
    # Track processed poles to avoid duplicates in operation numbering
    processed_poles = set()
    
    if job_data and "connections" in job_data:
        nodes_data = job_data.get("nodes", {})
        
        for conn_id, conn_data in job_data.get("connections", {}).items():
            node_id_1 = conn_data.get('node_id_1')
            node_id_2 = conn_data.get('node_id_2')
            
            # Skip invalid connections
            if not node_id_1 or node_id_1 not in nodes_data:
                continue
                
            # Get detailed node information
            node1_data = nodes_data.get(node_id_1, {})
            node2_data = nodes_data.get(node_id_2, {}) if node_id_2 else {}
            
            # Extract pole tags
            pole_tag_1 = extract_pole_tag(node1_data)
            pole_tag_2 = extract_pole_tag(node2_data) if node_id_2 else "N/A"
            
            # Extract SCIDs (e.g., work order or operation IDs)
            scid_1 = extract_scid(node1_data)
            scid_2 = extract_scid(node2_data) if node_id_2 else "N/A"
            
            # Extract location data
            lat1, lon1 = extract_location(node1_data)
            lat2, lon2 = extract_location(node2_data) if node_id_2 else (None, None)
            
            # Get span length
            span_length = extract_span_length(conn_data)
            
            # Get connection type
            connection_type = extract_connection_type(conn_data)
            
            # Get MR status
            mr_status = extract_mr_status(node1_data)
            
            # Get lowest heights for communications and electrical
            lowest_com, lowest_cps = get_lowest_heights_for_connection(job_data, conn_id)
            
            # Get pole-specific attributes for node1
            if node_id_1 not in processed_poles:
                pole_owner = extract_pole_owner(node1_data)
                pole_structure = extract_pole_structure(node1_data)
                pla_percentage = extract_pla_percentage(node1_data)
                construction_grade = extract_construction_grade(node1_data)
                proposed_riser = extract_proposed_riser(node1_data)
                proposed_guy = extract_proposed_guy(node_id_1, job_data)
                attachment_action = determine_attachment_action(node1_data, job_data)
                
                processed_poles.add(node_id_1)
            else:
                # For already processed poles, use placeholder values
                pole_owner = ""
                pole_structure = ""
                pla_percentage = ""
                construction_grade = ""
                proposed_riser = ""
                proposed_guy = ""
                attachment_action = ""
            
            # Get attacher data for node1
            attachers_data = get_attachers_for_node(job_data, node_id_1)
            main_attachers = attachers_data.get('main_attachers', [])
            
            # Determine if this is an underground connection
            is_underground = connection_type.lower() == "underground cable"
            
            # Generate movement summary and remedy description
            movement_summary = get_movement_summary(main_attachers)
            remedy_description = generate_remedy_description(main_attachers, is_underground)
            
            # Create the record
            record = {
                'operation_number': operation_counter if node_id_1 not in processed_poles else None,
                'attachment_action': attachment_action,
                'pole_owner': pole_owner,
                'pole_number': pole_tag_1,
                'pole_structure': pole_structure,
                'proposed_riser': proposed_riser,
                'proposed_guy': proposed_guy, 
                'pla_percentage': pla_percentage,
                'construction_grade': construction_grade,
                'node_id_1': node_id_1,
                'node_id_2': node_id_2,
                'connection_id': conn_id,
                'span_length': span_length,
                'pole_tag_1': pole_tag_1,
                'pole_tag_2': pole_tag_2,
                'latitude_1': lat1,
                'longitude_1': lon1,
                'latitude_2': lat2,
                'longitude_2': lon2,
                'lowest_com_height': lowest_com,
                'lowest_cps_height': lowest_cps,
                'scid_1': scid_1,
                'scid_2': scid_2,
                'connection_type': connection_type,
                'mr_status': mr_status,
                'movement_summary': movement_summary,
                'remedy_description': remedy_description,
                'attachers_data': attachers_data  # Store for later use in Excel generation
            }
            
            processed_records.append(record)
            if node_id_1 not in processed_poles:
                operation_counter += 1

    # Create DataFrame and ensure all columns exist
    if processed_records:
        df = pd.DataFrame(processed_records)
        for col in columns:
            if col not in df.columns:
                df[col] = None
        # Order columns as defined
        return df[columns].fillna("")
    else:
        return pd.DataFrame(columns=columns)


# Example usage (optional, for testing)
if __name__ == '__main__':
    import os
    
    # Create a dummy Katapult JSON for testing
    dummy_job_data = {
        "job_name": "Test Job 123",
        "nodes": {
            "nodeA": {
                "photos": {"photo1_nodeA": {"association": "main", "latitude": "34.0522", "longitude": "-118.2437", 
                                          "photofirst_data": {
                                              "wire": {
                                                  "wire1": {"_trace": "trace_neutral_A", "_measured_height": "240"},
                                                  "wire2": {"_trace": "trace_comm_A", "_measured_height": "200", "mr_move": "12"}
                                              },
                                              "guying": {
                                                   "guy1": {"_trace": "trace_guy_A", "_measured_height": "180"} # Below neutral
                                              }
                                          }}},
                "attributes": {"pole_tag": "Pole A"}
            },
            "nodeB": {
                "photos": {"photo1_nodeB": {"association": "main", "latitude": "34.0523", "longitude": "-118.2438",
                                           "photofirst_data": {
                                               "wire": {"wire3": {"_trace": "trace_neutral_B", "_measured_height": "238"}}
                                           }}},
                "attributes": {"pole_tag": "Pole B"}
            }
        },
        "connections": {
            "conn1": {
                "node_id_1": "nodeA", "node_id_2": "nodeB",
                "attributes": {"connection_type": {"button_added": "overhead_reference"}, "span_length": {"value": "150.5"}},
                "sections": {
                    "sec1_conn1": {
                        "latitude": "34.05225", "longitude": "-118.24375", # Midpoint
                        "photos": {"photo1_sec1": {"association": "main", 
                                                 "photofirst_data": {
                                                     "wire": {
                                                         "wire_s1": {"_trace": "trace_comm_A", "_measured_height": "190", "_effective_moves": {"eff1": "6"}},
                                                         "wire_s2": {"_trace": "trace_neutral_A", "_measured_height": "220"}
                                                     },
                                                     "guying": {
                                                         "guy_s1": {"_trace": "trace_guy_A", "_measured_height": "170"} # Below neutral
                                                     }
                                                 }}}
                    }
                }
            }
        },
        "traces": {
            "trace_data": {
                "trace_neutral_A": {"company": "CPS Energy", "cable_type": "Neutral"},
                "trace_comm_A": {"company": "ATT", "cable_type": "Fiber", "proposed": True},
                "trace_guy_A": {"company": "CPS Energy", "cable_type": "Anchor Guy"},
                "trace_neutral_B": {"company": "CPS Energy", "cable_type": "Neutral"}
            }
        }
    }
    
    # Create a dummy JSON file
    dummy_json_path = "dummy_katapult_data.json"
    with open(dummy_json_path, 'w') as f:
        json.dump(dummy_job_data, f, indent=4)
        
    output_excel = "dummy_output.xlsx"
    
    print(f"Processing dummy file: {dummy_json_path}")
    stats = process_katapult_json(dummy_json_path, output_excel)
    print("\nProcessing Statistics:")
    print(json.dumps(stats, indent=2))
    
    # Clean up dummy file
    if os.path.exists(dummy_json_path):
        os.remove(dummy_json_path)
    if os.path.exists(output_excel) and stats.get("status") == "success":
        print(f"\nDummy Excel report generated: {output_excel}")
    elif os.path.exists(output_excel): # remove if error
        os.remove(output_excel)
