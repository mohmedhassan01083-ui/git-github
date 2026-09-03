from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EstateConstructionMaterial(models.Model):
    _name = "estate.construction.material"
    _description = "Construction Material Cost"
    _order = "date desc, id desc"

    # =========================
    # Basic Information
    # =========================

    name = fields.Char(
        string="Material Name",
        required=True
    )

    material_code = fields.Char(
        string="Material Code"
    )

    project_id = fields.Many2one(
        "estate.construction.project",
        string="Construction Project",
        required=True,
        ondelete="cascade"
    )

    property_id = fields.Many2one(
        "estate.property",
        string="Property / Unit"
    )

    building_name = fields.Char(
        string="Building"
    )

    # =========================
    # Material Category
    # =========================

    category = fields.Selection(
        [
            ("concrete", "Concrete"),
            ("steel", "Steel"),
            ("cement", "Cement"),
            ("sand", "Sand"),
            ("gravel", "Gravel"),
            ("bricks", "Bricks"),
            ("blocks", "Blocks"),
            ("plumbing", "Plumbing"),
            ("electrical", "Electrical"),
            ("painting", "Painting"),
            ("flooring", "Flooring"),
            ("marble", "Marble"),
            ("aluminum", "Aluminum"),
            ("wood", "Wood"),
            ("glass", "Glass"),
            ("insulation", "Insulation"),
            ("doors", "Doors"),
            ("windows", "Windows"),
            ("finishing", "Finishing"),
            ("landscape", "Landscape"),
            ("other", "Other"),
        ],
        string="Category",
        required=True,
        default="other"
    )

    description = fields.Text(
        string="Description"
    )

    # =========================
    # Quantity & Unit
    # =========================

    quantity = fields.Float(
        string="Quantity",
        required=True,
        default=1.0
    )

    unit = fields.Selection(
        [
            ("unit", "Unit"),
            ("kg", "Kilogram"),
            ("ton", "Ton"),
            ("m", "Meter"),
            ("m2", "Square Meter"),
            ("m3", "Cubic Meter"),
            ("liter", "Liter"),
            ("bag", "Bag"),
            ("box", "Box"),
            ("piece", "Piece"),
            ("hour", "Hour"),
            ("other", "Other"),
        ],
        string="Unit",
        required=True,
        default="unit"
    )

    # =========================
    # Pricing
    # =========================

    unit_price = fields.Float(
        string="Unit Price",
        required=True,
        default=0.0
    )

    subtotal = fields.Float(
        string="Subtotal",
        compute="_compute_cost",
        store=True
    )

    waste_percentage = fields.Float(
        string="Waste %",
        default=0.0
    )

    waste_quantity = fields.Float(
        string="Waste Quantity",
        compute="_compute_cost",
        store=True
    )

    total_quantity = fields.Float(
        string="Total Quantity",
        compute="_compute_cost",
        store=True
    )

    total_cost = fields.Float(
        string="Total Cost",
        compute="_compute_cost",
        store=True
    )

    # =========================
    # Supplier
    # =========================

    supplier_id = fields.Many2one(
        "res.partner",
        string="Supplier"
    )

    supplier_invoice_number = fields.Char(
        string="Supplier Invoice Number"
    )

    purchase_date = fields.Date(
        string="Purchase Date"
    )

    date = fields.Date(
        string="Date",
        default=fields.Date.today,
        required=True
    )

    # =========================
    # Inventory
    # =========================

    product_id = fields.Many2one(
        "product.product",
        string="Inventory Product"
    )

    stock_location_id = fields.Many2one(
        "stock.location",
        string="Stock Location"
    )

    # =========================
    # Payment
    # =========================

    paid_amount = fields.Float(
        string="Paid Amount",
        default=0.0
    )

    remaining_amount = fields.Float(
        string="Remaining Amount",
        compute="_compute_remaining",
        store=True
    )

    # =========================
    # Notes
    # =========================

    notes = fields.Text(
        string="Notes"
    )

    # =========================
    # Computations
    # =========================

    @api.depends(
        "quantity",
        "unit_price",
        "waste_percentage"
    )
    def _compute_cost(self):
        for record in self:

            record.subtotal = (
                record.quantity
                * record.unit_price
            )

            record.waste_quantity = (
                record.quantity
                * record.waste_percentage
                / 100
            )

            record.total_quantity = (
                record.quantity
                + record.waste_quantity
            )

            record.total_cost = (
                record.total_quantity
                * record.unit_price
            )

    @api.depends(
        "total_cost",
        "paid_amount"
    )
    def _compute_remaining(self):
        for record in self:
            record.remaining_amount = max(
                record.total_cost
                - record.paid_amount,
                0.0
            )

    # =========================
    # Validation
    # =========================

    @api.constrains(
        "quantity",
        "unit_price",
        "waste_percentage",
        "paid_amount"
    )
    def _check_values(self):
        for record in self:

            if record.quantity <= 0:
                raise ValidationError(
                    "Material quantity must be greater than zero."
                )

            if record.unit_price < 0:
                raise ValidationError(
                    "Material unit price cannot be negative."
                )

            if record.waste_percentage < 0:
                raise ValidationError(
                    "Waste percentage cannot be negative."
                )

            if record.paid_amount < 0:
                raise ValidationError(
                    "Paid amount cannot be negative."
                )

            if record.paid_amount > record.total_cost:
                raise ValidationError(
                    "Paid amount cannot be greater than total cost."
                )