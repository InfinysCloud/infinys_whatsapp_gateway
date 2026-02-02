import logging
import requests
from odoo import models, fields
from ..controllers import wuzapi_controller

_logger = logging.getLogger(__name__)
_wuzapi_controller = wuzapi_controller.WuzapiController()

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    wapi_phone_number = fields.Char(
        string="WAPI Phone Number",
        config_parameter="wapi.phone_number",
        required=True
    )

    wapi_url = fields.Char(
        string="WAPI Base URL", 
        config_parameter="wapi.base_url",
        default="https://wapi.infinysystem.com/v1",
        required=True, store=True
    )

    wapi_user = fields.Char(
        string="WAPI User",
        config_parameter="wapi.user", 
        required=True
    )

    wapi_token = fields.Char(
        string="WAPI Token",
        config_parameter="wapi.token",
        required=True,  store=True
    )

     
    def get_wapi_status(self):
        """The actual logic to hit the API. Accessible by Button and Controller."""
        # Get params from DB (sudo is important for controllers)
        params = self.env['ir.config_parameter'].sudo()
        url = params.get_param('wapi.base_url')
        token = params.get_param('wapi.token')
        
        try:
            headers = {'Authorization': f'Bearer {token}'}
            # Use requests (plural) library here
            response = requests.get(f"{url}/health", headers=headers, timeout=10)
            if response.status_code == 200:
                return {'status': 'success'}
            return {'status': 'error', 'error': {'message': f'Status {response.status_code}'}}
        except Exception as e:
            return {'status': 'error', 'error': {'message': str(e)}}

    def action_wapi_check_health(self):
        """ Test connection to Infinys Gateway """
        # Ensure we use sudo to read parameters and provide a clean feedback
        self.ensure_one()
        result = self.get_wapi_status()
        if result['status'] == 'success':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': 'WAPI connection successful!',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'danger',
                    'message': f'WAPI connection failed: {result["error"]["message"]}',
                    'sticky': False,
                }
            }   
       