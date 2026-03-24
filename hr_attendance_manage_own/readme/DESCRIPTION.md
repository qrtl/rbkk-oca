This module allows users to create and edit their own attendance records without
requiring attendance manager or officer privileges, with configurable
field-level restrictions.

Without this module, regular internal users can only read their own
attendance records. Creating or modifying attendance records requires either the
Attendance Manager role (full access to all records) or the Attendance
Officer role with the employee's attendance manager set to that user.

This module introduces an "Own Manager" group that can create and edit attendance
records, except for fields configured as disallowed. The overtime_status
field is disallowed by default. Additionally, when the company overtime validation
is set to 'by_manager', overtime_status must be set to 'To Approve' when creating
records (if company uses auto-approval, there is no validation). Attendance records
that have been approved or refused cannot be modified.
