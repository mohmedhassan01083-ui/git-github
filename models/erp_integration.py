from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ConstructionProjectERP(models.Model):
    _inherit = "estate.construction.project"

    odoo_project_id = fields.Many2one(
        "project.project", string="Odoo Project", copy=False, readonly=True
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Analytic Account", copy=False, readonly=True
    )
    stock_location_id = fields.Many2one(
        "stock.location", string="Project Stock Location", copy=False, readonly=True
    )
    purchase_order_ids = fields.One2many(
        "purchase.order", "construction_project_id", string="Purchase Orders"
    )
    stock_picking_ids = fields.One2many(
        "stock.picking", "construction_project_id", string="Stock Transfers"
    )
    sale_order_ids = fields.One2many(
        "sale.order", "construction_project_id", string="Sales Orders"
    )
    invoice_ids = fields.One2many(
        "account.move", "construction_project_id", string="Invoices"
    )

    purchase_count = fields.Integer(compute="_compute_erp_counts")
    transfer_count = fields.Integer(compute="_compute_erp_counts")
    sale_count = fields.Integer(compute="_compute_erp_counts")
    invoice_count = fields.Integer(compute="_compute_erp_counts")

    @api.depends("purchase_order_ids", "stock_picking_ids", "sale_order_ids", "invoice_ids")
    def _compute_erp_counts(self):
        for rec in self:
            rec.purchase_count = len(rec.purchase_order_ids)
            rec.transfer_count = len(rec.stock_picking_ids)
            rec.sale_count = len(rec.sale_order_ids)
            rec.invoice_count = len(rec.invoice_ids)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._ensure_erp_links()
        return records

    def _ensure_erp_links(self):
        self.ensure_one()
        if not self.odoo_project_id:
            project = self.env["project.project"].create({
                "name": self.name,
                "company_id": self.company_id.id,
            })
            self.odoo_project_id = project.id

        if not self.analytic_account_id and "account.analytic.account" in self.env:
            analytic_model = self.env["account.analytic.account"]
            vals = {"name": self.name, "company_id": self.company_id.id}
            plan = self.env["account.analytic.plan"].search([], limit=1)
            if plan and "plan_id" in analytic_model._fields:
                vals["plan_id"] = plan.id
            self.analytic_account_id = analytic_model.create(vals).id

        if not self.stock_location_id:
            warehouse = self.env["stock.warehouse"].search(
                [("company_id", "=", self.company_id.id)], limit=1
            )
            if not warehouse:
                raise UserError(_("No warehouse was found for this company."))
            location = self.env["stock.location"].create({
                "name": _("Project - %s") % self.name,
                "location_id": warehouse.lot_stock_id.id,
                "usage": "internal",
                "company_id": self.company_id.id,
            })
            self.stock_location_id = location.id

    def action_open_odoo_project(self):
        self.ensure_one()
        self._ensure_erp_links()
        return {
            "type": "ir.actions.act_window",
            "name": _("Odoo Project"),
            "res_model": "project.project",
            "view_mode": "form",
            "res_id": self.odoo_project_id.id,
        }

    def action_open_stock_location(self):
        self.ensure_one()
        self._ensure_erp_links()
        return {
            "type": "ir.actions.act_window",
            "name": _("Project Stock"),
            "res_model": "stock.location",
            "view_mode": "form",
            "res_id": self.stock_location_id.id,
        }

    def action_open_purchases(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Purchase Orders"),
            "res_model": "purchase.order",
            "view_mode": "tree,form",
            "domain": [("construction_project_id", "=", self.id)],
        }

    def action_open_transfers(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Stock Transfers"),
            "res_model": "stock.picking",
            "view_mode": "tree,form",
            "domain": [("construction_project_id", "=", self.id)],
        }

    def action_open_sales(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Sales Orders"),
            "res_model": "sale.order",
            "view_mode": "tree,form",
            "domain": [("construction_project_id", "=", self.id)],
        }

    def action_open_invoices(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Invoices"),
            "res_model": "account.move",
            "view_mode": "tree,form",
            "domain": [("construction_project_id", "=", self.id)],
        }


class ConstructionMaterialERP(models.Model):
    _inherit = "estate.construction.material"

    purchase_order_id = fields.Many2one("purchase.order", string="Purchase Order", copy=False, readonly=True)
    stock_picking_id = fields.Many2one("stock.picking", string="Stock Transfer", copy=False, readonly=True)
    inventory_cost = fields.Float(
        string="Product Cost",
        related="product_id.standard_price",
        readonly=True,
    )

    @api.onchange("product_id")
    def _onchange_product_id_erp(self):
        for rec in self:
            if rec.product_id:
                rec.name = rec.product_id.display_name
                rec.unit_price = rec.product_id.standard_price
                rec.supplier_id = rec.supplier_id or rec.product_id.seller_ids[:1].partner_id

    def action_create_purchase(self):
        self.ensure_one()
        if not self.product_id:
            raise UserError(_("Select an Odoo product first."))
        if not self.supplier_id:
            raise UserError(_("Select a supplier first."))
        if self.quantity <= 0:
            raise ValidationError(_("Quantity must be greater than zero."))

        order = self.env["purchase.order"].create({
            "partner_id": self.supplier_id.id,
            "construction_project_id": self.project_id.id,
            "origin": self.project_id.name,
        })
        self.env["purchase.order.line"].create({
            "order_id": order.id,
            "product_id": self.product_id.id,
            "name": self.product_id.display_name,
            "product_qty": self.total_quantity,
            "product_uom": self.product_id.uom_po_id.id,
            "price_unit": self.unit_price,
            "date_planned": fields.Datetime.now(),
        })
        self.purchase_order_id = order.id
        return {
            "type": "ir.actions.act_window",
            "name": _("Purchase Order"),
            "res_model": "purchase.order",
            "view_mode": "form",
            "res_id": order.id,
        }

    def action_create_stock_transfer(self):
        self.ensure_one()
        if not self.product_id:
            raise UserError(_("Select an Odoo product first."))
        self.project_id._ensure_erp_links()
        if self.stock_picking_id:
            return self.stock_picking_id.get_formview_action()

        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.project_id.company_id.id)], limit=1
        )
        if not warehouse:
            raise UserError(_("No warehouse was found for this company."))

        picking = self.env["stock.picking"].create({
            "picking_type_id": warehouse.int_type_id.id,
            "location_id": warehouse.lot_stock_id.id,
            "location_dest_id": self.project_id.stock_location_id.id,
            "origin": "%s - %s" % (self.project_id.name, self.name),
            "construction_project_id": self.project_id.id,
        })
        move = self.env["stock.move"].create({
            "name": self.product_id.display_name,
            "product_id": self.product_id.id,
            "product_uom_qty": self.total_quantity,
            "product_uom": self.product_id.uom_id.id,
            "picking_id": picking.id,
            "location_id": warehouse.lot_stock_id.id,
            "location_dest_id": self.project_id.stock_location_id.id,
        })
        picking.action_confirm()
        picking.action_assign()
        self.stock_picking_id = picking.id
        return picking.get_formview_action()


class PurchaseOrderERP(models.Model):
    _inherit = "purchase.order"

    construction_project_id = fields.Many2one(
        "estate.construction.project", string="Construction Project", index=True, copy=False
    )


class StockPickingERP(models.Model):
    _inherit = "stock.picking"

    construction_project_id = fields.Many2one(
        "estate.construction.project", string="Construction Project", index=True, copy=False
    )


class SaleOrderERP(models.Model):
    _inherit = "sale.order"

    construction_project_id = fields.Many2one(
        "estate.construction.project", string="Construction Project", index=True, copy=False
    )


class AccountMoveERP(models.Model):
    _inherit = "account.move"

    construction_project_id = fields.Many2one(
        "estate.construction.project", string="Construction Project", index=True, copy=False
    )


class PropertyERP(models.Model):
    _inherit = "estate.property"

    construction_project_id = fields.Many2one(
        "estate.construction.project", string="Construction Project", index=True
    )


class SaleApplicationERP(models.Model):
    _inherit = "estate.sale.application"

    crm_lead_id = fields.Many2one("crm.lead", string="CRM Opportunity", copy=False, readonly=True)

    def action_create_crm_opportunity(self):
        self.ensure_one()
        if self.crm_lead_id:
            return self.crm_lead_id.get_formview_action()
        lead = self.env["crm.lead"].create({
            "name": _("Sale - %s") % self.property_id.display_name,
            "partner_id": self.customer_id.id,
            "type": "opportunity",
            "expected_revenue": self.property_price,
            "description": self.notes or "",
        })
        self.crm_lead_id = lead.id
        return lead.get_formview_action()
