import base64
import requests
import logging

_logger = logging.getLogger(__name__)


def convert_data_uri_to_bytes(mime_type, data_uri_string):
    """
    #Fetches content from a URL and base64 encodes it.
    #Returns the base64 encoded string (decoded from bytes to a utf-8 string).
    """
    encoded_string = None
    
    try:
        _logger.info(f"Fetching content from {data_uri_string}")
        response = requests.get(data_uri_string)
        response.raise_for_status() # Raise an exception for bad status codes
        _logger.info(f"Fetched content from {data_uri_string} with status {response.status_code}")

        mime_type = mime_type.lower()
        file_path = data_uri_string # In this case, data_uri_string is treated as a URL
        binary_content = response.content

        if (mime_type=="image"):
            encoded_bytes = base64.b64encode(binary_content)
            encoded_string = encoded_bytes.decode('utf-8')
            return encoded_string
        elif (mime_type=="document"):
            encoded_bytes = base64.b64encode(binary_content)
            encoded_string = encoded_bytes.decode('utf-8')
            return encoded_string
        elif (mime_type=="video"):
            encoded_bytes = base64.b64encode(binary_content)
            encoded_string = encoded_bytes.decode('utf-8')
            return encoded_string
        elif (mime_type=="audio"):
            encoded_bytes = base64.b64encode(binary_content)
            encoded_string = encoded_bytes.decode('utf-8')
            return encoded_string    
        else:
            _logger.error(f"Unsupported mime type: {mime_type}")
            return None
    except FileNotFoundError:
        print(f"Error: The file '{data_uri_string}' was not found.")
        return None
    except requests.RequestException as e:
        _logger.error(f"Error fetching content from URL: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def get_mime_type_from_filename(filename):
    """
    Extracts the MIME type from a data URI string.
    """
    try:
        mime_type = ['image', 'video', 'audio', 'document']
        file_ext = filename.split('.')[-1].lower()
        if file_ext in ['jpg', 'jpeg', 'png', 'gif']:
            return 'image'
        elif file_ext in ['mp4', 'avi', 'mov']:
            return 'video'
        elif file_ext in ['mp3', 'wav', 'aac']:
            return 'audio'
        elif file_ext in ['pdf', 'doc', 'docx', 'txt']:
            return 'document'
        else:
            return 'document'  # Default to document if unknown
    except Exception as e:
        _logger.error(f"Error extracting MIME type from data URI: {e}")
        return None
