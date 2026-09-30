# Event Management & Digital Technology User Guide

This guide describes the installed Odoo 19 module `event_management_system` using the menus, fields, buttons, statuses, permissions, and reports that are implemented in the module.

## 1. Module Purpose

**Event Management & Digital Technology** provides a controlled workspace for planning and executing events. It connects an event to its committees, activities, members, guests, registrations, badges, check-ins, technical incidents, readiness indicators, reports, notifications, and audit records.

The module extends Odoo's standard Events and Event Registrations applications. It does not replace the standard Odoo event registration desk or core user administration.

## 2. Prerequisites

Before installation, confirm the following:

- Odoo 19.0 is running.
- The Odoo `event` application is available.
- The Odoo `mail` application is available.
- The Python package `qrcode` is installed in the same Python environment used by Odoo.
- Users who operate the module are internal Odoo users, not portal or public users.
- Odoo outgoing mail is configured if notifications must be delivered by email.
- The Odoo PDF reporting dependencies, including `wkhtmltopdf` where required by the Odoo deployment, are available for PDF output.

The module manifest declares `event` and `mail` as dependencies and declares `qrcode` as an external Python dependency.

## 3. Installation

### 3.1 Install from the Odoo Apps interface

1. Place the `event_management_system` directory in an Odoo addons path.
2. Restart the Odoo server so it can discover the module.
3. Open the Odoo **Apps** application.
4. Use the Apps menu to choose **Update Apps List** when the module is not visible.
5. Search for **Event Management & Digital Technology**.
6. Select **Install**.
7. Refresh the browser after installation.

The installation loads security groups, access rules, sequences, default badge categories, views, menus, reports, and the deadline alert scheduled action.

### 3.2 Confirm installation

After installation, an authorized user should see **Event Operations**. If it is not visible, check the user's Event Management group and restart or update the Apps list.

## 4. Initial Configuration

Complete these steps before creating production event data.

### 4.1 Prepare internal users

1. Open **Event Operations > Configuration > Users & Access**.
2. Create or open each internal user in standard Odoo user administration.
3. Confirm the user is an internal user and has a valid login.
4. Assign the appropriate Event Management group if the user needs access before event-specific assignment.

Event-specific role assignment also adds the corresponding Odoo group to the assigned user. Committee creation or update adds **Committee Lead** to the lead and **Committee Member** to selected committee members.

The event role selector contains these roles:

- Event Administrator
- Event Coordinator
- Digital Technology Lead
- Registration Officer
- Guest Management Team
- Management / Viewer

System Administrator is a security group, not an option in the event role selector. Committee Lead and Committee Member are assigned through committee lead/member fields.

### 4.2 Confirm badge categories

1. Open **Event Operations > Configuration > Badge Categories**.
2. Confirm the default categories:
   - Committee Member
   - Guest
   - VIP
   - Management
   - Technical Team
   - Support Staff
3. Use the editable list to maintain **Sequence**, **Name**, **Color**, and **Active**.

Categories are loaded as non-updating initial data. Existing category changes are not overwritten by a normal module upgrade.

### 4.3 Configure the event alert window

**Due-soon days** is configured on the event's **Management** tab. The default is `3`, and the value must be at least `1`. The field is visible to Event Administrators and System Administrators.

## 5. Roles and Permissions

Access is controlled by both Odoo access control lists and record rules. A user may have a menu but still see only the events or committees allowed by the record rules.

| Group | Implemented access |
|---|---|
| System Administrator | Full system access through the Odoo system group and event manager permissions. |
| Event Administrator | Event administration, committees, activities, members, guests, registrations, badges, incidents, committee reports, and reports for assigned events. Can manage event roles. |
| Event Coordinator | Creates and updates events, committees, activities, incidents, and committee reports within assigned operational scope; coordinates activities. Guest and badge administration is not granted by this group alone. |
| Committee Lead | Own led committees, committee members, event activities, and committee reports. The group is added when a user is used as a committee lead. |
| Committee Member | Own committee visibility and assigned activities. A committee member can update only `status`, `exception`, and `remarks` on an activity. The group is added when selected as a committee member. |
| Digital Technology Lead | Assigned-event activities, member records, guests, registrations, badges, check-in logs, and technical incidents according to the access rules. |
| Registration Officer | Assigned-event members, guests for lookup, registrations, badges, registration desk, and check-in logs. |
| Guest Management Team | Assigned-event guest and invitation records and registration operations allowed by the access rules. |
| Management / Viewer | Read-only dashboard and reporting access within assigned events. Guest personal information is protected from this group. |

### 5.1 Record scope

- Event Administrator, Event Coordinator, Digital Technology Lead, Registration Officer, Guest Management Team, and Management / Viewer users see events with an active event role assignment.
- Committee Leads see committees they lead and the related records.
- Committee Members see committees where they are members and activities assigned to them.
- System Administrators are not restricted by the operational record rules.
- The event and committee data must be kept consistent: a member, activity, report, badge, registration, or guest must use the same event as its related record.

## 6. Menu and Navigation Reference

The root menu is **Event Operations**.

### Dashboard

- **Event Operations > Dashboard** opens **Event Dashboard**.

### Planning

- **Event Operations > Planning > Events** opens standard Odoo Events with the module's event management extension.
- **Event Operations > Planning > Committees** opens **Committees**.
- **Event Operations > Planning > Activities** opens **Activities**.
- **Event Operations > Planning > Committee Reports** opens **Committee Reports**.

### Participants

- **Event Operations > Participants > Members** opens **Members**.
- **Event Operations > Participants > Guests & Invitations** opens **Guests & Invitations**.
- **Event Operations > Participants > Registrations** opens standard Odoo event registrations.
- **Event Operations > Participants > Badges & QR** opens **Badges & QR Codes**.
- **Event Operations > Participants > Registration Desk** opens the standard Odoo event barcode registration desk.
- **Event Operations > Participants > Check-in Log** opens **Attendance & Check-in Log**.

### Technical Support

- **Event Operations > Technical Support > Incidents** opens **Technical Incidents**.

### Reporting

- **Event Operations > Reporting > Activity Analysis** opens Activities in analytical views.
- **Event Operations > Reporting > Guest Analysis** opens Guests & Invitations in analytical views.
- **Event Operations > Reporting > Badge Analysis** opens Badges & QR Codes in analytical views.
- **Event Operations > Reporting > Attendance Analysis** opens standard Odoo registrations.
- **Event Operations > Reporting > Incident Analysis** opens Technical Incidents in analytical views.
- **Event Operations > Reporting > Audit Trail** opens the read-only audit list.

### Configuration

- **Event Operations > Configuration > Badge Categories** opens badge category configuration.
- **Event Operations > Configuration > Users & Access** opens standard Odoo user administration for System Administrators.

## 7. Events

### 7.1 Create an event

1. Open **Event Operations > Planning > Events**.
2. Use the standard Odoo Events **New** action.
3. Enter the standard event information, including **Name**, **Date Begin**, and **Date End**.
4. Save the event.
5. Open the event's **Management** tab.

The management lifecycle starts at **Draft**.

### 7.2 Event management fields

The **Management** tab contains:

- **Management State**: the lifecycle status shown in the form header.
- **Readiness**: **Readiness Percent**, **Readiness State**, and **Due-soon days**.
- **Closure**: **Attendance Finalized**, **Reports Collected**, **Final Report Approved**, and the read-only **Closure Override Reason** when present.
- **Activity Status**: counts for **Activity Not Started Count**, **Activity Progress Count**, **Activity Completed Count**, **Activity Delayed Count**, **Activity Overdue Count**, and **Activity Due Soon Count**.
- **Roles**: inline event role assignments for permitted administrators.
- **Final Report**: **Final Report** and **Lessons Learned**.

The event form also provides stat buttons for **Committees**, **Activities**, **Guests**, **Badges Issued**, and **Open Incidents**. These open records filtered to the current event.

### 7.3 Assign event roles

1. Open the event's **Management** tab.
2. Open the **Roles** page.
3. Add a row in the inline list.
4. Select **User**.
5. Select **Role**.
6. Leave **Active** enabled for an active assignment.
7. Save the event.

The role assignment is unique per event, user, and role. Active assignments control event visibility and notifications. Creating an active event role also adds the corresponding Event Management security group to the user.

### 7.4 Move an event through its lifecycle

Use the header buttons in this order:

1. From **Draft**, select **Start Preparation**. The state becomes **Preparation**.
2. From **Preparation**, select **Readiness Review**. The state becomes **Readiness Review**.
3. From **Readiness Review**, select **Go Live**. The state becomes **Live** unless the event's **Readiness State** is **At Risk**.
4. From **Live**, select **Start Closure**. The state becomes **Closure**.
5. From **Closure**, select **Close Event**.

**Close Event** is allowed only when all of the following are true:

- All event activities have **Status** `Completed`.
- All event incidents have **Status** `Closed`.
- **Attendance Finalized** is enabled.
- **Reports Collected** is enabled.
- **Final Report Approved** is enabled.

The **Cancel** button moves the management state to **Cancelled**. It is hidden for events already in **Closed** or **Cancelled**.

## 8. Committees

### 8.1 Create a committee

1. Open **Event Operations > Planning > Committees**.
2. Select **New**.
3. Enter **Name**.
4. Select **Event**.
5. Select **Lead**.
6. Add users in **Committee Members**.
7. Save.

The **Lead** cannot also be in **Committee Members**. Committee names must be unique within an event.

### 8.2 Committee form pages

- **Members**: the `Committee Members` users.
- **Registered Members**: event member records connected to the committee.
- **Activities**: related activities with **Activity Code**, **Name**, **Responsible**, **Due Date**, **Status**, and **Exception**.
- **Closure Reports**: related committee reports with **Name**, **State**, **Submitted By**, and **Submitted On**.

The committee header shows **Activity Count**, **Completed Count**, and **Overdue Count**.

### 8.3 Find your committees

In **Committees**, use the **My Committees** filter to find committees where the current user is the **Lead** or appears in **Committee Members**. The search view also supports grouping by **Event** and **Lead**.

## 9. Activities

### 9.1 Create an activity

1. Open **Event Operations > Planning > Activities**.
2. Select **New**.
3. Enter **Name**.
4. Select **Event**, **Committee**, and **Responsible**.
5. Select **Priority**: **High**, **Medium**, or **Low**.
6. Select **Phase**: **Before Event**, **During Event**, or **After Event**.
7. Enter **Start Date** and **Due Date**.
8. Optionally enter **Description**, **Dependencies**, and **Remarks**.
9. Enable **Readiness Critical** when completion is required for readiness.
10. Save.

The system assigns an **Activity Code** from the `ACT/YYYY/00001` sequence. The code is read-only.

### 9.2 Activity statuses and actions

The **Status** values are:

- **Not Started**
- **In Progress**
- **Completed**

The form header provides:

- **Start**: changes **Status** from **Not Started** to **In Progress**.
- **Complete**: changes **Status** to **Completed** and resets **Exception** to **None**.
- **Mark Delayed**: changes **Exception** to **Delayed**.
- **Report Issue**: changes **Exception** to **Issue**.

The **Exception** values are **None**, **Delayed**, and **Issue**.

### 9.3 Activity rules

- **Due Date** cannot be before **Start Date**.
- Dependencies must belong to the same event.
- An activity cannot depend on itself or create a dependency cycle.
- An activity cannot be completed while a dependency is not **Completed**.
- Creating or changing **Responsible** schedules an Odoo to-do activity with the activity's **Due Date**.
- Committee Members may update only **Status**, **Exception**, and **Remarks**.

### 9.4 Activity search and analysis

The **Activities** search view provides:

- **My Activities**
- **Overdue**
- **Due Soon**
- **Delayed**
- **Issues**
- **Readiness**
- Group by **Event**, **Committee**, **Phase**, or **Status**

The **Activity Analysis** menu provides list, kanban, pivot, and graph views.

## 10. Members and Participants

### 10.1 Create a member

1. Open **Event Operations > Participants > Members**.
2. Select **New**.
3. Enter **Name**.
4. Select **Event** and **Committee**.
5. Optionally select the related internal **User**.
6. Enter **Organization**, **Position**, **Email**, and **Phone** when applicable.
7. Save.

The member form provides the **Register** button and pages for **Registrations** and **Badges**. A member can be registered only once per event for the same linked user.

### 10.2 Register a member

1. Open the member record.
2. Select **Register**.
3. Confirm the created standard Odoo event registration in the **Registrations** page.

If an active registration already exists, the action does not create another one.

## 11. Guests and Invitations

### 11.1 Create a guest

1. Open **Event Operations > Participants > Guests & Invitations**.
2. Select **New**.
3. Enter **Name** and **Event**.
4. Enter **Organization**, **Position**, **Phone**, and **Email**.
5. Select **Category**: **Guest**, **VIP**, **Management**, or **Speaker**.
6. Optionally select **Accompanying Guest Of**.
7. Save.

Accompanying guests must belong to the same event, and the relationship cannot be circular.

### 11.2 Invitation statuses and actions

The **Invitation Status** values are:

- **Draft**
- **Invited**
- **Pending**
- **Confirmed**
- **Declined**

Use these form buttons:

1. **Send Invitation** changes **Invitation Status** from **Draft** to **Invited** and records **Invited On**.
2. **Confirm** changes the status to **Confirmed** and records **Responded On**.
3. **Decline** changes the status to **Declined** and records **Responded On**.
4. **Register** is available for a confirmed guest and creates the standard Odoo event registration.

The **Confirmed Guest List** filter is available in the guest search view. Other filters include **Pending** and **Declined**, with grouping by **Event**, **Invitation Status**, and **Category**.

The **Send Invitation** action does not provide a custom email template or external invitation portal. It changes the status and triggers the implemented Odoo notification to active Event Administrator and Guest Management Team assignments.

## 12. Badges and QR Codes

### 12.1 Create a badge

1. Open **Event Operations > Participants > Badges & QR**.
2. Select **New**.
3. Select **Event** and **Category**.
4. Select exactly one of **Member** or **Guest**.
5. Save.

If the selected participant does not yet have an active registration, the module creates one. The badge receives the registration's unique **Badge Code** and a generated **QR Image**.

A badge must use exactly one member or guest, and the badge, participant, registration, and event must match.

### 12.2 Badge statuses and actions

The **Status** values are:

- **Pending**
- **Generated**
- **Printed**
- **Issued**

Use the header buttons as follows:

1. Select **Generate** on a **Pending** badge. The status becomes **Generated**.
2. Select **Print** on a **Generated** badge. The status becomes **Printed**, **Print Count** increases, **Printed On** is recorded, and the **Event Badge** PDF is returned.
3. Select **Issue** on a **Generated** or **Printed** badge. The status becomes **Issued** and **Issued On** is recorded.
4. For a printed or issued badge, enter **Reprint Reason**, then select **Reprint**. The print count increases and the badge PDF is returned.

The badge search view provides **Pending**, **Generated**, **Printed**, and **Issued** filters and grouping by **Event**, **Status**, and **Category**.

## 13. Registration and Check-in

### 13.1 Prepare a registration

Members and confirmed guests can be registered from their records with **Register**. A registration can also be reviewed from **Event Operations > Participants > Registrations**.

The registration form includes the module fields **Event Member** and **Event Guest**, and the **Badge & Check-in** page. A registration must not be linked to both an Event Member and an Event Guest.

### 13.2 QR or barcode check-in

1. Open **Event Operations > Participants > Registration Desk**.
2. Use the standard Odoo event barcode registration desk.
3. Scan the participant's badge QR code or registration barcode.
4. Verify the participant information.
5. Complete the standard Odoo registration check-in operation.

The module records an accepted check-in with **Method** `QR Scan` when the QR path is used. The check-in date/time is stored on the registration as the standard Odoo closing/check-in time. A badge in **Generated** or **Printed** status is automatically moved to **Issued** when the participant checks in.

### 13.3 Manual search fallback

1. Open **Event Operations > Participants > Registrations**.
2. Search by **QR / Badge ID**, **Event Member**, or **Event Guest** using the extended registration search view.
3. Open the registration and use the standard Odoo check-in operation.

The module records manual operations with **Method** `Manual Search` when that context is used.

### 13.4 Duplicate check-in and corrections

- A second normal check-in is blocked with the message `This participant is already checked in.`
- An authorized re-entry action requires a reason and records **Authorized Re-entry**.
- An authorized attendance correction requires a reason and records **Corrected**, including the previous date/time.
- Only System Administrator, Event Administrator, or Digital Technology Lead can authorize re-entry.
- Attendance correction is available to System Administrator, Event Administrator, Digital Technology Lead, or Registration Officer.
- The custom module does not add separate form buttons for these two correction actions. They are model actions intended for authorized operational tooling or administration.

### 13.5 Check-in log

Open **Event Operations > Participants > Check-in Log** to review **Attendance & Check-in Log**. The list contains **Create Date**, **Event**, **Registration**, **Method**, **Result**, **User**, **Reason**, and **Previous Datetime**.

**Result** values are **Accepted**, **Duplicate Blocked**, **Authorized Re-entry**, **Invalid QR**, and **Corrected**. Check-in logs cannot be created, edited, or deleted from the list, and the model protects them from changes except for superuser operations.

## 14. Technical Incidents

### 14.1 Log an incident

1. Open **Event Operations > Technical Support > Incidents**.
2. Select **New**.
3. Select **Event**.
4. Enter **Description** and **Location**.
5. Select **Priority**: **Critical**, **High**, **Medium**, or **Low**.
6. Optionally select **Assigned**.
7. Save.

The system assigns an **Incident Code** from the `INC/YYYY/00001` sequence. The initial **Status** is **Logged**, and **Opened On** is recorded automatically.

### 14.2 Incident workflow

Use the form header buttons in order:

1. From **Logged**, select **Assign** after selecting **Assigned**. The status becomes **Assigned**.
2. Select **Investigate**. The status becomes **Investigation**.
3. Enter **Resolution**, then select **Resolve**. The status becomes **Resolved**.
4. Select **Verify**. The status becomes **Verified**.
5. Select **Close**. The status becomes **Closed** and **Closed On** is recorded.

The **Assign** action requires an **Assigned** user. The **Resolve** action requires **Resolution** text. The **Close** action requires the incident to be **Verified**.

### 14.3 Incident analysis and alerts

Incident search filters are **Open**, **Critical**, and **Assigned to Me**. Grouping is available by **Event**, **Status**, and **Priority**.

An open **Critical** incident:

- Appears in the event's **Open Incidents** and **Critical Incident** dashboard counts.
- Makes **Readiness State** **At Risk**.
- Sends a notification to active Event Administrator and Digital Technology Lead assignments.
- Prevents **Go Live** until the blocker is resolved.

## 15. Readiness Activities and Alerts

### 15.1 Mark a readiness activity

1. Open or create an activity under **Event Operations > Planning > Activities**.
2. Enable **Readiness Critical**.
3. Use the normal activity workflow to move its **Status** to **Completed**.

Readiness Percent is the percentage of **Readiness Critical** activities with **Status** **Completed**.

### 15.2 Readiness states

- **Not Ready**: no readiness activity is completed and there is no active blocker state.
- **In Progress**: some readiness activities are completed.
- **At Risk**: an incomplete readiness activity is overdue or an open Critical incident exists.
- **Ready**: all readiness activities are completed and there is no active blocker.

With no readiness activities, the percentage is `0%` and the state is **Not Ready**.

### 15.3 Readiness alerts

When an event first becomes **At Risk**, the module sends an Odoo notification to active Event Administrator, Event Coordinator, and Digital Technology Lead assignments. The alert is deduplicated while the event remains at risk. When the risk is resolved, the internal alert state is cleared so a later risk can notify recipients again.

The event **Go Live** button raises an error while **Readiness State** is **At Risk**.

## 16. Dashboard and Analysis

### 16.1 Event Dashboard

Open **Event Operations > Dashboard**. **Event Dashboard** provides kanban, list, and form views.

The dashboard includes:

- Event lifecycle and date range.
- Readiness percentage and readiness state.
- Committee count.
- Total, completed, in-progress, and not-started activities.
- Delayed, overdue, and due-soon activity counts.
- Confirmed guests.
- Registered members and guests.
- Generated, printed, and issued badges.
- Checked-in participants.
- Open and critical incidents.

The list view highlights **At Risk** events and marks **Ready** events as successful.

### 16.2 Analytical views

The analytical menus use the same records as the operational menus:

- **Activity Analysis** supports filters **My Activities**, **Overdue**, **Due Soon**, **Delayed**, **Issues**, and **Readiness** and grouping by **Event**, **Committee**, **Phase**, and **Status**.
- **Guest Analysis** supports **Confirmed Guest List**, **Pending**, and **Declined** and grouping by **Event**, **Invitation Status**, and **Category**.
- **Badge Analysis** supports **Pending**, **Generated**, **Printed**, and **Issued** and grouping by **Event**, **Status**, and **Category**.
- **Attendance Analysis** opens standard Odoo event registration data.
- **Incident Analysis** supports **Open**, **Critical**, and **Assigned to Me** and grouping by **Event**, **Status**, and **Priority**.

## 17. Notifications

The module uses Odoo activities and mail notifications rather than custom email templates.

### Activity assignment

When an activity is created or **Responsible** changes, an Odoo to-do activity is scheduled for the responsible user with the activity's **Due Date**.

### Deadline alerts

The scheduled action **Event Management: Activity Deadline Alerts** runs once per day. It sends:

- **Event activity due soon** for an incomplete activity within the due-soon window.
- **Event activity overdue** for an incomplete activity whose **Due Date** has passed.

Each notification is marked internally so the same activity is not repeatedly notified for the same condition.

### Guest status notifications

Changing a guest's **Invitation Status** sends **Guest confirmation updated** to active Event Administrator and Guest Management Team event assignments.

### Critical incident notifications

Creating or changing an open Critical incident sends **Critical technical incident** to active Event Administrator and Digital Technology Lead event assignments.

### Email delivery

Notifications are created through Odoo's mail/activity system. To deliver them by email, configure the standard Odoo outgoing mail server and mail queue. Without that configuration, users can still see supported in-app activities and notifications according to their Odoo setup.

## 18. Reports

### 18.1 Event Badge PDF

1. Open **Event Operations > Participants > Badges & QR**.
2. Open a badge in **Generated** or **Printed** status.
3. Select **Print**.
4. Save or print the returned **Event Badge** PDF.

The report contains the event name, participant name, badge category, committee or guest organization where applicable, QR image, and badge code.

For an already printed or issued badge, enter **Reprint Reason** and select **Reprint**.

### 18.2 Final Event Report PDF

1. Open **Event Operations > Planning > Events**.
2. Open the event.
3. Use the standard Odoo **Print** interface for the event.
4. Select **Final Event Report**.

The report includes:

- Event name, period, lifecycle, and readiness.
- Executive Dashboard counts.
- Committee Activity summary.
- Technical Incident Summary.
- Committee Reports summary.
- Lessons Learned.
- Final Summary.
- Attendance, reports, and approval flags.

The report is available to Event Administrator, Event Coordinator, Management / Viewer, and System Administrator groups through the report access configuration.

### 18.3 Committee Closure Report PDF

1. Open **Event Operations > Planning > Committee Reports**.
2. Open the committee report.
3. Use the standard Odoo **Print** interface.
4. Select **Committee Closure Report**.

The report includes the event, committee, report status, submitter, submission time, **Summary**, and **Lessons Learned**.

The report is bound to `ems.committee.report`. The custom form provides **Submit** and, for Event Administrator/System Administrator, **Accept**; PDF generation is provided by the standard Odoo report interface rather than a separate custom form button.

## 19. Committee Closure Reports

### 19.1 Create and submit a report

1. Open **Event Operations > Planning > Committee Reports**.
2. Select **New**.
3. Enter **Name**, **Event**, and **Committee**.
4. Complete **Summary**.
5. Optionally complete **Lessons Learned**.
6. Save while **State** is **Draft**.
7. Select **Submit**.

The system records **Submitted By** and **Submitted On**, and changes **State** to **Submitted**.

### 19.2 Accept a report

1. Open a submitted committee report.
2. An Event Administrator or System Administrator selects **Accept**.
3. The **State** becomes **Accepted**.

The committee report and its committee must belong to the same event.

## 20. Audit Trail

### 20.1 Open the audit trail

Open **Event Operations > Reporting > Audit Trail**.

The audit list shows **Create Date**, **Event**, **User**, **Action**, **Model Name**, **Record ID**, **Record Name**, and optional **Details**. The form also displays **Before Values** and **After Values**.

### 20.2 Audit actions

The implemented action values are:

- **Create**
- **Update**
- **Status Change**
- **Delete**
- **Check-in**
- **Correction**
- **Print**

Use the **Status Changes** and **Deletes** filters. Grouping is available by **Event**, **User**, and **Action**.

Email, phone, password, and token values are masked in audit snapshots when present. The audit list and form are read-only. Audit records are protected from editing and deletion except for superuser-level operations.

## 21. Common End-to-End Workflows

### 21.1 Prepare and launch an event

1. Create the event in **Event Operations > Planning > Events**.
2. Assign active users on the event's **Management > Roles** page.
3. Create committees in **Event Operations > Planning > Committees**.
4. Add committee users in the committee's **Committee Members** field.
5. Create activities in **Event Operations > Planning > Activities**.
6. Set activity **Phase** to **Before Event**, **During Event**, or **After Event**.
7. Mark critical preparation activities with **Readiness Critical**.
8. Create members and guests under **Event Operations > Participants**.
9. Confirm invitations and create registrations.
10. Create badges, select **Generate**, and select **Print**.
11. Select **Start Preparation** on the event.
12. Review **Readiness Percent**, **Readiness State**, overdue activities, and incidents.
13. Select **Readiness Review**.
14. Resolve all readiness blockers.
15. Select **Go Live**.

### 21.2 Manage a guest invitation

1. Open **Event Operations > Participants > Guests & Invitations**.
2. Create the guest with **Category**, contact details, and optional **Accompanying Guest Of**.
3. Select **Send Invitation**. The status becomes **Invited**.
4. Select **Confirm** after confirmation is received. The status becomes **Confirmed**.
5. Select **Register** to create the event registration.
6. Create and print a badge from **Event Operations > Participants > Badges & QR**.

### 21.3 Prepare and issue a badge

1. Confirm the participant has a member or guest record.
2. Open **Event Operations > Participants > Badges & QR** and create a badge.
3. Select one of **Member** or **Guest**, never both.
4. Select **Category**.
5. Select **Generate**.
6. Select **Print** to produce the **Event Badge** PDF.
7. Select **Issue** before or during entry, or allow accepted check-in to issue a Generated/Printed badge automatically.

### 21.4 Run event-day registration

1. Open **Event Operations > Participants > Registration Desk**.
2. Scan the badge QR/barcode.
3. Verify the participant.
4. Complete the standard Odoo registration check-in operation.
5. Confirm the registration becomes checked in and the badge becomes **Issued** when applicable.
6. Review **Event Operations > Participants > Check-in Log** for accepted, duplicate, invalid, re-entry, or corrected records.

### 21.5 Resolve a technical incident

1. Open **Event Operations > Technical Support > Incidents**.
2. Create the incident with **Description**, **Location**, **Priority**, and **Assigned**.
3. Select **Assign**.
4. Select **Investigate**.
5. Enter **Resolution** and select **Resolve**.
6. Select **Verify**.
7. Select **Close**.
8. If the incident was Critical, confirm the event's **Readiness State** returns from **At Risk** after all other blockers are resolved.

### 21.6 Close the event

1. Complete all activities.
2. Close all incidents.
3. Submit committee reports from **Event Operations > Planning > Committee Reports**.
4. Set **Attendance Finalized**.
5. Set **Reports Collected**.
6. Complete **Final Report** and **Lessons Learned**.
7. Set **Final Report Approved**.
8. Select **Start Closure** while the event is **Live**.
9. Select **Close Event** while the event is in **Closure**.
10. Generate the **Final Event Report** from the event's standard Odoo **Print** interface.

## 22. Administrator Guide

### 22.1 Security groups

The module creates the Event Management privilege and nine groups. Assign groups only to internal users who need the corresponding operational access. Event role assignments can add the matching group automatically, but deactivating an event role does not act as a general user deactivation mechanism; review user groups separately when changing responsibilities.

The module also creates record rules for event, role, committee, activity, member, guest, registration, badge, check-in log, incident, committee report, and audit data. Test access with representative users before production rollout.

### 22.2 Scheduled action

The module creates **Event Management: Activity Deadline Alerts** as an active daily scheduled action. It runs `model._cron_deadline_notifications()` as the Odoo root user and handles due-soon and overdue activity notifications.

Review the scheduled action under the standard Odoo Technical settings if alerts are not being processed. Do not manually clear `due_soon_notified` or `overdue_notified` unless you intentionally want another notification cycle.

### 22.3 Email and notification behavior

The module uses:

- Odoo to-do activities for activity assignment.
- `message_notify` for guest status, critical incident, and readiness notifications.
- The Odoo mail/chatter framework on operational records.

There are no custom email templates in this module. Configure Odoo outgoing mail, mail queue processing, recipients' partner email addresses, and access to the event records if email delivery is required.

### 22.4 Configuration dependencies

- The standard Odoo Event model and event registration model must be installed.
- The standard Odoo event barcode/registration desk action must remain available.
- The Python `qrcode` package is required to compute badge QR images.
- PDF reporting requires the normal Odoo report rendering environment.
- Users must be internal users because role and responsible-user fields restrict shared/portal users.

### 22.5 Upgrade considerations

1. Back up the database and filestore.
2. Stop or maintenance-protect the Odoo service if required by the deployment.
3. Replace the module files in the configured custom addons path.
4. Restart Odoo with the correct addons path.
5. Update the Apps list if necessary.
6. Upgrade **Event Management & Digital Technology** from the Odoo Apps interface or the normal Odoo module upgrade procedure.
7. Review the upgrade log for module loading errors.
8. Run the module tests in a dedicated development database before production upgrade.

The initial badge categories, sequences, and scheduled action are loaded as `noupdate` data. Existing category names, sequence counters, and scheduled action settings should be reviewed after an upgrade. Do not modify Odoo core files to resolve module issues.

## 23. Troubleshooting

### Event Operations is not visible

- Confirm the user has at least one Event Management group.
- Confirm the module is installed, not pending installation or upgrade.
- Restart Odoo and update the Apps list after changing the addons path.
- Check that the user is an internal user.

### The user cannot see an event

- Confirm the user has an active event role assignment on the event.
- For a Committee Lead, confirm the user is the committee **Lead**.
- For a Committee Member, confirm the user is in **Committee Members**.
- Check that the event role or committee membership is **Active**.

### A committee member cannot edit a field

This is expected if the user is only in **Committee Member**. The implementation permits committee members to update only **Status**, **Exception**, and **Remarks** on assigned activities.

### Go Live is blocked

Review the event's **Readiness State** and **Open Incidents**. Complete overdue activities marked **Readiness Critical** and close open **Critical** incidents before selecting **Go Live**.

### An activity cannot be completed

Review its **Dependencies**. Every dependency must have **Status** **Completed** first. Also verify the activity's **Due Date** is not before its **Start Date**.

### No guest confirmation notification is received

- Confirm the guest's **Invitation Status** actually changed.
- Confirm an active Event Administrator or Guest Management Team role exists on the event.
- Confirm the recipient user has a partner email address if email is expected.
- Check the standard Odoo mail queue and outgoing mail configuration.

### No deadline notification is received

- Confirm the scheduled action **Event Management: Activity Deadline Alerts** is active.
- Confirm the activity is not **Completed**.
- Check **Due Date**, **is_due_soon**, and **is_overdue** in the activity form.
- Confirm the assigned user has a partner record.
- Check `due_soon_notified` and `overdue_notified`; they prevent repeat notifications.

### A badge has no QR image

- Confirm the registration was created and has a **Badge Code**.
- Confirm the Python `qrcode` dependency is installed in Odoo's Python environment.
- Check the Odoo server log for Python import errors.

### A badge cannot be issued

Select **Generate** first. The **Issue** action rejects a badge that is still **Pending**.

### A participant cannot be checked in twice

This is intentional. Normal duplicate check-in is blocked and creates a **Duplicate Blocked** log. Use an authorized re-entry operation with a reason when the participant is legitimately returning.

### A PDF report does not render

- Confirm the relevant report is available to the user's group.
- Confirm the Odoo PDF rendering dependencies are installed and executable.
- Check the Odoo report log and web asset availability.
- For a badge PDF, confirm the badge has a participant, registration, badge code, and QR image.

## 24. Known Limitations

- The module provides three QWeb PDF reports: **Event Badge**, **Final Event Report**, and **Committee Closure Report**. Activity, guest, badge, attendance, and incident analysis are primarily list, pivot, graph, or standard Odoo registration views rather than separate dedicated PDF reports.
- **Send Invitation** changes invitation status and sends the implemented Odoo notification; it does not provide a custom invitation email template or external guest confirmation portal.
- The standard Odoo Event barcode registration desk and standard Odoo registration UI provide part of the check-in interface. The module extends them rather than replacing them.
- Authorized re-entry and attendance correction are implemented model actions with reason requirements, but the custom module does not add standalone form buttons for them.
- The event **Force Close** model action requires an override reason but is not exposed as a custom event form button. The normal user workflow is **Start Closure** followed by **Close Event** after all closure checks pass.
- The activity **Due Soon** computed field uses the event's **Due-soon days** value, while the model's search implementation uses a three-day search window. Use the event dashboard and activity fields for the configured event window when exact event-specific filtering matters.
- There is no custom attachment management, advanced analytics package, or external integration in this module.
- Guest and participant personal information is deliberately restricted by access rules; users may see counts without being allowed to read the underlying guest details.

## 25. FAQ

### Can one badge be linked to both a member and a guest?

No. A badge must be linked to exactly one **Member** or one **Guest**.

### Can a guest be registered before confirmation?

The guest form exposes **Register** when **Invitation Status** is **Confirmed**. Confirm the guest first.

### Why did the badge become Issued during check-in?

Accepted check-in automatically issues a related badge that was **Generated** or **Printed**.

### Why is a committee lead also shown as a committee member?

The implementation prevents the same user from being both **Lead** and a value in **Committee Members** for one committee. Remove the duplicate membership.

### Why does a committee member see only some activities?

Committee member record rules restrict visibility to activities where the member is **Responsible**. The member can update only the permitted fields on those activities.

### Can a Management / Viewer user read guest email and phone values?

No. The viewer group can use permitted dashboard/report views, but guest personal fields are protected by model access rules.

### What must be true before Close Event works?

All activities must be **Completed**, all incidents **Closed**, **Attendance Finalized** must be enabled, **Reports Collected** must be enabled, and **Final Report Approved** must be enabled.

### Where can I find the activity ID or incident ID?

The activity's read-only **Activity Code** uses the `ACT/YYYY/00001` sequence. The incident's read-only **Incident Code** uses the `INC/YYYY/00001` sequence.

### How do I reprint an issued badge?

Open the badge, enter **Reprint Reason**, and select **Reprint**. The operation increments **Print Count** and generates the Event Badge PDF.

### Can I edit or delete a check-in log?

No. The check-in list is read-only and the model protects logs from edits and deletion except for superuser operations.

### Does changing an invitation status send an email automatically?

It creates the module's Odoo notification to active relevant event roles. Email delivery depends on standard Odoo outgoing mail configuration; there is no custom invitation email template.
