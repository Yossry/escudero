# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_is_zero, float_compare
from datetime import datetime
from collections import namedtuple, OrderedDict, defaultdict




    
class SaleOrderLine(models.Model):
    
    _inherit = 'sale.order.line'

    def _prepare_procurement_values(self,group_id):
        res = super(SaleOrderLine,self)._prepare_procurement_values(group_id=group_id)
        tag_ids = []
        for tag in self.analytic_tag_ids:
            tag_ids.append(tag.id)
        res.update({
            'analytic_account_id':self.order_id.analytic_account_id.id,
            'tag_ids':[(6,0,tag_ids)],
            })
        return res
    

