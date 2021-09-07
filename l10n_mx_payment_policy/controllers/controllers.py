# -*- coding: utf-8 -*-
# from odoo import http


# class L10nMxPaymentPolicy(http.Controller):
#     @http.route('/l10n_mx_payment_policy/l10n_mx_payment_policy/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_mx_payment_policy/l10n_mx_payment_policy/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_mx_payment_policy.listing', {
#             'root': '/l10n_mx_payment_policy/l10n_mx_payment_policy',
#             'objects': http.request.env['l10n_mx_payment_policy.l10n_mx_payment_policy'].search([]),
#         })

#     @http.route('/l10n_mx_payment_policy/l10n_mx_payment_policy/objects/<model("l10n_mx_payment_policy.l10n_mx_payment_policy"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_mx_payment_policy.object', {
#             'object': obj
#         })
