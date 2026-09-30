from odoo import api, fields, models
from odoo.exceptions import AccessError


class EventOverallDashboard(models.AbstractModel):
    _name = "ems.overall.dashboard"
    _description = "Event Management Overall Dashboard"

    @api.model
    def get_dashboard_data(self, event_id=False):
        user = self.env.user
        allowed_groups = (
            "base.group_system",
            "event_management_system.group_ems_system_admin",
            "event_management_system.group_ems_event_admin",
            "event_management_system.group_ems_coordinator",
            "event_management_system.group_ems_committee_lead",
            "event_management_system.group_ems_committee_member",
            "event_management_system.group_ems_technology",
            "event_management_system.group_ems_registration",
            "event_management_system.group_ems_guest",
            "event_management_system.group_ems_viewer",
        )
        if not any(user.has_group(group) for group in allowed_groups):
            raise AccessError("You are not allowed to view the event dashboard.")

        visible_events = self.env["event.event"].search([])
        all_visible_event_ids = visible_events.ids
        visible_event_ids = all_visible_event_ids
        if event_id:
            event_id = int(event_id)
            if event_id not in visible_event_ids:
                raise AccessError("You are not allowed to view this event.")
            visible_event_ids = [event_id]

        events = self.env["event.event"].sudo().browse(visible_event_ids)
        event_domain = [("event_id", "in", visible_event_ids)]
        today = fields.Date.context_today(self)

        def count(model, extra=()):
            return self.env[model].sudo().search_count(event_domain + list(extra))

        activity_states = [
            ("Not Started", "not_started"),
            ("In Progress", "in_progress"),
            ("Completed", "completed"),
        ]
        invitation_states = [
            ("Draft", "draft"),
            ("Invited", "invited"),
            ("Pending", "pending"),
            ("Confirmed", "confirmed"),
            ("Declined", "declined"),
        ]
        badge_states = [
            ("Pending", "pending"),
            ("Generated", "generated"),
            ("Printed", "printed"),
            ("Issued", "issued"),
        ]
        incident_priorities = [
            ("Critical", "critical"),
            ("High", "high"),
            ("Medium", "medium"),
            ("Low", "low"),
        ]

        def series(model, entries, field_name, extra=()):
            rows = []
            for label, value in entries:
                amount = count(model, list(extra) + [(field_name, "=", value)])
                rows.append({"label": label, "value": amount})
            maximum = max([row["value"] for row in rows] or [0])
            for row in rows:
                row["percent"] = round(row["value"] * 100 / maximum) if maximum else 0
            return rows

        activities_total = count("ems.activity")
        registrations_domain = event_domain + [("state", "in", ["open", "done"])]
        registrations_total = self.env["event.registration"].sudo().search_count(registrations_domain)
        checked_in = self.env["event.registration"].sudo().search_count(
            event_domain + [("state", "=", "done")]
        )
        open_incidents = count("ems.incident", [("status", "!=", "closed")])
        overdue = self.env["ems.activity"].sudo().search_count(
            event_domain + [("status", "!=", "completed"), ("due_date", "<", today)]
        )
        activity_series = series("ems.activity", activity_states, "status")
        invitation_series = series("ems.guest", invitation_states, "invitation_status")
        badge_series = series("ems.badge", badge_states, "status")
        incident_series = series(
            "ems.incident", incident_priorities, "priority", [("status", "!=", "closed")]
        )

        recent_events = self.env["event.event"].sudo().search_read(
            [("id", "in", visible_event_ids)],
            ["name", "management_state", "readiness_percent", "readiness_state", "date_begin"],
            order="date_begin desc, id desc",
            limit=8,
        )
        for event in recent_events:
            event["readiness_percent"] = round(event["readiness_percent"] or 0)
            event["date_begin"] = fields.Date.to_string(event["date_begin"]) if event["date_begin"] else ""

        return {
            "events": [
                {"id": event.id, "name": event.name}
                for event in self.env["event.event"].sudo().browse(all_visible_event_ids)
            ],
            "selected_event_id": event_id or False,
            "kpis": {
                "events": len(visible_event_ids),
                "committees": count("ems.committee"),
                "activities": activities_total,
                "overdue": overdue,
                "members": count("ems.member"),
                "guests": count("ems.guest"),
                "registrations": registrations_total,
                "checked_in": checked_in,
                "badges": count("ems.badge"),
                "issued_badges": count("ems.badge", [("status", "=", "issued")]),
                "open_incidents": open_incidents,
                "critical_incidents": count(
                    "ems.incident", [("status", "!=", "closed"), ("priority", "=", "critical")]
                ),
            },
            "attendance_percent": round(checked_in * 100 / registrations_total) if registrations_total else 0,
            "activity_chart": activity_series,
            "invitation_chart": invitation_series,
            "badge_chart": badge_series,
            "incident_chart": incident_series,
            "recent_events": recent_events,
            "activity_completion_percent": round(
                count("ems.activity", [("status", "=", "completed")]) * 100 / activities_total
            ) if activities_total else 0,
            "open_incidents": open_incidents,
        }
