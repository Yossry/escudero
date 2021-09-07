# -*- coding: utf-8 -*-
from odoo import models, fields

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    code_exit = fields.Char(string="Código corto (Egreso)")
    
    