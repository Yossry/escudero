# -*- coding: utf-8 -*-
from odoo import fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    disable_cfdi_validation = fields.Boolean(string="Inhabilitar Validar CFDI")