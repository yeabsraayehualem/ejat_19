from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class EventCommittee(models.Model):
    _name = "ems.committee"
    _description = "Event Committee"
    _inherit = ["mail.thread", "mail.activity.mixin", "ems.audit.mixin"]
    _order = "event_id, name"
    _audit_fields = ("name", "event_id", "lead_id", "member_user_ids", "active")

    name = fields.Char(required=True, tracking=True, index="trigram")
    event_id = fields.Many2one(
        "event.event", required=True, tracking=True, index=True, ondelete="cascade"
    )
    lead_id = fields.Many2one(
        "res.users", required=True, tracking=True, domain=[("share", "=", False)]
    )
    member_user_ids = fields.Many2many(
        "res.users",
        "ems_committee_user_rel",
        "committee_id",
        "user_id",
        string="Committee Members",
        domain=[("share", "=", False)],
    )
    participant_ids = fields.One2many("ems.member", "committee_id", string="Registered Members")
    event_activity_ids = fields.One2many("ems.activity", "committee_id", string="Event Activities")
    report_ids = fields.One2many("ems.committee.report", "committee_id")
    active = fields.Boolean(default=True)
    activity_count = fields.Integer(compute="_compute_activity_counts")
    completed_count = fields.Integer(compute="_compute_activity_counts")
    overdue_count = fields.Integer(compute="_compute_activity_counts")

    _event_committee_name_uniq = models.Constraint(
        "unique(event_id, name)", "Committee names must be unique per event."
    )

    @api.model_create_multi
    def create(self, vals_list):
        committees = super().create(vals_list)
        committees._ensure_committee_groups()
        return committees

    def write(self, vals):
        result = super().write(vals)
        if set(vals) & {"lead_id", "member_user_ids"}:
            self._ensure_committee_groups()
        return result

    def _ensure_committee_groups(self):
        lead_group = self.env.ref("event_management_system.group_ems_committee_lead")
        member_group = self.env.ref("event_management_system.group_ems_committee_member")
        for committee in self:
            committee.lead_id.sudo().write({"group_ids": [(4, lead_group.id)]})
            committee.member_user_ids.sudo().write({"group_ids": [(4, member_group.id)]})

    @api.depends("event_activity_ids.status", "event_activity_ids.due_date")
    def _compute_activity_counts(self):
        for committee in self:
            committee.activity_count = len(committee.event_activity_ids)
            committee.completed_count = len(
                committee.event_activity_ids.filtered(lambda item: item.status == "completed")
            )
            committee.overdue_count = len(committee.event_activity_ids.filtered("is_overdue"))

    @api.constrains("lead_id", "member_user_ids")
    def _check_lead_membership(self):
        for committee in self:
            if committee.lead_id in committee.member_user_ids:
                raise ValidationError(_("The committee lead must not be duplicated as a member."))


class EventMember(models.Model):
    _name = "ems.member"
    _description = "Event Member"
    _inherit = ["mail.thread", "mail.activity.mixin", "ems.audit.mixin"]
    _order = "event_id, name"
    _audit_fields = (
        "name",
        "event_id",
        "committee_id",
        "user_id",
        "organization",
        "position",
        "email",
        "phone",
        "active",
    )

    name = fields.Char(required=True, tracking=True, index="trigram")
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
    user_id = fields.Many2one("res.users", domain=[("share", "=", False)], tracking=True)
    organization = fields.Char()
    position = fields.Char()
    email = fields.Char(tracking=True)
    phone = fields.Char(tracking=True)
    active = fields.Boolean(default=True)
    registration_ids = fields.One2many("event.registration", "ems_member_id")
    badge_ids = fields.One2many("ems.badge", "member_id")
    registration_count = fields.Integer(compute="_compute_registration_count")

    _event_member_user_uniq = models.Constraint(
        "unique(event_id, user_id)", "A user can only be registered once as a member of an event."
    )

    @api.depends("registration_ids")
    def _compute_registration_count(self):
        for member in self:
            member.registration_count = len(member.registration_ids)

    @api.constrains("event_id", "committee_id")
    def _check_committee_event(self):
        if any(member.committee_id.event_id != member.event_id for member in self):
            raise ValidationError(_("The member and committee must belong to the same event."))

    def action_register(self):
        for member in self:
            if not member.registration_ids.filtered(lambda reg: reg.state != "cancel"):
                self.env["event.registration"].create(
                    {
                        "event_id": member.event_id.id,
                        "ems_member_id": member.id,
                        "name": member.name,
                        "email": member.email,
                        "phone": member.phone,
                        "company_name": member.organization,
                    }
                )
        return True


class CommitteeReport(models.Model):
    _name = "ems.committee.report"
    _description = "Committee Report"
    _inherit = ["mail.thread", "mail.activity.mixin", "ems.audit.mixin"]
    _order = "event_id, committee_id"
    _audit_fields = ("event_id", "committee_id", "state", "summary", "submitted_by", "submitted_on")

    name = fields.Char(required=True, default="Committee Closure Report")
    event_id = fields.Many2one("event.event", required=True, index=True, ondelete="cascade")
    committee_id = fields.Many2one(
        "ems.committee", required=True, index=True, ondelete="cascade", domain="[('event_id', '=', event_id)]"
    )
    state = fields.Selection(
        [("draft", "Draft"), ("submitted", "Submitted"), ("accepted", "Accepted")],
        default="draft",
        required=True,
        tracking=True,
    )
    summary = fields.Html(required=True)
    lessons_learned = fields.Html()
    submitted_by = fields.Many2one("res.users", readonly=True)
    submitted_on = fields.Datetime(readonly=True)

    @api.constrains("event_id", "committee_id")
    def _check_committee_event(self):
        if any(report.committee_id.event_id != report.event_id for report in self):
            raise ValidationError(_("The report and committee must belong to the same event."))

    def action_submit(self):
        self.write(
            {
                "state": "submitted",
                "submitted_by": self.env.user.id,
                "submitted_on": fields.Datetime.now(),
            }
        )
        return True

    def action_accept(self):
        self.write({"state": "accepted"})
        return True
