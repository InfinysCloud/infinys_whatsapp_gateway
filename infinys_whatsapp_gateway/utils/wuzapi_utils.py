import requests
import json
import base64 as basic64
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

def test_connection(whatapp_api_url, username, password, token, whatsapp_number):
    
        result = ping_health_checkserver(whatapp_api_url, username, password,token)
        if result.get('status') == 'success':
            result = ping_webhook_status(whatapp_api_url, username, password,token)
            return result
        else:
            _logger.error("Ping failed: %s", result)
            raise UserError(f"Failed to connect to wa-isi: {result.get('message', 'Unknown error')}")

def ping_health_checkserver(whatapp_api_url, username, password, token):

    _logger.info("Pinging ping_health_checkserver: %s", whatapp_api_url)
    
    headers = {
        'token': f'{token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    payload = { }
    
    try:
        
        response = requests.get(f'{whatapp_api_url}/health', headers=headers, data=payload)
        response.raise_for_status()
        return success_response(response.json())
    
    except requests.RequestException as e:
        _logger.error("Error pinging wa-api ISI: %s and header %s", e, headers)
        return {'status': 'error', 'message': str(e)}    


def ping_webhook_status(whatapp_api_url, username, password, token):
    _logger.info("Pinging get_webhook_status: %s", whatapp_api_url)

    headers = {
        'token': f'{token}', 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    payload = { }
    
    try:
        
        response = requests.get(f'{whatapp_api_url}/webhook', headers=headers, data=payload)
        response.raise_for_status()
        return success_response(response.json())
    
    except requests.RequestException as e:
        _logger.error("Error pinging get_webhook_status: %s and header %s", e, headers)
        return {'status': 'error', 'message': str(e)}    
    
def error_response(error, msg):
    return {
        "jsonrpc": "2.0",
        "id": None,
        "status": "error",
        "error": {
            "code": 200,
            "message": msg,
            "data": {
                "name": str(error),
                "debug": "",
                "message": msg,
                "arguments": list(error.args),
                "exception_type": type(error).__name__
            }
        }
    }

def success_response(data):
    return {
        "jsonrpc": "2.0",
        "id": None,
        "status": "success",
        "result": data
    }