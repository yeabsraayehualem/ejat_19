from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class TechnicalIncident(models.Model):
    _name = "ems.incident"
    _description = "Technical Incident"
    _inherit = ["mail.thread", "mail.activity.mixin", "ems.audit.mixin"]
    _order = "priority, opened_on desc"
    _audit_fields = (
        "incident_code",
        "event_id",
        "description",
        "location",
        "priority",
        "assigned_id",
        "status",
        "resolution",
        "opened_on",
        "closed_on",
    )

    incident_code = fields.Char(default="New", readonly=True, copy=False, index=True)
    event_id = fields.Many2one("event.event", required=True, index=True, tracking=True, ondelete="cascade")
    description = fields.Text(required=True, tracking=True)
    location = fields.Char(required=True, tracking=True)
    priority = fields.Selection(
        [("critical", "Critical"), ("high", "High"), ("medium", "Medium"), ("low", "Low")],
        default="medium",
        required=True,
        tracking=True,
        index=True,
    )
    assigned_id = fields.Many2one("res.users", tracking=True, index=True, domain=[("share", "=", False)])
    status = fields.Selection(
        [
            ("logged", "Logged"),
            ("assigned", "Assigned"),
            ("investigation", "Investigation"),
            ("resolved", "Resolved"),
            ("verified", "Verified"),
            ("closed", "Closed"),
        ],
        default="logged",
        required=True,
        tracking=True,
        index=True,
    )
    resolution = fields.Text(tracking=True)
    opened_on = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True)
    closed_on = fields.Datetime(readonly=True)

    _incident_code_uniq = models.Constraint(
        "unique(incident_code)", "Incident ID must be unique."
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("incident_code") or vals["incident_code"] == "New":
                vals["incident_code"] = self.env["ir.sequence"].next_by_code("ems.incident") or "New"
        incidents = super().create(vals_list)
        incidents._notify_critical()
        incidents.mapped("event_id")._notify_readiness_alert()
        return incidents

    def write(self, vals):
        events = self.mapped("event_id")
        result = super().write(vals)
        if vals.get("priority") == "critical":
            self._notify_critical()
        (events | self.mapped("event_id"))._notify_readiness_alert()
        return result

    def _notify_critical(self):
        for incident in self.filtered(lambda item: item.priority == "critical" and item.status != "closed"):
            recipients = incident.event_id.role_assignment_ids.filtered(
                lambda assignment: assignment.active and assignment.role in ("event_admin", "technology")
            ).user_id.partner_id
            if recipients:
                incident.message_notify(
                    subject=_("Critical technical incident"),
                    body=_("Critical incident %s was reported at %s.", incident.incident_code, incident.location),
                    partner_ids=recipients.ids,
                )

    def action_assign(self):
        if any(not incident.assigned_id for incident in self):
            raise UserError(_("Assign a technical person before moving to Assigned."))
        self.write({"status": "assigned"})
        return True

    def action_investigate(self):
        self.write({"status": "investigation"})
        return True

    def action_resolve(self):
        if any(not incident.resolution for incident in self):
            raise UserError(_("Enter the resolution before resolving the incident."))
        self.write({"status": "resolved"})
        return True

    def action_verify(self):
        self.write({"status": "verified"})
        return True

    def action_close(self):
        if any(incident.status != "verified" for incident in self):
            raise UserError(_("Verify the resolution before closing the incident."))
        self.write({"status": "closed", "closed_on": fields.Datetime.now()})
        return True
