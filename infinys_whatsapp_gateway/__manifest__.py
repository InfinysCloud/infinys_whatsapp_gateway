# -*- coding: utf-8 -*-
{
    "name": "Infinys Whatsapp Gateway",
    "summary": """
        Simple solution for Odoo with Infinys Whatsapp Gateway for sending one-way WhatsApp messages.
    """,
    "description": """
        Infinys WhatsApp Gateway is a simple solution for sending automated WhatsApp notifications from systems such as Odoo, ERP, or internal applications. It is designed for one-way message delivery only, ideal for reminders, alerts, and important system notifications without chat or reply features.
        Contact the Infinys Odoo Team to obtain a WhatsApp API tenant and integrate it into the Infinys WhatsApp Gateway for Odoo.
        For other WhatsApp-related more further, you can use WhatsApp Blasting by Infinys System Indonesia.

        Key Feature :
        - Send one-way WhatsApp messages from Odoo.
        - Support sending messages with media (image, video, audio, document)
        - Automate with scheduler for sending messages at specified times and for better performance.
        - Record all outgoing notification for compliance and analysis.
        - Simple model (infinys_wapi_outbox) for storing outgoing messages, make it easy to integrate with other odoo model/controller.
    """,
    "author": "Infinys System Indonesia",
    "website": "https://integra.isi.id/",
    "category": "Tools",
    "version": "1.0.0",
    "license": "AGPL-3",
    "live_test_url": "https://integra.atisicloud.com/",
    "icon": "/infinys_whatsapp_gateway/static/description/icon.png",
    "depends": ["base", "mail"],
    "data": [
        "security/ir.model.access.csv",        # 1. Load Access Rights first
        "views/res_config_settings_views.xml", # 2. Load Configuration
        "views/wapi_outbox_views.xml",         # 3. Load the UI Views
        "data/ir_cron_data.xml"               # 4. Load the Cron Job last
    ],
    "images": [
        "static/description/banner.png",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
