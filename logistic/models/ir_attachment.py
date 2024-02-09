# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InheritIrAttachment(models.Model):
    _name = 'ir.attachment'
    _inherit = 'ir.attachment'

    wr_id = fields.Many2one(comodel_name="logistic.wr", string="WR")
