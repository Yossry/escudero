# -*- coding: utf-8 -*-
# from odoo import http


# class SaleAnticipo(http.Controller):
#     @http.route('/sale_anticipo/sale_anticipo/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_anticipo/sale_anticipo/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_anticipo.listing', {
#             'root': '/sale_anticipo/sale_anticipo',
#             'objects': http.request.env['sale_anticipo.sale_anticipo'].search([]),
#         })

#     @http.route('/sale_anticipo/sale_anticipo/objects/<model("sale_anticipo.sale_anticipo"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_anticipo.object', {
#             'object': obj
#         })
