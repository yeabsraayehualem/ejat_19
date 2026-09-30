from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


ROLE_SELECTION = [
    ("event_admin", "Event Administrator"),
    ("coordinator", "Event Coordinator"),
    ("technology", "Digital Technology Lead"),
    ("registration", "Registration Officer"),
    ("guest_team", "Guest Management Team"),
    ("viewer", "Management / Viewer"),
]


class EventRoleAssignment(models.Model):
    _name = "ems.event.role"
    _description = "Event Role Assignment"
    _inherit = ["ems.audit.mixin"]
    _order = "event_id, role, user_id"
    _audit_fields = ("event_id", "user_id", "role", "active")

    event_id = fields.Many2one("event.event", required=True, index=True, ondelete="cascade")
    user_id = fields.Many2one(
        "res.users", required=True, index=True, domain=[("share", "=", False)]
    )
    role = fields.Selection(ROLE_SELECTION, required=True, index=True)
    active = fields.Boolean(default=True)

    _event_user_role_uniq = models.Constraint(
        "unique(event_id, user_id, role)",
        "A user can only hold a role once for an event.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        assignments = super().create(vals_list)
        assignments._ensure_user_groups()
        return assignments

    def write(self, vals):
        result = super().write(vals)
        if set(vals) & {"user_id", "role", "active"}:
            self._ensure_user_groups()
        return result

    def _ensure_user_groups(self):
        group_map = {
            "event_admin": "event_management_system.group_ems_event_admin",
            "coordinator": "event_management_system.group_ems_coordinator",
            "technology": "event_management_system.group_ems_technology",
            "registration": "event_management_system.group_ems_registration",
            "guest_team": "event_management_system.group_ems_guest",
            "viewer": "event_management_system.group_ems_viewer",
        }
        for assignment in self.filtered("active"):
            group = self.env.ref(group_map[assignment.role])
            assignment.user_id.sudo().write({"group_ids": [(4, group.id)]})


class EventEvent(models.Model):
    _name = "event.event"
    _inherit = ["event.event", "ems.audit.mixin"]
    _audit_fields = (
        "name",
        "date_begin",
        "date_end",
        "management_state",
        "attendance_finalized",
        "reports_collected",
        "final_report_approved",
        "readiness_alert_active",
    )

    management_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("preparation", "Preparation"),
            ("readiness", "Readiness Review"),
            ("live", "Live"),
            ("closure", "Closure"),
            ("closed", "Closed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    due_soon_days = fields.Integer(default=3, required=True)
    role_assignment_ids = fields.One2many("ems.event.role", "event_id", string="Event Roles")
    committee_ids = fields.One2many("ems.committee", "event_id")
    event_activity_ids = fields.One2many("ems.activity", "event_id", string="Event Activities")
    member_ids = fields.One2many("ems.member", "event_id")
    guest_ids = fields.One2many("ems.guest", "event_id")
    badge_ids = fields.One2many("ems.badge", "event_id")
    incident_ids = fields.One2many("ems.incident", "event_id")
    committee_report_ids = fields.One2many("ems.committee.report", "event_id")
    attendance_finalized = fields.Boolean(tracking=True)
    reports_collected = fields.Boolean(tracking=True)
    lessons_learned = fields.Html()
    final_report = fields.Html()
    final_report_approved = fields.Boolean(tracking=True)
    closure_override_reason = fields.Text(readonly=True)
    readiness_alert_active = fields.Boolean(copy=False)

    committee_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    activity_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    activity_completed_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    activity_progress_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    activity_not_started_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    activity_delayed_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    activity_overdue_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    activity_due_soon_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    guest_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    guest_confirmed_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    registered_member_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    registered_guest_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    badge_generated_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    badge_printed_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    badge_issued_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    checked_in_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    open_incident_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    critical_incident_count = fields.Integer(compute="_compute_management_dashboard", compute_sudo=True)
    readiness_percent = fields.Float(compute="_compute_management_dashboard", compute_sudo=True)
    readiness_state = fields.Selection(
        [("not_ready", "Not Ready"), ("in_progress", "In Progress"), ("at_risk", "At Risk"), ("ready", "Ready")],
        compute="_compute_management_dashboard",
        compute_sudo=True,
    )

    @api.constrains("due_soon_days")
    def _check_due_soon_days(self):
        if any(event.due_soon_days < 1 for event in self):
            raise ValidationError(_("Due-soon days must be at least one."))

    def _compute_management_dashboard(self):
        today = fields.Date.context_today(self)
        Activity = self.env["ems.activity"].sudo()
        Guest = self.env["ems.guest"].sudo()
        Registration = self.env["event.registration"].sudo()
        Badge = self.env["ems.badge"].sudo()
        Incident = self.env["ems.incident"].sudo()
        Committee = self.env["ems.committee"].sudo()
        for event in self:
            base = [("event_id", "=", event.id)]
            event.committee_count = Committee.search_count(base)
            event.activity_count = Activity.search_count(base)
            event.activity_completed_count = Activity.search_count(base + [("status", "=", "completed")])
            event.activity_progress_count = Activity.search_count(base + [("status", "=", "in_progress")])
            event.activity_not_started_count = Activity.search_count(base + [("status", "=", "not_started")])
            event.activity_delayed_count = Activity.search_count(base + [("exception", "=", "delayed")])
            event.activity_overdue_count = Activity.search_count(
                base + [("status", "!=", "completed"), ("due_date", "<", today)]
            )
            due_limit = fields.Date.add(today, days=event.due_soon_days)
            event.activity_due_soon_count = Activity.search_count(
                base
                + [
                    ("status", "!=", "completed"),
                    ("due_date", ">=", today),
                    ("due_date", "<=", due_limit),
                ]
            )
            event.guest_count = Guest.search_count(base)
            event.guest_confirmed_count = Guest.search_count(base + [("invitation_status", "=", "confirmed")])
            event.registered_member_count = Registration.search_count(
                base + [("ems_member_id", "!=", False), ("state", "in", ["open", "done"])]
            )
            event.registered_guest_count = Registration.search_count(
                base + [("ems_guest_id", "!=", False), ("state", "in", ["open", "done"])]
            )
            event.badge_generated_count = Badge.search_count(base + [("status", "in", ["generated", "printed", "issued"])])
            event.badge_printed_count = Badge.search_count(base + [("status", "in", ["printed", "issued"])])
            event.badge_issued_count = Badge.search_count(base + [("status", "=", "issued")])
            event.checked_in_count = Registration.search_count(base + [("state", "=", "done")])
            event.open_incident_count = Incident.search_count(base + [("status", "!=", "closed")])
            event.critical_incident_count = Incident.search_count(
                base + [("priority", "=", "critical"), ("status", "!=", "closed")]
            )
            readiness = Activity.search(base + [("readiness_item", "=", True)])
            completed = len(readiness.filtered(lambda item: item.status == "completed"))
            event.readiness_percent = 100.0 * completed / len(readiness) if readiness else 0.0
            has_blocker = bool(
                readiness.filtered(lambda item: item.is_overdue and item.status != "completed")
            ) or bool(event.critical_incident_count)
            if has_blocker:
                event.readiness_state = "at_risk"
            elif readiness and completed == len(readiness):
                event.readiness_state = "ready"
            elif completed:
                event.readiness_state = "in_progress"
            else:
                event.readiness_state = "not_ready"

    def _set_management_state(self, state):
        self.ensure_one()
        self.write({"management_state": state})
        return True

    def _notify_readiness_alert(self):
        for event in self:
            secure_event = event.sudo()
            secure_event.invalidate_recordset(["readiness_state"])
            recipients = secure_event.role_assignment_ids.filtered(
                lambda assignment: assignment.active
                and assignment.role in ("event_admin", "coordinator", "technology")
            ).user_id.partner_id
            at_risk = secure_event.readiness_state == "at_risk"
            if at_risk and recipients and not secure_event.readiness_alert_active:
                secure_event.message_notify(
                    subject=_("Event readiness at risk"),
                    body=_(
                        "Event %s requires attention before it can go live. "
                        "Review overdue readiness activities and critical incidents.",
                        secure_event.name,
                    ),
                    partner_ids=recipients.ids,
                )
                secure_event.with_context(skip_ems_audit=True).write(
                    {"readiness_alert_active": True}
                )
            elif not at_risk and secure_event.readiness_alert_active:
                secure_event.with_context(skip_ems_audit=True).write(
                    {"readiness_alert_active": False}
                )

    def action_start_preparation(self):
        return self._set_management_state("preparation")

    def action_readiness_review(self):
        return self._set_management_state("readiness")

    def action_go_live(self):
        self.ensure_one()
        if self.readiness_state == "at_risk":
            raise UserError(_("Resolve readiness blockers before starting the event."))
        return self._set_management_state("live")

    def action_start_closure(self):
        return self._set_management_state("closure")

    def action_close_event(self):
        self.ensure_one()
        problems = []
        if self.event_activity_ids.filtered(lambda item: item.status != "completed"):
            problems.append(_("all activities must be completed"))
        if self.incident_ids.filtered(lambda item: item.status != "closed"):
            problems.append(_("all incidents must be closed"))
        if not self.attendance_finalized:
            problems.append(_("attendance must be finalized"))
        if not self.reports_collected:
            problems.append(_("committee reports must be collected"))
        if not self.final_report_approved:
            problems.append(_("the final report must be approved"))
        if problems:
            raise UserError(_("The event cannot be closed: %s.") % ", ".join(problems))
        return self._set_management_state("closed")

    def action_force_close_event(self, reason=None):
        self.ensure_one()
        if not reason:
            raise UserError(_("An override reason is required."))
        self.write({"closure_override_reason": reason, "management_state": "closed"})
        return True

    def action_cancel_management(self):
        return self._set_management_state("cancelled")

    def action_open_management_records(self, model, domain=None):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env[model]._description,
            "res_model": model,
            "view_mode": "list,form,pivot,graph" if model in {"ems.activity", "ems.guest", "ems.badge", "ems.incident"} else "list,form",
            "domain": [("event_id", "=", self.id)] + (domain or []),
            "context": {"default_event_id": self.id},
        }

    def action_open_committees(self):
        return self.action_open_management_records("ems.committee")

    def action_open_activities(self):
        return self.action_open_management_records("ems.activity")

    def action_open_guests(self):
        return self.action_open_management_records("ems.guest")

    def action_open_badges(self):
        return self.action_open_management_records("ems.badge")

    def action_open_incidents(self):
        return self.action_open_management_records("ems.incident")
