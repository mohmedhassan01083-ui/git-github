from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EstateConstructionEquipment(models.Model):
    _name = "estate.construction.equipment"
    _description = "Construction Equipment Cost"
    _order = "date desc, id desc"

    # =========================
    # Basic Information
    # =========================

    name = fields.Char(
        string="Equipment Name",
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
    # Equipment Information
    # =========================

    equipment_type = fields.Selection(
        [
            ("excavator", "Excavator"),
            ("loader", "Loader"),
            ("crane", "Crane"),
            ("mixer", "Concrete Mixer"),
            ("truck", "Truck"),
            ("generator", "Generator"),
            ("compressor", "Compressor"),
            ("bulldozer", "Bulldozer"),
            ("forklift", "Forklift"),
            ("pump", "Pump"),
            ("other", "Other"),
        ],
        string="Equipment Type",
        required=True,
        default="other"
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Owner / Supplier"
    )

    description = fields.Text(
        string="Description"
    )

    # =========================
    # Usage & Payment
    # =========================

    payment_type = fields.Selection(
        [
            ("daily", "Daily"),
            ("hourly", "Hourly"),
            ("fixed", "Fixed Contract"),
        ],
        string="Payment Type",
        required=True,
        default="daily"
    )

    quantity = fields.Float(
        string="Quantity",
        default=1.0
    )

    usage_days = fields.Float(
        string="Usage Days",
        default=0.0
    )

    hours_per_day = fields.Float(
        string="Hours / Day",
        default=8.0
    )

    hourly_rate = fields.Float(
        string="Hourly Rate",
        default=0.0
    )

    daily_rate = fields.Float(
        string="Daily Rate",
        default=0.0
    )

    fixed_amount = fields.Float(
        string="Fixed Contract Amount",
        default=0.0
    )

    # =========================
    # Extra Costs
    # =========================

    fuel_cost = fields.Float(
        string="Fuel Cost",
        default=0.0
    )

    maintenance_cost = fields.Float(
        string="Maintenance Cost",
        default=0.0
    )

    transport_cost = fields.Float(
        string="Transport Cost",
        default=0.0
    )

    operator_cost = fields.Float(
        string="Operator Cost",
        default=0.0
    )

    other_cost = fields.Float(
        string="Other Cost",
        default=0.0
    )

    # =========================
    # Calculated Costs
    # =========================

    base_cost = fields.Float(
        string="Base Equipment Cost",
        compute="_compute_cost",
        store=True
    )

    extra_cost = fields.Float(
        string="Extra Costs",
        compute="_compute_cost",
        store=True
    )

    total_cost = fields.Float(
        string="Total Equipment Cost",
        compute="_compute_cost",
        store=True
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
    # Dates
    # =========================

    date = fields.Date(
        string="Date",
        default=fields.Date.today,
        required=True
    )

    start_date = fields.Date(
        string="Usage Start Date"
    )

    end_date = fields.Date(
        string="Usage End Date"
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
        "payment_type",
        "quantity",
        "usage_days",
        "hours_per_day",
        "hourly_rate",
        "daily_rate",
        "fixed_amount",
        "fuel_cost",
        "maintenance_cost",
        "transport_cost",
        "operator_cost",
        "other_cost"
    )
    def _compute_cost(self):

        for record in self:

            # -------------------------
            # Base Cost
            # -------------------------

            if record.payment_type == "daily":

                record.base_cost = (
                    record.quantity
                    * record.usage_days
                    * record.daily_rate
                )

            elif record.payment_type == "hourly":

                record.base_cost = (
                    record.quantity
                    * record.usage_days
                    * record.hours_per_day
                    * record.hourly_rate
                )

            else:

                record.base_cost = (
                    record.quantity
                    * record.fixed_amount
                )

            # -------------------------
            # Extra Costs
            # -------------------------

            record.extra_cost = (
                record.fuel_cost
                + record.maintenance_cost
                + record.transport_cost
                + record.operator_cost
                + record.other_cost
            )

            # -------------------------
            # Total
            # -------------------------

            record.total_cost = (
                record.base_cost
                + record.extra_cost
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

    @api.depends(
        "total_cost",
        "paid_amount"
    )
    def _compute_payment_status(self):

        for record in self:

            if record.paid_amount <= 0:

                record.payment_status = "unpaid"

            elif record.paid_amount >= record.total_cost:

                record.payment_status = "paid"

            else:

                record.payment_status = "partial"

    # =========================
    # Validation
    # =========================

    @api.constrains(
        "quantity",
        "usage_days",
        "hours_per_day",
        "hourly_rate",
        "daily_rate",
        "fixed_amount",
        "fuel_cost",
        "maintenance_cost",
        "transport_cost",
        "operator_cost",
        "other_cost",
        "paid_amount"
    )
    def _check_values(self):

        for record in self:

            values = {
                "Quantity": record.quantity,
                "Usage Days": record.usage_days,
                "Hours / Day": record.hours_per_day,
                "Hourly Rate": record.hourly_rate,
                "Daily Rate": record.daily_rate,
                "Fixed Contract Amount": record.fixed_amount,
                "Fuel Cost": record.fuel_cost,
                "Maintenance Cost": record.maintenance_cost,
                "Transport Cost": record.transport_cost,
                "Operator Cost": record.operator_cost,
                "Other Cost": record.other_cost,
                "Paid Amount": record.paid_amount,
            }

            for label, value in values.items():

                if value < 0:

                    raise ValidationError(
                        f"{label} cannot be negative."
                    )

            if record.quantity <= 0:

                raise ValidationError(
                    "Equipment quantity must be greater than zero."
                )

            if record.paid_amount > record.total_cost:

                raise ValidationError(
                    "Paid amount cannot be greater than "
                    "total equipment cost."
                )