# -*- coding: utf-8 -*-

from odoo import api, models, fields


class stock_location(models.Model):
    """
    Override to add features of allowed users
    """
    _inherit = 'stock.location'

    @api.depends('own_user_ids', 'location_id.own_user_ids', 'location_id.user_ids')
    def _compute_user_ids(self):
        """
        Compute method for user_ids
        We consider a location available for this location users and users of its parents hierarchilly
        """
        for loc in self:
            user_ids = (loc.location_id and loc.location_id.user_ids.ids or []) + loc.own_user_ids.ids
            loc.user_ids = [(6, 0, user_ids)]

    def _inverse_own_user_ids(self):
        """
        Inverse method for own_user_ids

        Methods:
         * _compute_user_ids - to recompute children users
         * _inverse_own_user_ids - to make recursion for hierarchy
        """
        self = self.sudo()
        for loc in self:
            children_ids = self.env['stock.location'].search([('location_id', '=', loc.id)])
            for child in children_ids:
                child._compute_user_ids()
                child._inverse_own_user_ids()

    own_user_ids = fields.Many2many(
        'res.users',
        'res_users_stock_location_own_rel_table',
        'res_users_own_id',
        'stock_location_own_id',
        'Own Accepted Users',
        inverse=_inverse_own_user_ids,
    )
    user_ids = fields.Many2many(
        "res.users",
        "res_users_stock_location_rel_table",
        "res_users_id",
        "stock_location_id",
        string='Accepted Users',
        compute=_compute_user_ids,
        compute_sudo=True,
        store=True,
    )

    def name_get(self):
        """
        To avoid security rights in name_get
        """
        return super(stock_location, self.sudo()).name_get()
