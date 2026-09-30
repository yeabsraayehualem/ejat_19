/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

export class EventOverallDashboard extends Component {
    static template = "event_management_dashboard.OverallDashboard";

    setup() {
        this.orm = useService("orm");
        this.state = useState({ data: null, loading: true, error: null, eventId: false });
        onWillStart(() => this.loadDashboard());
    }

    async loadDashboard() {
        this.state.loading = true;
        this.state.error = null;
        try {
            this.state.data = await this.orm.call(
                "ems.overall.dashboard",
                "get_dashboard_data",
                [this.state.eventId || false]
            );
        } catch (error) {
            this.state.error = error.message || "Dashboard data could not be loaded.";
        } finally {
            this.state.loading = false;
        }
    }

    async onEventChange(event) {
        this.state.eventId = event.target.value ? Number(event.target.value) : false;
        await this.loadDashboard();
    }

    async refresh() {
        await this.loadDashboard();
    }

    get kpiCards() {
        const k = this.state.data?.kpis;
        if (!k) return [];
        return [
            { label: "Events", value: k.events, icon: "fa-calendar", tone: "blue" },
            { label: "Committees", value: k.committees, icon: "fa-sitemap", tone: "purple" },
            { label: "Activities", value: k.activities, icon: "fa-list-check", tone: "teal", note: `${this.state.data.activity_completion_percent}% completed` },
            { label: "Overdue Activities", value: k.overdue, icon: "fa-clock-o", tone: "red" },
            { label: "Members", value: k.members, icon: "fa-users", tone: "blue" },
            { label: "Guests", value: k.guests, icon: "fa-address-card", tone: "purple" },
            { label: "Registered", value: k.registrations, icon: "fa-ticket", tone: "teal" },
            { label: "Checked In", value: k.checked_in, icon: "fa-check-circle", tone: "green", note: `${this.state.data.attendance_percent}% attendance` },
            { label: "Badges", value: k.badges, icon: "fa-id-badge", tone: "blue", note: `${k.issued_badges} issued` },
            { label: "Open Incidents", value: k.open_incidents, icon: "fa-wrench", tone: "orange", note: `${k.critical_incidents} critical` },
        ];
    }
}

registry.category("actions").add("event_management_dashboard.overall", EventOverallDashboard);
