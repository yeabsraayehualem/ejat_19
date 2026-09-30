{
    "name": "Event Management Overall Dashboard",
    "version": "19.0.1.0.0",
    "summary": "A consolidated, chart-based overview of event operations",
    "category": "Marketing/Events",
    "author": "Yoraki",
    "license": "LGPL-3",
    "depends": ["event_management_system", "web"],
    "data": ["views/dashboard_menu.xml"],
    "assets": {
        "web.assets_backend": [
            "event_management_dashboard/static/src/dashboard.js",
            "event_management_dashboard/static/src/dashboard.xml",
            "event_management_dashboard/static/src/dashboard.scss",
        ],
    },
    "application": True,
    "installable": True,
}
