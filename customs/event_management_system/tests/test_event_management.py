from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestEventManagement(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
        cls.event = cls.env["event.event"].create(
            {
                "name": "Requirements Test Event",
                "date_begin": fields.Datetime.now() + timedelta(days=10),
                "date_end": fields.Datetime.now() + timedelta(days=11),
            }
        )
        cls.lead = cls.env["res.users"].create(
            {"name": "Committee Lead", "login": "ems_test_lead"}
        )
        cls.member_user = cls.env["res.users"].create(
            {"name": "Committee Member", "login": "ems_test_member"}
        )
        cls.technician = cls.env["res.users"].create(
            {"name": "Technician", "login": "ems_test_technician"}
        )
        cls.committee = cls.env["ems.committee"].create(
            {
                "name": "Digital Technology",
                "event_id": cls.event.id,
                "lead_id": cls.lead.id,
                "member_user_ids": [(6, 0, cls.member_user.ids)],
            }
        )

    def _activity(self, name="Prepare Network", **values):
        vals = {
            "name": name,
            "event_id": self.event.id,
            "committee_id": self.committee.id,
            "responsible_id": self.member_user.id,
            "priority": "high",
            "phase": "before",
            "start_date": self.today,
            "due_date": self.today + timedelta(days=2),
        }
        vals.update(values)
        return self.env["ems.activity"].create(vals)

    def test_activity_fields_deadlines_dependencies_and_notifications(self):
        overdue = self._activity(
            "Overdue Setup",
            start_date=self.today - timedelta(days=3),
            due_date=self.today - timedelta(days=1),
            readiness_item=True,
        )
        due_soon = self._activity("Due Soon Setup")
        dependent = self._activity("Dependent Setup", dependency_ids=[(4, overdue.id)])

        self.assertNotEqual(overdue.activity_code, "New")
        self.assertTrue(overdue.is_overdue)
        self.assertTrue(due_soon.is_due_soon)
        self.assertEqual(overdue.priority, "high")
        self.assertEqual(overdue.phase, "before")
        self.assertTrue(overdue.activity_ids, "Assignment should schedule an Odoo activity.")

        self.env["ems.activity"]._cron_deadline_notifications()
        self.assertTrue(overdue.overdue_notified)
        self.assertTrue(due_soon.due_soon_notified)

        with self.assertRaises(ValidationError):
            dependent.action_complete()
        overdue.action_start()
        overdue.action_mark_delayed()
        overdue.action_complete()
        dependent.action_complete()
        self.assertEqual(dependent.status, "completed")

        with self.assertRaises(ValidationError):
            self._activity(
                "Invalid Dates",
                start_date=self.today + timedelta(days=2),
                due_date=self.today,
            )

    def test_guest_badge_qr_checkin_and_duplicate_prevention(self):
        guest = self.env["ems.guest"].create(
            {
                "name": "VIP Guest",
                "event_id": self.event.id,
                "organization": "Example Org",
                "position": "Director",
                "email": "vip@example.com",
                "phone": "+251900000000",
                "category": "vip",
            }
        )
        guest.action_invite()
        guest.action_confirm()
        self.assertEqual(guest.invitation_status, "confirmed")
        self.assertTrue(guest.invited_on)
        self.assertTrue(guest.responded_on)

        badge = self.env["ems.badge"].create(
            {
                "event_id": self.event.id,
                "guest_id": guest.id,
                "category_id": self.env.ref("event_management_system.badge_category_vip").id,
            }
        )
        self.assertTrue(badge.badge_code)
        self.assertTrue(badge.qr_image)
        self.assertEqual(badge.registration_id.ems_guest_id, guest)
        badge.action_generate()
        badge.action_print()
        self.assertEqual(badge.status, "printed")
        self.assertEqual(badge.print_count, 1)
        badge_report = self.env.ref("event_management_system.action_report_ems_badge")
        badge_html, badge_format = badge_report._render_qweb_html(
            badge_report.report_name, badge.ids
        )
        self.assertEqual(badge_format, "html")
        self.assertIn(b"QR Code", badge_html)

        registration = badge.registration_id.with_context(ems_checkin_method="qr")
        registration.action_set_done()
        self.assertEqual(registration.state, "done")
        self.assertEqual(badge.status, "issued")
        self.assertEqual(registration.ems_checkin_log_ids[-1].result, "accepted")
        with self.assertRaises(UserError):
            registration.action_set_done()

        registration.action_authorized_reentry("Participant briefly exited")
        self.assertIn("reentry", registration.ems_checkin_log_ids.mapped("result"))
        corrected = fields.Datetime.now() - timedelta(minutes=5)
        registration.action_correct_attendance(corrected, "Scanner clock correction")
        self.assertEqual(registration.date_closed, corrected)
        self.assertIn("corrected", registration.ems_checkin_log_ids.mapped("result"))

    def test_incident_workflow_dashboard_and_event_closure(self):
        readiness = self._activity("Readiness Review", readiness_item=True)
        self.env["ems.event.role"].create(
            {"event_id": self.event.id, "user_id": self.technician.id, "role": "technology"}
        )
        incident = self.env["ems.incident"].create(
            {
                "event_id": self.event.id,
                "description": "Registration network unavailable",
                "location": "Main gate",
                "priority": "critical",
                "assigned_id": self.technician.id,
            }
        )
        self.assertNotEqual(incident.incident_code, "New")
        self.assertEqual(self.event.critical_incident_count, 1)
        self.assertEqual(self.event.readiness_state, "at_risk")
        self.assertTrue(self.event.readiness_alert_active)
        self.assertTrue(
            self.env["mail.message"].search(
                [
                    ("model", "=", "event.event"),
                    ("res_id", "=", self.event.id),
                    ("subject", "=", "Event readiness at risk"),
                ],
                limit=1,
            )
        )
        with self.assertRaises(UserError):
            self.event.action_go_live()

        incident.action_assign()
        incident.action_investigate()
        incident.resolution = "Replaced failed network switch"
        incident.action_resolve()
        incident.action_verify()
        incident.action_close()
        readiness.action_complete()
        self.assertEqual(incident.status, "closed")
        self.assertEqual(self.event.readiness_state, "ready")
        self.assertFalse(self.event.readiness_alert_active)

        self.event.action_start_preparation()
        self.event.action_readiness_review()
        self.event.action_go_live()
        self.event.action_start_closure()
        with self.assertRaises(UserError):
            self.event.action_close_event()
        self.event.write(
            {
                "attendance_finalized": True,
                "reports_collected": True,
                "final_report_approved": True,
                "final_report": "All objectives achieved.",
                "lessons_learned": "Add redundant access switches.",
            }
        )
        self.event.action_close_event()
        self.assertEqual(self.event.management_state, "closed")

    def test_reports_and_audit_trail(self):
        guest = self.env["ems.guest"].create(
            {
                "name": "Audited Guest",
                "event_id": self.event.id,
                "email": "private@example.com",
                "phone": "+251911111111",
            }
        )
        guest.action_confirm()
        logs = self.env["ems.audit.log"].search(
            [("model_name", "=", "ems.guest"), ("record_id", "=", guest.id)]
        )
        self.assertTrue(logs)
        self.assertTrue(any('"email": "***"' in (log.after_values or "") for log in logs))
        self.assertTrue(any(log.action == "status" for log in logs))

        report = self.env.ref("event_management_system.action_report_ems_final_event")
        content, content_type = report._render_qweb_html(report.report_name, self.event.ids)
        self.assertEqual(content_type, "html")
        self.assertIn(b"Final Event Report", content)
        self.assertIn(b"Executive Dashboard", content)


class TestCommitteeReport(TransactionCase):
    def test_committee_report_submission(self):
        event = self.env["event.event"].create(
            {
                "name": "Report Event",
                "date_begin": fields.Datetime.now() + timedelta(days=2),
                "date_end": fields.Datetime.now() + timedelta(days=3),
            }
        )
        lead = self.env["res.users"].create({"name": "Report Lead", "login": "ems_report_lead"})
        committee = self.env["ems.committee"].create(
            {"name": "Protocol", "event_id": event.id, "lead_id": lead.id}
        )
        report = self.env["ems.committee.report"].create(
            {
                "event_id": event.id,
                "committee_id": committee.id,
                "summary": "Committee work completed.",
                "lessons_learned": "Confirm suppliers earlier.",
            }
        )
        report.action_submit()
        self.assertEqual(report.state, "submitted")
        self.assertTrue(report.submitted_on)
        report.action_accept()
        self.assertEqual(report.state, "accepted")
