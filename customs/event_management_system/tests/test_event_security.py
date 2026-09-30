from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestEventSecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.event_a = cls.env["event.event"].create(
            {
                "name": "Scoped Event A",
                "date_begin": fields.Datetime.now() + timedelta(days=1),
                "date_end": fields.Datetime.now() + timedelta(days=2),
            }
        )
        cls.event_b = cls.env["event.event"].create(
            {
                "name": "Scoped Event B",
                "date_begin": fields.Datetime.now() + timedelta(days=3),
                "date_end": fields.Datetime.now() + timedelta(days=4),
            }
        )
        cls.viewer = cls.env["res.users"].create(
            {"name": "EMS Viewer", "login": "ems_security_viewer"}
        )
        cls.member = cls.env["res.users"].create(
            {"name": "EMS Member", "login": "ems_security_member"}
        )
        cls.other = cls.env["res.users"].create(
            {"name": "Other Member", "login": "ems_security_other"}
        )
        cls.env["ems.event.role"].create(
            {"event_id": cls.event_a.id, "user_id": cls.viewer.id, "role": "viewer"}
        )
        cls.committee = cls.env["ems.committee"].create(
            {
                "name": "Security Committee",
                "event_id": cls.event_a.id,
                "lead_id": cls.other.id,
                "member_user_ids": [(6, 0, cls.member.ids)],
            }
        )
        cls.assigned = cls.env["ems.activity"].create(
            {
                "name": "Assigned Work",
                "event_id": cls.event_a.id,
                "committee_id": cls.committee.id,
                "responsible_id": cls.member.id,
                "start_date": fields.Date.today(),
                "due_date": fields.Date.today() + timedelta(days=1),
            }
        )
        cls.unassigned = cls.env["ems.activity"].create(
            {
                "name": "Other Work",
                "event_id": cls.event_a.id,
                "committee_id": cls.committee.id,
                "responsible_id": cls.other.id,
                "start_date": fields.Date.today(),
                "due_date": fields.Date.today() + timedelta(days=1),
            }
        )
        cls.guest = cls.env["ems.guest"].create(
            {"name": "Private Guest", "event_id": cls.event_a.id, "email": "private@example.com"}
        )

    def test_viewer_event_scope_and_pii_protection(self):
        visible = self.env["event.event"].with_user(self.viewer).search([])
        self.assertIn(self.event_a, visible)
        self.assertNotIn(self.event_b, visible)
        self.event_a.with_user(self.viewer).read(["readiness_percent", "guest_count"])
        with self.assertRaises(AccessError):
            self.guest.with_user(self.viewer).read(["name", "email"])

    def test_committee_member_only_sees_assigned_activities(self):
        visible = self.env["ems.activity"].with_user(self.member).search([])
        self.assertIn(self.assigned, visible)
        self.assertNotIn(self.unassigned, visible)
        self.assigned.with_user(self.member).write({"status": "in_progress", "remarks": "Started"})
        with self.assertRaises(AccessError):
            self.assigned.with_user(self.member).write({"name": "Unauthorized Rename"})

    def test_audit_log_is_immutable(self):
        admin = self.env["res.users"].create(
            {"name": "Event Admin", "login": "ems_security_admin"}
        )
        self.env["ems.event.role"].create(
            {"event_id": self.event_a.id, "user_id": admin.id, "role": "event_admin"}
        )
        log = self.env["ems.audit.log"].search([("event_id", "=", self.event_a.id)], limit=1)
        self.assertTrue(log)
        with self.assertRaises(AccessError):
            log.with_user(admin).write({"details": "Tampered"})
        with self.assertRaises(AccessError):
            log.with_user(admin).unlink()
