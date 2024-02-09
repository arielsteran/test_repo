# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Bundle(models.Model):
    _name = 'logistic.bundle'
    _description = 'Bulto'

    name = fields.Char(string="# Referencia", copied=False, store=True)
    packaging_id = fields.Many2one(comodel_name="logistic.packaging", string="Tipo")
    height = fields.Integer(string="Alto (inch)")
    width = fields.Integer(string="Ancho (inch)")
    length = fields.Integer(string="Largo (inch)")
    weight = fields.Integer(string="Peso (lb)")
    volume = fields.Float(string="Volúmen (ft3)", compute="compute_values")
    volumetric_weight = fields.Integer(string="Peso volumétrico (lb)", compute="compute_values")
    wr_id = fields.Many2one(comodel_name="logistic.wr", string="WR")
    alert_id = fields.Many2one(comodel_name="logistic.alert", string="Alerta")
    quantity = fields.Integer(string="Cantidad")

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'logistic.bundle.sequence') or 'Nuevo'
        result = super(Bundle, self).create(vals)
        return result

    @api.depends('height', 'width', 'length', 'quantity')
    def compute_values(self):
        """Falta calcular el peso volumetico en base a valores de largo, ancho y alto"""
        for record in self:
            record.volume = (record.height/12 * record.width/12 * record.length/12)*record.quantity
            record.volumetric_weight = ((record.height * record.width * record.length)/166)*record.quantity
            if record.volumetric_weight == 0:
                record.volumetric_weight = 1
