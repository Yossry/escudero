# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    po_amount_second = fields.Float('Monto Segunda Validación')
    po_amount_third = fields.Float('Monto Tercera Validación')
    #po_double_validation_user = fields.Many2many('res.users', string="Aprobador 2 Nivel")
    #po_double_validation_categories = fields.Many2many('product.category', related="company_id.po_double_validation_categories", string="Categorías para validaciones", readonly=False)
    #po_double_validation_analytic = fields.Many2one('account.analytic.account', related="company_id.po_double_validation_analytic", string="Cuenta analítica para validaciones", readonly=False)