from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EstateConstructionProject(models.Model):
    _name = "estate.construction.project"
    _description = "Construction Project Cost"
    _order = "id desc"

    # =========================
    # Project Information
    # =========================

    name = fields.Char(
        string="Project Name",
        required=True
    )

    code = fields.Char(
        string="Project Code"
    )

    description = fields.Text(
        string="Description"
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    )

    # =========================
    # Land Information
    # =========================

    land_area = fields.Float(
        string="Land Area (m²)"
    )

    land_price = fields.Float(
        string="Land Purchase Price"
    )

    land_price_per_meter = fields.Float(
        string="Land Price / m²",
        compute="_compute_land_price_per_meter",
        store=True
    )

    land_registration_cost = fields.Float(
        string="Land Registration Cost"
    )

    land_taxes = fields.Float(
        string="Land Taxes & Fees"
    )

    land_broker_cost = fields.Float(
        string="Land Broker Cost"
    )

    total_land_cost = fields.Float(
        string="Total Land Cost",
        compute="_compute_total_land_cost",
        store=True
    )

    # =========================
    # Project Dates
    # =========================

    start_date = fields.Date(
        string="Construction Start Date"
    )

    expected_end_date = fields.Date(
        string="Expected End Date"
    )

    actual_end_date = fields.Date(
        string="Actual End Date"
    )

    # =========================
    # Buildings & Units
    # =========================

    building_count = fields.Integer(
        string="Buildings"
    )

    unit_count = fields.Integer(
        string="Units"
    )

    total_built_area = fields.Float(
        string="Total Built Area (m²)"
    )

    # =========================
    # Budget
    # =========================

    planned_budget = fields.Float(
        string="Planned Budget"
    )

    contingency_percentage = fields.Float(
        string="Contingency %",
        default=5.0
    )

    contingency_amount = fields.Float(
        string="Contingency Amount",
        compute="_compute_contingency_amount",
        store=True
    )

    # =========================
    # Cost Categories
    # =========================

    material_cost = fields.Float(
        string="Materials Cost",
        compute="_compute_costs",
        store=True
    )

    labor_cost = fields.Float(
        string="Labor Cost",
        compute="_compute_costs",
        store=True
    )

    equipment_cost = fields.Float(
        string="Equipment Cost",
        compute="_compute_costs",
        store=True
    )

    expense_cost = fields.Float(
        string="Other Expenses",
        compute="_compute_costs",
        store=True
    )

    construction_cost = fields.Float(
        string="Construction Cost",
        compute="_compute_costs",
        store=True
    )

    total_project_cost = fields.Float(
        string="Total Project Cost",
        compute="_compute_total_project_cost",
        store=True
    )

    cost_per_meter = fields.Float(
        string="Cost / m²",
        compute="_compute_cost_per_meter",
        store=True
    )

    # =========================
    # Sales / Revenue
    # =========================

    expected_sales_value = fields.Float(
        string="Expected Sales Value"
    )

    actual_sales_value = fields.Float(
        string="Actual Sales Value"
    )

    expected_profit = fields.Float(
        string="Expected Profit",
        compute="_compute_profit",
        store=True
    )

    actual_profit = fields.Float(
        string="Actual Profit",
        compute="_compute_profit",
        store=True
    )

    expected_profit_percentage = fields.Float(
        string="Expected Profit %",
        compute="_compute_profit_percentage",
        store=True
    )

    actual_profit_percentage = fields.Float(
        string="Actual Profit %",
        compute="_compute_profit_percentage",
        store=True
    )

    # =========================
    # Payment
    # =========================

    total_paid = fields.Float(
        string="Total Paid"
    )

    total_remaining = fields.Float(
        string="Remaining Amount",
        compute="_compute_remaining",
        store=True
    )

    # =========================
    # Progress
    # =========================

    progress_percentage = fields.Float(
        string="Construction Progress %",
        default=0.0
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("planning", "Planning"),
            ("construction", "Under Construction"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True
    )

    notes = fields.Text(
        string="Notes"
    )

    # =========================
    # Cost Lines
    # =========================

    material_line_ids = fields.One2many(
        "estate.construction.material",
        "project_id",
        string="Materials"
    )

    labor_line_ids = fields.One2many(
        "estate.construction.labor",
        "project_id",
        string="Labor"
    )

    equipment_line_ids = fields.One2many(
        "estate.construction.equipment",
        "project_id",
        string="Equipment"
    )

    expense_line_ids = fields.One2many(
        "estate.construction.expense",
        "project_id",
        string="Expenses"
    )

    # =========================
    # Computations
    # =========================

    @api.depends("land_price", "land_area")
    def _compute_land_price_per_meter(self):
        for record in self:
            if record.land_area > 0:
                record.land_price_per_meter = (
                    record.land_price / record.land_area
                )
            else:
                record.land_price_per_meter = 0.0

    @api.depends(
        "land_price",
        "land_registration_cost",
        "land_taxes",
        "land_broker_cost"
    )
    def _compute_total_land_cost(self):
        for record in self:
            record.total_land_cost = (
                record.land_price
                + record.land_registration_cost
                + record.land_taxes
                + record.land_broker_cost
            )

    @api.depends(
        "planned_budget",
        "contingency_percentage"
    )
    def _compute_contingency_amount(self):
        for record in self:
            record.contingency_amount = (
                record.planned_budget
                * record.contingency_percentage
                / 100
            )

    @api.depends(
        "material_line_ids.total_cost",
        "labor_line_ids.total_cost",
        "equipment_line_ids.total_cost",
        "expense_line_ids.amount"
    )
    def _compute_costs(self):
        for record in self:

            record.material_cost = sum(
                record.material_line_ids.mapped("total_cost")
            )

            record.labor_cost = sum(
                record.labor_line_ids.mapped("total_cost")
            )

            record.equipment_cost = sum(
                record.equipment_line_ids.mapped("total_cost")
            )

            record.expense_cost = sum(
                record.expense_line_ids.mapped("amount")
            )

            record.construction_cost = (
                record.material_cost
                + record.labor_cost
                + record.equipment_cost
                + record.expense_cost
            )

    @api.depends(
        "total_land_cost",
        "construction_cost",
        "contingency_amount"
    )
    def _compute_total_project_cost(self):
        for record in self:
            record.total_project_cost = (
                record.total_land_cost
                + record.construction_cost
                + record.contingency_amount
            )

    @api.depends(
        "total_project_cost",
        "total_built_area"
    )
    def _compute_cost_per_meter(self):
        for record in self:
            if record.total_built_area > 0:
                record.cost_per_meter = (
                    record.total_project_cost
                    / record.total_built_area
                )
            else:
                record.cost_per_meter = 0.0

    @api.depends(
        "expected_sales_value",
        "actual_sales_value",
        "total_project_cost"
    )
    def _compute_profit(self):
        for record in self:
            record.expected_profit = (
                record.expected_sales_value
                - record.total_project_cost
            )

            record.actual_profit = (
                record.actual_sales_value
                - record.total_project_cost
            )

    @api.depends(
        "expected_profit",
        "actual_profit",
        "expected_sales_value",
        "actual_sales_value"
    )
    def _compute_profit_percentage(self):
        for record in self:

            if record.expected_sales_value > 0:
                record.expected_profit_percentage = (
                    record.expected_profit
                    / record.expected_sales_value
                    * 100
                )
            else:
                record.expected_profit_percentage = 0.0

            if record.actual_sales_value > 0:
                record.actual_profit_percentage = (
                    record.actual_profit
                    / record.actual_sales_value
                    * 100
                )
            else:
                record.actual_profit_percentage = 0.0

    @api.depends(
        "total_project_cost",
        "total_paid"
    )
    def _compute_remaining(self):
        for record in self:
            record.total_remaining = max(
                record.total_project_cost
                - record.total_paid,
                0.0
            )

    # =========================
    # Validation
    # =========================

    @api.constrains(
        "land_area",
        "total_built_area",
        "progress_percentage",
        "contingency_percentage"
    )
    def _check_percentages_and_areas(self):
        for record in self:

            if record.land_area < 0:
                raise ValidationError(
                    "Land area cannot be negative."
                )

            if record.total_built_area < 0:
                raise ValidationError(
                    "Total built area cannot be negative."
                )

            if not 0 <= record.progress_percentage <= 100:
                raise ValidationError(
                    "Construction progress must be between 0 and 100."
                )

            if record.contingency_percentage < 0:
                raise ValidationError(
                    "Contingency percentage cannot be negative."
                )

    # =========================
    # Actions
    # =========================

    def action_start_planning(self):
        for record in self:
            record.state = "planning"

    def action_start_construction(self):
        for record in self:
            record.state = "construction"

    def action_complete(self):
        for record in self:
            record.progress_percentage = 100
            record.state = "completed"

    def action_cancel(self):
        for record in self:
            record.state = "cancelled"

    def action_reset_to_draft(self):
        for record in self:
            record.state = "draft"