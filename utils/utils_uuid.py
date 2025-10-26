# utils/utils_uuid.py
import uuid
import datetime

def generate_uuid(input_string=None, namespace=uuid.NAMESPACE_DNS):
    """
    Generate a UUID from the current datetime (microsecond precision) and an optional string.
    
    Args:
        input_string (str, optional): The string to include in UUID generation. Defaults to None.
        namespace (uuid.UUID): UUID namespace (default: uuid.NAMESPACE_DNS).
        
    Returns:
        str: The generated UUID as a string.
        
    Raises:
        ValueError: If input_string is provided and is not a string.
    """
    if input_string is not None and not isinstance(input_string, str):
        raise ValueError("Input string must be a string or None")
    
    # Get current timestamp with microsecond precision
    timestamp = datetime.datetime.now().isoformat()  # e.g., '2025-10-24T17:23:45.123456'
    
    # Combine timestamp with input string (use empty string if None)
    combined_input = timestamp + (input_string or "")
    
    # Generate UUID using uuid5
    uuid_from_combined = uuid.uuid5(namespace, combined_input)
    
    return str(uuid_from_combined)


def derive_uuid(input_string, namespace=uuid.NAMESPACE_DNS):
    """
    Generate a UUID from a single string using uuid5 and a specified namespace.
    
    Args:
        input_string (str): The string to generate a UUID for.
        namespace (uuid.UUID): UUID namespace (default: uuid.NAMESPACE_DNS).
        
    Returns:
        str: The generated UUID as a string.
        
    Raises:
        ValueError: If input_string is not a non-empty string.
    """
    if not isinstance(input_string, str):
        raise ValueError("Input must be a string")
    if not input_string:
        raise ValueError("Input string cannot be empty")
    
    uuid_from_string = uuid.uuid5(namespace, input_string)
    return str(uuid_from_string)
