import base64
from io import BytesIO

import qrcode

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class BadgeCategory(models.Model):
    _name = "ems.badge.category"
    _description = "Badge Category"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    color = fields.Integer()
    active = fields.Boolean(default=True)


class EventBadge(models.Model):
    _name = "ems.badge"
    _description = "Event Badge"
    _inherit = ["mail.thread", "mail.activity.mixin", "ems.audit.mixin"]
    _rec_name = "badge_code"
    _order = "event_id, id"
    _audit_fields = (
        "event_id",
        "category_id",
        "member_id",
        "guest_id",
        "registration_id",
        "badge_code",
        "status",
        "print_count",
        "printed_on",
        "issued_on",
        "reprint_reason",
    )

    event_id = fields.Many2one("event.event", required=True, index=True, ondelete="cascade")
    category_id = fields.Many2one("ems.badge.category", required=True, tracking=True, ondelete="restrict")
    member_id = fields.Many2one("ems.member", index=True, ondelete="cascade", domain="[('event_id', '=', event_id)]")
    guest_id = fields.Many2one("ems.guest", index=True, ondelete="cascade", domain="[('event_id', '=', event_id)]")
    registration_id = fields.Many2one("event.registration", required=True, index=True, ondelete="cascade")
    badge_code = fields.Char(related="registration_id.barcode", store=True, index=True)
    qr_image = fields.Binary(compute="_compute_qr_image", attachment=False)
    participant_name = fields.Char(related="registration_id.name", store=True)
    status = fields.Selection(
        [("pending", "Pending"), ("generated", "Generated"), ("printed", "Printed"), ("issued", "Issued")],
        default="pending",
        required=True,
        tracking=True,
        index=True,
    )
    print_count = fields.Integer(default=0, readonly=True)
    printed_on = fields.Datetime(readonly=True)
    issued_on = fields.Datetime(readonly=True)
    reprint_reason = fields.Text(copy=False)

    _registration_badge_uniq = models.Constraint(
        "unique(registration_id)", "A registration can only have one badge."
    )

    @api.depends("badge_code")
    def _compute_qr_image(self):
        for badge in self:
            if not badge.badge_code:
                badge.qr_image = False
                continue
            output = BytesIO()
            qrcode.make(badge.badge_code).save(output, format="PNG")
            badge.qr_image = base64.b64encode(output.getvalue())

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            member = self.env["ems.member"].browse(vals.get("member_id"))
            guest = self.env["ems.guest"].browse(vals.get("guest_id"))
            if bool(member) == bool(guest):
                raise ValidationError(_("Select exactly one member or guest for the badge."))
            participant = member or guest
            if vals.get("event_id") and participant.event_id.id != vals["event_id"]:
                raise ValidationError(_("The badge participant must belong to the selected event."))
            if not vals.get("registration_id"):
                participant.action_register()
                registration = participant.registration_ids.filtered(lambda reg: reg.state != "cancel")[:1]
                vals["registration_id"] = registration.id
        return super().create(vals_list)

    @api.constrains("member_id", "guest_id", "event_id", "registration_id")
    def _check_participant(self):
        for badge in self:
            if bool(badge.member_id) == bool(badge.guest_id):
                raise ValidationError(_("A badge must be linked to exactly one member or guest."))
            participant = badge.member_id or badge.guest_id
            registration_participant = badge.registration_id.ems_member_id or badge.registration_id.ems_guest_id
            if participant.event_id != badge.event_id or badge.registration_id.event_id != badge.event_id:
                raise ValidationError(_("Badge, participant and registration must belong to the same event."))
            if participant != registration_participant:
                raise ValidationError(_("The badge and registration must belong to the same participant."))

    def action_generate(self):
        self.write({"status": "generated"})
        return True

    def action_print(self):
        for badge in self:
            if badge.status == "pending":
                badge.action_generate()
            badge.write(
                {
                    "status": "printed" if badge.status != "issued" else "issued",
                    "print_count": badge.print_count + 1,
                    "printed_on": fields.Datetime.now(),
                }
            )
            badge._create_audit_log("print", details=_("Badge printed."))
        return self.env.ref("event_management_system.action_report_ems_badge").report_action(self)

    def action_reprint(self):
        if any(not badge.reprint_reason for badge in self):
            raise UserError(_("Enter a reprint reason before reprinting a badge."))
        return self.action_print()

    def action_issue(self):
        if any(badge.status == "pending" for badge in self):
            raise UserError(_("Generate the badge before issuing it."))
        self.write({"status": "issued", "issued_on": fields.Datetime.now()})
        return True
