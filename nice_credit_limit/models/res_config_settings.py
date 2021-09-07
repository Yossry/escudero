# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    ##self.env['ir.config_parameter'].sudo().get_param('sale.automatic_invoice')
    use_global_limit = fields.Boolean('Use Global Limit', default=False)
    global_limit = fields.Monetary("Global Credit Limit",  default=0.0)

    on_exceeded = fields.Selection(
        [('raise_exception', 'Raise an exception.'),
        ('leave_undecided', 'Leave to the concerned user role.')], 
        string='On Limit Exceeded')

    include_uninvoiced = fields.Boolean('Include Uninvoiced Amount',  default=True)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        Param = self.env['ir.config_parameter'].sudo()
        res['use_global_limit'] = Param.get_param('partner_credit_limit.use_global_limit')
        res['global_limit'] = float(Param.get_param('partner_credit_limit.global_limit')) or 0.0
        res['on_exceeded'] = Param.get_param('partner_credit_limit.on_exceeded') or 'raise_exception'
        res['include_uninvoiced'] = Param.get_param('partner_credit_limit.include_uninvoiced') #or True
        
        return res

    @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        Param = self.env['ir.config_parameter'].sudo()
        Param.set_param('partner_credit_limit.use_global_limit', self.use_global_limit)
        if self.use_global_limit:
            Param.set_param('partner_credit_limit.global_limit', self.global_limit)

        Param.set_param('partner_credit_limit.on_exceeded', self.on_exceeded)
        Param.set_param('partner_credit_limit.include_uninvoiced', self.include_uninvoiced)
