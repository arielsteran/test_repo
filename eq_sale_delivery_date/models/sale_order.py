# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################


from odoo import api, fields, models, _
from datetime import datetime, date, timedelta
from odoo.exceptions import Warning
from itertools import groupby


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def change_delivery_date(self):
        select_order_line = self.order_line.filtered(lambda l:l.select_so_lines)
        if not select_order_line:
            raise Warning (_('Please select some order line for change delivery date.'))
        return {
            'name': 'Change Delivery Date',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model':'wizard.sale.dispatch.date',
            'view_id':self.env.ref('eq_sale_delivery_date.wizard_sale_dispatch_date_form_view').id,
            'target':'new',
            'context':{'default_sale_line_ids':[(6, 0, select_order_line.ids)]}
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    dispatch_date = fields.Date(string="Delivery Date")
    select_so_lines = fields.Boolean(string="Select", copy=False)

    @api.onchange('product_id')
    def product_id_change(self):
        domain = super(SaleOrderLine, self).product_id_change()
        self.dispatch_date = False
        if self.product_id:
            dispatch_date = date.today() + timedelta(days=self.customer_lead)
            self.dispatch_date = dispatch_date
        return domain

    def _prepare_procurement_values(self, group_id=False):
        res = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        if self.dispatch_date:
            res.update({'date_planned':self.dispatch_date})
        return res

    def write(self, values):
        lines = self.env['sale.order.line']
        res = super(SaleOrderLine, self).write(values)
        if 'dispatch_date' in values:
            lines = self
        if lines:
            previous_product_uom_qty = {line.id: line.product_uom_qty for line in lines}
            lines.with_context(previous_product_uom_qty=previous_product_uom_qty)._action_launch_stock_rule()
        return res


class stock_move(models.Model):
    _inherit = 'stock.move'

    def _search_picking_for_assignation(self):
        self.ensure_one()
        domain = [
                ('group_id', '=', self.group_id.id),
                ('location_id', '=', self.location_id.id),
                ('location_dest_id', '=', self.location_dest_id.id),
                ('picking_type_id', '=', self.picking_type_id.id),
                ('printed', '=', False),
                ('state', 'in', ['draft', 'confirmed', 'waiting', 'partially_available', 'assigned'])]

        if self.sale_line_id and self.sale_line_id.dispatch_date:
            domain += [('scheduled_date', '=', self.date_expected)]
        picking = self.env['stock.picking'].search(domain, limit=1)
        return picking

    def check_sale_order_move(self):
        """
            Chech that stock move is created from sales order or not.
        """

        flag = False
        if any(move.sale_line_id and move.sale_line_id.dispatch_date for move in self):
            flag = True
        return flag

    def _assign_picking(self):

        """ Try to assign the moves to an existing picking that has not been
        reserved yet and has the same procurement group, locations and picking
        type (moves should already have them identical). Otherwise, create a new
        picking to assign them to. 
        
        Override the method to group by moves based on sale order line 
        delivery date(Expected Date).
        """

        Picking = self.env['stock.picking']
        grouped_moves = groupby(sorted(self, key=lambda m: [f.id for f in m._key_assign_picking()]), key=lambda m: [m._key_assign_picking()])

        # Custom Code to group by moves based on delivery date.
        if self.check_sale_order_move():
            grouped_moves = groupby(sorted(self, key=lambda m: [f.id for f in m._key_assign_picking()] and m.date_expected), key=lambda m: [m._key_assign_picking()] and m.date_expected)

        for group, moves in grouped_moves:
            moves = self.env['stock.move'].concat(*list(moves))
            new_picking = False
            # Could pass the arguments contained in group but they are the same
            # for each move that why moves[0] is acceptable
            picking = moves[0]._search_picking_for_assignation()
            if picking:
                if any(picking.partner_id.id != m.partner_id.id or
                        picking.origin != m.origin for m in moves):
                    # If a picking is found, we'll append `move` to its move list and thus its
                    # `partner_id` and `ref` field will refer to multiple records. In this
                    # case, we chose to  wipe them.
                    picking.write({
                        'partner_id': False,
                        'origin': False,
                    })
            else:
                new_picking = True
                picking = Picking.create(moves._get_new_picking_values())

            moves.write({'picking_id': picking.id})
            moves._assign_picking_post_process(new=new_picking)
        return True


class wizard_sale_dispatch_date(models.TransientModel):
    _name = 'wizard.sale.dispatch.date'
    _description = "Wizard Sale Dispatch Date"

    date = fields.Date(string="Date", default=date.today())
    sale_line_ids = fields.Many2many('sale.order.line', 'wizard_change_date_sol_rel')

    def do_change_date(self):
        for so_line in self.sale_line_ids:
            so_line.dispatch_date = self.date
            so_line.select_so_lines = False

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: