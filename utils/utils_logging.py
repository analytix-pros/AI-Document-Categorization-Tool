"""Logging utility for tracking user interactions and system events."""
import logging
from database.db_models import Logging, create_connection
from utils.utils_uuid import generate_uuid
from utils.utils import get_utc_datetime


class AppLogger:
    """
    Application logger that writes to database and optionally to console.
    Tracks all user interactions and system events.
    """
    
    # Map Python logging levels to string representations
    LEVEL_MAP = {
        logging.DEBUG: 'DEBUG',
        logging.INFO: 'INFO',
        logging.WARNING: 'WARNING',
        logging.ERROR: 'ERROR',
        logging.CRITICAL: 'CRITICAL'
    }
    
    def __init__(self, organization_uuid=None, user_uuid=None, console_output=False):
        """
        Initialize the AppLogger.
        
        Args:
            organization_uuid (str, optional): Organization UUID for logging context
            user_uuid (str, optional): User UUID for logging context
            console_output (bool): Whether to also print logs to console
        """
        self.organization_uuid = organization_uuid or ""
        self.user_uuid = user_uuid or ""
        self.console_output = console_output
        self.db_logger = Logging()
    
    def _get_logging_uuid(self):
        """Generate logging UUID from organization and user UUIDs."""
        combined_string = f"{self.organization_uuid}{self.user_uuid}"
        return generate_uuid(combined_string)
    
    def _write_log(self, page, message, level):
        """
        Write log entry to database.
        
        Args:
            page (str): Page/location where action occurred
            message (str): Log message (no PII or credentials)
            level (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        try:
            self.db_logger.insert(
                organization_uuid=self.organization_uuid if self.organization_uuid else None,
                user_uuid=self.user_uuid if self.user_uuid else None,
                page=page,
                message=message,
                level=level
            )
            
            if self.console_output:
                print(f"[{level}] {page}: {message}")
                
        except Exception as e:
            # Fallback to console if database write fails
            print(f"ERROR: Failed to write log to database: {str(e)}")
            print(f"[{level}] {page}: {message}")
    
    def debug(self, page, message):
        """Log DEBUG level message."""
        self._write_log(page, message, 'DEBUG')
    
    def info(self, page, message):
        """Log INFO level message."""
        self._write_log(page, message, 'INFO')
    
    def warning(self, page, message):
        """Log WARNING level message."""
        self._write_log(page, message, 'WARNING')
    
    def error(self, page, message):
        """Log ERROR level message."""
        self._write_log(page, message, 'ERROR')
    
    def critical(self, page, message):
        """Log CRITICAL level message."""
        self._write_log(page, message, 'CRITICAL')
    
    def log_action(self, page, action, details=None, level='INFO'):
        """
        Log a user action with optional details.
        
        Args:
            page (str): Page where action occurred
            action (str): Action performed (e.g., 'login', 'add_user', 'delete_org')
            details (str, optional): Additional context (no PII)
            level (str): Log level
        """
        message = f"Action: {action}"
        if details:
            message += f" | Details: {details}"
        
        self._write_log(page, message, level)
    
    def log_error_with_exception(self, page, message, exception):
        """
        Log an error with exception details.
        
        Args:
            page (str): Page where error occurred
            message (str): Error description
            exception (Exception): The exception object
        """
        error_message = f"{message} | Exception: {type(exception).__name__}: {str(exception)}"
        self._write_log(page, error_message, 'ERROR')


def get_logger_from_session(session_state, console_output=False):
    """
    Create an AppLogger instance from Streamlit session state.
    
    Args:
        session_state: Streamlit session state object
        console_output (bool): Whether to also print logs to console
    
    Returns:
        AppLogger: Configured logger instance
    """
    org_uuid = session_state.get('org_uuid', None)
    user_uuid = session_state.get('user_uuid', None)
    
    return AppLogger(
        organization_uuid=org_uuid,
        user_uuid=user_uuid,
        console_output=console_output
    )


def log_page_view(session_state, page_name):
    """
    Convenience function to log page views.
    
    Args:
        session_state: Streamlit session state object
        page_name (str): Name of the page being viewed
    """
    logger = get_logger_from_session(session_state)
    logger.info(page_name, "Page viewed")


def log_form_submit(session_state, page_name, form_name, success=True, details=None):
    """
    Convenience function to log form submissions.
    
    Args:
        session_state: Streamlit session state object
        page_name (str): Name of the page
        form_name (str): Name of the form submitted
        success (bool): Whether submission was successful
        details (str, optional): Additional context (no PII)
    """
    logger = get_logger_from_session(session_state)
    status = "successful" if success else "failed"
    message = f"Form '{form_name}' submission {status}"
    
    if details:
        message += f" | {details}"
    
    level = 'INFO' if success else 'ERROR'
    logger._write_log(page_name, message, level)


def log_button_click(session_state, page_name, button_name, action_taken=None):
    """
    Convenience function to log button clicks.
    
    Args:
        session_state: Streamlit session state object
        page_name (str): Name of the page
        button_name (str): Name/label of the button
        action_taken (str, optional): Description of action performed
    """
    logger = get_logger_from_session(session_state)
    message = f"Button clicked: {button_name}"
    
    if action_taken:
        message += f" | Action: {action_taken}"
    
    logger.info(page_name, message)


def log_authentication(username, success, failure_reason=None):
    """
    Log authentication attempts (no password or sensitive data).
    
    Args:
        username (str): Username attempting to authenticate
        success (bool): Whether authentication succeeded
        failure_reason (str, optional): Reason for failure
    """
    logger = AppLogger()  # No user context yet
    
    if success:
        message = f"User '{username}' logged in successfully"
        logger.info('/login', message)
    else:
        message = f"Failed login attempt for user '{username}'"
        if failure_reason:
            message += f" | Reason: {failure_reason}"
        logger.warning('/login', message)


def log_database_operation(session_state, page_name, operation, table, success=True, error_msg=None):
    """
    Log database operations (CRUD).
    
    Args:
        session_state: Streamlit session state object
        page_name (str): Name of the page
        operation (str): Operation type (INSERT, UPDATE, DELETE, SELECT)
        table (str): Table name
        success (bool): Whether operation succeeded
        error_msg (str, optional): Error message if failed
    """
    logger = get_logger_from_session(session_state)
    message = f"Database {operation} on table '{table}'"
    
    if success:
        message += " completed successfully"
        logger.info(page_name, message)
    else:
        if error_msg:
            message += f" failed | Error: {error_msg}"
        else:
            message += " failed"
        logger.error(page_name, message)


def get_recent_logs(limit=100, organization_uuid=None, user_uuid=None, page=None, level=None):
    """
    Retrieve recent logs from database with optional filtering.
    
    Args:
        limit (int): Maximum number of logs to retrieve
        organization_uuid (str, optional): Filter by organization
        user_uuid (str, optional): Filter by user
        page (str, optional): Filter by page
        level (str, optional): Filter by log level
    
    Returns:
        list: List of log entries as tuples
    """
    conn = create_connection()
    c = conn.cursor()
    
    query = "SELECT * FROM logging WHERE 1=1"
    params = []
    
    if organization_uuid:
        query += " AND organization_uuid = ?"
        params.append(organization_uuid)
    
    if user_uuid:
        query += " AND user_uuid = ?"
        params.append(user_uuid)
    
    if page:
        query += " AND page = ?"
        params.append(page)
    
    if level:
        query += " AND level = ?"
        params.append(level)
    
    query += " ORDER BY created_datetime DESC LIMIT ?"
    params.append(limit)
    
    c.execute(query, params)
    results = c.fetchall()
    conn.close()
    
    return results


# Example usage in comments for reference
"""
# In a Streamlit page:
import streamlit as st
from utils.utils_logging import get_logger_from_session, log_page_view, log_button_click

# Log page view
log_page_view(st.session_state, '/admin/organizations')

# Or use the logger directly
logger = get_logger_from_session(st.session_state)
logger.info('/admin/organizations', 'Viewing organizations list')

# Log button click
if st.button('Add Organization'):
    log_button_click(st.session_state, '/admin/organizations', 'Add Organization', 'Opening add form')
    
# Log form submission
if form_submitted:
    log_form_submit(st.session_state, '/admin/organizations', 'add_organization_form', 
                   success=True, details='Organization XYZ added')

# Log database operation
try:
    org.insert(...)
    log_database_operation(st.session_state, '/admin/organizations', 'INSERT', 
                          'organization', success=True)
except Exception as e:
    log_database_operation(st.session_state, '/admin/organizations', 'INSERT', 
                          'organization', success=False, error_msg=str(e))
"""