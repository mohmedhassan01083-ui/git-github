from odoo import models, fields, api
from odoo.exceptions import ValidationError
import urllib.parse


class EstateRentalApplication(models.Model):
    _name = "estate.rental.application"
    _description = "Estate Rental Application"
    _order = "id desc"

    # =========================
    # Customer / Contact
    # =========================

    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True
    )

    customer_name = fields.Char(
        string="Customer Name",
        related="customer_id.name",
        store=True,
        readonly=True
    )

    phone = fields.Char(
        string="Phone",
        related="customer_id.phone",
        store=True,
        readonly=True
    )

    customer_email = fields.Char(
        string="Email",
        related="customer_id.email",
        store=True,
        readonly=True
    )

    address = fields.Char(
        string="Address",
        related="customer_id.contact_address",
        store=True,
        readonly=True
    )

    # =========================
    # Property Information
    # =========================

    property_id = fields.Many2one(
        "estate.property",
        string="Property",
        required=True,
        ondelete="restrict"
    )

    product_id = fields.Many2one(
        "product.product",
        string="Inventory Product",
        related="property_id.product_id",
        store=True,
        readonly=True
    )

    property_type = fields.Selection(
        related="property_id.unit_type",
        string="Property Type",
        store=True,
        readonly=True
    )

    area = fields.Float(
        string="Required Area (m²)",
        required=True
    )

    monthly_rent = fields.Float(
        string="Monthly Rent",
        related="property_id.price",
        store=True,
        readonly=True
    )

    budget = fields.Float(
        string="Customer Budget"
    )

    # =========================
    # Rental Duration
    # =========================

    rent_duration = fields.Selection(
        [
            ("1", "1 Year"),
            ("2", "2 Years"),
            ("3", "3 Years"),
        ],
        string="Rental Duration",
        default="1",
        required=True
    )

    # =========================
    # Rental Dates
    # =========================

    rent_start_date = fields.Date(
        string="Rent Start Date"
    )

    rent_end_date = fields.Date(
        string="Rent End Date"
    )

    # =========================
    # Application Status
    # =========================

    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Status",
        default="pending",
        required=True
    )

    notes = fields.Text(
        string="Notes"
    )

    reject_reason = fields.Text(
        string="Reject Reason"
    )

    # =========================
    # Approval Information
    # =========================

    approved_by = fields.Many2one(
        "res.users",
        string="Approved By",
        readonly=True
    )

    approved_date = fields.Datetime(
        string="Approved Date",
        readonly=True
    )

    whatsapp_sent = fields.Boolean(
        string="WhatsApp Sent",
        default=False,
        readonly=True
    )

    # =========================
    # Property Change
    # =========================

    @api.onchange("property_id")
    def _onchange_property_id(self):

        for record in self:

            if not record.property_id:
                continue

            record.area = record.property_id.area

            if record.property_id.unit_type != "rent":
                return {
                    "warning": {
                        "title": "Wrong Property Type",
                        "message": (
                            "The selected property is not available "
                            "for rental."
                        )
                    }
                }

    # =========================
    # Area Validation
    # =========================

    @api.constrains("area")
    def _check_area(self):

        for record in self:

            if record.area < 90 or record.area > 200:
                raise ValidationError(
                    "The required rental area must be between "
                    "90 and 200 m²."
                )

    # =========================
    # Budget Validation
    # =========================

    @api.constrains("budget")
    def _check_budget(self):

        for record in self:

            if record.budget < 0:
                raise ValidationError(
                    "Customer Budget cannot be negative."
                )

    # =========================
    # Property Validation
    # =========================

    @api.constrains("property_id")
    def _check_property_type(self):

        for record in self:

            if (
                record.property_id
                and record.property_id.unit_type != "rent"
            ):
                raise ValidationError(
                    "The selected property must be a rental property."
                )

    # =========================
    # Rental Date Validation
    # =========================

    @api.constrains("rent_start_date", "rent_end_date")
    def _check_rent_dates(self):

        for record in self:

            if (
                record.rent_start_date
                and record.rent_end_date
                and record.rent_end_date < record.rent_start_date
            ):
                raise ValidationError(
                    "Rent End Date cannot be before Rent Start Date."
                )

    # =========================
    # Approve
    # =========================

    def action_approve(self):

        for record in self:

            if not record.customer_id:
                raise ValidationError(
                    "Please select a customer from Contacts."
                )

            if not record.property_id:
                raise ValidationError(
                    "Please select a property first."
                )

            if record.property_id.unit_type != "rent":
                raise ValidationError(
                    "The selected property is not available for rent."
                )

            if record.property_id.state == "rented":
                raise ValidationError(
                    "This property has already been rented."
                )

            record.status = "approved"

            record.approved_by = self.env.user

            record.approved_date = fields.Datetime.now()

            record.property_id.customer_id = record.customer_id

            record.property_id.state = "rented"

    # =========================
    # Reject
    # =========================

    def action_reject(self):

        for record in self:

            if not record.reject_reason:
                raise ValidationError(
                    "Please enter the reject reason."
                )

            record.status = "rejected"

            record.approved_by = False
            record.approved_date = False

    # =========================
    # Send WhatsApp
    # =========================

    def action_send_whatsapp(self):

        self.ensure_one()

        if not self.customer_id:
            raise ValidationError(
                "Please select a customer from Contacts."
            )

        if not self.phone:
            raise ValidationError(
                "Please enter the customer's phone number "
                "in Contacts."
            )

        phone = self.phone.strip()

        phone = (
            phone.replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        if phone.startswith("0"):
            phone = "20" + phone[1:]

        elif phone.startswith("+20"):
            phone = phone[1:]

        elif not phone.startswith("20"):
            raise ValidationError(
                "Please enter a valid Egyptian phone number."
            )

        if self.status == "approved":

            message = f"""
السلام عليكم {self.customer_name}

يسعدنا إبلاغكم بأنه تم قبول طلب الإيجار الخاص بكم بنجاح ✅

العقار:
{self.property_id.name}

المساحة:
{self.area} متر

الإيجار الشهري:
{self.monthly_rent:,.0f} جنيه

مدة الإيجار:
{self.rent_duration} سنة
"""

            if self.rent_start_date:

                message += f"""
تاريخ بداية الإيجار:
{self.rent_start_date}
"""

            if self.rent_end_date:

                message += f"""
تاريخ نهاية الإيجار:
{self.rent_end_date}
"""

            message += """
برجاء التواصل مع خدمة العملاء لاستكمال الإجراءات.

شكراً لاختياركم شركتنا.
"""

        elif self.status == "rejected":

            message = f"""
السلام عليكم {self.customer_name}

نأسف لإبلاغكم بأنه تم رفض طلب الإيجار الخاص بكم.

العقار:
{self.property_id.name}

سبب الرفض:
{self.reject_reason}

يمكنكم التواصل مع خدمة العملاء لمزيد من التفاصيل.

شكراً لكم.
"""

        else:

            message = f"""
السلام عليكم {self.customer_name}

تم استلام طلب الإيجار الخاص بكم بنجاح ✅

العقار:
{self.property_id.name}

المساحة:
{self.area} متر

سيتم مراجعة الطلب والرد عليكم قريباً.

شكراً لاختياركم شركتنا.
"""

        url = (
            "https://wa.me/"
            + phone
            + "?text="
            + urllib.parse.quote(message)
        )

        self.whatsapp_sent = True

        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }