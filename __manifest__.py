{
    'name': 'Real Estate',
    'version': '1.0',

    'depends': [
        'base',
        'stock',
        'sale_management',
        'purchase',
        'account',
        'project',
        'crm',
        'hr',
    ],

    'data': [
        # =========================
        # SECURITY
        # =========================
        'security/ir.model.access.csv',

        # =========================
        # REAL ESTATE
        # =========================
        'views/property_views.xml',
        'views/booking_views.xml',
        'views/installment_views.xml',
        'views/sale_application_views.xml',
        'views/rental_application_views.xml',

        # =========================
        # CONSTRUCTION
        # =========================
        'views/construction_project_views.xml',
        'views/construction_material_views.xml',
        'views/construction_labor_views.xml',
        'views/construction_equipment_views.xml',
        'views/construction_expense_views.xml',
        'views/erp_integration_views.xml',

        # =========================
        # REPORTS
        # =========================
        'reports/property_report.xml',
        'reports/property_template.xml',

        'reports/sale_application_report.xml',
        'reports/sale_application_template.xml',
    ],

    'installable': True,
    'application': True,
}