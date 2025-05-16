"""
Utilities for extracting photo-related data, especially photofirst_data,
from Katapult JSON structures, handling various potential paths.
"""

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

    # Attempt 1: photofirst_data nested directly in the provided photo_entry_data
    if photo_entry_data:
        photofirst_data = photo_entry_data.get("photofirst_data")

    # Attempt 2: photofirst_data in top-level job_data["photo_summary"]
    if not photofirst_data and photo_id and job_data.get("photo_summary"):
        photofirst_data = job_data.get("photo_summary", {}).get(photo_id, {}).get("photofirst_data")

    # Attempt 3: photofirst_data in top-level job_data["photos"]
    # (This was the old primary way in some functions, now a fallback if job_data["photos"] contains full details)
    if not photofirst_data and photo_id and job_data.get("photos"):
        # Check if job_data["photos"][photo_id] is the full photo detail map
        # or just a shallow map like the one under nodes.
        # For safety, we assume it might contain full details.
        top_level_photo_data = job_data.get("photos", {}).get(photo_id, {})
        if isinstance(top_level_photo_data, dict) and "photofirst_data" in top_level_photo_data:
             photofirst_data = top_level_photo_data.get("photofirst_data")

    return photofirst_data if photofirst_data else {}
