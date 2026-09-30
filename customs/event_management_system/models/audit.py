import json

from odoo import api, fields, models
from odoo.exceptions import AccessError


class EventAuditLog(models.Model):
    _name = "ems.audit.log"
    _description = "Event Audit Log"
    _order = "create_date desc, id desc"

    event_id = fields.Many2one("event.event", index=True, ondelete="set null")
    user_id = fields.Many2one(
        "res.users", required=True, index=True, default=lambda self: self.env.user
    )
    action = fields.Selection(
        [
            ("create", "Create"),
            ("update", "Update"),
            ("status", "Status Change"),
            ("delete", "Delete"),
            ("check_in", "Check-in"),
            ("correction", "Correction"),
            ("print", "Print"),
        ],
        required=True,
        index=True,
    )
    model_name = fields.Char(required=True, index=True)
    record_id = fields.Integer(required=True, index=True)
    record_name = fields.Char(required=True)
    before_values = fields.Text()
    after_values = fields.Text()
    details = fields.Text()

    def write(self, vals):
        if not self.env.su:
            raise AccessError("Audit records are immutable.")
        return super().write(vals)

    def unlink(self):
        if not self.env.su:
            raise AccessError("Audit records cannot be deleted.")
        return super().unlink()


class EventAuditMixin(models.AbstractModel):
    _name = "ems.audit.mixin"
    _description = "Event Audit Mixin"

    _audit_fields = ()
    _audit_status_fields = (
        "state",
        "status",
        "management_state",
        "invitation_status",
        "exception",
    )

    def _audit_event(self):
        self.ensure_one()
        if self._name == "event.event":
            return self
        if "event_id" in self._fields:
            return self.event_id
        return self.env["event.event"]

    @api.model
    def _audit_mask(self, values):
        protected = ("email", "phone", "password", "token")
        return {
            key: "***" if any(item in key.lower() for item in protected) and value else value
            for key, value in values.items()
        }

    def _audit_snapshot(self, requested_fields=None):
        self.ensure_one()
        names = requested_fields or self._audit_fields
        names = [name for name in names if name in self._fields]
        if not names:
            return {}
        return self._audit_mask(self.read(names)[0])

    def _create_audit_log(self, action, before=None, after=None, details=None):
        self.ensure_one()
        event = self._audit_event()
        self.env["ems.audit.log"].sudo().create(
            {
                "event_id": event.id if event else False,
                "user_id": self.env.user.id,
                "action": action,
                "model_name": self._name,
                "record_id": self.id,
                "record_name": self.display_name,
                "before_values": json.dumps(before or {}, default=str, sort_keys=True),
                "after_values": json.dumps(after or {}, default=str, sort_keys=True),
                "details": details,
            }
        )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get("skip_ems_audit"):
            for record, vals in zip(records, vals_list):
                fields_to_log = set(record._audit_fields) | set(vals)
                record._create_audit_log(
                    "create", after=record._audit_snapshot(fields_to_log)
                )
        return records

    def write(self, vals):
        if self.env.context.get("skip_ems_audit"):
            return super().write(vals)
        fields_to_log = set(self._audit_fields) | set(vals)
        before = {record.id: record._audit_snapshot(fields_to_log) for record in self}
        result = super().write(vals)
        action = "status" if set(vals) & set(self._audit_status_fields) else "update"
        for record in self:
            record._create_audit_log(
                action,
                before=before[record.id],
                after=record._audit_snapshot(fields_to_log),
            )
        return result

    def unlink(self):
        if not self.env.context.get("skip_ems_audit"):
            for record in self:
                record._create_audit_log(
                    "delete", before=record._audit_snapshot(record._audit_fields)
                )
        return super().unlink()
