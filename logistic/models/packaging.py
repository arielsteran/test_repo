# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Packaging(models.Model):
    _name = 'logistic.packaging'
    _description = 'Embalaje'

    name = fields.Char(string="Nombre")
