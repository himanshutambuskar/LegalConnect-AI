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


@st.cache_data
def get_cached_css() -> str:
    return STYLE_PATH.read_text(encoding="utf-8")


def load_css() -> None:
    css = get_cached_css()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def current_page() -> str:
    url_page = st.query_params.get("page")
    if url_page and url_page in {"home", "chat", "resources", "categories", "about"}:
        st.session_state["page"] = url_page
    elif "page" not in st.session_state:
        st.session_state["page"] = "home"
    return st.session_state["page"]


def goto(page: str, **params) -> None:
    st.session_state["page"] = page
    next_params = {"page": page}
    for key, value in params.items():
        if value is not None and value != "":
            next_params[key] = value
            st.session_state[key] = value
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
    with st.container(key="lc_header_container"):
        col_logo, col_links, col_start = st.columns(
            [0.22, 0.58, 0.20], vertical_alignment="center"
        )
        with col_logo:
            if st.button("Legal Connect", key="nav_btn_logo", use_container_width=False):
                goto("home")
        with col_links:
            n_cols = st.columns(len(NAV_ITEMS))
            for idx, (key, label) in enumerate(NAV_ITEMS):
                with n_cols[idx]:
                    is_active = active == key
                    btn_type = "primary" if is_active else "secondary"
                    if st.button(label, key=f"nav_btn_{key}", type=btn_type, use_container_width=True):
                        goto(key)
        with col_start:
            if st.button("Start Chat", key="nav_btn_start", type="primary", use_container_width=True):
                goto("chat")


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
