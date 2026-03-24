# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime
from unittest.mock import patch

import psycopg2

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestHrAttendanceRestTime(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.calendar = cls.env["resource.calendar"].create(
            {
                "name": "Flex Calendar",
                "company_id": cls.company.id,
                "flexible_hours": True,
                "hours_per_day": 8,
                "full_time_required_hours": 40,
                "rest_time_rule_ids": [
                    Command.create({"min_hours": 4.0, "rest_time": 0.25}),
                    Command.create({"min_hours": 6.0, "rest_time": 0.5}),
                    Command.create({"min_hours": 8.0, "rest_time": 1.0}),
                ],
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "company_id": cls.company.id,
                "resource_calendar_id": cls.calendar.id,
            }
        )

    def _create_attendance(self, employee=None, check_in=None, check_out=None):
        """Helper to create attendance records with default values."""
        return self.env["hr.attendance"].create(
            {
                "employee_id": (employee or self.employee).id,
                "check_in": check_in or datetime(2025, 1, 6, 8, 0),
                "check_out": check_out,
            }
        )

    def _create_user_with_groups(self, name, login, group_xmlids):
        """Helper to create users with specific security groups."""
        return self.env["res.users"].create(
            {
                "name": name,
                "login": login,
                "groups_id": [
                    Command.set([self.env.ref(xmlid).id for xmlid in group_xmlids])
                ],
            }
        )

    def test_rest_time_applied(self):
        """Rest time is applied when gross hours >= threshold."""
        att = self._create_attendance(check_out=datetime(2025, 1, 6, 17, 0))
        self.assertEqual(att.rest_time, 1.0, "9 hours should match 8.0 rule")
        self.assertEqual(att.worked_hours, 8.0)

    def test_rest_time_not_applied(self):
        att = self._create_attendance(check_out=datetime(2025, 1, 6, 11, 0))
        self.assertEqual(att.rest_time, 0.0, "3 hours should not match any rule")
        self.assertEqual(att.worked_hours, 3.0)

    def test_multiple_rules_highest_match(self):
        att1 = self._create_attendance(check_out=datetime(2025, 1, 6, 13, 0))
        self.assertEqual(att1.rest_time, 0.25, "5 hours should match 4.0 rule")
        att2 = self._create_attendance(
            check_in=datetime(2025, 1, 7, 8, 0),
            check_out=datetime(2025, 1, 7, 15, 0),
        )
        self.assertEqual(att2.rest_time, 0.5, "7 hours should match 6.0 rule")

    def test_manual_override(self):
        att = self._create_attendance(check_out=datetime(2025, 1, 6, 17, 0))
        self.assertEqual(att.rest_time, 1.0)
        self.assertEqual(att.worked_hours, 8.0)
        att.rest_time = 0.5
        self.assertEqual(att.worked_hours, 8.5)

    def test_constraint_rest_time_exceeds_gross(self):
        att = self._create_attendance(check_out=datetime(2025, 1, 6, 10, 0))
        with self.assertRaises(ValidationError):
            att.rest_time = 3.0

    def test_constraint_negative_rest_time(self):
        with self.assertRaises(ValidationError, msg="Rest time must be >= 0"):
            self.env["resource.calendar.rest.time.rule"].create(
                {
                    "calendar_id": self.calendar.id,
                    "min_hours": 10.0,
                    "rest_time": -0.5,
                }
            )

    def test_constraint_negative_min_hours(self):
        with self.assertRaises(ValidationError, msg="Minimum hours must be >= 0"):
            self.env["resource.calendar.rest.time.rule"].create(
                {
                    "calendar_id": self.calendar.id,
                    "min_hours": -2.0,
                    "rest_time": 0.5,
                }
            )

    def test_constraint_unique_min_hours_per_calendar(self):
        with (
            self.assertRaises(
                psycopg2.IntegrityError, msg="Duplicate min_hours should be rejected"
            ),
            mute_logger("odoo.sql_db"),
        ):
            self.env["resource.calendar.rest.time.rule"].create(
                {
                    "calendar_id": self.calendar.id,
                    "min_hours": 6.0,
                    "rest_time": 0.75,
                }
            )
        other_calendar = self.env["resource.calendar"].create(
            {
                "name": "Other Calendar",
                "company_id": self.company.id,
                "flexible_hours": True,
            }
        )
        rule = self.env["resource.calendar.rest.time.rule"].create(
            {
                "calendar_id": other_calendar.id,
                "min_hours": 6.0,
                "rest_time": 0.5,
            }
        )
        self.assertTrue(rule)

    def test_inverse_rest_time_updates_overtime(self):
        """Verify that _inverse_rest_time calls _update_overtime."""
        att = self._create_attendance(check_out=datetime(2025, 1, 6, 17, 0))
        self.assertEqual(att.rest_time, 1.0)
        with patch.object(
            type(att), "_update_overtime", wraps=att._update_overtime
        ) as mock_update:
            att.rest_time = 0.5
            mock_update.assert_called_once()

    def test_boundary_exact_threshold(self):
        """Test exact boundary matching with >= comparison."""
        att1 = self._create_attendance(check_out=datetime(2025, 1, 6, 12, 0))
        self.assertEqual(
            att1.rest_time, 0.25, "Exactly 4.0 hours should match 4.0 rule"
        )
        att2 = self._create_attendance(
            check_in=datetime(2025, 1, 7, 8, 0),
            check_out=datetime(2025, 1, 7, 11, 59, 24),  # 3.99 hours
        )
        self.assertEqual(att2.rest_time, 0.0, "3.99 hours should not match any rule")
        att3 = self._create_attendance(
            check_in=datetime(2025, 1, 8, 8, 0),
            check_out=datetime(2025, 1, 8, 14, 0),  # Exactly 6 hours
        )
        self.assertEqual(att3.rest_time, 0.5, "Exactly 6.0 hours should match 6.0 rule")
        att4 = self._create_attendance(
            check_in=datetime(2025, 1, 9, 8, 0),
            check_out=datetime(2025, 1, 9, 16, 0),  # Exactly 8 hours
        )
        self.assertEqual(att4.rest_time, 1.0, "Exactly 8.0 hours should match 8.0 rule")

    def test_open_attendance_missing_check_out(self):
        """Test that open attendance (no check_out) returns 0.0 rest_time."""
        att = self._create_attendance()  # No check_out
        self.assertEqual(
            att.rest_time, 0.0, "Open attendance should have 0.0 rest_time"
        )
        self.assertEqual(
            att.worked_hours, 0.0, "Open attendance should have 0.0 worked_hours"
        )

    def test_non_flexible_calendar_employee(self):
        """Test that non-flexible calendar returns 0.0 rest_time."""
        non_flex_calendar = self.env["resource.calendar"].create(
            {
                "name": "Standard Calendar",
                "company_id": self.company.id,
                "flexible_hours": False,
                "attendance_ids": [
                    Command.create(
                        {
                            "name": "Monday",
                            "dayofweek": "0",
                            "hour_from": 8.0,
                            "hour_to": 17.0,
                            "day_period": "morning",
                        }
                    ),
                ],
            }
        )
        non_flex_employee = self.env["hr.employee"].create(
            {
                "name": "Standard Employee",
                "company_id": self.company.id,
                "resource_calendar_id": non_flex_calendar.id,
            }
        )
        att = self.env["hr.attendance"].create(
            {
                "employee_id": non_flex_employee.id,
                "check_in": datetime(2025, 1, 6, 8, 0),
                "check_out": datetime(2025, 1, 6, 17, 0),  # 9 hours
            }
        )
        self.assertEqual(
            att.rest_time,
            0.0,
            "Non-flexible calendar should not apply rest time rules",
        )
        self.assertEqual(
            att.worked_hours, 9.0, "Worked hours should be full gross time"
        )

    def test_is_rest_time_readonly_manager(self):
        """Test is_rest_time_readonly for attendance manager."""
        manager_user = self._create_user_with_groups(
            "Attendance Manager",
            "manager",
            ["base.group_user", "hr_attendance.group_hr_attendance_manager"],
        )
        att = self._create_attendance(check_out=datetime(2025, 1, 6, 17, 0))
        att_as_manager = att.with_user(manager_user)
        self.assertFalse(
            att_as_manager.is_rest_time_readonly,
            "Manager should be able to edit rest_time",
        )

    def test_is_rest_time_readonly_officer_own_employee(self):
        """Test is_rest_time_readonly for officer managing their own employee."""
        officer_user = self._create_user_with_groups(
            "Attendance Officer",
            "officer",
            ["base.group_user", "hr_attendance.group_hr_attendance_officer"],
        )
        self.employee.attendance_manager_id = officer_user
        att = self._create_attendance(check_out=datetime(2025, 1, 6, 17, 0))
        att_as_officer = att.with_user(officer_user)
        self.assertFalse(
            att_as_officer.is_rest_time_readonly,
            "Officer should be able to edit rest_time for their managed employees",
        )

    def test_is_rest_time_readonly_officer_other_employee(self):
        """Test is_rest_time_readonly for officer with non-managed employee."""
        officer_user = self._create_user_with_groups(
            "Attendance Officer",
            "officer2",
            ["base.group_user", "hr_attendance.group_hr_attendance_officer"],
        )
        att = self._create_attendance(check_out=datetime(2025, 1, 6, 17, 0))
        att_as_officer = att.with_user(officer_user)
        self.assertTrue(
            att_as_officer.is_rest_time_readonly,
            "Officer should not be able to edit rest_time for non-managed employees",
        )

    def test_is_rest_time_readonly_user_approved_overtime(self):
        """Test is_rest_time_readonly for regular user with approved overtime."""
        regular_user = self._create_user_with_groups(
            "Regular User", "user", ["base.group_user"]
        )
        att = self._create_attendance(check_out=datetime(2025, 1, 6, 17, 0))
        att.overtime_status = "approved"
        att_as_user = att.with_user(regular_user)
        self.assertTrue(
            att_as_user.is_rest_time_readonly,
            "Regular user should not edit rest_time when overtime is approved",
        )

    def test_is_rest_time_readonly_user_pending_overtime(self):
        """Test is_rest_time_readonly for regular user with pending overtime."""
        regular_user = self._create_user_with_groups(
            "Regular User", "user2", ["base.group_user"]
        )
        att = self._create_attendance(check_out=datetime(2025, 1, 6, 17, 0))
        att.overtime_status = False
        att_as_user = att.with_user(regular_user)
        self.assertFalse(
            att_as_user.is_rest_time_readonly,
            "Regular user should be able to edit rest_time when overtime not approved",
        )
