# -*- coding: utf-8 -*-
from __future__ import annotations

import time
import json
import logging
from datetime import datetime

import requests

from typing import Any

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from ..utils import texttohtml_utils
from ..utils import generic_utils

_logger = logging.getLogger(__name__)
_texttohtml_utils = texttohtml_utils
_generic_utils = generic_utils


class WapiOutbox(models.Model):
    _name = 'infinys.wapi.outbox'
    _description = 'WAPI Message Outbox'
    _order = 'create_date desc, is_queued desc, is_delivered desc'

    name = fields.Char(string="Subject")
    phone = fields.Char(
        string="Phone Number",
        required=True,
        store=True,
        index=True,
        help="International format, digits only, without '+' or '-'. "
             "Example: 628176057749",
    )
    message = fields.Html(string="Message", sanitize=False)  # allow HTML tags
    error_msg = fields.Text(string="Error Message")

    hasmedia = fields.Boolean(
        string="Has Media",
        default=False,
        store=False,
        compute='_compute_hasmedia',
    )
    media_url = fields.Char(string="Media URL")
    media_filename = fields.Char(string="Media Filename")
    media_base64 = fields.Text(string="Media Base64")
    media_mime_type = fields.Char(string="Media MIME Type")
    # keep copy=False to avoid linking attachments; we have to copy them instead
    attachment_id = fields.Many2many('ir.attachment', string="Attachment", copy=False)
    # module name that sent this message like sales, purchase order, etc
    module_name = fields.Char(string="Module Name")
    note = fields.Text(string="Note")  # any note that we want to add to this message

    scheduled_date = fields.Datetime(string="Scheduled Date", default=fields.Datetime.now)
    sent_date = fields.Datetime(string="Sent Date", readonly=True)
    is_queued = fields.Boolean(string="Is Queued", default=True)
    is_delivered = fields.Boolean(string="Is Delivered", default=False)
    # NOTE: create_date is an automatic Odoo log-access field. It is intentionally
    # NOT redefined here (doing so is incompatible with Odoo 19). It remains
    # available automatically and is used in _order above.

    # -- Phone Number Normalization & Validation --#
    @staticmethod
    def _normalize_phone(phone):
        """Strip '+', '-', spaces and other separators; keep digits only."""
        return _generic_utils.normalize_phone_number(phone)

    @api.onchange('phone')
    def _onchange_phone(self) -> None:
        """Clean the phone number live in the form as the user types/pastes it."""
        if self.phone:
            self.phone = self._normalize_phone(self.phone)

    @api.constrains('phone')
    def _check_phone(self) -> None:
        """Ensure the stored phone number is digits-only international format."""
        for record in self:
            if not record.phone:
                continue
            if not _generic_utils.is_valid_phone_number(record.phone):
                raise ValidationError(_(
                    "Invalid phone number '%s'.\n\n"
                    "Use international format with digits only, no '+' or '-' "
                    "and no leading zero.\nExample: 628176057749"
                ) % record.phone)

    @api.model_create_multi
    def create(self, vals_list: list[dict[str, Any]]) -> "WapiOutbox":
        for vals in vals_list:
            if vals.get('phone'):
                vals['phone'] = self._normalize_phone(vals['phone'])
        return super().create(vals_list)

    def write(self, vals: dict[str, Any]) -> bool:
        if vals.get('phone'):
            vals['phone'] = self._normalize_phone(vals['phone'])
        return super().write(vals)

    @api.depends('attachment_id')
    def _compute_hasmedia(self) -> None:
        for record in self:
            if record.attachment_id:
                base_url = self.env['ir.config_parameter'].sudo().get_str('web.base.url')
                attachment = record.attachment_id[0]
                attachment.public = True

                record.media_filename = attachment.name
                record.media_mime_type = _generic_utils.get_mime_type_from_filename(attachment.name)
                url = f"{base_url}/web/content/{attachment.id}"
                record.media_url = url
                record.hasmedia = len(record.attachment_id.ids) > 0
                record.media_base64 = _generic_utils.convert_data_uri_to_bytes(
                    record.media_mime_type, url
                )
            elif record.media_base64:
                record.hasmedia = True
            else:
                record.hasmedia = False
                record.media_filename = False
                record.media_url = False
                record.media_base64 = False
                record.media_mime_type = False

    def send_message_immediate(self) -> bool | None:
        status = None
        for record in self:
            record.scheduled_date = fields.Datetime.now()
            record.is_queued = True
            record.is_delivered = False
            record.error_msg = None
            _logger.info(
                "Sending immediate message to %s at %s.",
                record.phone, record.sent_date,
            )
            status = self.execute_send_message(record)
        return status

    def send_message(self) -> None:
        for record in self:
            record.scheduled_date = fields.Datetime.now()
            record.is_queued = True
            record.is_delivered = False
            record.error_msg = None
            _logger.info(
                "Queued message to %s for sending at %s.",
                record.phone, record.scheduled_date,
            )

    # -- Core Methods --#
    def execute_send_message(self, queued_records) -> bool | None:
        status = None

        for record in queued_records:
            try:
                if not record.is_queued:
                    continue

                # Simulate typing presence
                time.sleep(5)  # Simulate processing delay
                self.set_user_typing()

                if not record.hasmedia:
                    _logger.info("Sending text message to %s with no media.", record.phone)
                    result = self.send_text_message(record.phone, record.message)
                    _logger.info(
                        "HTTP Status for send_text_message to %s: %s and response: %s",
                        record.phone, status, result,
                    )

                    if result is True:
                        status = True
                        record.write({
                            'is_queued': False,
                            'sent_date': datetime.now(),
                            'is_delivered': True,
                            'error_msg': None,
                        })
                        _logger.info("Text message to %s sent successfully.", record.phone)
                    else:
                        record.write({
                            'is_queued': False,
                            'sent_date': datetime.now(),
                            'is_delivered': False,
                            'error_msg': self._extract_error(result),
                        })
                        _logger.error(
                            "Failed to send text message to %s: %s",
                            record.phone, record.error_msg,
                        )
                else:
                    _logger.info("Sending message to %s with media.", record.phone)
                    result_media = self.send_media_message(
                        record.phone,
                        record.message,
                        record.media_mime_type,
                        record.media_filename,
                        record.media_base64,
                    )
                    _logger.info(
                        "HTTP Status for send_media_message to %s: %s and response: %s",
                        record.phone, status, result_media,
                    )

                    if result_media is True:
                        status = True
                        record.write({
                            'is_queued': False,
                            'is_delivered': True,
                            'sent_date': datetime.now(),
                            'error_msg': None,
                        })
                        _logger.info("Media message to %s sent successfully.", record.phone)
                    else:
                        record.write({
                            'is_queued': False,
                            'is_delivered': False,
                            'sent_date': datetime.now(),
                            'error_msg': self._extract_error(result_media),
                        })
                        _logger.error(
                            "Failed to send media message to %s: %s",
                            record.phone, record.error_msg,
                        )
            except Exception as e:
                record.write({
                    'is_queued': False,
                    'is_delivered': False,
                    'sent_date': None,
                    'error_msg': str(e),
                })
                _logger.error("Error in execute_send_message for %s: %s", record.phone, e)
                status = False

        _logger.info("Final status after sending messages: %s", status)
        return status

    @staticmethod
    def _extract_error(result) -> str:
        """Safely extract an error message from a send result."""
        if isinstance(result, dict):
            return result.get("error", "Unknown error")
        return "Unknown error"

    # -- Helper Methods --#
    def mark_as_delivered(self) -> None:
        for record in self:
            if not record.is_delivered:
                record.is_delivered = True
                _logger.info("Message to %s marked as delivered.", record.phone)
            else:
                _logger.info("Message to %s is already marked as delivered.", record.phone)

    @api.model
    def _cron_send_queued_messages(self) -> None:
        """Method called by Scheduled Action to process the queue."""
        now = fields.Datetime.now()
        _logger.info("_cron_send_queued_messages started now %s.", now)

        queued_messages = self.sudo().search(
            [('is_queued', '=', True)],
            limit=20,
            order='scheduled_date asc, id asc',
        )

        if queued_messages:
            _logger.info("WAPI Cron: Processing %s total queued messages", len(queued_messages))
            try:
                for record in queued_messages:
                    record.error_msg = None
                    self.execute_send_message(record)
                    time.sleep(2)
            except Exception as e:
                _logger.error("Error sending queued messages: %s", e)

    # -- WAPI Integration Methods --#
    def set_user_typing(self) -> str:
        try:
            get_str = self.env['ir.config_parameter'].sudo().get_str
            wapi_url = get_str('wapi.base_url')
            wapi_token = get_str('wapi.token')
            wapi_phone_number = get_str('wapi.phone_number')

            payload = json.dumps({
                "Phone": wapi_phone_number,
                "State": "composing",
                "Media": "",
            })

            headers = {
                'token': f'{wapi_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }

            url = f"{wapi_url}/chat/presence"
            _logger.info("Setting presence with URL: %s and payload: %s", url, payload)

            response = requests.post(url, headers=headers, data=payload, timeout=30)
            response.raise_for_status()
            status = response.json().get("success", "unknown")
            _logger.info("WAPI Presence Status: %s", status)
            return status
        except requests.RequestException as e:
            _logger.error("Failed to set presence: %s", e)
            return "error"

    # -- WAPI Message Sending Methods --#
    def send_text_message(self, phone_to: str, message: str):
        try:
            get_str = self.env['ir.config_parameter'].sudo().get_str
            wapi_url = get_str('wapi.base_url')
            wapi_token = get_str('wapi.token')

            payload = json.dumps({
                "Phone": phone_to,
                "Body": _texttohtml_utils.clean_html_for_whatsapp(message),
                "LinkPreview": True,
            })

            headers = {
                'token': f'{wapi_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }

            url = f"{wapi_url}/chat/send/text"
            _logger.info("Sending text message with URL: %s and payload: %s", url, payload)
            response = requests.post(url, headers=headers, data=payload, timeout=30)
            response.raise_for_status()

            status = response.json().get("success", "unknown")
            _logger.info("WAPI Text Message Status: %s", status)
            return status
        except requests.RequestException as e:
            _logger.error("Failed to send text message to %s: %s", phone_to, e)
            return {"error": str(e)}

    def send_media_message(
        self,
        phone_to: str,
        message: str,
        mime_type: str,
        media_filename: str,
        media_base64: str,
    ):
        try:
            get_str = self.env['ir.config_parameter'].sudo().get_str
            wapi_url = get_str('wapi.base_url')
            wapi_token = get_str('wapi.token')

            message = _texttohtml_utils.clean_html_for_whatsapp(message)

            if mime_type == 'image':
                payload = json.dumps({
                    "Phone": phone_to,
                    "Image": f"data:image/jpeg;base64,{media_base64}",
                    "Caption": message,
                    "FileName": media_filename,
                })
                url = f"{wapi_url}/chat/send/image"
            elif mime_type == 'video':
                payload = json.dumps({
                    "Phone": phone_to,
                    "Video": f"data:video/mp4;base64,{media_base64}",
                    "Caption": message,
                    "FileName": media_filename,
                })
                url = f"{wapi_url}/chat/send/video"
            elif mime_type == 'audio':
                payload = json.dumps({
                    "Phone": phone_to,
                    "Audio": f"data:audio/ogg;base64,{media_base64}",
                    "Caption": message,
                    "FileName": media_filename,
                })
                url = f"{wapi_url}/chat/send/audio"
            else:  # document
                payload = json.dumps({
                    "Phone": phone_to,
                    "Document": f"data:application/octet-stream;base64,{media_base64}",
                    "Caption": message,
                    "FileName": media_filename,
                })
                url = f"{wapi_url}/chat/send/document"

            headers = {
                'token': f'{wapi_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }

            _logger.info("Sending media message to %s with URL: %s", phone_to, url)
            response = requests.post(url, headers=headers, data=payload, timeout=60)
            response.raise_for_status()

            status = response.json().get("success", "unknown")
            _logger.info("WAPI Media Message Status: %s", status)
            return status
        except requests.RequestException as e:
            _logger.error("Failed to send media message to %s: %s", phone_to, e)
            return {"error": str(e)}
