from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class EventGuest(models.Model):
    _name = "ems.guest"
    _description = "Event Guest"
    _inherit = ["mail.thread", "mail.activity.mixin", "ems.audit.mixin"]
    _order = "event_id, name"
    _audit_fields = (
        "name",
        "event_id",
        "organization",
        "position",
        "phone",
        "email",
        "category",
        "invitation_status",
        "accompanying_of_id",
        "invited_on",
        "responded_on",
        "active",
    )

    name = fields.Char(required=True, tracking=True, index="trigram")
    event_id = fields.Many2one(
        "event.event", required=True, tracking=True, index=True, ondelete="cascade"
    )
    organization = fields.Char(tracking=True)
    position = fields.Char(tracking=True)
    phone = fields.Char(tracking=True)
    email = fields.Char(tracking=True)
    category = fields.Selection(
        [("guest", "Guest"), ("vip", "VIP"), ("management", "Management"), ("speaker", "Speaker")],
        default="guest",
        required=True,
        tracking=True,
    )
    invitation_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("invited", "Invited"),
            ("pending", "Pending"),
            ("confirmed", "Confirmed"),
            ("declined", "Declined"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    accompanying_of_id = fields.Many2one(
        "ems.guest", string="Accompanying Guest Of", domain="[('event_id', '=', event_id), ('id', '!=', id)]"
    )
    accompanying_guest_ids = fields.One2many("ems.guest", "accompanying_of_id")
    invited_on = fields.Datetime(readonly=True)
    responded_on = fields.Datetime(readonly=True)
    active = fields.Boolean(default=True)
    registration_ids = fields.One2many("event.registration", "ems_guest_id")
    badge_ids = fields.One2many("ems.badge", "guest_id")

    @api.constrains("event_id", "accompanying_of_id")
    def _check_accompanying_guest(self):
        for guest in self:
            if guest.accompanying_of_id.event_id and guest.accompanying_of_id.event_id != guest.event_id:
                raise ValidationError(_("Accompanying guests must belong to the same event."))
            if guest.accompanying_of_id.accompanying_of_id == guest:
                raise ValidationError(_("Accompanying guest relationships cannot contain cycles."))

    def write(self, vals):
        previous = {guest.id: guest.invitation_status for guest in self}
        if vals.get("invitation_status") == "invited":
            vals.setdefault("invited_on", fields.Datetime.now())
        if vals.get("invitation_status") in ("confirmed", "declined"):
            vals.setdefault("responded_on", fields.Datetime.now())
        result = super().write(vals)
        if "invitation_status" in vals:
            for guest in self.filtered(lambda item: previous[item.id] != item.invitation_status):
                recipients = guest.event_id.role_assignment_ids.filtered(
                    lambda assignment: assignment.active and assignment.role in ("event_admin", "guest_team")
                ).user_id.partner_id
                if recipients:
                    guest.message_notify(
                        subject=_("Guest confirmation updated"),
                        body=_("%s is now %s.", guest.name, guest.invitation_status),
                        partner_ids=recipients.ids,
                    )
        return result

    def action_invite(self):
        self.write({"invitation_status": "invited"})
        return True

    def action_confirm(self):
        self.write({"invitation_status": "confirmed"})
        return True

    def action_decline(self):
        self.write({"invitation_status": "declined"})
        return True

    def action_register(self):
        for guest in self:
            if not guest.registration_ids.filtered(lambda reg: reg.state != "cancel"):
                self.env["event.registration"].create(
                    {
                        "event_id": guest.event_id.id,
                        "ems_guest_id": guest.id,
                        "name": guest.name,
                        "email": guest.email,
                        "phone": guest.phone,
                        "company_name": guest.organization,
                    }
                )
        return True
