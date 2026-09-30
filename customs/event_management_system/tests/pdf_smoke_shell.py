"""Manual Odoo shell smoke test for the two PDF reports.

Run it against a database where the module is installed and an HTTP server is
listening (QWeb PDF rendering goes through wkhtmltopdf, which fetches the
report URL over HTTP):

    ./odoo-bin shell -d <database> --http-port=8070 < tests/pdf_smoke_shell.py

The rendered PDFs are written next to this file so they can be inspected.
"""

import os
import tempfile
from datetime import timedelta

from odoo import fields


event = env["event.event"].create(
    {
        "name": "PDF Smoke Event",
        "date_begin": fields.Datetime.now() + timedelta(days=1),
        "date_end": fields.Datetime.now() + timedelta(days=2),
        "final_report": "PDF rendering verified.",
        "lessons_learned": "Keep automated report smoke coverage.",
    }
)
guest = env["ems.guest"].create(
    {"name": "PDF Guest", "event_id": event.id, "organization": "Smoke Org"}
)
badge = env["ems.badge"].create(
    {
        "event_id": event.id,
        "guest_id": guest.id,
        "category_id": env.ref("event_management_system.badge_category_guest").id,
    }
)
badge.action_generate()

badge_report = env.ref("event_management_system.action_report_ems_badge")
badge_pdf, badge_type = badge_report.with_context(force_report_rendering=True)._render_qweb_pdf(
    badge_report.report_name, badge.ids
)
final_report = env.ref("event_management_system.action_report_ems_final_event")
final_pdf, final_type = final_report.with_context(force_report_rendering=True)._render_qweb_pdf(
    final_report.report_name, event.ids
)

assert badge_type == "pdf" and badge_pdf.startswith(b"%PDF")
assert final_type == "pdf" and final_pdf.startswith(b"%PDF")
output_dir = os.path.join(tempfile.gettempdir(), "ems_report_smoke")
os.makedirs(output_dir, exist_ok=True)
badge_path = os.path.join(output_dir, "ems_badge_smoke.pdf")
final_path = os.path.join(output_dir, "ems_final_smoke.pdf")
with open(badge_path, "wb") as badge_file:
    badge_file.write(badge_pdf)
with open(final_path, "wb") as final_file:
    final_file.write(final_pdf)
print(f"badge_pdf={len(badge_pdf)} bytes -> {badge_path}")
print(f"final_pdf={len(final_pdf)} bytes -> {final_path}")
env.cr.rollback()
