"""Page view implementations for Legal Connect."""

from __future__ import annotations

import html
import re
from datetime import datetime

import streamlit as st

from api_client import ask_question
from chrome import chat_link, goto, render_footer
from content import (
    CATEGORIES,
    CHAT_SIDEBAR_CATEGORIES,
    LEGAL_AID,
    STATUTES,
    SUGGESTED_QUESTIONS,
    get_category,
)

SVG_ICONS = {
    "shield": '<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M12 3 5 6v6c0 5 3.4 7.8 7 9 3.6-1.2 7-4 7-9V6l-7-3Z"/></svg>',
    "gavel": '<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="m14 4 6 6M4 20l7-7M9 7l8 8M3 21h8"/></svg>',
    "cart": '<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="9" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/><path d="M3 4h2l2.2 11h10.3L20 8H7"/></svg>',
    "female": '<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M12 12v9M9 18h6"/></svg>',
    "book": '<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M4 5h7a3 3 0 0 1 3 3v13H7a3 3 0 0 0-3 3V5Zm9 0h7v16a3 3 0 0 0-3-3h-4"/></svg>',
    "car": '<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M3 13h18l-1.5-5H4.5L3 13Zm2 0v4m14-4v4M6.5 17h.01M17.5 17h.01M7 8l1.2-3h7.6L17 8"/></svg>',
    "scales": '<svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M12 3v18M8 21h8M4 8h16M7 8c0 2-1.3 4-3 4S1 10 1 8m22 0c0 2-1.3 4-3 4s-3-2-3-4"/></svg>',
    "home": '<svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M4 11 12 4l8 7v9H4v-9Z"/></svg>',
    "briefcase": '<svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5h8v2"/></svg>',
    "doc": '<svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M7 3h8l5 5v13H7V3Z"/><path d="M15 3v5h5"/></svg>',
    "globe": '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18"/></svg>',
    "phone": '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M6 3h4l1 5-2 1a12 12 0 0 0 6 6l1-2 5 1v4a2 2 0 0 1-2 2A16 16 0 0 1 4 5a2 2 0 0 1 2-2Z"/></svg>',
    "warn": '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M12 3 2 20h20L12 3Zm0 7v5m0 3h.01"/></svg>',
    "checkdoc": '<svg width="22" height="22" fill="none" stroke="#0B2253" stroke-width="1.8" viewBox="0 0 24 24"><path d="M8 3h7l5 5v13H8V3Z"/><path d="m9 14 2 2 4-4"/></svg>',
    "translate": '<svg width="22" height="22" fill="none" stroke="#0B2253" stroke-width="1.8" viewBox="0 0 24 24"><path d="M4 6h10M9 6c0 8-5 12-5 12m5-12c0 8 5 12 5 12M5 18h8M13 13l7 8m0-8-7 8"/></svg>',
    "list": '<svg width="22" height="22" fill="none" stroke="#0B2253" stroke-width="1.8" viewBox="0 0 24 24"><path d="M9 6h12M9 12h12M9 18h12M4 6h.01M4 12h.01M4 18h.01"/></svg>',
    "bot": '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><rect x="5" y="8" width="14" height="10" rx="2"/><path d="M12 8V5M9 13h.01M15 13h.01M8 18v2h8v-2"/></svg>',
    "chat": '<svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M5 16 3 21l5-2h9a4 4 0 0 0 4-4V7a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v5a4 4 0 0 0 4 4Z"/></svg>',
}


def get_icon_html(name: str) -> str:
    return SVG_ICONS.get(name, SVG_ICONS["shield"])


def init_session() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("in_flight", False)
    st.session_state.setdefault("pending_question", None)
    st.session_state.setdefault("sidebar_category", None)
    st.session_state.setdefault(
        "chat_started_at", datetime.now().strftime("%I:%M %p").lstrip("0")
    )


def clean_model_answer(text: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S | re.I)
    cleaned = re.sub(r"</?think>", "", cleaned, flags=re.I)
    return cleaned.strip()


def answer_to_html(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    lines = escaped.splitlines()
    parts: list[str] = []
    list_type = None

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            parts.append(f"</{list_type}>")
            list_type = None

    for raw in lines:
        line = raw.strip()
        if not line:
            close_list()
            continue
        numbered = re.match(r"^(\d+)\.\s+(.*)$", line)
        bullet = re.match(r"^[-*]\s+(.*)$", line)
        heading = re.match(r"^#{2,6}\s+(.*)$", line)
        if numbered:
            if list_type != "ol":
                close_list()
                parts.append('<ol class="lc-steps-ol">')
                list_type = "ol"
            parts.append(f"<li>{numbered.group(2)}</li>")
        elif bullet:
            if list_type != "ul":
                close_list()
                parts.append("<ul>")
                list_type = "ul"
            parts.append(f"<li>{bullet.group(1)}</li>")
        elif heading:
            close_list()
            parts.append(f"<h4>{heading.group(1)}</h4>")
        else:
            close_list()
            parts.append(f"<p>{line}</p>")
    close_list()
    return "".join(parts) or f"<p>{escaped}</p>"


def split_heading(answer: str) -> tuple[str, str]:
    text = clean_model_answer(answer)
    if not text:
        return "Legal Awareness Answer", ""
    lines = [ln.rstrip() for ln in text.splitlines()]
    first = lines[0].strip()
    first = re.sub(r"^#+\s*", "", first).strip("*_ ")
    if 8 <= len(first) <= 110 and not first.startswith(("-", "*", "1.")):
        rest = "\n".join(lines[1:]).strip()
        return first, rest or text
    return "Legal Awareness Guidance", text


def format_source_label(source: dict) -> str:
    act = (source.get("act") or "").strip() or "Official Legal Source"
    section = source.get("section")
    title = (source.get("title") or "").strip()
    if section not in (None, "", "N/A"):
        sec_str = str(section).strip()
        if not sec_str.lower().startswith("section"):
            sec_str = f"Section {sec_str}"
        return f"{act} — {sec_str}"
    if title:
        return f"{act} — {title}"
    return act


def render_assistant_message(message: dict) -> None:
    if message.get("error"):
        st.markdown(
            f'<div class="lc-error" style="background:#FFF5F5; border:1px solid #F0C7C2; color:#9E2A2B; border-radius:12px; padding:16px;">{html.escape(message["error"])}</div>',
            unsafe_allow_html=True,
        )
        return

    heading, body = split_heading(message.get("content") or "")
    sources = message.get("sources") or []
    pills = []
    seen = set()

    for source in sources:
        if not isinstance(source, dict):
            continue
        label = format_source_label(source)
        url = source.get("source_url") or ""
        key = (label, url)
        if key in seen:
            continue
        seen.add(key)
        safe_label = html.escape(label)

        if url:
            safe_url = html.escape(url, quote=True)
            pills.append(
                f'<a class="lc-source-btn" href="{safe_url}" target="_blank" rel="noopener noreferrer">📄 {safe_label}</a>'
            )
        else:
            pills.append(
                f'<span class="lc-source-btn" style="cursor:default;">📄 {safe_label}</span>'
            )

    sources_html = ""
    if pills:
        sources_html = (
            '<div class="lc-sources-section">'
            '<div class="lc-sources-title">SOURCES REFERENCED</div>'
            f'<div class="lc-sources-pills">{"".join(pills)}</div>'
            "</div>"
        )

    body_html = answer_to_html(body) if body else ""
    st.markdown(
        f"""
        <div class="lc-ai-msg-card">
          <div class="lc-ai-header-badge">{get_icon_html("bot")} Legal Connect AI</div>
          <h3>{html.escape(heading)}</h3>
          <div class="body">{body_html}</div>
          {sources_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_user_message(content: str) -> None:
    st.markdown(
        f'<div class="lc-user-msg-row"><div class="lc-user-msg-bubble">{html.escape(content)}</div></div>',
        unsafe_allow_html=True,
    )


def run_backend_question(question: str) -> None:
    if st.session_state.in_flight:
        return
    clean_query = question.strip()
    if not clean_query:
        st.warning("Please enter a valid question.")
        return

    st.session_state.in_flight = True
    st.session_state.messages.append({"role": "user", "content": clean_query})
    with st.spinner("Retrieving verified legal sources and preparing answer..."):
        result = ask_question(clean_query)
    st.session_state.in_flight = False

    if result["ok"]:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": result["answer"],
                "sources": result["sources"],
            }
        )
    else:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "error": result["error"],
                "content": "",
                "sources": [],
            }
        )


def render_home() -> None:
    st.markdown(
        """
        <section class="lc-home-hero">
          <h1>Understand Your Legal Rights, Instantly.</h1>
          <p>Access verified, plain-language legal information to guide your next steps with confidence.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # Search Bar (Native Streamlit Form, no hash anchors)
    _, search_col, _ = st.columns([0.1, 0.8, 0.1])
    with search_col:
        with st.form("home_search", border=False, clear_on_submit=False):
            qcol, bcol = st.columns([0.82, 0.18], vertical_alignment="center")
            with qcol:
                query = st.text_input(
                    "Ask a legal question",
                    placeholder="Ask a legal question...",
                    label_visibility="collapsed",
                )
            with bcol:
                submitted = st.form_submit_button(
                    "Ask", type="primary", use_container_width=True
                )
        if submitted:
            if not query.strip():
                st.warning("Please enter a legal question.")
            else:
                st.session_state.pending_question = query.strip()
                goto("chat")

    # Suggested Questions Pills as Native Interactive Buttons (No URL Hash!)
    st.markdown('<div class="lc-suggested-pills-label">SUGGESTED QUESTIONS</div>', unsafe_allow_html=True)
    pcols = st.columns(len(SUGGESTED_QUESTIONS))
    for idx, q_text in enumerate(SUGGESTED_QUESTIONS):
        with pcols[idx]:
            if st.button(q_text, key=f"sugg_chip_{idx}", use_container_width=True):
                st.session_state.pending_question = q_text
                goto("chat")

    # Section Title
    st.markdown('<h2 class="lc-section-heading">Six ways we can help</h2>', unsafe_allow_html=True)

    # 6 Category Cards Grid in 3 columns desktop layout
    for row_idx in range(0, len(CATEGORIES), 3):
        cols = st.columns(3)
        for col_idx, col in enumerate(cols):
            cat_index = row_idx + col_idx
            if cat_index < len(CATEGORIES):
                cat = CATEGORIES[cat_index]
                with col:
                    card_html = f"""
                    <a target="_self" class="lc-cat-card" href="?page=categories&cat={cat['id']}">
                      <div class="lc-card-icon-box">{get_icon_html(cat['icon'])}</div>
                      <h3>{html.escape(cat['name'])}</h3>
                      <p>{html.escape(cat['tagline'])}</p>
                    </a>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

    # Bottom 3 Feature Pillars
    st.markdown('<div class="lc-home-features-divider"></div>', unsafe_allow_html=True)
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        st.markdown(
            f"""
            <div class="lc-feature-item">
              <div class="lc-card-icon-box">{get_icon_html("checkdoc")}</div>
              <h3>Grounded in Verified Sources</h3>
              <p>Information curated from official government databases and updated legal codes.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with fcol2:
        st.markdown(
            f"""
            <div class="lc-feature-item">
              <div class="lc-card-icon-box">{get_icon_html("translate")}</div>
              <h3>Plain-Language Answers</h3>
              <p>Complex legal jargon simplified for immediate comprehension.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with fcol3:
        st.markdown(
            f"""
            <div class="lc-feature-item">
              <div class="lc-card-icon-box">{get_icon_html("list")}</div>
              <h3>Step-by-Step Guidance</h3>
              <p>Clear, actionable steps on how to proceed with legal procedures.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_footer()


def render_resources() -> None:
    helplines_html = """
      <div class="lc-helpline-grid">
        <div class="lc-helpline-box"><span>WOMEN IN DISTRESS</span><strong>181</strong></div>
        <div class="lc-helpline-box"><span>CYBER CRIME</span><strong>1930</strong></div>
        <div class="lc-helpline-box"><span>CONSUMER HELPLINE</span><strong>1915</strong></div>
      </div>
    """
    # Emergency Card (Self-contained HTML snippet)
    st.markdown(
        f"""
        <div class="lc-emergency-card-wrapper">
          <div class="lc-emergency-title-box">
            <h2>{get_icon_html("warn")} Emergency Contacts</h2>
            <p>Immediate assistance helplines for critical situations.</p>
          </div>
          {helplines_html}
        </div>
        <h1 style="font-size:42px; margin-bottom:12px;">Verified Resources</h1>
        <p style="color:var(--slate-gray); font-size:16.5px; max-width:740px; margin-bottom:28px;">
          A curated directory of official legal resources, statutory portals, and trusted advisory bodies for comprehensive legal research.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Native Streamlit Expanders
    with st.expander("Official Statutes & Codes", expanded=False):
        for item in STATUTES:
            st.markdown(
                f"**[{item['title']}]({item['url']})**  \n*{item['detail']}*"
            )
    with st.expander("Legal Aid Services", expanded=False):
        for item in LEGAL_AID:
            st.markdown(
                f"**[{item['title']}]({item['url']})**  \n*{item['detail']}*"
            )

    render_footer()


def render_about() -> None:
    st.markdown(
        """
        <div style="max-width:1040px; margin:0 auto; padding:24px 16px;">
          <h1 style="font-size:42px; margin-bottom:16px;">About Legal Connect</h1>
          <p style="color:var(--slate-gray); font-size:17px; line-height:1.65; max-width:840px;">
            Legal Connect is an AI-powered legal awareness platform designed to help citizens understand official Indian laws, citizen rights, and legal procedures in plain language.
          </p>
          <p style="color:var(--slate-gray); font-size:16px; line-height:1.65; max-width:840px;">
            All answers are generated using a Retrieval-Augmented Generation (RAG) pipeline trained over verified primary sources, including the Bharatiya Nyaya Sanhita, 2023 (BNS), the Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS), and the Bharatiya Sakshya Adhiniyam, 2023 (BSA).
          </p>
          <p style="color:var(--slate-gray); font-size:16px; line-height:1.65; max-width:840px; margin-bottom:36px;">
            <strong>Legal Disclaimer:</strong> Legal Connect provides legal information for awareness only and does not constitute formal legal advice. For formal proceedings or legal representation, consult a qualified advocate.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        st.markdown(
            f"""
            <div class="lc-feature-item" style="background:#fff; border:1px solid var(--border-light); border-radius:12px; padding:24px;">
              <div class="lc-card-icon-box">{get_icon_html("checkdoc")}</div>
              <h3>Verified Legal Sources</h3>
              <p>Direct citations and official source links returned with every query response.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with fcol2:
        st.markdown(
            f"""
            <div class="lc-feature-item" style="background:#fff; border:1px solid var(--border-light); border-radius:12px; padding:24px;">
              <div class="lc-card-icon-box">{get_icon_html("translate")}</div>
              <h3>Plain-Language Clarity</h3>
              <p>Legal acts and complex statutory sections explained in accessible, clear English.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with fcol3:
        st.markdown(
            f"""
            <div class="lc-feature-item" style="background:#fff; border:1px solid var(--border-light); border-radius:12px; padding:24px;">
              <div class="lc-card-icon-box">{get_icon_html("list")}</div>
              <h3>Structured Guidance</h3>
              <p>Clear recommended steps and actionable procedures for legal situations.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_footer()


def render_categories() -> None:
    # Full Category Navigation Bar (All categories accessible!)
    selected_cat_id = st.query_params.get("cat", CATEGORIES[0]["id"])
    
    st.markdown('<h1 style="font-size:42px; margin-bottom:16px;">Legal Categories</h1>', unsafe_allow_html=True)
    
    cat_cols = st.columns(len(CATEGORIES))
    for idx, c_item in enumerate(CATEGORIES):
        with cat_cols[idx]:
            is_active = c_item["id"] == selected_cat_id
            btn_type = "primary" if is_active else "secondary"
            if st.button(c_item["name"], key=f"cat_tab_{c_item['id']}", type=btn_type, use_container_width=True):
                st.query_params["page"] = "categories"
                st.query_params["cat"] = c_item["id"]
                st.rerun()

    cat = get_category(selected_cat_id)

    # Hero Banner (Self-contained HTML)
    st.markdown(
        f"""
        <section class="lc-cat-hero-banner">
          <div class="lc-cat-hero-content">
            <h1>{html.escape(cat['name'])}</h1>
            <p>{html.escape(cat['description'])}</p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([1.7, 0.9], gap="large")

    with left_col:
        st.markdown('<h2 style="font-size:26px; margin-bottom:16px;">Common Questions</h2>', unsafe_allow_html=True)
        for faq in cat["faqs"]:
            with st.expander(faq["q"], expanded=False):
                st.write(faq["a"])

        st.markdown(
            f'<h2 style="font-size:26px; margin:32px 0 16px;">{html.escape(cat["stepper_title"])}</h2>',
            unsafe_allow_html=True,
        )

        scols = st.columns(4)
        for idx, step in enumerate(cat["steps"], start=1):
            with scols[idx - 1]:
                step_html = f"""
                <div class="lc-step-item">
                  <div class="lc-step-circle">{idx}</div>
                  <h4>{html.escape(step['title'])}</h4>
                  <p>{html.escape(step['detail'])}</p>
                </div>
                """
                st.markdown(step_html, unsafe_allow_html=True)

    with right_col:
        resources_html = "".join(
            f"""
            <div class="lc-widget-item">
              <div>{get_icon_html(res['icon'])}</div>
              <div>
                <a target="_blank" href="{html.escape(res['url'], quote=True)}" rel="noopener noreferrer">{html.escape(res['title'])}</a>
                <span>{html.escape(res['detail'])}</span>
              </div>
            </div>
            """
            for res in cat["resources"]
        )
        st.markdown(
            f"""
            <div class="lc-resource-widget-card">
              <h3>{get_icon_html("shield")} Verified Resources</h3>
              {resources_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Bottom CTA Button
    if st.button(f"💬 Ask Legal Connect about {cat['name']}", type="primary", use_container_width=False):
        st.session_state.pending_question = cat["ask_prompt"]
        goto("chat")

    render_footer()


def render_chat_sidebar() -> None:
    if st.button("＋  New Chat", use_container_width=True, disabled=st.session_state.in_flight):
        st.session_state.messages = []
        st.session_state.pending_question = None
        st.session_state.sidebar_category = None
        st.session_state.chat_started_at = (
            datetime.now().strftime("%I:%M %p").lstrip("0")
        )
        st.query_params.clear()
        st.query_params["page"] = "chat"
        st.rerun()

    st.markdown(
        "<p style='margin:20px 0 10px 4px; font-size:11px; letter-spacing:0.12em; color:var(--muted-gray); font-weight:700; text-transform:uppercase;'>CATEGORIES</p>",
        unsafe_allow_html=True,
    )

    for item in CHAT_SIDEBAR_CATEGORIES:
        selected = st.session_state.sidebar_category == item["id"]
        label = f" {item['name']}"
        if st.button(
            label,
            key=f"sidebar_cat_{item['id']}",
            use_container_width=True,
            disabled=st.session_state.in_flight,
        ):
            st.session_state.sidebar_category = item["id"]
            st.session_state.pending_question = item["prompt"]
            st.rerun()
        if selected:
            st.caption("Asking from verified statutes")


def render_chat() -> None:
    incoming_query = st.query_params.get("q")
    if incoming_query:
        st.session_state.pending_question = incoming_query
        st.query_params.clear()
        st.query_params["page"] = "chat"

    pending = st.session_state.pending_question
    if pending and not st.session_state.in_flight:
        st.session_state.pending_question = None
        run_backend_question(pending)
        st.rerun()

    # Date Pill
    st.markdown(
        f'<div class="lc-chat-date-pill"><span>Today, {html.escape(st.session_state.chat_started_at)}</span></div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.messages:
        st.markdown(
            '<div style="text-align:center; color:var(--slate-gray); padding:48px 16px; font-size:15px;">Ask a legal question to receive plain-language guidance grounded in official statutes. This is legal awareness information, not legal advice.</div>',
            unsafe_allow_html=True,
        )

    for message in st.session_state.messages:
        if message["role"] == "user":
            render_user_message(message["content"])
        else:
            render_assistant_message(message)

    # Chat Input Form Bar
    _, chat_form_col, _ = st.columns([0.05, 0.9, 0.05])
    with chat_form_col:
        with st.form("chat_form", border=False, clear_on_submit=True):
            c_attach, c_input, c_mic, c_send = st.columns(
                [0.08, 0.72, 0.08, 0.12], vertical_alignment="center"
            )
            with c_attach:
                st.form_submit_button(
                    "📎", disabled=True, help="File attachments disabled."
                )
            with c_input:
                follow_up = st.text_input(
                    "Follow-up",
                    placeholder="Ask a follow-up question...",
                    label_visibility="collapsed",
                    disabled=st.session_state.in_flight,
                )
            with c_mic:
                st.form_submit_button(
                    "🎤", disabled=True, help="Voice input disabled."
                )
            with c_send:
                sent = st.form_submit_button(
                    "➤", type="primary", disabled=st.session_state.in_flight
                )
        if sent:
            if st.session_state.in_flight:
                st.info("Please wait for the current answer to complete.")
            elif not (follow_up or "").strip():
                st.warning("Please enter a valid question.")
            else:
                st.session_state.pending_question = follow_up.strip()
                st.rerun()

        st.markdown(
            '<p class="lc-chat-disclaimer-note">AI can make mistakes. Verify important information.</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="lc-chat-disclaimer-note">This AI-powered tool provides information, not legal advice. Consult a qualified professional for legal proceedings.</p>',
            unsafe_allow_html=True,
        )
