"""Reusable UI building blocks for the STATPRO "Base" dashboard theme."""

from html import escape
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent

PRIMARY = "#605BFF"
INK = "#030229"
MUTED = "#8A8AA0"
GRID = "#F0F0F6"
PALETTE = ["#605BFF", "#5B93FF", "#FF8F6B", "#FFC327", "#3DD598", "#A66DD4", "#2BC8C8", "#FF5A5F"]
SEQ_SCALE = [[0, "#F2F1FF"], [0.5, "#A9A6FF"], [1, "#605BFF"]]
DIV_SCALE = [[0, "#FF8F6B"], [0.5, "#FFFFFF"], [1, "#605BFF"]]
PLOTLY_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]}


def is_id_like(name):
    n = str(name).lower()
    return n in ("id", "index", "row", "rownum") or n.endswith("_id") or n.startswith("id_")


def default_index(columns):
    """Index of the first column that is not an identifier (for selectbox defaults)."""
    for i, c in enumerate(columns):
        if not is_id_like(c):
            return i
    return 0


def inject_css():
    css_path = ROOT / "assets" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def icon(name, size=None):
    style = f' style="font-size:{size}px"' if size else ""
    return f'<span class="material-symbols-rounded"{style}>{name}</span>'


def page_header(title, subtitle, eyebrow="STATPRO", right_html=""):
    st.markdown(
        f"""
        <div class="sp-header">
          <div>
            <div class="sp-eyebrow">{escape(eyebrow)}</div>
            <div class="sp-title">{escape(title)}</div>
            <p class="sp-subtitle">{escape(subtitle)}</p>
          </div>
          <div>{right_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def dataset_chip(name, rows):
    return f'<span class="sp-chip"><span class="dot"></span>{escape(str(name))} · {rows:,} rows</span>'


def kpi_cards(items):
    """items: list of dicts with label, value, icon, tone, optional delta & delta_tone."""
    cards = []
    for it in items:
        delta = ""
        if it.get("delta"):
            delta = f'<div class="sp-kpi-delta txt-{it.get("delta_tone", "muted")}">{escape(it["delta"])}</div>'
        cards.append(
            f"""<div class="sp-kpi">
                  <div class="sp-kpi-icon tone-{it.get('tone', 'indigo')}">{icon(it.get('icon', 'insights'))}</div>
                  <div><div class="sp-kpi-value">{escape(str(it['value']))}</div>
                  <div class="sp-kpi-label">{escape(it['label'])}</div>{delta}</div>
                </div>"""
        )
    st.markdown(f'<div class="sp-kpi-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def stat_row(items):
    """Compact statistic tiles. items: list of (label, value)."""
    html = "".join(
        f'<div class="sp-stat"><div class="l">{escape(str(l))}</div><div class="v">{escape(str(v))}</div></div>'
        for l, v in items
    )
    st.markdown(f'<div class="sp-stat-row">{html}</div>', unsafe_allow_html=True)


def section(title, caption=None, right_html=""):
    cap = f"<p>{escape(caption)}</p>" if caption else ""
    st.markdown(
        f'<div class="sp-section"><div><h4>{escape(title)}</h4>{cap}</div><div>{right_html}</div></div>',
        unsafe_allow_html=True,
    )


def card(key):
    """A white rounded card container (styled via the st-key-card* class)."""
    return st.container(key=f"card_{key}")


def verdict(kind, title, text):
    """kind: sig | nsig | warn"""
    ic = {"sig": "check_circle", "nsig": "info", "warn": "warning"}.get(kind, "info")
    color = {"sig": "#1FB57A", "nsig": "#5B93FF", "warn": "#E8A900"}.get(kind, PRIMARY)
    st.markdown(
        f"""<div class="sp-verdict {kind}">
              <span class="material-symbols-rounded" style="color:{color};font-size:26px">{ic}</span>
              <div><div class="ttl">{escape(title)}</div><div class="txt">{text}</div></div>
            </div>""",
        unsafe_allow_html=True,
    )


def badge(text, kind="info"):
    return f'<span class="sp-badge {kind}">{escape(text)}</span>'


def bar_list(rows, color=PRIMARY):
    """rows: list of (name, fraction 0..1, label)."""
    html = "".join(
        f"""<div class="sp-bar-row"><div class="n" title="{escape(str(n))}">{escape(str(n))}</div>
             <div class="t"><div class="f" style="width:{max(0, min(1, f)) * 100:.1f}%;background:{color}"></div></div>
             <div class="p">{escape(lbl)}</div></div>"""
        for n, f, lbl in rows
    )
    st.markdown(html, unsafe_allow_html=True)


def empty_state(title, text, icon_name="upload_file"):
    st.markdown(
        f"""<div class="sp-feature" style="text-align:center;padding:48px 24px;">
              <div class="sp-kpi-icon tone-indigo" style="margin:0 auto;width:68px;height:68px">{icon(icon_name, 32)}</div>
              <h5 style="font-size:1.2rem;margin-top:16px">{escape(title)}</h5>
              <p style="max-width:460px;margin:0 auto">{escape(text)}</p>
            </div>""",
        unsafe_allow_html=True,
    )


def style_fig(fig, height=360, legend=True, title=None):
    fig.update_layout(
        template="plotly_white",
        height=height,
        title=dict(text=title, font=dict(size=14, color=INK), x=0, xanchor="left") if title else None,
        font=dict(family="Nunito, Segoe UI, sans-serif", color=INK, size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=PALETTE,
        margin=dict(l=8, r=8, t=40 if title else 16, b=8),
        hoverlabel=dict(bgcolor=INK, font_color="#FFFFFF", bordercolor=INK, font_family="Nunito"),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=MUTED)),
        bargap=0.25,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=GRID, tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID, tickfont=dict(color=MUTED))
    return fig


def show_fig(fig, key=None):
    st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG, key=key)


def donut(labels, values, center_title, center_sub, height=300):
    fig = go.Figure(
        go.Pie(
            labels=labels, values=values, hole=0.72, sort=False,
            marker=dict(colors=PALETTE[: len(labels)], line=dict(color="#FFFFFF", width=3)),
            textinfo="none", hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
        )
    )
    fig.add_annotation(text=f"<b>{center_title}</b>", x=0.5, y=0.54, showarrow=False, font=dict(size=24, color=INK))
    fig.add_annotation(text=center_sub, x=0.5, y=0.42, showarrow=False, font=dict(size=12, color=MUTED))
    style_fig(fig, height=height)
    fig.update_layout(legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center", yanchor="top"))
    return fig


def fmt(value, digits=4):
    """Human-friendly number formatting."""
    try:
        if value is None:
            return "—"
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    if v != v:  # NaN
        return "—"
    if abs(v) >= 1e6 or (abs(v) < 1e-3 and v != 0):
        return f"{v:.3e}"
    if float(v).is_integer() and abs(v) < 1e6:
        return f"{int(v):,}"
    return f"{v:,.{digits}f}"


def fmt_p(p):
    try:
        p = float(p)
    except (TypeError, ValueError):
        return "—"
    if p != p:
        return "—"
    return "< 0.0001" if p < 1e-4 else f"{p:.4f}"


def footer(text="STATPRO · Statistical Analysis & Reporting Platform"):
    st.markdown(f'<div class="sp-footer">{escape(text)}</div>', unsafe_allow_html=True)
