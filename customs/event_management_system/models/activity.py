from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class EventActivity(models.Model):
    _name = "ems.activity"
    _description = "Event Activity"
    _inherit = ["mail.thread", "mail.activity.mixin", "ems.audit.mixin"]
    _order = "due_date, priority, id"
    _audit_fields = (
        "activity_code",
        "name",
        "event_id",
        "committee_id",
        "responsible_id",
        "priority",
        "phase",
        "status",
        "exception",
        "start_date",
        "due_date",
        "dependency_ids",
        "remarks",
        "readiness_item",
    )

    activity_code = fields.Char(default="New", readonly=True, copy=False, index=True)
    name = fields.Char(required=True, tracking=True, index="trigram")
    description = fields.Html()
    event_id = fields.Many2one(
        "event.event", required=True, tracking=True, index=True, ondelete="cascade"
    )
    committee_id = fields.Many2one(
        "ems.committee",
        required=True,
        tracking=True,
        index=True,
        ondelete="restrict",
        domain="[('event_id', '=', event_id)]",
    )
    responsible_id = fields.Many2one(
        "res.users", required=True, tracking=True, index=True, domain=[("share", "=", False)]
    )
    priority = fields.Selection(
        [("high", "High"), ("medium", "Medium"), ("low", "Low")],
        default="medium",
        required=True,
        tracking=True,
        index=True,
    )
    phase = fields.Selection(
        [("before", "Before Event"), ("during", "During Event"), ("after", "After Event")],
        default="before",
        required=True,
        tracking=True,
        index=True,
    )
    status = fields.Selection(
        [("not_started", "Not Started"), ("in_progress", "In Progress"), ("completed", "Completed")],
        default="not_started",
        required=True,
        tracking=True,
        index=True,
    )
    exception = fields.Selection(
        [("none", "None"), ("delayed", "Delayed"), ("issue", "Issue")],
        default="none",
        required=True,
        tracking=True,
        index=True,
    )
    start_date = fields.Date(required=True, tracking=True)
    due_date = fields.Date(required=True, tracking=True, index=True)
    dependency_ids = fields.Many2many(
        "ems.activity",
        "ems_activity_dependency_rel",
        "activity_id",
        "dependency_id",
        string="Dependencies",
        domain="[('event_id', '=', event_id), ('id', '!=', id)]",
    )
    remarks = fields.Text(tracking=True)
    readiness_item = fields.Boolean(string="Readiness Critical", tracking=True)
    is_overdue = fields.Boolean(compute="_compute_deadline_state", search="_search_is_overdue")
    is_due_soon = fields.Boolean(compute="_compute_deadline_state", search="_search_is_due_soon")
    due_soon_notified = fields.Boolean(copy=False)
    overdue_notified = fields.Boolean(copy=False)

    _activity_code_uniq = models.Constraint(
        "unique(activity_code)", "Activity ID must be unique."
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("activity_code") or vals["activity_code"] == "New":
                vals["activity_code"] = self.env["ir.sequence"].next_by_code("ems.activity") or "New"
        records = super().create(vals_list)
        records._notify_assignment()
        records.mapped("event_id")._notify_readiness_alert()
        return records

    def write(self, vals):
        events = self.mapped("event_id")
        if self.env.user.has_group("event_management_system.group_ems_committee_member") and not any(
            self.env.user.has_group(group)
            for group in [
                "event_management_system.group_ems_event_admin",
                "event_management_system.group_ems_coordinator",
                "event_management_system.group_ems_committee_lead",
                "event_management_system.group_ems_technology",
            ]
        ):
            allowed = {"status", "exception", "remarks"}
            if set(vals) - allowed:
                raise AccessError(_("Committee members may only update status, exception and remarks."))
        result = super().write(vals)
        if "responsible_id" in vals:
            self._notify_assignment()
        (events | self.mapped("event_id"))._notify_readiness_alert()
        return result

    def unlink(self):
        events = self.mapped("event_id")
        result = super().unlink()
        events._notify_readiness_alert()
        return result

    @api.depends("due_date", "status", "event_id.due_soon_days")
    def _compute_deadline_state(self):
        today = fields.Date.context_today(self)
        for activity in self:
            activity.is_overdue = bool(
                activity.due_date and activity.due_date < today and activity.status != "completed"
            )
            limit = fields.Date.add(today, days=activity.event_id.due_soon_days or 3)
            activity.is_due_soon = bool(
                activity.due_date
                and today <= activity.due_date <= limit
                and activity.status != "completed"
            )

    def _search_is_overdue(self, operator, value):
        today = fields.Date.context_today(self)
        positive = operator in ("=", "==") and value or operator == "!=" and not value
        domain = [("due_date", "<", today), ("status", "!=", "completed")]
        return domain if positive else ["!", *domain]

    def _search_is_due_soon(self, operator, value):
        today = fields.Date.context_today(self)
        limit = fields.Date.add(today, days=3)
        positive = operator in ("=", "==") and value or operator == "!=" and not value
        domain = [("due_date", ">=", today), ("due_date", "<=", limit), ("status", "!=", "completed")]
        return domain if positive else ["!", *domain]

    @api.constrains("start_date", "due_date")
    def _check_dates(self):
        if any(activity.due_date < activity.start_date for activity in self):
            raise ValidationError(_("The due date cannot be before the start date."))

    @api.constrains("event_id", "committee_id", "dependency_ids")
    def _check_relationships(self):
        for activity in self:
            if activity.committee_id.event_id != activity.event_id:
                raise ValidationError(_("The activity and committee must belong to the same event."))
            if activity in activity.dependency_ids:
                raise ValidationError(_("An activity cannot depend on itself."))
            if any(dependency.event_id != activity.event_id for dependency in activity.dependency_ids):
                raise ValidationError(_("Dependencies must belong to the same event."))
            visited = set()

            def visit(item):
                if item.id in visited:
                    return
                visited.add(item.id)
                if activity in item.dependency_ids:
                    raise ValidationError(_("Activity dependencies cannot contain cycles."))
                for dependency in item.dependency_ids:
                    visit(dependency)

            for dependency in activity.dependency_ids:
                visit(dependency)

    @api.constrains("status", "dependency_ids")
    def _check_completion_dependencies(self):
        for activity in self.filtered(lambda item: item.status == "completed"):
            if activity.dependency_ids.filtered(lambda item: item.status != "completed"):
                raise ValidationError(_("Complete all dependencies before completing this activity."))

    def _notify_assignment(self):
        for activity in self.filtered("responsible_id"):
            activity.activity_schedule(
                "mail.mail_activity_data_todo",
                user_id=activity.responsible_id.id,
                date_deadline=activity.due_date,
                summary=_("Assigned event activity: %s", activity.name),
            )

    @api.model
    def _cron_deadline_notifications(self):
        activities = self.search([("status", "!=", "completed")])
        for activity in activities:
            if activity.is_overdue and not activity.overdue_notified:
                activity.message_notify(
                    subject=_("Event activity overdue"),
                    body=_("Activity %s is overdue.", activity.display_name),
                    partner_ids=activity.responsible_id.partner_id.ids,
                )
                activity.with_context(skip_ems_audit=True).write({"overdue_notified": True})
            elif activity.is_due_soon and not activity.due_soon_notified:
                activity.message_notify(
                    subject=_("Event activity due soon"),
                    body=_("Activity %s is approaching its due date.", activity.display_name),
                    partner_ids=activity.responsible_id.partner_id.ids,
                )
                activity.with_context(skip_ems_audit=True).write({"due_soon_notified": True})

    def action_start(self):
        self.write({"status": "in_progress"})
        return True

    def action_complete(self):
        self.write({"status": "completed", "exception": "none"})
        return True

    def action_mark_delayed(self):
        self.write({"exception": "delayed"})
        return True

    def action_mark_issue(self):
        self.write({"exception": "issue"})
        return True
