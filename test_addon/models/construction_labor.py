from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EstateConstructionLabor(models.Model):
    _name = "estate.construction.labor"
    _description = "Construction Labor Cost"
    _order = "date desc, id desc"

    # =========================
    # Basic Information
    # =========================

    name = fields.Char(
        string="Worker / Contractor Name",
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
    # Worker Information
    # =========================

    worker_type = fields.Selection(
        [
            ("worker", "Worker"),
            ("technician", "Technician"),
            ("engineer", "Engineer"),
            ("supervisor", "Supervisor"),
            ("contractor", "Contractor"),
            ("company", "Contracting Company"),
            ("other", "Other"),
        ],
        string="Worker Type",
        required=True,
        default="worker"
    )

    job_position = fields.Char(
        string="Job / Profession"
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Worker / Contractor Contact"
    )

    description = fields.Text(
        string="Description"
    )

    # =========================
    # Work Calculation
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

    work_days = fields.Float(
        string="Work Days",
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

    overtime_hours = fields.Float(
        string="Overtime Hours",
        default=0.0
    )

    overtime_rate = fields.Float(
        string="Overtime Rate",
        default=0.0
    )

    # =========================
    # Extra Payments
    # =========================

    bonus = fields.Float(
        string="Bonus",
        default=0.0
    )

    transport_allowance = fields.Float(
        string="Transport Allowance",
        default=0.0
    )

    accommodation_allowance = fields.Float(
        string="Accommodation Allowance",
        default=0.0
    )

    other_allowance = fields.Float(
        string="Other Allowance",
        default=0.0
    )

    deductions = fields.Float(
        string="Deductions",
        default=0.0
    )

    # =========================
    # Cost
    # =========================

    base_cost = fields.Float(
        string="Base Cost",
        compute="_compute_cost",
        store=True
    )

    overtime_cost = fields.Float(
        string="Overtime Cost",
        compute="_compute_cost",
        store=True
    )

    allowances_total = fields.Float(
        string="Total Allowances",
        compute="_compute_cost",
        store=True
    )

    total_cost = fields.Float(
        string="Total Labor Cost",
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
        string="Work Start Date"
    )

    end_date = fields.Date(
        string="Work End Date"
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
        "work_days",
        "hours_per_day",
        "hourly_rate",
        "daily_rate",
        "fixed_amount",
        "overtime_hours",
        "overtime_rate",
        "bonus",
        "transport_allowance",
        "accommodation_allowance",
        "other_allowance",
        "deductions"
    )
    def _compute_cost(self):

        for record in self:

            # -------------------------
            # Base Cost
            # -------------------------

            if record.payment_type == "daily":

                record.base_cost = (
                    record.work_days
                    * record.daily_rate
                )

            elif record.payment_type == "hourly":

                record.base_cost = (
                    record.work_days
                    * record.hours_per_day
                    * record.hourly_rate
                )

            else:

                record.base_cost = record.fixed_amount

            # -------------------------
            # Overtime
            # -------------------------

            record.overtime_cost = (
                record.overtime_hours
                * record.overtime_rate
            )

            # -------------------------
            # Allowances
            # -------------------------

            record.allowances_total = (
                record.bonus
                + record.transport_allowance
                + record.accommodation_allowance
                + record.other_allowance
            )

            # -------------------------
            # Total
            # -------------------------

            record.total_cost = (
                record.base_cost
                + record.overtime_cost
                + record.allowances_total
                - record.deductions
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
        "work_days",
        "hours_per_day",
        "hourly_rate",
        "daily_rate",
        "fixed_amount",
        "overtime_hours",
        "overtime_rate",
        "bonus",
        "transport_allowance",
        "accommodation_allowance",
        "other_allowance",
        "deductions",
        "paid_amount"
    )
    def _check_values(self):

        for record in self:

            values = {
                "Work Days": record.work_days,
                "Hours / Day": record.hours_per_day,
                "Hourly Rate": record.hourly_rate,
                "Daily Rate": record.daily_rate,
                "Fixed Contract Amount": record.fixed_amount,
                "Overtime Hours": record.overtime_hours,
                "Overtime Rate": record.overtime_rate,
                "Bonus": record.bonus,
                "Transport Allowance": record.transport_allowance,
                "Accommodation Allowance": record.accommodation_allowance,
                "Other Allowance": record.other_allowance,
                "Deductions": record.deductions,
                "Paid Amount": record.paid_amount,
            }

            for label, value in values.items():

                if value < 0:

                    raise ValidationError(
                        f"{label} cannot be negative."
                    )

            if record.paid_amount > record.total_cost:

                raise ValidationError(
                    "Paid amount cannot be greater than total labor cost."
                )