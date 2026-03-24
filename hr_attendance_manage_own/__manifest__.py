# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "HR Attendance Own Management",
    "version": "18.0.1.0.0",
    "category": "Human Resources/Attendances",
    "summary": "Allow users to create and edit their own attendance records",
    "author": "Quartile, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "license": "AGPL-3",
    "depends": ["hr_attendance"],
    "data": [
        "security/hr_attendance_manage_own_security.xml",
        "security/ir.model.access.csv",
        "data/hr_attendance_disallowed_field_data.xml",
        "views/hr_attendance_disallowed_field_views.xml",
    ],
    "installable": True,
}
