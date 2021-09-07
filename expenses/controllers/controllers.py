# -*- coding: utf-8 -*-
# from odoo import http


# class Expenses(http.Controller):
#     @http.route('/expenses/expenses/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/expenses/expenses/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('expenses.listing', {
#             'root': '/expenses/expenses',
#             'objects': http.request.env['expenses.expenses'].search([]),
#         })

#     @http.route('/expenses/expenses/objects/<model("expenses.expenses"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('expenses.object', {
#             'object': obj
#         })
