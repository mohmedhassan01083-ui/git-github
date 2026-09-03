from odoo import models, fields, api
from odoo.exceptions import ValidationError
import urllib.parse


class EstateBooking(models.Model):
    _name = "estate.booking"
    _description = "Estate Booking"
    _order = "id desc"

    # =========================
    # Customer
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
        string="Customer Email",
        related="customer_id.email",
        store=True,
        readonly=True
    )

    # =========================
    # Property
    # =========================

    property_id = fields.Many2one(
        "estate.property",
        string="Property",
        required=True,
        ondelete="restrict"
    )

    property_type = fields.Selection(
        related="property_id.unit_type",
        string="Property Type",
        store=True,
        readonly=True
    )

    booking_type = fields.Selection(
        [
            ("rent", "Rent"),
            ("sale", "Sale"),
        ],
        string="Booking Type",
        required=True,
        default="sale"
    )

    # =========================
    # Status
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

    # =========================
    # Notes
    # =========================

    notes = fields.Text(
        string="Notes"
    )

    # =========================
    # Rental Information
    # =========================

    rent_amount = fields.Float(
        string="Rent Amount"
    )

    rent_start_date = fields.Date(
        string="Rent Start Date"
    )

    rent_end_date = fields.Date(
        string="Rent End Date"
    )

    rent_duration = fields.Integer(
        string="Rent Duration (Months)",
        readonly=True
    )

    # =========================
    # Reject Information
    # =========================

    reject_reason_type = fields.Selection(
        [
            ("documents", "Documents are incomplete"),
            ("income", "Insufficient income"),
            ("unavailable", "Property is unavailable"),
            ("other", "Other"),
        ],
        string="Reject Reason"
    )

    reject_reason = fields.Text(
        string="Other Reject Reason"
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

    # =========================
    # Communication
    # =========================

    whatsapp_sent = fields.Boolean(
        string="WhatsApp Sent",
        default=False,
        readonly=True
    )

    email_sent = fields.Boolean(
        string="Email Sent",
        default=False,
        readonly=True
    )

    # =========================
    # Property Type Onchange
    # =========================

    @api.onchange("property_id")
    def _onchange_property_id(self):
        for record in self:

            if not record.property_id:
                continue

            # Get Sale / Rental automatically
            if record.property_id.unit_type == "rent":
                record.booking_type = "rent"

                # Get property rent price
                record.rent_amount = record.property_id.price

            elif record.property_id.unit_type == "sale":
                record.booking_type = "sale"

                record.rent_amount = 0

    # =========================
    # Rental Dates Calculation
    # =========================

    @api.onchange("rent_start_date", "rent_end_date")
    def _onchange_rent_dates(self):

        for record in self:

            if not record.rent_start_date or not record.rent_end_date:
                record.rent_duration = 0
                continue

            if record.rent_end_date < record.rent_start_date:

                record.rent_duration = 0

                return {
                    "warning": {
                        "title": "Invalid Dates",
                        "message": (
                            "Rent End Date cannot be before "
                            "Rent Start Date."
                        )
                    }
                }

            start = record.rent_start_date
            end = record.rent_end_date

            months = (
                (end.year - start.year) * 12
                + (end.month - start.month)
            )

            if end.day < start.day:
                months -= 1

            record.rent_duration = max(months, 0)

    # =========================
    # Validation
    # =========================

    @api.constrains(
        "rent_start_date",
        "rent_end_date"
    )
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

    @api.constrains("rent_amount")
    def _check_rent_amount(self):

        for record in self:

            if record.rent_amount < 0:
                raise ValidationError(
                    "Rent Amount cannot be negative."
                )

    @api.constrains("property_id", "booking_type")
    def _check_booking_type(self):

        for record in self:

            if not record.property_id:
                continue

            if (
                record.booking_type
                != record.property_id.unit_type
            ):
                raise ValidationError(
                    "Booking Type must match the Property Type."
                )

    # =========================
    # Submit
    # =========================

    def action_submit(self):

        for record in self:

            record.status = "pending"

            record.approved_by = False
            record.approved_date = False

    # =========================
    # Approve
    # =========================

    def action_approve(self):

        for record in self:

            if not record.customer_id:
                raise ValidationError(
                    "Please select a customer first."
                )

            if not record.property_id:
                raise ValidationError(
                    "Please select a property first."
                )

            if record.property_id.unit_type == "rent":

                if (
                    not record.rent_start_date
                    or not record.rent_end_date
                ):
                    raise ValidationError(
                        "Please enter the rental start and end dates."
                    )

                record.property_id.state = "rented"

            elif record.property_id.unit_type == "sale":

                record.property_id.state = "sold"

            # Link customer to property
            record.property_id.customer_id = record.customer_id

            record.status = "approved"

            record.approved_by = self.env.user

            record.approved_date = fields.Datetime.now()

    # =========================
    # Reject
    # =========================

    def action_reject(self):

        for record in self:

            if not record.reject_reason_type:
                raise ValidationError(
                    "Please select a reject reason."
                )

            if (
                record.reject_reason_type == "other"
                and not record.reject_reason
            ):
                raise ValidationError(
                    "Please write the reject reason."
                )

            record.status = "rejected"

    # =========================
    # Send WhatsApp
    # =========================

    def action_send_whatsapp(self):

        self.ensure_one()

        if not self.phone:
            raise ValidationError(
                "Please enter the customer's phone number first."
            )

        phone = self.phone.strip()

        # Remove spaces and common symbols
        phone = (
            phone.replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        # Egyptian phone number
        if phone.startswith("0"):

            phone = "20" + phone[1:]

        elif phone.startswith("+20"):

            phone = phone[1:]

        elif not phone.startswith("20"):

            raise ValidationError(
                "Please enter a valid Egyptian phone number."
            )

        # =========================
        # Approved Message
        # =========================

        if self.status == "approved":

            message = f"""
السلام عليكم {self.customer_name}

يسعدنا إبلاغكم بأنه تم قبول طلب الحجز الخاص بكم بنجاح ✅

نوع العقار:
{self.property_type}

نوع الطلب:
{self.booking_type}

العقار:
{self.property_id.name}

السعر:
{self.property_id.price}

برجاء التوجه إلى خدمة العملاء لاستكمال الإجراءات.

شكراً لاختياركم شركتنا.
"""

        # =========================
        # Rejected Message
        # =========================

        elif self.status == "rejected":

            reason = self.reject_reason or ""

            if self.reject_reason_type == "documents":

                reason = "الأوراق غير مكتملة"

            elif self.reject_reason_type == "income":

                reason = "الدخل غير كاف"

            elif self.reject_reason_type == "unavailable":

                reason = "لا توجد وحدة مناسبة"

            message = f"""
السلام عليكم {self.customer_name}

نأسف لإبلاغكم بأنه تم رفض طلب الحجز الخاص بكم.

العقار:
{self.property_id.name}

سبب الرفض:

{reason}

يمكنكم التواصل مع خدمة العملاء لمزيد من التفاصيل.

شكراً لكم.
"""

        # =========================
        # Pending Message
        # =========================

        else:

            message = f"""
السلام عليكم {self.customer_name}

تم استلام طلب الحجز الخاص بكم بنجاح ✅

العقار:
{self.property_id.name}

نوع الطلب:
{self.booking_type}

سيتم مراجعة الطلب والرد عليكم قريباً.

شكراً لاختياركم شركتنا.
"""

        encoded_message = urllib.parse.quote(message)

        url = (
            "https://wa.me/"
            + phone
            + "?text="
            + encoded_message
        )

        self.whatsapp_sent = True

        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }