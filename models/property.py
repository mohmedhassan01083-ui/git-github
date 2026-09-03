from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Property(models.Model):
    _name = "estate.property"
    _description = "Real Estate Property"

    # =========================
    # Property Information
    # =========================

    name = fields.Char(
        string="Property Name",
        required=True
    )

    description = fields.Text(
        string="Description"
    )

    price = fields.Float(
        string="Price"
    )

    area = fields.Float(
        string="Area"
    )

    bedrooms = fields.Integer(
        string="Bedrooms"
    )

    bathrooms = fields.Integer(
        string="Bathrooms"
    )

    garden = fields.Boolean(
        string="Has Garden"
    )

    garden_area = fields.Integer(
        string="Garden Area"
    )

    # =========================
    # Property Status
    # =========================

    state = fields.Selection(
        [
            ("new", "New"),
            ("sold", "Sold"),
            ("rented", "Rented"),
        ],
        string="Status",
        default="new",
        required=True
    )

    # =========================
    # Sale / Rental
    # =========================

    unit_type = fields.Selection(
        [
            ("sale", "For Sale"),
            ("rent", "For Rent"),
        ],
        string="Property Type",
        default="sale",
        required=True
    )

    rent_period = fields.Selection(
        [
            ("1_month", "1 Month"),
            ("3_months", "3 Months"),
            ("6_months", "6 Months"),
            ("1_year", "1 Year"),
            ("2_years", "2 Years"),
        ],
        string="Rent Period"
    )

    # =========================
    # Customer
    # =========================

    customer_id = fields.Many2one(
        "res.partner",
        string="Customer"
    )

    # =========================
    # Inventory Product
    # =========================

    product_id = fields.Many2one(
        "product.product",
        string="Inventory Product",
        readonly=True,
        help="Inventory product linked to this property."
    )

    # =========================
    # Installment Information
    # =========================

    down_payment = fields.Float(
        string="Down Payment"
    )

    interest_rate = fields.Float(
        string="Interest Rate",
        default=30
    )

    years = fields.Integer(
        string="Installment Years"
    )

    remaining_amount = fields.Float(
        string="Remaining Amount"
    )

    total_after_interest = fields.Float(
        string="Total Amount After Interest"
    )

    monthly_installment = fields.Float(
        string="Monthly Installment"
    )

    # =========================
    # Installment Calculation
    # =========================

    @api.onchange(
        "price",
        "down_payment",
        "interest_rate",
        "years"
    )
    def _calculate_installment(self):
        for record in self:

            record.remaining_amount = (
                record.price - record.down_payment
            )

            record.total_after_interest = (
                record.remaining_amount
                + (
                    record.remaining_amount
                    * record.interest_rate
                    / 100
                )
            )

            if record.years > 0:
                record.monthly_installment = (
                    record.total_after_interest
                    / (record.years * 12)
                )
            else:
                record.monthly_installment = 0

    # =========================
    # Create Inventory Product
    # =========================

    def action_create_product(self):
        self.ensure_one()

        if self.product_id:
            raise ValidationError(
                "A Product is already linked to this property."
            )

        if not self.name:
            raise ValidationError(
                "Please enter the Property Name first."
            )

        if self.price <= 0:
            raise ValidationError(
                "Please enter a valid Property Price first."
            )

        product = self.env["product.product"].create({
            "name": self.name,
            "list_price": self.price,
            "description_sale": self.description,
        })

        self.product_id = product.id

        return {
            "type": "ir.actions.act_window",
            "name": "Property Product",
            "res_model": "product.product",
            "view_mode": "form",
            "res_id": product.id,
            "target": "current",
        }

    # =========================
    # Open Inventory Product
    # =========================

    def action_open_product(self):
        self.ensure_one()

        if not self.product_id:
            raise ValidationError(
                "There is no Product linked to this property."
            )

        return {
            "type": "ir.actions.act_window",
            "name": "Property Product",
            "res_model": "product.product",
            "view_mode": "form",
            "res_id": self.product_id.id,
            "target": "current",
        }

    # =========================
    # Print Property Report
    # =========================

    def action_print_report(self):
        self.ensure_one()

        return self.env.ref(
            "test_addon.action_property_report"
        ).report_action(self)

    # =========================
    # Booking
    # =========================

    def action_open_booking(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Booking",
            "res_model": "estate.booking",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_property_id": self.id,
            },
        }

    # =========================
    # Rental Application
    # =========================

    def action_open_rental(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Rental Application",
            "res_model": "estate.rental.application",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_area": self.area,
                "default_property_id": self.id,
            },
        }