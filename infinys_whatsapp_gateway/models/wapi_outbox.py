import time
import requests
import json
import logging
from odoo import models, fields, api
from datetime import datetime, timedelta
from ..utils import texttohtml_utils
from ..utils import generic_utils

_logger = logging.getLogger(__name__)
_texttohtml_utils = texttohtml_utils
_genenric_utils = generic_utils

class WapiOutbox(models.Model):
    _name = 'infinys.wapi.outbox'
    _description = 'WAPI Message Outbox'
    _order = 'create_date desc, is_queued desc, is_delivered desc'

    name = fields.Char(string="Subject")
    phone = fields.Char(string="Phone Number", required=True, store=True, index=True)
    message = fields.Html(string="Message",  sanitize=False) # allow HTML tags
    error_msg = fields.Text(string="Error Message")
    
    hasmedia = fields.Boolean(string="Has Media", default=False, store=False, compute='set_hasmedia')
    media_url = fields.Char(string="Media URL")
    media_filename = fields.Char(string="Media Filename")   
    media_base64 = fields.Text(string="Media Base64")
    media_mime_type = fields.Char(string="Media MIME Type")
    attachment_id = fields.Many2many('ir.attachment', string="Attachment", copy=False) # keep False to avoid linking attachments; we have to copy them instead
    module_name = fields.Char(string="Module Name") # module name that sent this message like sales, purchase order, etc
    note = fields.Text(string="Note") # any note that we want to add to this message

    scheduled_date = fields.Datetime(string="Scheduled Date", default=fields.Datetime.now)
    sent_date = fields.Datetime(string="Sent Date", readonly=True)
    is_queued = fields.Boolean(string="Is Queued", default=True)
    is_delivered = fields.Boolean(string="Is Delivered", default=False)
    create_date = fields.Datetime(string="Created At", default=fields.Datetime.now, readonly=True)

    @api.depends('attachment_id')
    def set_hasmedia(self):
        for record in self:
            if record.attachment_id:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                attachment = record.attachment_id[0]
                attachment.public = True

                record.media_filename = attachment.name
                record.media_mime_type = _genenric_utils.get_mime_type_from_filename(attachment.name)
                record.media_url = url = f"{base_url}/web/content/{attachment.id}"
                record.hasmedia = len(record.attachment_id.ids) > 0
                record.media_base64 = _genenric_utils.convert_data_uri_to_bytes(record.media_mime_type, url)
            elif record.media_base64:
                record.hasmedia = True
            else:
                record.hasmedia = False
                record.media_filename = False
                record.media_url = False
                record.media_base64 = False
                record.media_mime_type = False
 
    def send_message_immediate(self):       
        for record in self:
            if record.hasmedia is None:
                self.set_hasmedia()
                
            record.scheduled_date = fields.Datetime.now()
            record.is_queued = True
            record.is_delivered = False
            record.error_msg = None
            _logger.info(f"Sending immediate message to {record.phone} at {record.sent_date}.")
            status = self.execute_send_message(record)
            return status
            
    def send_message(self):
        for record in self:

            if record.hasmedia is None:
                self.set_hasmedia()

            record.scheduled_date = fields.Datetime.now()
            record.is_queued = True
            record.is_delivered = False
            record.error_msg = None
            _logger.info(f"Queued message to {record.phone} for sending at {record.scheduled_date}.")
            
        
    #-- Core Methods --#
    def execute_send_message(self, queued_records):
        status = None

        try:
            for record in queued_records:
                if record.is_queued:
                    # Simulate typing presence
                    time.sleep(5)  # Simulate processing delay
                    set_presence = self.set_user_typing()
                    
                    #record hasemedia false
                    if not record.hasmedia:
                        _logger.info(f"Sending text message to {record.phone} with no media.")
                        result = self.send_text_message(record.phone, record.message)
                        _logger.info(f"HTTP Status for send_text_message to {record.phone}: {status} and response: {result}")

                        if result == True:
                            status = True
                            record.write(
                                    {   'is_queued': False,
                                        'sent_date' : datetime.now(),
                                        'is_delivered': True,
                                        'error_msg': None
                                    } 
                                )
                            _logger.info(f"Text message to {record.phone} sent successfully.")
                        else:
                            record.write(
                                    {   'is_queued': False,
                                        'sent_date' : datetime.now(),
                                        'is_delivered': False,
                                        'error_msg': result.get("error", "Unknown error")
                                    } 
                                )
                            _logger.error(f"Failed to send text message to {record.phone}: {record.error_msg}")
                        
                    else:
                        _logger.info(f"Sending text message to {record.phone} with has media.")

                        result_media = self.send_media_message(record.phone, 
                                record.message,
                                record.media_mime_type, 
                                record.media_filename, 
                                record.media_base64)
                        _logger.info(f"HTTP Status for send_media_message to {record.phone}: {status} and response: {result_media}")
                       
                        if result_media == True:
                            status = True
                            record.write(
                                    {   'is_queued': False,
                                        'is_delivered': True,
                                        'sent_date' : datetime.now(),
                                        'error_msg': None
                                    } 
                                )
                            _logger.info(f"Media message to {record.phone} sent successfully.")
                        else:
                            record.write(
                                   { 'is_delivered': False,
                                    'sent_date' : datetime.now(),
                                    'error_msg': result.get("error", "Unknown error")
                                    } 
                                )
                            _logger.error(f"Failed to send media message to {record.phone}: {record.error_msg}")

                _logger.info(f"Final status after sending messages: {status}")    
                return status
        except Exception as e:
            record.is_queued = False
            record.is_delivered = False
            record.sent_date = None
            record.error_msg = str(e)
            _logger.error(f"Error in send_message: {e}")
            return False
            
    #-- Helper Methods --#   
    def mark_as_delivered(self):
        for record in self:
            if not record.is_delivered:
                record.is_delivered = True
                _logger.info(f"Message to {record.phone} marked as delivered.")
            else:
                _logger.info(f"Message to {record.phone} is already marked as delivered.")
    
    @api.model
    def _cron_send_queued_messages(self):
        """ Method called by Scheduled Action to process the queue """
        now = fields.Datetime.now()
        _logger.info("_cron_send_queued_messages started now %s.", now)
        #buffer_minutes = 10
        #one_minute_ago = now - timedelta(minutes=buffer_minutes)
        #one_minute_after = now + timedelta(minutes=2)
        #_logger.info("one_minute_ago: %s", one_minute_ago)
        #_logger.info("one_minute_after: %s", one_minute_after)  

        #queued_messages = self.sudo().search([('is_queued', '=', True),
        #                                ('sent_date', '>=', one_minute_ago),
        #                                ('sent_date', '<=', one_minute_after)
        #                            ], limit=100)

        queued_messages = self.sudo().search([('is_queued', '=', True)], limit=20, order='scheduled_date asc, id asc')

        if queued_messages:
            _logger.info("WAPI Cron: Processing %s Total queued messages", len(queued_messages))
            
            try:
                for record in queued_messages:
                    record.error_msg = None
                    self.execute_send_message(record)
                    time.sleep(2)
            except Exception as e:
                _logger.error("Error sending queued messages: %s", e)


    #-- WAPI Integration Methods --#
    def set_user_typing(self):
        try:
            get_param = self.env['ir.config_parameter'].sudo().get_param
            wapi_url = get_param('wapi.base_url')
            wapi_user = get_param('wapi.user')
            wapi_token = get_param('wapi.token')
            wapi_phone_number = get_param('wapi.phone_number')
            
            payload = json.dumps({
                "Phone": wapi_phone_number,
                "State": "composing",
                "Media": ""
            })
            
            headers = {
                'token': f'{wapi_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            url = f"{wapi_url}/chat/presence"
            _logger.info(f"Setting presence with URL: {url} and payload: {payload}")

            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            status = response.json().get("success", "unknown")
            _logger.info(f"WAPI Presence Status: {status}")
            return status
        except requests.RequestException as e:
            _logger.error(f"Failed to set presence: {e}")
            return "error"

    #-- WAPI Message Sending Methods --#
    def send_text_message(self, phone_to, message):
        try:
            url = None
            payload = None
            wapi_url = None

            get_param = self.env['ir.config_parameter'].sudo().get_param
            wapi_url = get_param('wapi.base_url')
            wapi_user = get_param('wapi.user')
            wapi_token = get_param('wapi.token')

            payload = json.dumps({
                "Phone": phone_to,
                "Body": _texttohtml_utils.clean_html_for_whatsapp(message),
                "LinkPreview": True
            })

            headers = {
                'token': f'{wapi_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            url = f"{wapi_url}/chat/send/text"
            _logger.info(f"Sending text message with URL: {url} and payload: {payload}")
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()

            status = response.json().get("success", "unknown")
            _logger.info(f"WAPI Text Message Status: {status}")
            return status
        except requests.RequestException as e:
            _logger.error(f"Failed to send text message to {phone_to}: {e}")
            return {"error": str(e)}

    def send_media_message(self, phone_to, message, mime_type, media_filename, media_base64):
        try:
            url = None
            payload = None
            wapi_url = None

            get_param = self.env['ir.config_parameter'].sudo().get_param
            wapi_url = get_param('wapi.base_url')
            wapi_user = get_param('wapi.user')
            wapi_token = get_param('wapi.token')

            message = _texttohtml_utils.clean_html_for_whatsapp(message)
            
            if mime_type == 'image':
                payload = json.dumps({
                    "Phone": phone_to,
                    "Image": f"data:image/jpeg;base64,{media_base64}",
                    "Caption": message,
                    "FileName": media_filename
                })
                url = f"{wapi_url}/chat/send/image"
            elif mime_type == 'video':
                payload = json.dumps({
                    "Phone": phone_to,
                    "Video": f"data:video/mp4;base64,{media_base64}",
                    "Caption": message,
                    "FileName": media_filename
                })
                url = f"{wapi_url}/chat/send/video"

                #send media message
                self.send_text_message(phone_to, message)

            elif mime_type == 'audio':
                payload = json.dumps({
                    "Phone": phone_to,
                    "Audio": f"data:audio/ogg;base64,{media_base64}",
                    "Caption": message,
                    "FileName": media_filename
                })
                url = f"{wapi_url}/chat/send/audio"

                 #send media message
                self.send_text_message(phone_to, message)
            else:  # document
                payload = json.dumps({
                    "Phone": phone_to,
                    "Document": f"data:application/octet-stream;base64,{media_base64}",
                    "Caption": message,
                    "FileName": media_filename
                })   
                url = f"{wapi_url}/chat/send/document"
            
            headers = {
                'token': f'{wapi_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            _logger.info(f"Sending media message phono_to {phone_to} with URL: {url} and payload")
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()

            status = response.json().get("success", "unknown")
            _logger.info(f"WAPI Media Message Status: {status}")
            return status
        except requests.RequestException as e:
            _logger.error(f"Failed to send media message to {phone_to}: {e}")
            return {"error": str(e)}