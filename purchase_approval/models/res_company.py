# -*- coding: utf-8 -*- 

from odoo import fields, models

class CompanyAddition(models.Model):
    _inherit = 'res.company'

    po_amount_second = fields.Float('Monto Segunda Validación')
    po_amount_third = fields.Float('Monto Tercera Validación')
    