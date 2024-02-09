# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Conmer(models.Model):
    _name = 'logistic.conmer'
    _order = "search_date desc, id desc"
    _description = 'CONMER'
    _order = 'date_search desc,id desc'

    name = fields.Char(string="# Referencia")

    filter_by = fields.Selection(
        help="Campo útil para filtrar los WRs según la necesidad de cada momento.",
        selection=[
            ('name', 'Referencia de WR'), ('state', 'Estado de WR'), ('supplier_id', 'Proveedor de WR'),
            ('consignee_id', 'Consignatario de WR'), ('tracking', 'Tracking de WR'), ('type', 'Tipo de WR'),
            ('transport_type', 'Transporte de WR'), ('stored_date', 'Fecha Almacenaje de WR'),
            ('assigned_date', 'Fecha Asignación de WR'), ('in_transit_date', 'Fecha en Tránsito de WR'),
            ('delivered_date', 'Fecha de entrega de WR')
        ], default="assigned_date",
        required="True", string="Filtro"
    )
    filter_type = fields.Char(compute="set_filter_type", string="Tipo de Filtro")
    filter_text = fields.Char(string="Buscar por texto")
    search_date = fields.Date(default=fields.Date.today(), string="Buscar por fecha")
    has_alerts = fields.Boolean(
        help="Este campo es útil para indicar si el conmer tiene o no alertas enlazadas",
        string="Tiene Alertas"
    )
    """Campo útil para enlazar las alertas con el conmer,
    pero está comentado porque aún no había desarrollado las alertas"""
    count_alerts = fields.Integer(
        help="",
        string="# Alertas"
    )
    wr_ids = fields.One2many(
        comodel_name="logistic.wr", inverse_name="conmer_id",
        help=".", string="WRs"
    )
    po_ids = fields.One2many(
        comodel_name="logistic.po", inverse_name="conmer_id",
        compute="set_pos", string="Ordenes de Compra"
    )

    wrs_to_alert_create = fields.Many2many(comodel_name="logistic.wr", string="WH seleccionados")

    date_search = fields.Date(string="Fecha Busqueda")




    @api.onchange('date_search')
    def _asignar_nombre2(self):
        if self.date_search:
            for record in self:
                record.name = fields.Date.from_string(
                    record.date_search).strftime('%d-%m-%Y')
            self.name =  fields.Date.from_string(
                    self.date_search).strftime('%d-%m-%Y')


    @api.onchange('filter_by')
    def set_filter_type(self):
        for record in self:
            field = record.env['ir.model.fields'] \
                .search([('model_id', '=', 'logistic.wr'), ('name', '=', record.filter_by)])
            record.filter_type = field.ttype

    def search_wrs(self):
        if self.filter_type == 'selection':
            wrs = self.env['logistic.wr'].search([(self.filter_by, 'ilike', self.search_selection)])
            print(wrs, 'Que es esto 1')
            self.wr_ids = False
            self.wr_ids = wrs.ids
        elif self.filter_type == 'date':
            wrs = self.env['logistic.wr'].search([(self.filter_by, '=', self.search_date)])
            print(wrs, 'Que es esto 2')
            self.wr_ids = False
            self.wr_ids = wrs.ids
        else:
            wrs = self.env['logistic.wr'].search([(self.filter_by, 'ilike', self.filter_text)])
            print(wrs, 'Que es esto 3')
            self.wr_ids = False
            self.wr_ids = wrs.ids

    def set_pos(self):
        for record in self:
            pos = self.env['logistic.po'].search([('wr_id', 'in', record.wr_ids.ids)])
            if pos:
                record.po_ids = pos.ids
            else:
                record.po_ids = False

    """Falta terminar accion planificada para crear conmers (CRON)"""
    def action_cron_conmer(self):
        wrs = self.env['logistic.wr'].search([('assigned_date', '=', fields.Date.today())])
        pos = self.env['logistic.po'].search([('wr_id', 'in', wrs)])
        values = {'wr_ids': wrs.ids, 'po_ids': pos.ids}
        self.create(values)

    """Falta lógica para crear las alertas en base a los WRs seleccionados.
    Si no hay WRs seleccionados para generar alerta, mostrar error descriptivo de este hecho."""
    def action_generate_alert(self):
        wrs_to_alert = self.wr_ids.filtered(lambda w: w['generate_alert'])
        for wr in wrs_to_alert:
            print('GENERAR ALERTA')
            wr.state = 'in_transit'
            wr.in_transit_date = fields.Date.today()
            wr.in_alert = True
        if not self.has_alerts:
            self.has_alerts = True

    def print_conmer(self):
        pass

    def generate_alert_action(self):
        for id_consigneer_for in self.wrs_to_alert_create:
            id_consigneed_commer = id_consigneer_for.consignee_id.id
        print(id_consigneed_commer)
        merchandises = self.wrs_to_alert_create.sudo().merchandise_ids
        print(merchandises, 'merchandises')
        bundles = self.wrs_to_alert_create.sudo().bundle_ids
        vals = {
        'consignee_id':id_consigneed_commer,
        'merchandise_ids': merchandises.ids,
        'bundle_ids': bundles.ids,
        'wh_linked': self.wrs_to_alert_create.ids
        }
        res = self.env['logistic.alert'].create(vals)

    """
    Funcion para actualizar los datos del estado en SO desde el CONMER
    """


