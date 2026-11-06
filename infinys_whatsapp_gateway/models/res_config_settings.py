# -*- coding: utf-8 -*-
from __future__ import annotations

import logging

import requests

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from ..utils import generic_utils

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    wapi_phone_number = fields.Char(
        string="WAPI Phone Number",
        config_parameter="wapi.phone_number",
        required=True,
        help="International format, digits only, without '+' or '-'. "
             "Example: 628176057749",
    )

    wapi_url = fields.Char(
        string="WAPI Base URL",
        config_parameter="wapi.base_url",
        default="https://wapi.infinysystem.com/v1",
        required=True,
        store=True,
    )

    wapi_user = fields.Char(
        string="WAPI User",
        config_parameter="wapi.user",
        required=True,
    )

    wapi_token = fields.Char(
        string="WAPI Token",
        config_parameter="wapi.token",
        required=True,
        store=True,
    )

    @api.onchange('wapi_phone_number')
    def _onchange_wapi_phone_number(self) -> None:
        """Clean the sender number live as the user types/pastes it."""
        if self.wapi_phone_number:
            self.wapi_phone_number = generic_utils.normalize_phone_number(
                self.wapi_phone_number
            )

    def set_values(self) -> None:
        """Normalize and validate the sender number before persisting it."""
        if self.wapi_phone_number:
            normalized = generic_utils.normalize_phone_number(self.wapi_phone_number)
            if not generic_utils.is_valid_phone_number(normalized):
                raise ValidationError(_(
                    "Invalid WAPI Phone Number '%s'.\n\n"
                    "Use international format with digits only, no '+' or '-' "
                    "and no leading zero.\nExample: 628176057749"
                ) % self.wapi_phone_number)
            self.wapi_phone_number = normalized
        return super().set_values()

    def get_wapi_status(self) -> dict:
        """The actual logic to hit the API. Accessible by Button and Controller."""
        # Get params from DB (sudo is important for controllers)
        params = self.env['ir.config_parameter'].sudo()
        url = params.get_str('wapi.base_url')
        token = params.get_str('wapi.token')

        try:
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(f"{url}/health", headers=headers, timeout=10)
            if response.status_code == 200:
                return {'status': 'success'}
            return {'status': 'error', 'error': {'message': f'Status {response.status_code}'}}
        except Exception as e:
            return {'status': 'error', 'error': {'message': str(e)}}

    def action_wapi_check_health(self) -> dict:
        """Test connection to Infinys Gateway."""
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
                },
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'danger',
                'message': f'WAPI connection failed: {result["error"]["message"]}',
                'sticky': False,
            },
        }
