# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

#WR
class WR(models.Model):
    _name = 'logistic.wr'
    _order = "id desc"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'WR'

    def set_count_bundle(self):
        for record in self:
            record.count_bundle = len(record.bundle_ids)

    name = fields.Char(copied=False, string="# Referencia", store=True, tracking=True)
    state = fields.Selection(
        selection=[
            ('stored', 'Almacenado'), ('assigned', 'Asignado'),
            ('in_transit', 'En Tránsito'), ('delivered', 'Entregado')
        ],
        default="stored",
        string="Estado", tracking=True

    )
    wh_in = fields.Many2one('stock.picking', tracking=True)
    generate_alert = fields.Boolean(help="Campo útil para generar alerta al seleccionarlo.", string="Generar Alerta", tracking=True)
    in_alert = fields.Boolean(help="Campo útil para saber si ya fue generada alerta para este WR.", string="En Alerta", tracking=True)
    stored_date = fields.Date(string="Fecha Almacenado", tracking=True)
    assigned_date = fields.Date(string="Fecha Asigando", tracking=True)
    in_transit_date = fields.Date(string="Fecha En Tránsito", tracking=True)
    delivered_date = fields.Date(string="Fecha Entregado", tracking=True)
    supplier_id = fields.Many2one(comodel_name="res.partner", required=True, string="Proveedor", tracking=True)
    consignee_id = fields.Many2one(comodel_name="res.partner", required=True, string="Consignatario", tracking=True)
    date_prueba = fields.Datetime(string="Fecha:", tracking=True)
    prepared_date = fields.Date(string="Fecha Preparado", tracking=True)
    picking_type_id = fields.Many2one('stock.picking.type', tracking=True)
    wbin_location_id = fields.Many2one('stock.location', tracking=True)
    wbin_location_des_id = fields.Many2one('stock.location', tracking=True)
    product_oum = fields.Many2one('uom.uom', tracking=True)
    location = fields.Many2one('stock.location')
    customs_policy = fields.Char(string="Póliza aduana", tracking=True)
    guide_BL = fields.Char(string="Guía/BL", tracking=True)
    dispatch_date = fields.Date(string="Fecha de despacho", tracking=True)
    currency_exchange = fields.Float(string="Tipo cambio", tracking=True)
    carrier_id = fields.Many2one(comodel_name="res.partner", string="Transportista", tracking=True)
    note = fields.Text(string="Notas", help="Notas para el reporte de WR", tracking=True)
    tracking = fields.Char(
        help="Campo útil para ingresar el número de tracking con el que llega a ubicación Miami.",
        string="# Tracking", tracking=True
    )
    type = fields.Selection(
        selection=[
            ('spare_parts', 'Repuestos'), ('freights', 'Fletes')
        ],
        default="spare_parts",
        required=True,
        string="Tipo", tracking=True
    )
    transport_type = fields.Selection(
        selection=[
            ('maritime', 'Marítimo'), ('air', 'Aéreo'),
            ('courier', 'Courier'), ('land', 'Terrestre')
        ],
        default="maritime",
        required=True,
        string="Transporte", tracking=True
    )
    is_separated = fields.Boolean(
        help="Campo informativo, que indica si el actual WR está o no separado en otros WR.",
        string="Está Separado", tracking=True
    )
    wr_child_ids = fields.One2many(
        comodel_name="logistic.wr", inverse_name="wr_parent_id",
        help="Campo útil para indicar en el WR padre los WR hijos al separarlo.", string="WR hijos", tracking=True
    )
    wr_parent_id = fields.Many2one(
        comodel_name="logistic.wr",
        help="Campo útil para indicar en cada WR hijo, el WR padre que fue separado.", string="WR padre", tracking=True
    )
    po_ids = fields.One2many(
        comodel_name="logistic.po", inverse_name="wr_id", string="Ordenes de Compra", tracking=True
    )
    bundle_ids = fields.One2many(
        comodel_name="logistic.bundle", inverse_name="wr_id", string="Bultos", tracking=True
    )
    count_bundle = fields.Integer(
        help="Campo útil para informar el número de bultos en el WR",
        compute="set_count_bundle",
        string="# Bultos"
    )
    merchandise_ids = fields.One2many(
        comodel_name="logistic.merchandise", inverse_name="wr_id", string="Mercadería", tracking=True
    )
    #photo_ids = fields.One2many(
    #    comodel_name="ir.attachment", inverse_name="wr_id", string="Fotografías", tracking=True
    #)
    doc_ids = fields.One2many(
        comodel_name="ir.attachment", inverse_name="wr_id", string="Documentos", tracking=True
    )
    conmer_id = fields.Many2one(
        comodel_name="logistic.conmer",
        help="Campo útil para identificar a qué CONMER pertecene el WR.", string="Conmer", tracking=True
    )

    total_amount_merchandise = fields.Float(help="campo que muestra la suma de todos los montos", string="Monto Total", tracking=True)
    alert_id = fields.Many2one(comodel_name="logistic.alert", string="Alerta", tracking=True)
    alert_with_so_id = fields.Many2one(comodel_name="logistic.alert", string="Alerta con SO", tracking=True)

    fact_id = fields.Many2one(comodel_name="account.move", string="Fact", tracking=True)
    flag_domain = fields.Boolean(string="Ya ha sido seleccionado", tracking=True)
    create_so_bool = fields.Boolean(string="Crear SO/PO", tracking=True)

    bool_with_so = fields.Boolean(string="SO Creado", readonly="1", tracking=True)
    bool_with_po = fields.Boolean(string="PO Creado", readonly="1", tracking=True)


    @api.model
    def create(self, vals):
        if vals.get('type') == 'freights':
            self.state = 'assigned'
            self.assigned_date = fields.Date.today()
        else:
            self.state = 'stored'
            self.stored_date = fields.Date.today()
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'logistic.wr.sequence') or 'Nuevo'
        result = super(WR, self).create(vals)
        return result

    """Revisar si falta algo aun"""

    def prepare_wr_values(self):
        return {
            'stored_date': self.stored_date, 'supplier_id': self.supplier_id.id,
            'consignee_id': self.consignee_id.id, 'tracking': self.tracking, 'type': self.type,
            'transport_type': self.transport_type, 'bundle_ids': False, 'merchandise_ids': False,
            'wr_parent_id': self.id
        }

    def action_separate_wr(self):
        merchants_to_evaluate = self.merchandise_ids.filtered(lambda m: m['separate_wr'])
        if not merchants_to_evaluate:
            raise ValidationError('Debe seleccionar al menos una mercadería para separar un WR.')
        view = self.env.ref('logistic.wizard_separate_wr_form_view')
        ctx = {'default_wr_id': self.id}

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'logistic.separate_wr_wiz',
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'target': 'new',
            'context': ctx
        }

    @api.onchange('alert_id')
    def domain(self):
        if self.alert_id:
            self.flag_domain = True
        else:
            self.flag_domain = False


    @api.onchange('po_ids')
    def set_dates_and_state(self):
        if self.po_ids and self.type == 'spare_parts':
            self.state = 'assigned'
            self.assigned_date = fields.Date.today()

    #@api.onchange("merchandise_ids")
    #def cumpute_total_amount(self):
    #    self.total_amount_merchandise = 0.0
    #    for merchandise in self.merchandise_ids:
    #        self.total_amount_merchandise += merchandise.amount

    """En vista formulario falta agregar un boton para ENTREGAR WR, enlazado a esta funcion"""

    def action_close_wr(self):
        self.state = 'delivered'
        self.delivered_date = fields.Date.today()

    def action_generate_whin(self):
        instance_picking = self.env['stock.picking']
        picking_created = []
        obj_picking = {'scheduled_date': self.date_prueba,
                       'picking_type_id': self.picking_type_id.id,
                       'location_id': self.wbin_location_id.id,
                       'location_dest_id': self.wbin_location_des_id.id,
                       }
        for i in self.merchandise_ids:
            print(i.product_id.name)
            print(self.id)
            data = {}
            obj_picking['move_ids_without_package'] = [[0, 0, {'product_uom': self.product_oum,
                                                               'product_id': i.product_id.id,
                                                               'name': i.product_id.name,
                                                               'partner_id': self.supplier_id.id
                                                               }
                                                        ]]
        picking_created.append(instance_picking.create(obj_picking))

    def create_merchandise(self):
        """
        Eliminar los registros ya establecidos con anterioridad
        """
        factor_compute = 1.75


        for wr in self.po_ids:
            for wh in wr.picking_id:
                for so_lines in wh.move_ids_without_package:
                    for taxes in so_lines.purchase_line_id.sale_line_id.sudo().product_id.supplier_taxes_id:
                        if taxes.amount_type == "fixed":
                            factor_compute = taxes.logistic_factor

                    vals = {
                        'product_id': so_lines.product_id.id,
                        'qty': so_lines.product_uom_qty,
                        'wr_id': self.id,
                        'po_lines_ids': so_lines.purchase_line_id.id,
                        'product_dai' : so_lines.product_id.supplier_taxes_id.ids,
                        'default_code': so_lines.product_id.default_code,
                        'factor':factor_compute,
                        'price_unit': so_lines.purchase_line_id.price_unit * factor_compute,
                        'amount': so_lines.purchase_line_id.price_unit * so_lines.product_uom_qty * factor_compute,
                        'company_id_location': so_lines.purchase_line_id.sale_line_id.sudo().company_id.id,
                        'real_price': so_lines.purchase_line_id.price_unit,
                        'name': so_lines.name
                }
                    res = self.env['logistic.merchandise'].create(vals)

            wr.name = wr.picking_id.purchase_id.id
        """
        actualizar estado en sale.order_id3
        """
        #if self.merchandise_ids.po_lines_ids:
        #    for merchandise in self.merchandise_ids:
        #        merchandise.po_lines_ids.sale_line_id.sudo().logistic_state = "wr_logistic"
