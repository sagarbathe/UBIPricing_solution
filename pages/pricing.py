"""
📐 Pricing / Actuarial Persona Page

Purpose: "Are we pricing risk correctly, and will we hit our target loss ratio?"

Power BI Report: Pricing Adequacy Dashboard
Data Agent: Pricing Copilot
"""

import streamlit as st

from config import POWERBI_REPORTS, DATA_AGENTS
from components.powerbi_embed import render_powerbi_report
from components.data_agent_chat import render_data_agent_chat, render_data_agent_chat_input


def render() -> None:
    """Render the Pricing / Actuarial persona page."""

    st.header("📐 Pricing / Actuarial")
    st.caption(
        "Are we pricing risk correctly, and will we hit our target loss ratio?"
    )
    st.divider()

    # ── View mode management ──────────────────────────────
    view_key = "pricing_view_mode"
    if view_key not in st.session_state:
        st.session_state[view_key] = "both"

    view_mode = st.session_state[view_key]

    # ── View toggle toolbar ───────────────────────────────
    tb = st.columns([1, 1, 1, 4])
    with tb[0]:
        if st.button("◻️ Split View", key="pricing_split",
                     disabled=(view_mode == "both"),
                     use_container_width=True):
            st.session_state[view_key] = "both"
            st.rerun()
    with tb[1]:
        if st.button("📊 Expand Report", key="pricing_expand_report",
                     disabled=(view_mode == "report"),
                     use_container_width=True):
            st.session_state[view_key] = "report"
            st.rerun()
    with tb[2]:
        if st.button("💬 Expand Agent", key="pricing_expand_agent",
                     disabled=(view_mode == "agent"),
                     use_container_width=True):
            st.session_state[view_key] = "agent"
            st.rerun()

    # ── Helper: render report content ─────────────────────
    def _render_report():
        report = POWERBI_REPORTS["pricing"]
        render_powerbi_report(
            embed_url=report["embed_url"],
            title=report["title"],
            description=report["description"],
            report_id=report.get("report_id", ""),
            group_id=report.get("group_id", ""),
        )
        st.divider()
        st.markdown("#### 📋 Report Contents")
        st.markdown(
            """
- **Expected Loss Cost vs Recommended Premium** — scatter view to identify mispriced policies
- **Loss Ratio by Coverage Type** — are certain coverages consistently unprofitable?
- **Policies where ELC > Premium** — underpricing risk flagged visually
            """
        )

    # ── Helper: render agent content ──────────────────────
    def _render_agent():
        agent = DATA_AGENTS["pricing"]
        render_data_agent_chat(
            agent_name=agent["name"],
            endpoint=agent["endpoint"],
            suggested_prompts=agent["suggested_prompts"],
        )

    # ── Layout based on view mode ─────────────────────────
    if view_mode == "both":
        col_report, col_agent = st.columns([3, 2])
        with col_report:
            _render_report()
        with col_agent:
            _render_agent()
    elif view_mode == "report":
        _render_report()
    elif view_mode == "agent":
        _render_agent()

    # Chat input must be at root level (Streamlit restriction)
    if view_mode in ("both", "agent"):
        agent = DATA_AGENTS["pricing"]
        render_data_agent_chat_input(
            agent_name=agent["name"],
            endpoint=agent["endpoint"],
        )
