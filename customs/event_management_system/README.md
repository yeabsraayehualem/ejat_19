# Event Management & Digital Technology

Odoo 19 module for coordinating events, committees, activities, participants, invitations, badges, QR-based registration, technical incidents, readiness, reporting, notifications, and audit history.

## Module Details

- Technical name: `event_management_system`
- Display name: `Event Management & Digital Technology`
- Version: `19.0.1.0.0`
- Odoo version: 19.0
- License: LGPL-3
- Category: Marketing/Events
- Dependencies: `event`, `mail`
- Python dependency: `qrcode`

## Main Features

- Event lifecycle: Draft, Preparation, Readiness Review, Live, Closure, Closed, and Cancelled.
- Event-scoped roles and record rules.
- Committee leads, members, participant members, and committee closure reports.
- Activities with priorities, event phases, dependencies, deadlines, exceptions, and readiness flags.
- Guest records, accompanying guests, invitations, and confirmation tracking.
- Member and guest registration using the standard Odoo Event registration model.
- Badge categories, unique badge IDs, generated QR images, printing, issuing, and controlled reprinting.
- QR/manual check-in logging and duplicate check-in prevention.
- Technical incident workflow from Logged through Closed.
- Event dashboard, activity/guest/badge/incident analysis, attendance analysis, and audit trail.
- Odoo mail activities and notifications for assignment, deadlines, guest status changes, critical incidents, and readiness risk.
- QWeb PDF reports for badges, final events, and committee closure reports.

## Installation

1. Put this directory in an Odoo addons path.
2. Ensure the Odoo 19 `event` and `mail` applications are available.
3. Install the Python package `qrcode` in the Python environment used by Odoo.
4. Restart Odoo and update the Apps list.
5. Search for `Event Management & Digital Technology` and select **Install**.

The module creates its own security groups, sequences, badge categories, record rules, views, actions, reports, and the scheduled action `Event Management: Activity Deadline Alerts`.

## Quick Start

1. Open **Event Operations > Configuration > Users & Access** and prepare internal users.
2. Open **Event Operations > Configuration > Badge Categories** and confirm the default categories.
3. Open **Event Operations > Planning > Events** and create the event.
4. On the event's **Management** tab, assign users in **Roles**.
5. Create committees in **Event Operations > Planning > Committees**.
6. Create activities in **Event Operations > Planning > Activities**.
7. Add members and guests from **Event Operations > Participants**.
8. Generate, print, and issue badges from **Event Operations > Participants > Badges & QR**.
9. Use **Registration Desk** or **Registrations** for event-day check-in.
10. Monitor the event in **Event Operations > Dashboard**.

## Navigation

The module adds the root menu **Event Operations**. Available child menus depend on the user's security groups and event/committee record rules.

- **Dashboard**: Event Dashboard.
- **Planning > Events**: Standard Odoo Events with the module's management fields.
- **Planning > Committees**: Committees and their members, activities, and closure reports.
- **Planning > Activities**: Activity planning and analysis.
- **Planning > Committee Reports**: Committee closure reports.
- **Participants > Members**: Registered event members.
- **Participants > Guests & Invitations**: Guests and invitation statuses.
- **Participants > Registrations**: Standard Odoo event registrations extended with member/guest links.
- **Participants > Badges & QR**: Badge records and QR codes.
- **Participants > Registration Desk**: Standard Odoo barcode registration desk.
- **Participants > Check-in Log**: Immutable check-in records.
- **Technical Support > Incidents**: Technical issue workflow.
- **Reporting > Activity Analysis**: Activity list, pivot, graph, filters, and groupings.
- **Reporting > Guest Analysis**: Guest list, pivot, graph, filters, and groupings.
- **Reporting > Badge Analysis**: Badge list, pivot, graph, filters, and groupings.
- **Reporting > Attendance Analysis**: Standard Odoo event registration analysis.
- **Reporting > Incident Analysis**: Incident list, pivot, graph, filters, and groupings.
- **Reporting > Audit Trail**: Read-only audit records.
- **Configuration > Badge Categories**: Badge category setup.
- **Configuration > Users & Access**: Standard Odoo user administration for System Administrators.

## Security Summary

The module defines these groups under the **Event Management** privilege:

- System Administrator
- Event Administrator
- Event Coordinator
- Committee Lead
- Committee Member
- Digital Technology Lead
- Registration Officer
- Guest Management Team
- Management / Viewer

Record rules restrict operational users to assigned events, committee leads to their committees, and committee members to their own committee and assigned activities. Guest personal information is not readable by Management / Viewer. See [USER_GUIDE.md](USER_GUIDE.md) for the complete permission and workflow reference.

## Reports

- **Event Badge**: Generated by the badge **Print** or **Reprint** action.
- **Final Event Report**: Bound to `event.event` and available through the standard Odoo report/print interface for permitted users.
- **Committee Closure Report**: Bound to `ems.committee.report` and available through the standard Odoo report/print interface.

## Notifications

- Creating or reassigning an activity schedules an Odoo to-do activity for `Responsible`.
- The daily scheduled action checks for activities that are `Due Soon` or `Overdue`.
- Guest invitation status changes notify active Event Administrator and Guest Management Team assignments.
- Critical open incidents notify active Event Administrator and Digital Technology Lead assignments.
- The first readiness-risk transition notifies active Event Administrator, Event Coordinator, and Digital Technology Lead assignments.

These notifications use Odoo mail/activity mechanisms. Actual email delivery requires normal Odoo outgoing mail configuration.

## Validation

The module includes transaction tests in `tests/` covering activities, deadlines, dependencies, guests, invitations, badges, QR data, check-in, duplicate prevention, incidents, readiness, closure, reports, audit masking, and security scoping.

For user procedures, administrator configuration, limitations, and troubleshooting, read [USER_GUIDE.md](USER_GUIDE.md).
