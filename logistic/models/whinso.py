
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round
from dateutil.relativedelta import relativedelta


class WHINSO(models.Model):
    _inherit = 'stock.picking'

    relation_logic_wh = fields.Many2one(comodel_name='logistic.wr', string='Relacion de WH')
    partner_po = fields.Many2one(comodel_name='res.partner', string="campo de aliado")
    company_id = fields.Many2one(comodel_name="res.company", string="Compañia para PO")
    currency = fields.Many2one(comodel_name="res.currency", string="Moneda para PO")
    picking_type_id = fields.Many2one(comodel_name="stock.picking.type", string="Tipo")

    def generate_poem(self):
        instance_po = self.env['purchase.order']
        po_created = []
        print(self.partner_id)

        print("po se creo")

"""
Clase para ordenes de compra
-botton_confirm                 actualizacion de confirmacion para el estado del producto por linea
"""
class PurchaseOrderConfirm(models.Model):
    _name = "purchase.order"
    _inherit = "purchase.order"

    alert_from_logistic = fields.Char(string="Logistica Alerta", readonly=True)
    exchange_rate = fields.Float(
        string="Tasa de Cambio",
        digits=(12, 5)
    )

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        # Ensures all properties and fiscal positions
        # are taken with the company of the order
        # if not defined, force_company doesn't change anything.
        if not self.alert_from_logistic:
            self = self.with_context(force_company=self.company_id.id)
            if not self.partner_id:
                self.fiscal_position_id = False
                self.currency_id = self.env.company.currency_id.id
            else:
                self.fiscal_position_id = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id)
                self.payment_term_id = self.partner_id.property_supplier_payment_term_id.id
                self.currency_id = self.partner_id.property_purchase_currency_id.id or self.env.company.currency_id.id
        return {}


    @api.onchange("order_line")
    def generate_alert_in_SO(self):
        if self.origin:
            for lines in self.order_line:
                lines.sale_order_id.sudo().change_products_po_alert = True





    def _create_picking(self):
        print("Entra a logistica")
        StockPicking = self.env['stock.picking']
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))



                if not pickings:
                    res = order._prepare_picking()
                    picking = StockPicking.create(res)
                else:
                    picking = pickings[0]
                moves = order.order_line._create_stock_moves(picking)

                if order.exchange_rate:
                    for moves_lines in moves:
                        moves_lines.price_unit = moves_lines.purchase_line_id.price_unit * order.exchange_rate
                        print("----moves1----")
                        print(moves_lines.name)
                        print(moves_lines.price_unit)
                        print("-------")


                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()





                seq = 0
                for move in sorted(moves, key=lambda move: move.date_expected):
                    seq += 5
                    move.sequence = seq


                moves._action_assign()


                picking.message_post_with_view('mail.message_origin_link',
                    values={'self': picking, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
        return True



    #funcion de confirmacion.
    #def button_confirm(self):
    #    for line in self.order_line:
    #        if line.sale_line_id:
    #            line.sale_line_id.sudo().logistic_state = "wh_in"

    #    result = super(PurchaseOrderConfirm, self).button_confirm()
    #    return result


class PurchaseOrderInherit(models.Model):
    _name = "purchase.order.line"
    _inherit = "purchase.order.line"

    default_code = fields.Char(string="No. Parte")
    merchandise_ids = fields.Many2one(comodel_name="logistic.merchandise", string="Mercaderia en Logistica")

    @api.onchange('product_id')
    def compute_default_code(self):
        self.default_code = self.product_id.default_code
        self.x_product_part_no = self.default_code

    #funcion para buscar el producto por el default code
    @api.onchange('default_code')
    def compute_search_product_by_default_code(self):
        search_product = self.env['product.product'].search([('default_code', '=', self.default_code)])
        if search_product != "" and search_product and self.default_code and self.default_code != "":
            self.product_id = search_product.id

    def _get_stock_move_price_unit(self):

        self.ensure_one()
        line = self[0]
        order = line.order_id
        price_unit = line.price_unit
        price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
        if line.taxes_id:
            qty = line.product_qty or 1
            price_unit = line.taxes_id.with_context(round=False).compute_all(
                price_unit, currency=line.order_id.currency_id, quantity=qty, product=line.product_id,
                partner=line.order_id.partner_id
            )['total_void']
            price_unit = float_round(price_unit / qty, precision_digits=price_unit_prec)
        if line.product_uom.id != line.product_id.uom_id.id:
            price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
        if order.currency_id != order.company_id.currency_id:
            if order.exchange_rate:
                price_unit *= order.exchange_rate
            else:
                price_unit = order.currency_id._convert(
                    price_unit, order.company_id.currency_id, self.company_id, self.date_order or fields.Date.today(),
                    round=False)
        return price_unit


class SaleOrderIinherit(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    alert_from_logistic = fields.Char(string="Logistica Alerta", readonly=True)
    company_po = fields.Many2one("res.company")
    create_po_bool = fields.Boolean(string="crear PO")
    change_products_po_alert = fields.Boolean(string="Alerta de PO")
    company_generate_po = fields.Many2one(comodel_name="res.company", string="Donde generar.")
    #def action_confirm(self):
    #    if self.create_po_bool:
    #        for line in self.order_line:
    #            line.logistic_state = "purchase_order"
    #    result = super(SaleOrderIinherit, self).action_confirm()
    #    return result



class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    default_code = fields.Char(strint="No. Parte")

    #logistic_state  = fields.Selection([ ('sale_order', 'Orden de Venta Inicial'),
    #                                    ('purchase_order', 'Orden de Compra'),
    #                                    ('wh_in', 'WH/IN'),
    #                                    ('wr_logistic', 'WR Logistica'),
    #                                    ('conmer_logistic', 'Conmer Logistica'),
    #                                    ('alert_logistic', 'Alerta Logistica'),
    #                                    ('sale_order_emp', 'Venta Final'),],
    #                                    'Estado Logistica', default='sale_order')


    #@api.onchange("product_template_id")
    #def compute_logistic_state(self):
    #    self.logistic_state = "sale_order"


    """
    cambiar el estado de linea de SO cuando tenga una linea en orden de compra
    """
    #@api.onchange("purchase_line_ids")
    #def compute_logistic_state_po(self):
    #    self.logistic_state = "purchase_order"

    @api.onchange('product_id')
    def compute_default_code(self):
        self.default_code = self.product_id.default_code

    #funcion para buscar el producto por el default code
    @api.onchange('default_code')
    def compute_search_product_by_default_code(self):
        search_product = self.env['product.product'].search([('default_code', '=', self.default_code)], limit=1)
        if search_product != "" and search_product and self.default_code and self.default_code != "":
            self.product_id = search_product.id



    def _purchase_service_prepare_order_values(self, supplierinfo):
        """ Returns the values to create the purchase order from the current SO line.
            :param supplierinfo: record of product.supplierinfo
            :rtype: dict
        """



        config_duplicate_nit = self.env['res.config.settings'] \
            .search([('company_id', '=', self.env.company.id)], order='write_date desc', limit=1)

        """if config_duplicate_nit:
            create_po = config_duplicate_nit.company_generate_po
        else:
            create_po = False
            """
        create_po = self.order_id.company_generate_po

        if create_po and self.order_id.create_po_bool and self.supplier_id:
            self.ensure_one()
            partner_supplier = supplierinfo.name
            fiscal_position_id = self.env['account.fiscal.position'].sudo().get_fiscal_position(partner_supplier.id)
            date_order = self._purchase_get_date_order(supplierinfo)
            return {
                'partner_id': self.supplier_id.id,
                'partner_ref': self.supplier_id.ref,
                'company_id': create_po.id,
                'currency_id': partner_supplier.property_purchase_currency_id.id or self.env.company.currency_id.id,
                'dest_address_id': False,  # False since only supported in stock
                'origin': self.order_id.name,
                'payment_term_id': partner_supplier.property_supplier_payment_term_id.id,
                'date_order': date_order,
                'fiscal_position_id': fiscal_position_id,
            }

        elif create_po and self.order_id.create_po_bool and not self.supplier_id:
            self.ensure_one()
            partner_supplier = supplierinfo.name
            fiscal_position_id = self.env['account.fiscal.position'].sudo().get_fiscal_position(partner_supplier.id)
            date_order = self._purchase_get_date_order(supplierinfo)
            return {
                'partner_id': partner_supplier.id,
                'partner_ref': partner_supplier.ref,
                'company_id': create_po.id,
                'currency_id': partner_supplier.property_purchase_currency_id.id or self.env.company.currency_id.id,
                'dest_address_id': False,  # False since only supported in stock
                'origin': self.order_id.name,
                'payment_term_id': partner_supplier.property_supplier_payment_term_id.id,
                'date_order': date_order,
                'fiscal_position_id': fiscal_position_id,
            }

    # codigo exclusivo para crear Orden de Compra al confirmar Pedido de Venta
    def _purchase_service_prepare_line_values(self, purchase_order, quantity=False):
            self.ensure_one()

            product_quantity = self.product_uom_qty
            if quantity:
                product_quantity = quantity

            purchase_qty_uom = self.product_uom._compute_quantity(product_quantity, self.product_id.uom_po_id)

            if self.to_quote:
                if self.supplier_id:
                    supplierinfo = self.supplier_cost_ids.filtered(
                        lambda vendor: vendor.name == self.supplier_id and vendor.quote_supplier)
                else:
                    raise UserError(
                        _("No se ha checho el costeo para el producto - %s. Por favor espere a que sea costeado "
                          "o proceda a desactivar el costeo.") % (
                            self.product_id.display_name,))
            else:
                supplierinfo = self.product_id._select_seller(
                    partner_id=purchase_order.partner_id,
                    quantity=purchase_qty_uom,
                    date=purchase_order.date_order and purchase_order.date_order.date(),
                    uom_id=self.product_id.uom_po_id
                )
            fpos = purchase_order.fiscal_position_id
            taxes = fpos.map_tax(self.product_id.supplier_taxes_id) if fpos else self.product_id.supplier_taxes_id
            if taxes:
                taxes = taxes.filtered(lambda t: t.company_id.id == self.company_id.id)

            price_unit = 0.0
            if supplierinfo:
                if self.to_quote:
                    price_unit = self.env['account.tax'].sudo()._fix_tax_included_price_company(supplierinfo.cost,
                                                                                                self.product_id.supplier_taxes_id,
                                                                                                taxes, self.company_id)
                else:
                    price_unit = self.env['account.tax'].sudo()._fix_tax_included_price_company(supplierinfo.price,
                                                                                                self.product_id.supplier_taxes_id,
                                                                                                taxes, self.company_id)
                if purchase_order.currency_id and supplierinfo.currency_id != purchase_order.currency_id:
                    price_unit = supplierinfo.currency_id.compute(price_unit, purchase_order.currency_id)

            product_in_supplier_lang = self.product_id.with_context(
                lang=supplierinfo.name.lang,
                partner_id=supplierinfo.name.id,
            )
            name = '[%s] %s' % (self.product_id.x_code, product_in_supplier_lang.display_name)
            if product_in_supplier_lang.description_purchase:
                name += '\n' + product_in_supplier_lang.description_purchase

            return {
                'name': '[%s] %s' % (
                    self.product_id.x_code, self.name) if self.product_id.x_code else self.name,
                'product_qty': purchase_qty_uom,
                'product_id': self.product_id.id,
                'product_uom': self.product_id.uom_po_id.id,
                'price_unit': self.price_unit,
                'date_planned': fields.Date.from_string(purchase_order.date_order) + relativedelta(days=int(supplierinfo.delay)),
                'taxes_id': [(6, 0, taxes.ids)],
                'order_id': purchase_order.id,
                'sale_line_id': self.id,
                'default_code': self.default_code,
            }

        # codigo exclusivo para crear Orden de Compra al confirmar Pedido de Venta

    # codigo exclusivo para crear Orden de Compra al confirmar Pedido de Venta
    def _purchase_service_create(self, quantity=False):
        """config_duplicate_nit = self.env['res.config.settings'] \
            .search([('company_id', '=', self.env.company.id)], order='write_date desc', limit=1)

        if config_duplicate_nit:
            create_po = config_duplicate_nit.company_generate_po
        else:
            create_po = False
"""
        create_po = self.order_id.company_generate_po
        if create_po and self.order_id.create_po_bool:
            PurchaseOrder = self.env['purchase.order']
            supplier_po_map = {}
            sale_line_purchase_map = {}
            for line in self:
                line = line.with_context(force_company=line.company_id.id)
                if line.to_quote:
                    if line.supplier_id:
                        suppliers = line.supplier_cost_ids.filtered(
                            lambda vendor: vendor.name == line.supplier_id and vendor.quote_supplier)
                    else:
                        raise UserError(
                            _("No se ha checho el costeo para el producto - %s. Por favor espere a que sea costeado "
                            "o proceda a desactivar el costeo.") % (
                                line.product_id.display_name,))
                else:
                    suppliers = line.product_id.seller_ids.filtered(
                        lambda vendor: (not vendor.company_id or vendor.company_id == line.company_id) and (
                                not vendor.product_id or vendor.product_id == line.product_id))

                if not suppliers:
                    raise UserError(
                        _("No hay proveedor(es) asociados al producto - %s. "
                        "Por favor defina un proveedor para el producto.") % (
                            line.product_id.display_name,))

                supplierinfo = suppliers[0]
                partner_supplier = supplierinfo.name

                purchase_order = supplier_po_map.get(partner_supplier.id)
                if not purchase_order:
                    purchase_order = PurchaseOrder.search([
                        ('partner_id', '=', partner_supplier.id),
                        ('state', '=', 'draft'),
                        ('company_id', '=', create_po.id),
                    ], limit=1)
                if not purchase_order:
                    values = line._purchase_service_prepare_order_values(supplierinfo)
                    purchase_order = PurchaseOrder.create(values)
                else:
                    so_name = line.order_id.name
                    origins = []
                    if purchase_order.origin:
                        origins = purchase_order.origin.split(', ') + origins
                    if so_name not in origins:
                        origins += [so_name]
                        purchase_order.write({
                            'origin': ', '.join(origins)
                        })
                supplier_po_map[partner_supplier.id] = purchase_order
                values = line._purchase_service_prepare_line_values(purchase_order, quantity=quantity)
                purchase_line = line.env['purchase.order.line'].create(values)

                sale_line_purchase_map.setdefault(line, line.env['purchase.order.line'])
                sale_line_purchase_map[line] |= purchase_line
            return sale_line_purchase_map

            # codigo exclusivo para crear Orden de Compra al confirmar Pedido de Venta

            # codigo exclusivo para crear Orden de Compra al confirmar Pedido de Venta

    def _purchase_service_generation(self):

        """config_create_po = self.env['res.config.settings'] \
            .search([('company_id', '=', self.env.company.id)], order='write_date desc', limit=1)

        if config_create_po:
            create_po = config_create_po.company_generate_po
        else:
            create_po = False"""

        create_po = self.order_id.company_generate_po

        if self.order_id.create_po_bool:
            sale_line_purchase_map = {}
            for line in self:
                #if line.product_id.service_to_purchase and not line.purchase_line_count:
                if not line.purchase_line_count:
                    result = line._purchase_service_create()
                    sale_line_purchase_map.update(result)

            return sale_line_purchase_map

        # codigo exclusivo para crear Orden de Compra al confirmar Pedido de Venta


class ResConfigAccount(models.TransientModel):
    _inherit = "res.config.settings"



    company_generate_po = fields.Many2one("res.company", string="Empresa para PO", default=lambda self: self._get_default_res_config_create_po())
    bool_generate_po = fields.Boolean(help="Campo para generar automaticamente los PO desde un SO", string="¿Desea generar un PO?",default=lambda self: self._get_default_res_config_bool_generate_po())

    def _get_default_res_config_create_po(self):
        config_create_po = self.env['res.config.settings'] \
            .search([('company_id', '=', self.env.company.id)], order='write_date desc', limit=1)
        if config_create_po:
            return config_create_po.company_generate_po
        else:
            return False

    def _get_default_res_config_bool_generate_po(self):
        config_bool_generate_po = self.env['res.config.settings'] \
            .search([('company_id', '=', self.env.company.id)], order='write_date desc', limit=1)
        if config_bool_generate_po:
            return config_bool_generate_po.bool_generate_po
        else:
            return False
class ConfigNoParte(models.Model):
    _inherit = "stock.move.line"


    default_code = fields.Char(related="product_id.default_code", string="No. Parte", help="El numero de parte del producto")

    @api.depends("product_id")
    def compute_default_code(self):
        self.default_code = self.product_id.default_code
# class AccountMoveReference(models.Model):
#         _inherit = "account.move"
#
#
#         reference = fields.One2many("logistic.wr", string="WRs", inverse_name="fact_id")

class LinesAccountMove(models.Model):
    _inherit = "account.move.line"
    default_code = fields.Char(related="product_id.default_code", string="No. Parte", help="El numero de parte del producto")
    box = fields.Char(string="Caja", related="sale_line_ids.order_id.alert_from_logistic")

class AccountIncoterms(models.Model):
    _inherit="account.incoterms"

    _rec_name = "code"




class InheritStockMove(models.Model):
    _inherit = "stock.move"

    default_code = fields.Char(related="product_id.default_code", string="No. Parte" , help="El numero de parte del producto", readonly="1")

    def _get_price_unit(self):
        """ Returns the unit price for the move"""
        self.ensure_one()
        print("1")
        if self.purchase_line_id and self.product_id.id == self.purchase_line_id.product_id.id:
            price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
            line = self.purchase_line_id
            order = line.order_id
            price_unit = line.price_unit
            if line.taxes_id:
                qty = line.product_qty or 1
                price_unit = line.taxes_id.with_context(round=False).compute_all(price_unit, currency=line.order_id.currency_id, quantity=qty)['total_void']
                price_unit = float_round(price_unit / qty, precision_digits=price_unit_prec)
            if line.product_uom.id != line.product_id.uom_id.id:
                price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
            if order.currency_id != order.company_id.currency_id:
                # The date must be today, and not the date of the move since the move move is still
                # in assigned state. However, the move date is the scheduled date until move is
                # done, then date of actual move processing. See:
                # https://github.com/odoo/odoo/blob/2f789b6863407e63f90b3a2d4cc3be09815f7002/addons/stock/models/stock_move.py#L36
                if order.exchange_rate:
                    price_unit *= order.exchange_rate
                else:
                    price_unit = order.currency_id._convert(
                        price_unit, order.company_id.currency_id, order.company_id, fields.Date.context_today(self), round=False)
            return price_unit
        return super(InheritStockMove, self)._get_price_unit()