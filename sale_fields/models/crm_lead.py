



# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    
    def action_new_quotation(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale_crm.sale_action_quotations_new")
        action['context'] = {
            'search_default_opportunity_id': self.id,
            'default_opportunity_id': self.id,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_team_id': self.team_id.id,
            'default_campaign_id': self.campaign_id.id,
            'default_medium_id': self.medium_id.id,
            'default_origin': self.name,
            'default_source_id': self.source_id.id,
            'default_company_id': self.company_id.id or self.env.company.id,
            'default_tag_ids': [(6, 0, self.tag_ids.ids)],            
            'default_contact_name': self.contact_name,
            'default_partner_name': self.partner_name,
            'default_function': self.function,
            'default_title': self.title.id,
            'default_email_from': self.email_from,
            'default_phone': self.phone,
            'default_mobile': self.mobile,
            'default_website': self.website,
            'default_street': self.street,
            'default_street2': self.street2,
            'default_zip': self.zip,
            'default_city': self.city,
            'default_state_id': self.state_id.id,
            'default_country_id': self.country_id.id

        }
        return action