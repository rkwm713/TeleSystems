"""
Utilities for extracting photo-related data, especially photofirst_data,
from Katapult JSON structures, handling various potential paths.
"""
import logging

# Set up logging
logger = logging.getLogger(__name__)

def get_photofirst_data(photo_id, photo_entry_data, job_data):
    """
    Retrieves photofirst_data for a given photo_id, checking multiple common paths.

    Args:
        photo_id (str): The ID of the photo.
        photo_entry_data (dict): The photo entry data, typically from a node's or section's 'photos' dictionary.
                                 Example: node_data.get('photos', {}).get(photo_id, {})
        job_data (dict): The full Katapult job data.

    Returns:
        dict: The photofirst_data dictionary, or an empty dictionary if not found.
    """
    photofirst_data = None
    
    # For debugging
    search_paths = []

    # Attempt 1: photofirst_data nested directly in the provided photo_entry_data
    if photo_entry_data:
        search_paths.append("photo_entry_data.photofirst_data")
        photofirst_data = photo_entry_data.get("photofirst_data")

    # Attempt 2: photofirst_data in top-level job_data["photo_summary"]
    if not photofirst_data and photo_id and job_data.get("photo_summary"):
        search_paths.append("job_data.photo_summary[photo_id].photofirst_data")
        photofirst_data = job_data.get("photo_summary", {}).get(photo_id, {}).get("photofirst_data")

    # Attempt 3: photofirst_data in top-level job_data["photos"]
    if not photofirst_data and photo_id and job_data.get("photos"):
        search_paths.append("job_data.photos[photo_id].photofirst_data")
        top_level_photo_data = job_data.get("photos", {}).get(photo_id, {})
        if isinstance(top_level_photo_data, dict) and "photofirst_data" in top_level_photo_data:
             photofirst_data = top_level_photo_data.get("photofirst_data")

    # Attempt 4: Look in job_data.photos[photo_id].data.photofirst_data (alternative structure)
    if not photofirst_data and photo_id and job_data.get("photos"):
        search_paths.append("job_data.photos[photo_id].data.photofirst_data")
        top_level_photo = job_data.get("photos", {}).get(photo_id, {})
        if isinstance(top_level_photo, dict) and "data" in top_level_photo:
            photofirst_data = top_level_photo.get("data", {}).get("photofirst_data")

    # Attempt 5: Look in job_data.nodes[node_id].properties.photos[photo_id].photofirst_data
    # Only applicable if node_id is retrievable from the context
    node_id = None
    if photo_entry_data and "node_id" in photo_entry_data:
        node_id = photo_entry_data.get("node_id")
    
    if not photofirst_data and node_id and photo_id:
        search_paths.append(f"job_data.nodes[{node_id}].properties.photos[{photo_id}].photofirst_data")
        node_properties = job_data.get("nodes", {}).get(node_id, {}).get("properties", {})
        node_photos = node_properties.get("photos", {})
        if photo_id in node_photos:
            photofirst_data = node_photos.get(photo_id, {}).get("photofirst_data")

    if not photofirst_data:
        logger.debug(f"Could not find photofirst_data for photo_id={photo_id}. Searched paths: {', '.join(search_paths)}")
        return {}
    
    if not isinstance(photofirst_data, dict):
        logger.warning(f"Found photofirst_data for photo_id={photo_id} but it's not a dictionary: {type(photofirst_data)}")
        return {}
        
    return photofirst_data

def get_utility_company_names():
    """
    Returns a list of possible utility company names used in the Katapult data.
    This allows for case-insensitive matching and handling of variations.
    
    Returns:
        list: A list of utility company name patterns
    """
    return ["CPS ENERGY", "CPS Energy", "CPS", "CPSE"]
