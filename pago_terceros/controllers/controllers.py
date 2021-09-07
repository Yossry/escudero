# -*- coding: utf-8 -*-
# from odoo import http


# class PagoTerceros(http.Controller):
#     @http.route('/pago_terceros/pago_terceros/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pago_terceros/pago_terceros/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pago_terceros.listing', {
#             'root': '/pago_terceros/pago_terceros',
#             'objects': http.request.env['pago_terceros.pago_terceros'].search([]),
#         })

#     @http.route('/pago_terceros/pago_terceros/objects/<model("pago_terceros.pago_terceros"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pago_terceros.object', {
#             'object': obj
#         })
