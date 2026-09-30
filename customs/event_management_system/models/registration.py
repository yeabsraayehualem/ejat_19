from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class EventRegistration(models.Model):
    _name = "event.registration"
    _inherit = ["event.registration", "ems.audit.mixin"]
    _audit_fields = (
        "event_id",
        "ems_member_id",
        "ems_guest_id",
        "name",
        "email",
        "phone",
        "company_name",
        "state",
        "date_closed",
    )

    ems_member_id = fields.Many2one("ems.member", string="Event Member", index=True, ondelete="cascade")
    ems_guest_id = fields.Many2one("ems.guest", string="Event Guest", index=True, ondelete="cascade")
    ems_badge_ids = fields.One2many("ems.badge", "registration_id")
    ems_checkin_log_ids = fields.One2many("ems.checkin.log", "registration_id")

    @api.constrains("event_id", "ems_member_id", "ems_guest_id")
    def _check_ems_participant(self):
        for registration in self:
            if registration.ems_member_id and registration.ems_guest_id:
                raise ValidationError(_("A registration cannot be linked to both a member and a guest."))
            participant = registration.ems_member_id or registration.ems_guest_id
            if participant and participant.event_id != registration.event_id:
                raise ValidationError(_("The participant and registration must belong to the same event."))

    def write(self, vals):
        protected = {"name", "email", "phone", "company_name", "date_closed"}
        if set(vals) & protected and any(reg.ems_member_id or reg.ems_guest_id for reg in self):
            permitted = any(
                self.env.user.has_group(group)
                for group in [
                    "event_management_system.group_ems_system_admin",
                    "event_management_system.group_ems_event_admin",
                    "event_management_system.group_ems_technology",
                    "event_management_system.group_ems_registration",
                ]
            )
            if not permitted and not self.env.context.get("ems_internal_update"):
                raise AccessError(_("Only authorized registration staff may correct participant records."))
        return super().write(vals)

    def action_set_done(self):
        for registration in self:
            self.env.cr.execute(
                "SELECT state FROM event_registration WHERE id = %s FOR UPDATE",
                [registration.id],
            )
            state = self.env.cr.fetchone()[0]
            registration.invalidate_recordset(["state"])
            if state == "done":
                raise UserError(_("This participant is already checked in."))
            super(EventRegistration, registration).action_set_done()
            badge = registration.ems_badge_ids[:1]
            if badge and badge.status in ("generated", "printed"):
                badge.action_issue()
            self.env["ems.checkin.log"].sudo().create(
                {
                    "event_id": registration.event_id.id,
                    "registration_id": registration.id,
                    "result": "accepted",
                    "method": self.env.context.get("ems_checkin_method", "manual"),
                    "user_id": self.env.user.id,
                }
            )
            registration._create_audit_log("check_in", details=_("Participant checked in."))
        return True

    @api.model
    def register_attendee(self, barcode, event_id):
        registration = self.search([("barcode", "=", barcode)], limit=1)
        result = super().register_attendee(barcode, event_id)
        if registration and result.get("status") == "already_registered":
            self.env["ems.checkin.log"].sudo().create(
                {
                    "event_id": registration.event_id.id,
                    "registration_id": registration.id,
                    "result": "duplicate_blocked",
                    "method": "qr",
                    "user_id": self.env.user.id,
                }
            )
        elif not registration and event_id:
            self.env["ems.checkin.log"].sudo().create(
                {
                    "event_id": event_id,
                    "result": "invalid",
                    "method": "qr",
                    "user_id": self.env.user.id,
                    "reason": barcode,
                }
            )
        return result

    def action_authorized_reentry(self, reason=None):
        if not reason:
            raise UserError(_("A re-entry reason is required."))
        if not (self.env.su or self.env.user.has_group("base.group_system") or any(
            self.env.user.has_group(group)
            for group in [
                "event_management_system.group_ems_system_admin",
                "event_management_system.group_ems_event_admin",
                "event_management_system.group_ems_technology",
            ]
        )):
            raise AccessError(_("You are not authorized to approve duplicate check-in."))
        for registration in self:
            if registration.state != "done":
                raise UserError(_("The participant has not checked in yet."))
            self.env["ems.checkin.log"].sudo().create(
                {
                    "event_id": registration.event_id.id,
                    "registration_id": registration.id,
                    "result": "reentry",
                    "method": "manual",
                    "reason": reason,
                    "user_id": self.env.user.id,
                }
            )
            registration._create_audit_log("check_in", details=_("Authorized re-entry: %s", reason))
        return True

    def action_correct_attendance(self, attended_on=None, reason=None):
        if not reason:
            raise UserError(_("A correction reason is required."))
        if not (self.env.su or self.env.user.has_group("base.group_system") or any(
            self.env.user.has_group(group)
            for group in [
                "event_management_system.group_ems_system_admin",
                "event_management_system.group_ems_event_admin",
                "event_management_system.group_ems_technology",
                "event_management_system.group_ems_registration",
            ]
        )):
            raise AccessError(_("You are not authorized to correct attendance."))
        attended_on = attended_on or fields.Datetime.now()
        for registration in self:
            old_date = registration.date_closed
            registration.with_context(ems_internal_update=True).write(
                {"state": "done", "date_closed": attended_on}
            )
            self.env["ems.checkin.log"].sudo().create(
                {
                    "event_id": registration.event_id.id,
                    "registration_id": registration.id,
                    "result": "corrected",
                    "method": "manual",
                    "reason": reason,
                    "previous_datetime": old_date,
                    "user_id": self.env.user.id,
                }
            )
            registration._create_audit_log("correction", details=reason)
        return True


class EventCheckinLog(models.Model):
    _name = "ems.checkin.log"
    _description = "Event Check-in Log"
    _order = "create_date desc, id desc"

    event_id = fields.Many2one("event.event", required=True, index=True, ondelete="cascade")
    registration_id = fields.Many2one("event.registration", index=True, ondelete="set null")
    user_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user)
    method = fields.Selection([("qr", "QR Scan"), ("manual", "Manual Search")], required=True)
    result = fields.Selection(
        [
            ("accepted", "Accepted"),
            ("duplicate_blocked", "Duplicate Blocked"),
            ("reentry", "Authorized Re-entry"),
            ("invalid", "Invalid QR"),
            ("corrected", "Corrected"),
        ],
        required=True,
        index=True,
    )
    reason = fields.Text()
    previous_datetime = fields.Datetime()

    def write(self, vals):
        if not self.env.su:
            raise AccessError(_("Check-in logs are immutable."))
        return super().write(vals)

    def unlink(self):
        if not self.env.su:
            raise AccessError(_("Check-in logs cannot be deleted."))
        return super().unlink()
