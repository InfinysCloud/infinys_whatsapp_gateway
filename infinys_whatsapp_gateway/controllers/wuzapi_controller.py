import re
import json
import logging
from curses import raw
from datetime import datetime
from odoo import http
from odoo.http import request
from ..utils import texttohtml_utils

_logger = logging.getLogger(__name__)
_texttohtml_utils = texttohtml_utils

#API V1 Whatsapp Controller 
class WuzapiController(http.Controller):

    @http.route('/api/wapi/wuzapi/health', type='json', auth='public', methods=['POST'], csrf=False)
    def wapi_health(self, **post):
        _logger.info("WAPI Health Check: %s", post)
        try:
            status = request.env['res.config.settings'].sudo().get_wapi_status()
            return success_response(None, status)
        except Exception as e:
            _logger.error("WAPI Health Check Error: %s", e)
            return error_response(e, "Failed to check WAPI health.")

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

def success_response(id,data):
    return {
        "jsonrpc": "2.0",
        "id": id,
        "status": "success",
        "result": data
    }