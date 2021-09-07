# -*- coding: utf-8 -*-

from odoo import models, fields, api

class DataTemplateSale(models.Model):
    _name = 'data.template.sale'


    name = fields.Char('Nombre de la Plantilla')
    garantias = fields.Text('Garantias')
    notas = fields.Text('Notas')
    recomendacion = fields.Text('Recomendaciones')
    fletes = fields.Text('Fletes y Estadias')