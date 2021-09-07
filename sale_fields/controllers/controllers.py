# -*- coding: utf-8 -*-
# from odoo import http


# class SaleFields(http.Controller):
#     @http.route('/sale_fields/sale_fields/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_fields/sale_fields/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_fields.listing', {
#             'root': '/sale_fields/sale_fields',
#             'objects': http.request.env['sale_fields.sale_fields'].search([]),
#         })

#     @http.route('/sale_fields/sale_fields/objects/<model("sale_fields.sale_fields"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_fields.object', {
#             'object': obj
#         })
