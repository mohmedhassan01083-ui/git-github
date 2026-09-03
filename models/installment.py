from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EstateInstallment(models.Model):
    _name = "estate.installment"
    _description = "Estate Installment"
    _order = "due_date asc, installment_number asc"

    # =========================
    # Basic Information
    # =========================

    name = fields.Char(
        string="Installment Reference",
        compute="_compute_name",
        store=True,
    )

    installment_number = fields.Integer(
        string="Installment Number",
        required=True,
    )

    # =========================
    # Sale Application
    # =========================

    sale_application_id = fields.Many2one(
        "estate.sale.application",
        string="Sale Application",
        required=True,
        ondelete="cascade",
    )

    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="sale_application_id.customer_id",
        store=True,
        readonly=True,
    )

    property_id = fields.Many2one(
        "estate.property",
        string="Property",
        related="sale_application_id.property_id",
        store=True,
        readonly=True,
    )

    # =========================
    # Financial Information
    # =========================

    amount = fields.Float(
        string="Installment Amount",
        required=True,
    )

    paid_amount = fields.Float(
        string="Paid Amount",
        default=0.0,
    )

    remaining_amount = fields.Float(
        string="Remaining Amount",
        compute="_compute_remaining_amount",
        store=True,
    )

    # =========================
    # Dates
    # =========================

    due_date = fields.Date(
        string="Due Date",
        required=True,
    )

    payment_date = fields.Date(
        string="Payment Date",
    )

    # =========================
    # Status
    # =========================

    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("partial", "Partially Paid"),
            ("paid", "Paid"),
            ("late", "Late"),
        ],
        string="Status",
        compute="_compute_status",
        store=True,
        default="pending",
    )

    # =========================
    # Invoice
    # =========================

    invoice_id = fields.Many2one(
        "account.move",
        string="Invoice",
        readonly=True,
    )

    invoice_name = fields.Char(
        string="Invoice Number",
        related="invoice_id.name",
        readonly=True,
    )

    # =========================
    # Compute Name
    # =========================

    @api.depends(
        "installment_number",
        "property_id",
    )
    def _compute_name(self):
        for record in self:
            property_name = (
                record.property_id.name
                if record.property_id
                else "Property"
            )

            record.name = (
                f"{property_name} - "
                f"Installment #{record.installment_number}"
            )

    # =========================
    # Remaining Amount
    # =========================

    @api.depends(
        "amount",
        "paid_amount",
    )
    def _compute_remaining_amount(self):
        for record in self:
            remaining = record.amount - record.paid_amount

            record.remaining_amount = max(
                remaining,
                0.0,
            )

    # =========================
    # Status
    # =========================

    @api.depends(
        "amount",
        "paid_amount",
        "due_date",
    )
    def _compute_status(self):
        today = fields.Date.today()

        for record in self:

            if record.amount <= 0:
                record.status = "pending"
                continue

            if record.paid_amount >= record.amount:
                record.status = "paid"

            elif record.paid_amount > 0:
                record.status = "partial"

            elif record.due_date and record.due_date < today:
                record.status = "late"

            else:
                record.status = "pending"

    # =========================
    # Validation
    # =========================

    @api.constrains(
        "amount",
        "paid_amount",
    )
    def _check_amounts(self):
        for record in self:

            if record.amount <= 0:
                raise ValidationError(
                    "Installment amount must be greater than zero."
                )

            if record.paid_amount < 0:
                raise ValidationError(
                    "Paid amount cannot be negative."
                )

            if record.paid_amount > record.amount:
                raise ValidationError(
                    "Paid amount cannot be greater than "
                    "the installment amount."
                )

    @api.constrains("installment_number")
    def _check_installment_number(self):
        for record in self:

            if record.installment_number <= 0:
                raise ValidationError(
                    "Installment number must be greater than zero."
                )

    # =========================
    # Register Payment
    # =========================

    def action_register_payment(self):
        for record in self:

            if record.status == "paid":
                raise ValidationError(
                    "This installment is already fully paid."
                )

            record.write({
                "paid_amount": record.amount,
                "payment_date": fields.Date.today(),
            })