"""Logging utility for tracking user interactions and system events."""
import sqlite3
import os
import logging
import random
import json

from config.config import FULL_DATABASE_FILE_PATH
from utils.utils_system_specs import get_system_specs
from utils.utils_uuid import generate_uuid
from utils.utils import get_utc_datetime


# --------------------------------------------------------------------------- #
# CONNECTION
# --------------------------------------------------------------------------- #
def create_connection():
    conn = sqlite3.connect(FULL_DATABASE_FILE_PATH)
    print(f"[DB] Connected to {FULL_DATABASE_FILE_PATH}")
    return conn


# --------------------------------------------------------------------------- #
# LOGGING MODEL (moved here)
# --------------------------------------------------------------------------- #
class Logging:
    table = "logging"
    uuid_field = "logging_uuid"

    @staticmethod
    def insert(organization_uuid, user_uuid, page, message, level):
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        random_number = random.randint(1, 999999999)
        logging_uuid = generate_uuid(f"{organization_uuid}{user_uuid}{page}{str(random_number)}")
        logging_sql = f"""
INSERT INTO logging (logging_uuid, organization_uuid, user_uuid, page, message, level, created_datetime)
VALUES ('{logging_uuid}', '{organization_uuid}', '{user_uuid}', '{page}', '{message}', '{level}', '{now}')
"""
        # print(f"{logging_uuid}\t{page}\t{random_number}")
        # print(f"{logging_sql}")

        try:
            c.execute(logging_sql)
            conn.commit()
            return logging_uuid
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()


# --------------------------------------------------------------------------- #
# APP LOGGER
# --------------------------------------------------------------------------- #
class AppLogger:
    LEVEL_MAP = {
        logging.DEBUG: 'DEBUG',
        logging.INFO: 'INFO',
        logging.WARNING: 'WARNING',
        logging.ERROR: 'ERROR',
        logging.CRITICAL: 'CRITICAL'
    }

    def __init__(self, organization_uuid=None, user_uuid=None, console_output=False):
        self.organization_uuid = organization_uuid or ""
        self.user_uuid = user_uuid or ""
        self.console_output = console_output

    def _write_log(self, page, message, level):
        try:
            Logging.insert(
                organization_uuid=self.organization_uuid,
                user_uuid=self.user_uuid,
                page=page,
                message=message,
                level=level
            )
            if self.console_output:
                print(f"[{level}] {page}: {message}")
        except Exception as e:
            print(f"ERROR: Failed to write log: {e}")
            print(f"[{level}] {page}: {message}")

    def debug(self, page, message):    self._write_log(page, message, 'DEBUG')
    def info(self, page, message):     self._write_log(page, message, 'INFO')
    def warning(self, page, message):  self._write_log(page, message, 'WARNING')
    def error(self, page, message):    self._write_log(page, message, 'ERROR')
    def critical(self, page, message): self._write_log(page, message, 'CRITICAL')

    def log_action(self, page, action, details=None, level='INFO'):
        msg = f"Action: {action}" + (f" | Details: {details}" if details else "")
        self._write_log(page, msg, level)

    def log_error_with_exception(self, page, message, exception):
        msg = f"{message} | Exception: {type(exception).__name__}: {str(exception)}"
        self._write_log(page, msg, 'ERROR')


# --------------------------------------------------------------------------- #
# HELPER FUNCTIONS
# --------------------------------------------------------------------------- #
def get_logger_from_session(session_state, console_output=False):
    org_uuid = session_state.get('org_uuid')
    user_uuid = session_state.get('user_uuid')
    return AppLogger(org_uuid, user_uuid, console_output)


def log_landing_page(session_state, page_name): 
    get_logger_from_session(session_state).info(page_name, json.dumps(get_system_specs(), indent=4, default=str))


def log_system_status(session_state, system_status_payload, page_name='/system_status'): 
    get_logger_from_session(session_state).info(page_name, json.dumps(system_status_payload, indent=4, default=str))


def log_page_view(session_state, page_name):
    get_logger_from_session(session_state).info(page_name, "Page viewed")


def log_form_submit(session_state, page_name, form_name, success=True, details=None):
    logger = get_logger_from_session(session_state)
    status = "successful" if success else "failed"
    msg = f"Form '{form_name}' submission {status}" + (f" | {details}" if details else "")
    level = 'INFO' if success else 'ERROR'
    logger._write_log(page_name, msg, level)


def log_button_click(session_state, page_name, button_name, action_taken=None):
    msg = f"Button clicked: {button_name}" + (f" | Action: {action_taken}" if action_taken else "")
    get_logger_from_session(session_state).info(page_name, msg)


def log_authentication(username, success, failure_reason=None):
    logger = AppLogger()
    if success:
        logger.info('/login', f"User '{username}' logged in successfully")
    else:
        msg = f"Failed login attempt for user '{username}'"
        if failure_reason:
            msg += f" | Reason: {failure_reason}"
        logger.warning('/login', msg)


def log_database_operation(session_state, page_name, operation, table, success=True, error_msg=None):
    logger = get_logger_from_session(session_state)
    message = f"Database {operation} on table '{table}'"
    if success:
        message += " completed successfully"
        logger.info(page_name, message)
    else:
        message += f" failed | Error: {error_msg or 'Unknown'}"
        logger.error(page_name, message)


def get_recent_logs(limit=100, organization_uuid=None, user_uuid=None, page=None, level=None):
    conn = create_connection()
    c = conn.cursor()
    query = "SELECT * FROM logging WHERE 1=1"
    params = []
    if organization_uuid: query += " AND organization_uuid = ?"; params.append(organization_uuid)
    if user_uuid: query += " AND user_uuid = ?"; params.append(user_uuid)
    if page: query += " AND page = ?"; params.append(page)
    if level: query += " AND level = ?"; params.append(level)
    query += " ORDER BY created_datetime DESC LIMIT ?"
    params.append(limit)
    c.execute(query, params)
    results = c.fetchall()
    conn.close()
    return results