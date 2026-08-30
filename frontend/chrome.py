"""Shared layout components: emergency strip, global header, awareness bar, footer."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

import streamlit as st

STYLE_PATH = Path(__file__).with_name("styles.css")

NAV_ITEMS = [
    ("home", "Home"),
    ("resources", "Resources"),
    ("categories", "Categories"),
    ("about", "About"),
]


def load_css() -> None:
    css = STYLE_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def current_page() -> str:
    page = st.query_params.get("page", "home")
    if page not in {"home", "chat", "resources", "categories", "about"}:
        return "home"
    return page


def goto(page: str, **params) -> None:
    next_params = {"page": page}
    for key, value in params.items():
        if value is not None and value != "":
            next_params[key] = value
    st.query_params.clear()
    st.query_params.update(next_params)
    st.rerun()


def hide_sidebar() -> None:
    st.markdown(
        """
        <style>
          [data-testid="stSidebar"],
          [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_emergency() -> None:
    st.markdown(
        '<div class="lc-emergency-strip">✱ EMERGENCY: '
        '<a href="tel:100">100</a> / <a href="tel:112">112</a> / '
        '<a href="tel:181">181</a></div>',
        unsafe_allow_html=True,
    )


def render_header(active: str) -> None:
    links = []
    for key, label in NAV_ITEMS:
        nav_active = "active" if active == key else ""
        links.append(
            f'<a target="_self" class="{nav_active}" href="?page={key}">{label}</a>'
        )

    start_class = (
        "lc-btn-start solid" if active in {"categories", "chat"} else "lc-btn-start"
    )

    html = f"""
    <div class="lc-header">
      <a target="_self" class="lc-logo" href="?page=home">Legal Connect</a>
      <nav class="lc-nav-links">{''.join(links)}</nav>
      <a target="_self" class="{start_class}" href="?page=chat">Start Chat</a>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_awareness_bar() -> None:
    st.markdown(
        '<div class="lc-awareness-bar">ⓘ You’re getting legal awareness guidance, not legal advice</div>',
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        """
        <footer class="lc-footer">
          <div class="lc-footer-inner">
            <div class="lc-footer-top">
              <a target="_self" class="lc-logo" href="?page=home">Legal Connect</a>
              <div class="lc-footer-links">
                <a target="_self" href="?page=about">Legal Disclaimer</a>
                <a target="_self" href="?page=about">Privacy Policy</a>
                <a target="_self" href="?page=about">Terms of Service</a>
                <a target="_self" href="?page=about">Institutional Credits</a>
              </div>
            </div>
            <p class="lc-footer-disclaimer">
              © 2024 Legal Connect. This AI-powered tool provides information, not legal advice.
              Consult a qualified professional for legal proceedings.
            </p>
          </div>
        </footer>
        """,
        unsafe_allow_html=True,
    )


def chat_link(question: str) -> str:
    return f"?page=chat&q={quote(question)}"
