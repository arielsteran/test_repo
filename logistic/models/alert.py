# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_is_zero



class Alert(models.Model):
    """ campos del modelo """
    _name = 'logistic.alert'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Alerta'
    _order = "name desc, id desc"

    """Clase utilizada para las alertas generadas desde un Conmer con WR seleccionados."""

    name = fields.Char(
        string="# Referencia",
        copied=False,
        store=True,
        tracking=True
    )
    state = fields.Selection(
        selection=[
            ('prepared', 'Preparado'), ('in_transit', 'En Tránsito'),
            ('customs', 'Aduana'), ('in_warehouse', 'En Bodega')
        ],
        default="prepared",
        string="Estado", tracking=True
    )
    supplier_id = fields.Many2one(
        comodel_name="res.partner",
        string="Proveedor",
        tracking=True
    )
    consignee_id = fields.Many2one(
        comodel_name="res.partner",
        string="Consignatario",
        tracking=True
    )
    carrier_id = fields.Many2one(
        comodel_name="res.partner",
        string="Transportista",
        tracking=True
    )
    reference = fields.Char(
        string="Referencia",
        tracking=True
    )
    guide_BL = fields.Char(
        string="Guía/BL",
        tracking=True
    )
    dispatch_date = fields.Date(
        string="Fecha de despacho",
        tracking=True
    )
    currency_exchange = fields.Float(
        string="Tipo cambio",
        tracking=True
    )

    """Conforme cambia el estado, agregar fecha a los campos de fechas acorde al estado"""
    prepared_date = fields.Date(
        string="Fecha Preparado",
        tracking=True
    )
    in_transit_date = fields.Date(
        string="Fecha En Tránsito",
        tracking=True
    )
    customs_date = fields.Date(
        string="Fecha Aduana",
        tracking=True
    )
    in_warehouse_date = fields.Date(
        string="Fecha Entregado",
        tracking=True
    )

    """Conforme cambia el estado, agregar fecha a los campos de fechas acorde al estado"""
    transport_type = fields.Selection(
        selection=[
            ('maritime', 'Marítimo'),
            ('air', 'Aéreo'),
            ('courier', 'Courier'), 
            ('land', 'Terrestre')
        ],
        default="maritime",
        string="Transporte", tracking=True
    )
    type = fields.Selection(
        selection=[
            ('own', 'Propio'),
            ('third', 'Tercero'),
        ],
        default="own",
        string="Tipo", tracking=True
    )
    wr_ids = fields.One2many(
        comodel_name="logistic.wr",
        inverse_name="conmer_id",
        help=".",
        string="WRs", tracking=True
    )

    bundle_ids = fields.One2many(
        comodel_name="logistic.bundle",
        inverse_name="alert_id",
        string="Bultos", tracking=True
    )
    count_bundle = fields.Integer(
        help="Campo útil para informar el número de bultos en el WR",
        string="# Bultos", tracking=True
    )
    merchandise_ids = fields.One2many(
        comodel_name="logistic.merchandise",
        inverse_name="alert_id",
        string="Mercadería",
        tracking=True
    )

    sale_order_id = fields.Many2one(
        'sale.order',
        tracking=True
    )
    supplier_po = fields.Many2one(
        comodel_name="res.partner",
        string="Proveedor para PO",
        tracking=True
    )
    expence_date = fields.Date(
        string="Fecha",
        tracking=True
    )
    picking_ids_expence = fields.Many2many(
        comodel_name="stock.picking",
        string="Transferencias",
        tracking=True
    )
    expence_journal = fields.Many2one(
        comodel_name="account.journal",
        string="Diario",
        tracking=True
    )
    expence_company = fields.Many2one(
        comodel_name="res.company",
        string="compañia",
        tracking=True
    )
    expence_vendor_bill = fields.Many2one(
        comodel_name="account.move",
        string="Factura de proveedor",
        tracking=True
    )
    model_name = fields.Char(
        string="Nombre en letras del modelo",
        tracking=True
    )

    cost_lines = fields.One2many(
        comodel_name="stock.landed.cost.lines",
        inverse_name="alert_id",
        tracking=True
    )
    valuation_adjustment_lines = fields.One2many(
        comodel_name="stock.valuation.adjustment.lines",
        inverse_name="alert_id",
        tracking=True
    )
    total_amount_merchandise = fields.Float(
        help="campo que muestra la suma de todos los montos",
        string="Monto Total",
        tracking=True
    )


    wh_linked = fields.Many2many(
        comodel_name="logistic.wr",
        string="WH relacionados",
        inverse_name="alert_id",
        tracking=True
    )
    shipping_cost = fields.One2many(
        comodel_name="shipping.cost",
        string="Gastos de Envio",
        inverse_name="alert_id",
        tracking=True)


    flag_create_so = fields.Boolean(
        string="generar SO",
        tracking=True
    )
    flag_create_po = fields.Boolean(
        string="generar PO",
        tracking=True
    )


    company_create_so_po= fields.Many2one(
        comodel_name="res.company",
        string="Empresa",
        tracking=True
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moneda",
        tracking=True,
        default=lambda self: self.env.ref('base.USD').id
    )

    sales_ids = fields.Many2many(
        string='Ventas',
        comodel_name='sale.order',
        relation='alert_relation',
    )
    purchases_ids = fields.Many2many(
        string='Compras',
        comodel_name='purchase.order',
        relation='alert_closing_relation',
    )

    exchange_rate = fields.Float(
        string="Tasa de Cambio",
        digits=(12, 5)

    )

    sales_count = fields.Integer(compute='compute_count_sales')
    purchase_count = fields.Integer(compute='compute_count_purchase')

    def compute_count_sales(self):
        for record in self:
            record.sales_count = self.env['sale.order'].search_count(
                [('alert_from_logistic', '=', self.name)])

    def compute_count_purchase(self):
        for record in self:
            record.purchase_count = self.env['purchase.order'].search_count(
                [('alert_from_logistic', '=', self.name)])

    def action_view_so(self):
        data = []
        for sales in self.sales_ids:
            data.append(sales.id)
        return {
            'type': 'ir.actions.act_window',
            'domain': [('alert_from_logistic', '=', self.name)],
            'name': 'Pagos',
            'view_mode': 'tree,form',
            'view_id': False,
            'res_model': 'sale.order',
            'context': {'alert': self.id}
        }

    def action_view_po(self):
        data = []
        for purchase in self.purchases_ids:
            data.append(purchase.id)
        return {
            'type': 'ir.actions.act_window',
            'domain': [('alert_from_logistic', '=', self.name)],
            'name': 'Pagos',
            'view_mode': 'tree,form',
            'view_id': False,
            'res_model': 'purchase.order',
            'context': {'alert': self.id}
        }


    def compute_domain(self):
        for line in self.wh_linked:
            #line.merchandise_ids.po_lines_ids.sale_line_id.sudo().logistic_state = "alert_logistic"
            line.flag_domain = True
            line.alert_id = self.id
            if line.create_so_bool == True:
                for merchandise in line.merchandise_ids:
                    merchandise.bool_true_so_created = True
                    merchandise.bool_true_po_created = True
            else:
                for merchandise in line.merchandise_ids:
                    merchandise.bool_true_so_created = False
                    merchandise.bool_true_po_created = False
        self.merchandise_ids = self.wh_linked.sudo().merchandise_ids
        self.bundle_ids = self.wh_linked.sudo().bundle_ids


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'logistic.alert.sequence') or 'Nuevo'
        result = super(Alert, self).create(vals)
        return result


    def action_create_so(self):
        self.flag_create_so = True
        for merchandise in self.merchandise_ids:
            if not merchandise.bool_create_so_form_alert  and merchandise.bool_true_so_created:

                merchandise.bool_create_so_form_alert = True
                merchandise.bool_true_so_created = False

                vals = {
                    'partner_id': merchandise.company_id_location.partner_id.id,
                    'alert_from_logistic': self.name,
                    'currency_id': self.currency_id.id
                }
                res = self.env['sale.order'].create(vals)
                line_env = self.env['sale.order.line']

                new_line = line_env.create({
                                            'product_id': merchandise.product_id.id,
                                            'name': merchandise.name,
                                            'order_id': res.id,
                                            'product_uom_qty': merchandise.qty,
                                            'customer_lead': 30.21,
                                            'price_unit': merchandise.price_unit,
                                            'default_code': merchandise.default_code
                                            })
                #merchandise.po_lines_ids.sale_line_id.sudo().logistic_state = "sale_order_emp"
                merchandise.wr_id.create_so_bool = False
                merchandise.wr_id.bool_with_so = True

                for rest_of_lines in self.merchandise_ids:
                    if rest_of_lines.bool_create_so_form_alert == False and rest_of_lines.bool_true_so_created == True:
                        if rest_of_lines.company_id_location.partner_id.id == merchandise.company_id_location.partner_id.id and rest_of_lines.transport_type == merchandise.transport_type:
                            rest_of_lines.bool_create_so_form_alert = True
                            rest_of_lines.bool_true_so_created = False
                            new_line = line_env.create({
                                                        'product_id': rest_of_lines.product_id.id,
                                                        'name': rest_of_lines.name,
                                                        'order_id': res.id,
                                                        'product_uom_qty' : rest_of_lines.qty,
                                                        'customer_lead': 30.21,
                                                        'price_unit': rest_of_lines.price_unit,
                                                        'default_code': rest_of_lines.default_code,

                                                        })
                            rest_of_lines.wr_id.create_so_bool = False
                            rest_of_lines.wr_id.bool_with_so = True

    def action_create_po(self):
        for merchandise in self.merchandise_ids:
            if merchandise.bool_create_po_form_alert == False and merchandise.bool_true_po_created == True:
                merchandise.bool_create_po_form_alert = True
                merchandise.bool_true_po_created = False
                vals = {'partner_id': self.env.user.company_id.partner_id.id,
                        'company_id': merchandise.company_id_location.id,
                        'alert_from_logistic': self.name,
                        'currency_id': self.currency_id.id,
                        'exchange_rate': self.exchange_rate
                        }
                res = self.env['purchase.order'].sudo().create(vals)
                line_env = self.env['purchase.order.line']

                taxes = merchandise.product_id.supplier_taxes_id
                if taxes:
                    taxes = taxes.filtered(lambda t: t.company_id.id == self.env.company.id)
                new_line = line_env.sudo().create({
                                    'product_id': merchandise.product_id.id,
                                    'name': merchandise.name,
                                    'order_id': res.id,
                                    'product_uom_qty': merchandise.qty,
                                    'product_qty': merchandise.qty,
                                    'price_unit': merchandise.price_unit,
                                    'product_uom': merchandise.product_id.uom_id.id,
                                    'sale_line_id': False,
                                    'date_planned': fields.Date.from_string(res.date_order) + relativedelta(days=0),
                                    'taxes_id': [(6, 0, taxes.ids)],
                                    'company_id': merchandise.company_id_location.id
                                    })
                merchandise.wr_id.create_po_bool = False
                merchandise.wr_id.bool_with_po = True

                for rest_of_lines in self.merchandise_ids:
                    if rest_of_lines.bool_create_po_form_alert == False and rest_of_lines.bool_true_po_created == True:
                        if rest_of_lines.company_id_location.partner_id.id == merchandise.company_id_location.partner_id.id and rest_of_lines.transport_type == merchandise.transport_type:
                            rest_of_lines.bool_create_po_form_alert = True
                            rest_of_lines.bool_true_po_created = False

                            taxes = rest_of_lines.product_id.supplier_taxes_id
                            if taxes:
                                taxes = taxes.filtered(lambda t: t.company_id.id == self.env.company.id)
                            new_line = line_env.sudo().create({
                                                'product_id': rest_of_lines.product_id.id,
                                                'name': rest_of_lines.name,
                                                'order_id': res.id,
                                                'product_uom_qty': rest_of_lines.qty,
                                                'product_qty': rest_of_lines.qty,
                                                'price_unit': rest_of_lines.price_unit,
                                                'product_uom':rest_of_lines.product_id.uom_id.id,
                                                'sale_line_id': False,
                                                'date_planned': fields.Date.from_string(res.date_order) + relativedelta(days=0),
                                                'taxes_id': [(6, 0, taxes.ids)],
                                                'company_id': rest_of_lines.company_id_location.id
                                                })
                            rest_of_lines.wr_id.create_po_bool = False
                            rest_of_lines.wr_id.bool_with_po = True


class StockLandedCostLine(models.Model):
    _name = "stock.landed.cost.lines"
    _inherit = "stock.landed.cost.lines"

    alert_id = fields.Many2one(comodel_name="logistic.alert", string="Alerta")
    dolar_price = fields.Float(string="Precio USD")


class StockValuationAdjustmentLine(models.Model):
    _name="stock.valuation.adjustment.lines"
    _inherit="stock.valuation.adjustment.lines"

    alert_id = fields.Many2one(comodel_name="logistic.alert", string="Alerta")
    price_dai = fields.Float(string="% dai", readonly="False")


class StockLandedCost(models.Model):
    _name = "stock.landed.cost"
    _inherit = "stock.landed.cost"

    reference = fields.Char(string="Referencia")
    exchange_rate = fields.Float(string="Tasa de Cambio", digits=(12,5))
    calculate_dai = fields.Many2one(comodel_name="product.product")
    alert_inherit = fields.Many2one(comodel_name="logistic.alert", string="Gastos desde alertas")
    total_dai_aditional_cost = fields.Float(string="Total Dai")
    total_dai_adjustments_lines = fields.Float(string="Total Dai")
    total_usd_price = fields.Float(string="Total USD")
    police_reference = fields.Char(string="No. Póliza")

    @api.onchange("cost_lines", "valuation_adjustment_lines","exchange_rate")
    def compute_total_dai_aditional_cost(self):
        self.total_dai_aditional_cost = 0
        self.total_usd_price = 0
        for lines_cost in self.cost_lines:
            if lines_cost.product_id == self.calculate_dai:
                self.total_dai_aditional_cost += lines_cost.price_unit
            self.total_usd_price += lines_cost.dolar_price
            if lines_cost.dolar_price != 0:
                lines_cost.price_unit = self.exchange_rate * lines_cost.dolar_price

    @api.onchange("valuation_adjustment_lines")
    def compute_total_dai_adjustments_lines(self):
        self.total_dai_adjustments_lines = 0
        for lines_adjustments in self.valuation_adjustment_lines:
            if lines_adjustments.cost_line_id.product_id == self.calculate_dai:
                self.total_dai_adjustments_lines += lines_adjustments.additional_landed_cost

    def create_expenses(self):
        if self.alert_inherit:
            for lines in self.alert_inherit.shipping_cost:
                line_env = self.env['stock.landed.cost.lines']

                new_line = line_env.create({
                                            'product_id': lines.product_id.id,
                                            'name': lines.name,
                                            'account_id': lines.account_id.id,
                                            'split_method' : lines.split_method,
                                            'dolar_price': lines.dolar_price,
                                            'price_unit': lines.price_unit,
                                            'cost_id': self.id
                                                        })

        #accion para generar dai en los productos.
    def action_generation_dai(self):
        temp = 0
        for i in self.valuation_adjustment_lines:
            if i.cost_line_id.product_id == self.calculate_dai:
                temp += i.additional_landed_cost


        for j in self.cost_lines:
            if j.product_id == self.calculate_dai:
                j.price_unit = temp
        self.compute_total_dai_aditional_cost()
        self.compute_total_dai_adjustments_lines()

    def action_compute_dai(self):
        adjustementLines = self.env['stock.valuation.adjustment.lines']
        count = 0
        list_former_cost = []
        # creando linea de costos adicionales
        cost_lines = self.env['stock.landed.cost.lines']
        cost_vals = {

            'product_id': self.calculate_dai.id,
            'cost_id': self.id,
            'price_unit': 0,
            'split_method': 'equal',
            'name': self.calculate_dai.name,
        }
        cost_res = cost_lines.create(cost_vals)


        for wh_in in self.picking_ids:
            for product in wh_in.move_ids_without_package:
                print("----Nombre producto--")
                print(product.name)
                print("------")
                vals = {
                    'product_id': product.product_id.id,
                    'quantity': product .quantity_done,
                    'cost_id': self.id,
                    'cost_line_id': cost_res.id,
                    'move_id': self.valuation_adjustment_lines[0].move_id.id
                    # 'former_cost': float(list_former_cost[product])
                }

                validation_settings_line = adjustementLines.create(vals)

                price_unit_temp = 0
                price_total = 0
                for lines in self.valuation_adjustment_lines:

                    if lines.product_id.id == validation_settings_line.product_id.id:
                        if lines.former_cost != 0:
                            price_total = lines.former_cost
                        price_unit_temp += lines.additional_landed_cost
                        #validation_settings_line.former_cost = price_total + price_unit_temp
                validation_settings_line.former_cost = price_unit_temp + price_total

                for taxes in product.product_id.supplier_taxes_id:
                    if taxes.group_type == "dai":
                        validation_settings_line.additional_landed_cost = taxes.logistic_value_dai/100 * validation_settings_line.former_cost
                        validation_settings_line.price_dai = taxes.logistic_value_dai
                        count = count + validation_settings_line.additional_landed_cost

        cost_res.price_unit = count
        return True

    #funcion para agregar lineas day
    def compute_landed_cost(self):
        # self.action_compute_dai()
        AdjustementLines = self.env['stock.valuation.adjustment.lines']
        AdjustementLines.search([('cost_id', 'in', self.ids)]).unlink()

        digits = self.env['decimal.precision'].precision_get('Product Price')
        towrite_dict = {}
        for cost in self.filtered(lambda cost: cost._get_targeted_move_ids()):
            total_qty = 0.0
            total_cost = 0.0
            total_weight = 0.0
            total_volume = 0.0
            total_line = 0.0
            all_val_line_values = cost.get_valuation_lines()

            for val_line_values in all_val_line_values:
                for cost_line in cost.cost_lines:
                    val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id})
                    self.env['stock.valuation.adjustment.lines'].create(val_line_values)
                total_qty += val_line_values.get('quantity', 0.0)
                total_weight += val_line_values.get('weight', 0.0)
                total_volume += val_line_values.get('volume', 0.0)

                former_cost = val_line_values.get('former_cost', 0.0)
                # round this because former_cost on the valuation lines is also rounded
                total_cost += tools.float_round(former_cost, precision_digits=digits) if digits else former_cost

                total_line += 1

            for line in cost.cost_lines:
                value_split = 0.0
                for valuation in cost.valuation_adjustment_lines:
                    value = 0.0
                    if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
                        if line.split_method == 'by_quantity' and total_qty:
                            per_unit = (line.price_unit / total_qty)
                            value = valuation.quantity * per_unit
                        elif line.split_method == 'by_weight' and total_weight:
                            per_unit = (line.price_unit / total_weight)
                            value = valuation.weight * per_unit
                        elif line.split_method == 'by_volume' and total_volume:
                            per_unit = (line.price_unit / total_volume)
                            value = valuation.volume * per_unit
                        elif line.split_method == 'equal':
                            value = (line.price_unit / total_line)
                        elif line.split_method == 'by_current_cost_price' and total_cost:
                            per_unit = (line.price_unit / total_cost)
                            value = valuation.former_cost * per_unit
                        else:
                            value = (line.price_unit / total_line)

                        if digits:
                            value = tools.float_round(value, precision_digits=digits, rounding_method='UP')
                            fnc = min if line.price_unit > 0 else max
                            value = fnc(value, line.price_unit - value_split)
                            value_split += value

                        if valuation.id not in towrite_dict:
                            towrite_dict[valuation.id] = value
                        else:
                            towrite_dict[valuation.id] += value
        for key, value in towrite_dict.items():
            AdjustementLines.browse(key).write({'additional_landed_cost': value})
        if self.calculate_dai:
            self.action_compute_dai()
        self.compute_total_dai_aditional_cost()
        self.compute_total_dai_adjustments_lines()
        return True

    def _get_targeted_move_ids(self):
        return self.picking_ids.move_lines


"""
Clase para los costos de envio
"""
class ShippingCost(models.Model):
    _name = "shipping.cost"
    _description = "gastos de envio en logostica"

    account_id = fields.Many2one(comodel_name="account.account", string="Cuenta")
    dolar_price = fields.Float(string="Precio USD")
    name = fields.Char(string="Description")
    price_unit = fields.Float(string="Coste")
    product_id = fields.Many2one(comodel_name="product.product", string="Producto")
    alert_id = fields.Many2one(comodel_name="logistic.alert", string="Alerta", tracking=True)
    split_method = fields.Selection(
        selection=[
            ('equal', 'Igual'), ('by_quantity', 'Por cantidad'),
            ('by_current_cost_price', 'Por coste actual'), ('by_weight', 'Por peso'),
            ('by_volume', 'Por volumen')
        ],
        default="prepared",
        string="Método de división")
