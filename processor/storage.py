import os
import io
import logging
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger(__name__)

# Configuration from environment variables
S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
USE_S3 = os.environ.get('USE_S3', 'False').lower() == 'true'

# Initialize S3 client if using S3
s3_client = None
if USE_S3:
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        logger.info("S3 client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize S3 client: {e}")


def save_file(file_path, file_object, content_type=None):
    """
    Save a file either locally or to S3 based on environment configuration.
    
    Args:
        file_path (str): Local file path or relative path for S3
        file_object: File-like object or bytes to save
        content_type (str, optional): MIME type of the file
        
    Returns:
        str: Path to the saved file (local or S3 URI)
    """
    # If using S3 and client is properly initialized
    if USE_S3 and s3_client:
        try:
            # Prepare extra arguments
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            # Get file name from path and use it as the S3 key
            file_name = os.path.basename(file_path)
            
            # If file_object is a file-like object, upload it
            if hasattr(file_object, 'read'):
                # If it's a file uploaded by the user, it might need to be reset
                if hasattr(file_object, 'seek'):
                    file_object.seek(0)
                
                s3_client.upload_fileobj(file_object, S3_BUCKET, file_name, ExtraArgs=extra_args)
            # If file_object is bytes or string, convert and upload
            else:
                if isinstance(file_object, str):
                    file_object = file_object.encode('utf-8')
                    
                s3_client.upload_fileobj(
                    io.BytesIO(file_object), 
                    S3_BUCKET, 
                    file_name, 
                    ExtraArgs=extra_args
                )
                
            logger.info(f"File saved to S3: {file_name}")
            return f"s3://{S3_BUCKET}/{file_name}"
        
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            # Fall back to local storage if S3 fails
            logger.warning("Falling back to local storage")
        
    # Local file storage (default or fallback)
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Handle file-like objects
        if hasattr(file_object, 'read'):
            if hasattr(file_object, 'seek'):
                file_object.seek(0)
                
            with open(file_path, 'wb') as f:
                f.write(file_object.read())
                
        # Handle bytes or string
        else:
            mode = 'wb' if isinstance(file_object, bytes) else 'w'
            with open(file_path, mode) as f:
                f.write(file_object)
                
        logger.info(f"File saved locally: {file_path}")
        return file_path
    
    except Exception as e:
        logger.error(f"Error saving file locally: {e}")
        raise


def get_file(file_path):
    """
    Retrieve a file from local storage or S3.
    
    Args:
        file_path (str): Path to the file, can be local or S3 URI
        
    Returns:
        bytes: The file content
    """
    # Check if path is an S3 URI
    if USE_S3 and s3_client and file_path.startswith(f"s3://{S3_BUCKET}/"):
        try:
            file_name = file_path.split(f"s3://{S3_BUCKET}/")[1]
            
            # Get the object from S3
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=file_name)
            content = response['Body'].read()
            
            logger.info(f"File retrieved from S3: {file_name}")
            return content
            
        except ClientError as e:
            logger.error(f"S3 download error: {e}")
            raise
            
    # Local file retrieval
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            
        logger.info(f"File retrieved locally: {file_path}")
        return content
        
    except Exception as e:
        logger.error(f"Error retrieving local file: {e}")
        raise


def delete_file(file_path):
    """
    Delete a file from local storage or S3.
    
    Args:
        file_path (str): Path to the file, can be local or S3 URI
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    # Check if path is an S3 URI
    if USE_S3 and s3_client and file_path.startswith(f"s3://{S3_BUCKET}/"):
        try:
            file_name = file_path.split(f"s3://{S3_BUCKET}/")[1]
            
            # Delete the object from S3
            s3_client.delete_object(Bucket=S3_BUCKET, Key=file_name)
            
            logger.info(f"File deleted from S3: {file_name}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
            return False
            
    # Local file deletion
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File deleted locally: {file_path}")
            return True
        else:
            logger.warning(f"Local file not found for deletion: {file_path}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting local file: {e}")
        return False
