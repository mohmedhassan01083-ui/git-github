from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EstateConstructionExpense(models.Model):
    _name = "estate.construction.expense"
    _description = "Construction Other Expense"
    _order = "date desc, id desc"

    # =========================
    # Basic Information
    # =========================

    name = fields.Char(
        string="Expense Name",
        required=True
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
    # Expense Category
    # =========================

    category = fields.Selection(
        [
            ("permits", "Permits & Licenses"),
            ("engineering", "Engineering & Consulting"),
            ("security", "Security"),
            ("utilities", "Utilities"),
            ("transport", "Transportation"),
            ("storage", "Storage"),
            ("insurance", "Insurance"),
            ("taxes", "Taxes & Government Fees"),
            ("legal", "Legal Expenses"),
            ("marketing", "Marketing"),
            ("administration", "Administration"),
            ("cleaning", "Cleaning"),
            ("waste", "Waste Removal"),
            ("testing", "Testing & Inspection"),
            ("communication", "Communication"),
            ("other", "Other"),
        ],
        string="Expense Category",
        required=True,
        default="other"
    )

    description = fields.Text(
        string="Description"
    )

    # =========================
    # Financial Information
    # =========================

    amount = fields.Float(
        string="Expense Amount",
        required=True,
        default=0.0
    )

    paid_amount = fields.Float(
        string="Paid Amount",
        default=0.0
    )

    remaining_amount = fields.Float(
        string="Remaining Amount",
        compute="_compute_remaining",
        store=True
    )

    payment_status = fields.Selection(
        [
            ("unpaid", "Unpaid"),
            ("partial", "Partially Paid"),
            ("paid", "Paid"),
        ],
        string="Payment Status",
        compute="_compute_payment_status",
        store=True
    )

    # =========================
    # Supplier / Vendor
    # =========================

    partner_id = fields.Many2one(
        "res.partner",
        string="Vendor / Service Provider"
    )

    invoice_number = fields.Char(
        string="Invoice / Reference Number"
    )

    # =========================
    # Dates
    # =========================

    date = fields.Date(
        string="Expense Date",
        default=fields.Date.today,
        required=True
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
        "amount",
        "paid_amount"
    )
    def _compute_remaining(self):

        for record in self:

            record.remaining_amount = max(
                record.amount - record.paid_amount,
                0.0
            )

    @api.depends(
        "amount",
        "paid_amount"
    )
    def _compute_payment_status(self):

        for record in self:

            if record.paid_amount <= 0:

                record.payment_status = "unpaid"

            elif record.paid_amount >= record.amount:

                record.payment_status = "paid"

            else:

                record.payment_status = "partial"

    # =========================
    # Validation
    # =========================

    @api.constrains(
        "amount",
        "paid_amount"
    )
    def _check_values(self):

        for record in self:

            if record.amount < 0:

                raise ValidationError(
                    "Expense amount cannot be negative."
                )

            if record.paid_amount < 0:

                raise ValidationError(
                    "Paid amount cannot be negative."
                )

            if record.paid_amount > record.amount:

                raise ValidationError(
                    "Paid amount cannot be greater than "
                    "the expense amount."
                )