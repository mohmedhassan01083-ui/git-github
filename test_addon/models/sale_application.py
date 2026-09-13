from odoo import models, fields, api
from odoo.exceptions import ValidationError
import urllib.parse
from dateutil.relativedelta import relativedelta


class EstateSaleApplication(models.Model):
    _name = "estate.sale.application"
    _description = "Estate Sale Application"
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

    area = fields.Float(
        string="Required Area (m²)",
        required=True
    )

    property_price = fields.Float(
        string="Property Price",
        related="property_id.price",
        store=True,
        readonly=True
    )

    # =========================
    # Sales Order
    # =========================

    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sales Order",
        readonly=True,
        copy=False
    )

    sale_order_name = fields.Char(
        string="Sales Order Number",
        related="sale_order_id.name",
        readonly=True
    )

    # =========================
    # Invoice
    # =========================

    invoice_id = fields.Many2one(
        "account.move",
        string="Invoice",
        readonly=True,
        copy=False
    )

    invoice_name = fields.Char(
        string="Invoice Number",
        related="invoice_id.name",
        readonly=True
    )

    # =========================
    # Payment Information
    # =========================

    payment_type = fields.Selection(
        [
            ("cash", "Cash"),
            ("installment", "Installment"),
        ],
        string="Payment Type",
        required=True,
        default="cash"
    )

    installment_years = fields.Integer(
        string="Installment Years"
    )

    annual_interest = fields.Float(
        string="Annual Interest %",
        default=30.0,
        readonly=True
    )

    total_installment_amount = fields.Float(
        string="Total Installment Amount",
        compute="_compute_installment_amount",
        store=True
    )

    yearly_payment = fields.Float(
        string="Yearly Payment",
        compute="_compute_installment_amount",
        store=True
    )

    # =========================
    # Installment Schedule
    # =========================

    installment_ids = fields.One2many(
        "estate.installment",
        "sale_application_id",
        string="Installments",
        copy=False
    )

    installment_count = fields.Integer(
        string="Installment Count",
        compute="_compute_installment_totals",
        store=True
    )

    total_paid_amount = fields.Float(
        string="Total Paid",
        compute="_compute_installment_totals",
        store=True
    )

    total_remaining_amount = fields.Float(
        string="Total Remaining",
        compute="_compute_installment_totals",
        store=True
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
    # Installment Calculation
    # =========================

    @api.depends(
        "property_price",
        "payment_type",
        "installment_years",
        "annual_interest"
    )
    def _compute_installment_amount(self):

        for record in self:

            record.total_installment_amount = 0
            record.yearly_payment = 0

            if (
                record.payment_type != "installment"
                or record.installment_years <= 0
                or record.property_price <= 0
            ):
                continue

            total = record.property_price

            for _year in range(record.installment_years):
                total *= (
                    1 + record.annual_interest / 100
                )

            record.total_installment_amount = total

            record.yearly_payment = (
                total / record.installment_years
            )

    # =========================
    # Installment Totals
    # =========================

    @api.depends(
        "installment_ids",
        "installment_ids.amount",
        "installment_ids.paid_amount",
        "installment_ids.remaining_amount"
    )
    def _compute_installment_totals(self):

        for record in self:

            installments = record.installment_ids

            record.installment_count = len(installments)

            record.total_paid_amount = sum(
                installments.mapped("paid_amount")
            )

            record.total_remaining_amount = sum(
                installments.mapped("remaining_amount")
            )

    # =========================
    # Create Installment Schedule
    # =========================

    def _create_installment_schedule(self):

        self.ensure_one()

        if self.payment_type != "installment":
            return

        if self.installment_years <= 0:
            raise ValidationError(
                "Installment years must be greater than zero."
            )

        if self.total_installment_amount <= 0:
            raise ValidationError(
                "Total installment amount must be greater than zero."
            )

        # Prevent duplicate installments
        if self.installment_ids:
            return

        yearly_amount = (
            self.total_installment_amount
            / self.installment_years
        )

        installments = []

        for number in range(1, self.installment_years + 1):

            due_date = fields.Date.today() + relativedelta(
                years=number
            )

            amount = yearly_amount

            # Fix rounding difference on final installment
            if number == self.installment_years:

                previous_total = yearly_amount * (
                    self.installment_years - 1
                )

                amount = (
                    self.total_installment_amount
                    - previous_total
                )

            installments.append({
                "installment_number": number,
                "sale_application_id": self.id,
                "amount": amount,
                "due_date": due_date,
            })

        self.env["estate.installment"].create(
            installments
        )

    # =========================
    # Property Change
    # =========================

    @api.onchange("property_id")
    def _onchange_property_id(self):

        for record in self:

            if record.property_id:
                record.area = record.property_id.area

    # =========================
    # Area Validation
    # =========================

    @api.constrains("area")
    def _check_area(self):

        for record in self:

            if record.area < 90 or record.area > 600:
                raise ValidationError(
                    "The required area must be between 90 and 600 m²."
                )

    # =========================
    # Property Validation
    # =========================

    @api.constrains("property_id")
    def _check_property_product(self):

        for record in self:

            if record.property_id and not record.product_id:
                raise ValidationError(
                    "This property is not linked to an Inventory Product. "
                    "Please create the Product from the Property first."
                )

            if (
                record.property_id
                and record.property_id.unit_type != "sale"
            ):
                raise ValidationError(
                    "The selected property must be a sale property."
                )

    # =========================
    # Installment Years Validation
    # =========================

    @api.constrains("installment_years")
    def _check_installment_years(self):

        for record in self:

            if (
                record.payment_type == "installment"
                and record.installment_years <= 0
            ):
                raise ValidationError(
                    "Installment years must be greater than zero."
                )

    # =========================
    # Create Sales Order
    # =========================

    def _create_sale_order(self):

        self.ensure_one()

        if self.sale_order_id:
            return self.sale_order_id

        if not self.customer_id:
            raise ValidationError(
                "Please select a customer from Contacts."
            )

        if not self.property_id:
            raise ValidationError(
                "Please select a property first."
            )

        if not self.product_id:
            raise ValidationError(
                "The selected property is not linked to an Inventory Product."
            )

        if self.payment_type == "installment":
            sale_price = self.total_installment_amount
        else:
            sale_price = self.property_price

        if sale_price <= 0:
            raise ValidationError(
                "The property price must be greater than zero."
            )

        sale_order = self.env["sale.order"].create({
            "partner_id": self.customer_id.id,
            "origin": self.property_id.name,
        })

        self.env["sale.order.line"].create({
            "order_id": sale_order.id,
            "product_id": self.product_id.id,
            "product_uom_qty": 1,
            "price_unit": sale_price,
            "name": (
                f"Property: {self.property_id.name}\n"
                f"Area: {self.area} m²\n"
                f"Payment Type: "
                f"{'Installment' if self.payment_type == 'installment' else 'Cash'}"
            ),
        })

        self.sale_order_id = sale_order.id

        return sale_order

    # =========================
    # Create Invoice
    # =========================

    def _create_invoice(self, sale_order):

        self.ensure_one()

        if not sale_order:
            raise ValidationError(
                "Sales Order was not created."
            )

        if sale_order.invoice_ids:

            invoice = sale_order.invoice_ids.filtered(
                lambda inv: inv.move_type == "out_invoice"
            )[:1]

            if invoice:
                self.invoice_id = invoice.id
                return invoice

        invoices = sale_order._create_invoices()

        if not invoices:
            raise ValidationError(
                "Unable to create the invoice from the Sales Order."
            )

        invoice = invoices[:1]

        invoice.write({
            "invoice_origin": sale_order.name,
        })

        self.invoice_id = invoice.id

        return invoice

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

            if not record.product_id:
                raise ValidationError(
                    "The selected property is not linked to an Inventory Product."
                )

            if record.property_id.unit_type != "sale":
                raise ValidationError(
                    "The selected property is not available for sale."
                )

            if record.property_id.state == "sold":
                raise ValidationError(
                    "This property has already been sold."
                )

            if record.payment_type == "installment":
                if record.installment_years <= 0:
                    raise ValidationError(
                        "Installment years must be greater than zero."
                    )

            # =========================
            # Create Sales Order
            # =========================

            sale_order = record._create_sale_order()

            # =========================
            # Confirm Sales Order
            # =========================

            if sale_order.state not in ("sale", "done"):
                sale_order.action_confirm()

            # =========================
            # Create Invoice
            # =========================

            invoice = record._create_invoice(
                sale_order
            )

            # =========================
            # Create Installment Schedule
            # =========================

            record._create_installment_schedule()

            # =========================
            # Update Application
            # =========================

            record.status = "approved"

            record.approved_by = self.env.user

            record.approved_date = fields.Datetime.now()

            record.property_id.customer_id = record.customer_id

            record.property_id.state = "sold"

            record.invoice_id = invoice.id

    # =========================
    # Open Sales Order
    # =========================

    def action_open_sale_order(self):

        self.ensure_one()

        if not self.sale_order_id:
            raise ValidationError(
                "There is no Sales Order linked to this application."
            )

        return {
            "type": "ir.actions.act_window",
            "name": "Sales Order",
            "res_model": "sale.order",
            "view_mode": "form",
            "res_id": self.sale_order_id.id,
            "target": "current",
        }

    # =========================
    # Open Invoice
    # =========================

    def action_open_invoice(self):

        self.ensure_one()

        if not self.invoice_id:
            raise ValidationError(
                "There is no Invoice linked to this application."
            )

        return {
            "type": "ir.actions.act_window",
            "name": "Invoice",
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": self.invoice_id.id,
            "target": "current",
        }

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
    # Print Customer Report
    # =========================

    def action_print_report(self):

        self.ensure_one()

        if self.status == "pending":
            raise ValidationError(
                "You can print the customer report only after "
                "the application is approved or rejected."
            )

        return self.env.ref(
            "test_addon.action_sale_application_report"
        ).report_action(self)

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
                "Please enter the customer's phone number in Contacts."
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

        # =========================
        # Approved Message
        # =========================

        if self.status == "approved":

            message = f"""
السلام عليكم {self.customer_name}

يسعدنا إبلاغكم بأنه تم قبول طلب التمليك الخاص بكم بنجاح ✅

العقار:
{self.property_id.name}

المساحة:
{self.area} متر

سعر الوحدة:
{self.property_price:,.0f} جنيه

طريقة الدفع:
{self.payment_type}
"""

            if self.payment_type == "installment":

                message += f"""
عدد سنوات التقسيط:
{self.installment_years}

إجمالي المبلغ بعد الفائدة:
{self.total_installment_amount:,.0f} جنيه

القسط السنوي:
{self.yearly_payment:,.0f} جنيه

عدد الأقساط:
{self.installment_count}

المتبقي:
{self.total_remaining_amount:,.0f} جنيه
"""

            message += f"""
رقم أمر البيع:
{self.sale_order_id.name if self.sale_order_id else 'غير متوفر'}

رقم الفاتورة:
{self.invoice_id.name if self.invoice_id else 'غير متوفر'}

برجاء التواصل مع خدمة العملاء لاستكمال الإجراءات.

شكراً لاختياركم شركتنا.
"""

        # =========================
        # Rejected Message
        # =========================

        elif self.status == "rejected":

            message = f"""
السلام عليكم {self.customer_name}

نأسف لإبلاغكم بأنه تم رفض طلب التمليك الخاص بكم.

العقار:
{self.property_id.name}

سبب الرفض:
{self.reject_reason}

يمكنكم التواصل مع خدمة العملاء لمزيد من التفاصيل.

شكراً لكم.
"""

        # =========================
        # Pending Message
        # =========================

        else:

            message = f"""
السلام عليكم {self.customer_name}

تم استلام طلب التمليك الخاص بكم بنجاح.

العقار:
{self.property_id.name}

سيتم مراجعة الطلب والرد عليكم قريباً.

شكراً لكم.
"""

        # =========================
        # WhatsApp URL
        # =========================

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