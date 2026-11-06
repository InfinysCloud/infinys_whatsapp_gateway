# -*- coding: utf-8 -*-
import base64
import logging
import re

import requests

_logger = logging.getLogger(__name__)


def normalize_phone_number(phone):
    """Normalize a phone number to the WAPI-required format.

    The gateway expects digits only, in international format without a leading
    plus sign and without separators, e.g. ``628176057749``.

    This helper:
      - strips spaces, dashes, dots, slashes and parentheses,
      - removes a leading ``+`` (and any ``00`` international prefix),
      - keeps only digits.

    Returns the cleaned string, or the original input untouched when it is empty.
    Validation of the result is handled separately by the model constraint.
    """
    if not phone:
        return phone

    cleaned = str(phone).strip()
    # Remove a single leading '+' if present.
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]
    # Drop every character that is not a digit (spaces, '-', '.', '(', ')', etc.).
    cleaned = re.sub(r'\D', '', cleaned)
    # Convert a '00' international prefix to bare international format.
    if cleaned.startswith('00'):
        cleaned = cleaned[2:]
    return cleaned


def is_valid_phone_number(phone):
    """Return True when ``phone`` is in the required digits-only format.

    Accepts 8 to 15 digits (E.164 allows up to 15) with no leading zero and
    no symbols. Normalize first with :func:`normalize_phone_number`.
    """
    if not phone:
        return False
    return bool(re.fullmatch(r'[1-9]\d{7,14}', str(phone)))


def convert_data_uri_to_bytes(mime_type, data_uri_string):
    """
    Fetches content from a URL and base64 encodes it.
    Returns the base64 encoded string (decoded from bytes to a utf-8 string).
    """
    try:
        _logger.info("Fetching content from %s", data_uri_string)
        response = requests.get(data_uri_string, timeout=60)
        response.raise_for_status()  # Raise an exception for bad status codes
        _logger.info(
            "Fetched content from %s with status %s",
            data_uri_string, response.status_code,
        )

        mime_type = (mime_type or "").lower()
        binary_content = response.content

        if mime_type in ("image", "document", "video", "audio"):
            encoded_bytes = base64.b64encode(binary_content)
            return encoded_bytes.decode('utf-8')

        _logger.error("Unsupported mime type: %s", mime_type)
        return None
    except requests.RequestException as e:
        _logger.error("Error fetching content from URL: %s", e)
        return None
    except Exception as e:
        _logger.error("An error occurred while encoding content: %s", e)
        return None


def get_mime_type_from_filename(filename):
    """Determine a coarse media category from a filename extension."""
    try:
        file_ext = filename.split('.')[-1].lower()
        if file_ext in ['jpg', 'jpeg', 'png', 'gif']:
            return 'image'
        elif file_ext in ['mp4', 'avi', 'mov']:
            return 'video'
        elif file_ext in ['mp3', 'wav', 'aac']:
            return 'audio'
        elif file_ext in ['pdf', 'doc', 'docx', 'txt']:
            return 'document'
        return 'document'  # Default to document if unknown
    except Exception as e:
        _logger.error("Error extracting MIME type from filename: %s", e)
        return None
