"""Page view implementations for Legal Connect."""

from __future__ import annotations

import html
import re
from datetime import datetime

import streamlit as st

from api_client import ask_question, ask_question_stream
from chrome import chat_link, goto, render_footer

try:
    from citation_utils import extract_allowed_section_numbers, sanitize_unsupported_citations
except ImportError:
    from frontend.citation_utils import extract_allowed_section_numbers, sanitize_unsupported_citations
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
    cleaned = re.sub(r"<think>.*$", "", cleaned, flags=re.S | re.I)
    cleaned = re.sub(r"</?think>", "", cleaned, flags=re.I)
    return cleaned.strip()


def answer_to_html(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"(?<!\*)\*(?!\s)([^*\n]+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", escaped)
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
            h_text = heading.group(1).strip()
            h_lower = h_text.lower()
            badge_class = "lc-section-header"
            if "what this means" in h_lower:
                badge_class += " lc-sec-means"
            elif "what the law says" in h_lower:
                badge_class += " lc-sec-law"
            elif "what you can" in h_lower or "consider doing" in h_lower:
                badge_class += " lc-sec-actions"
            elif "important" in h_lower:
                badge_class += " lc-sec-important"
            parts.append(f'<h4 class="{badge_class}">{h_text}</h4>')
        else:
            close_list()
            parts.append(f"<p>{line}</p>")
    close_list()
    return "".join(parts) or f"<p>{escaped}</p>"


def split_heading(answer: str) -> tuple[str, str]:
    text = clean_model_answer(answer)
    if not text:
        return "Legal Awareness Guidance", ""
    lines = [ln.rstrip() for ln in text.splitlines()]
    first = lines[0].strip()
    m = re.match(r"^#+\s*(.+)$", first)
    if m:
        h = m.group(1).strip("*_ ")
        h_lower = h.lower()
        if not any(h_lower.startswith(sec) for sec in ["what this means", "what the law says", "what you can", "consider doing", "important", "legal awareness"]):
            rest = "\n".join(lines[1:]).strip()
            return h, rest or text
    return "Legal Awareness Guidance", text


def render_sources_section(sources: list) -> str:
    if not sources:
        return ""

    cards = []
    seen = set()
    for s in sources:
        if not isinstance(s, dict):
            continue
        act = (s.get("act") or "").strip()
        sec = s.get("section") or s.get("section_number") or ""
        title = (s.get("title") or "").strip()
        source_name = (s.get("source") or "").strip()
        url = (s.get("source_url") or "").strip()

        sec_str = str(sec).strip()
        if sec_str and not sec_str.lower().startswith("section"):
            sec_str = f"Section {sec_str}"

        key = (act, sec_str, title)
        if key in seen:
            continue
        seen.add(key)

        detail_line = f"{sec_str} — {title}" if (sec_str and title) else (sec_str or title or "Statutory Provision")
        source_badge = f'<span class="lc-source-tag">{html.escape(source_name)}</span>' if source_name else ""
        link_html = (
            f'<a class="lc-source-link" href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">View Official Statute ↗</a>'
            if url
            else ""
        )

        cards.append(
            '<div class="lc-source-card">'
            '<div class="lc-source-card-top">'
            f'<span class="lc-source-act">{html.escape(act or "Official Indian Statute")}</span>'
            f'{source_badge}'
            '</div>'
            f'<div class="lc-source-card-sec">{html.escape(detail_line)}</div>'
            f'{link_html}'
            '</div>'
        )

    if not cards:
        return ""

    return (
        '<div class="lc-sources-section">'
        '<div class="lc-sources-title">Sources referenced</div>'
        f'<div class="lc-sources-grid">{"".join(cards)}</div>'
        '</div>'
    )


def render_assistant_message(message: dict) -> None:
    if message.get("error"):
        st.markdown(
            f'<div class="lc-error" style="background:#FFF5F5; border:1px solid #F0C7C2; color:#9E2A2B; border-radius:12px; padding:16px;">{html.escape(message["error"])}</div>',
            unsafe_allow_html=True,
        )
        return

    content = clean_model_answer(message.get("content") or "")
    heading, body = split_heading(content)
    sources = message.get("sources") or []
    sources_html = render_sources_section(sources)
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
        f"""
        <div class="lc-user-msg-row">
          <div class="lc-user-msg-wrapper">
            <div class="lc-user-label">You</div>
            <div class="lc-user-msg-bubble">{html.escape(content)}</div>
          </div>
        </div>
        """,
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

    # Prepare prior conversation history (last 6 turns)
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[-6:]
        if "content" in m and m["content"]
    ]

    # Append user question to state immediately so it renders in conversation
    st.session_state.messages.append({"role": "user", "content": clean_query})

    sources = []
    full_text = ""
    error_msg = None

    status_placeholder = st.empty()
    status_placeholder.markdown(
        """
        <div class="lc-ai-msg-card lc-ai-msg-streaming">
          <div class="lc-ai-header-badge">⚖️ Legal Connect AI</div>
          <div class="lc-searching-indicator">
            <span class="lc-pulse-dot"></span> Searching verified legal sources & preparing response...
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    card_placeholder = st.empty()

    try:
        for event in ask_question_stream(clean_query, history=history):
            evt_type = event.get("type")
            if evt_type == "meta":
                sources = event.get("sources", [])
                status_placeholder.markdown(
                    """
                    <div class="lc-ai-msg-card lc-ai-msg-streaming">
                      <div class="lc-ai-header-badge">⚖️ Legal Connect AI</div>
                      <div class="lc-searching-indicator">
                        <span class="lc-pulse-dot"></span> Legal sources identified. Generating grounded response...
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif evt_type == "token":
                status_placeholder.empty()
                full_text += event.get("token", "")
                cleaned_so_far = clean_model_answer(full_text)
                heading, body = split_heading(cleaned_so_far)
                body_html = answer_to_html(body) if body else ""
                card_placeholder.markdown(
                    f"""
                    <div class="lc-ai-msg-card lc-ai-msg-streaming">
                      <div class="lc-ai-header-badge">{get_icon_html("bot")} Legal Connect AI</div>
                      <h3>{html.escape(heading)}</h3>
                      <div class="body">{body_html}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif evt_type == "error":
                error_msg = event.get("error")
    except Exception:
        error_msg = "I couldn't generate a response right now. Please try again."

    status_placeholder.empty()
    card_placeholder.empty()
    st.session_state.in_flight = False

    cleaned_final = clean_model_answer(full_text)
    if sources:
        try:
            allowed = extract_allowed_section_numbers(sources)
            cleaned_final = sanitize_unsupported_citations(cleaned_final, allowed)
        except Exception:
            pass

    if error_msg and not cleaned_final:
        # Fallback to standard ask_question if stream encounters issue
        fallback = ask_question(clean_query, history=history)
        if fallback["ok"]:
            fb_content = clean_model_answer(fallback["answer"])
            if fallback.get("sources"):
                try:
                    fb_allowed = extract_allowed_section_numbers(fallback["sources"])
                    fb_content = sanitize_unsupported_citations(fb_content, fb_allowed)
                except Exception:
                    pass
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": fb_content,
                    "sources": fallback["sources"],
                }
            )
        else:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "error": fallback.get("error") or error_msg,
                    "content": "",
                    "sources": [],
                }
            )
    else:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": cleaned_final,
                "sources": sources,
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

    # Search Bar & Suggested Questions (Unified Global Container Width)
    with st.form("home_search", border=False, clear_on_submit=False):
        qcol, bcol = st.columns([0.84, 0.16], vertical_alignment="center")
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

    # Suggested Questions Pills inside the exact same container width
    st.markdown('<div class="lc-suggested-pills-label">SUGGESTED QUESTIONS</div>', unsafe_allow_html=True)
    pcols = st.columns(len(SUGGESTED_QUESTIONS))
    for idx, q_text in enumerate(SUGGESTED_QUESTIONS):
        with pcols[idx]:
            if st.button(q_text, key=f"sugg_chip_{idx}", use_container_width=True):
                st.session_state.pending_question = q_text
                goto("chat")

    # Section Title
    st.markdown('<h2 class="lc-section-heading">Six ways we can help</h2>', unsafe_allow_html=True)

    # 6 Category Cards Grid in strict 3-column CSS Grid (Equal width, equal height, consistent icons & text)
    cards_html = []
    for cat in CATEGORIES:
        card = (
            f'<a target="_self" class="lc-cat-card" href="?page=categories&cat={cat["id"]}">'
            f'<div class="lc-card-icon-box">{get_icon_html(cat["icon"])}</div>'
            f'<h3>{html.escape(cat["name"])}</h3>'
            f'<p>{html.escape(cat["tagline"])}</p>'
            '</a>'
        )
        cards_html.append(card)
    grid_html = f'<div class="lc-cat-grid">{"".join(cards_html)}</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

    # Bottom 3 Feature Pillars in strict 3-column CSS Grid
    st.markdown('<div class="lc-home-features-divider"></div>', unsafe_allow_html=True)
    features_html = (
        '<div class="lc-features-grid">'
        f'<div class="lc-feature-item"><div class="lc-card-icon-box">{get_icon_html("checkdoc")}</div><h3>Grounded in Verified Sources</h3><p>Information curated from official government databases and updated legal codes.</p></div>'
        f'<div class="lc-feature-item"><div class="lc-card-icon-box">{get_icon_html("translate")}</div><h3>Plain-Language Answers</h3><p>Complex legal jargon simplified for immediate comprehension.</p></div>'
        f'<div class="lc-feature-item"><div class="lc-card-icon-box">{get_icon_html("list")}</div><h3>Step-by-Step Guidance</h3><p>Clear, actionable steps on how to proceed with legal procedures.</p></div>'
        '</div>'
    )
    st.markdown(features_html, unsafe_allow_html=True)

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
        <h1 class="lc-page-title" style="margin-top:24px; text-align:left;">Verified Resources</h1>
        <p class="lc-page-subtitle" style="text-align:left; margin:0 0 24px 0;">
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
        <div class="lc-about-hero">
          <h1 class="lc-page-title" style="text-align:left; margin-bottom:16px;">About Legal Connect</h1>
          <p class="lc-page-body" style="font-size:16.5px; line-height:1.65; margin-bottom:16px;">
            Legal Connect is an AI-powered legal awareness platform designed to help citizens understand official Indian laws, citizen rights, and legal procedures in plain language.
          </p>
          <p class="lc-page-body" style="font-size:15.5px; line-height:1.65; margin-bottom:16px;">
            All answers are generated using a Retrieval-Augmented Generation (RAG) pipeline trained over verified primary sources, including the Bharatiya Nyaya Sanhita, 2023 (BNS), the Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS), and the Bharatiya Sakshya Adhiniyam, 2023 (BSA).
          </p>
          <p class="lc-page-body lc-disclaimer-callout" style="font-size:15px; line-height:1.65; margin-bottom:32px;">
            <strong>Legal Disclaimer:</strong> Legal Connect provides legal information for awareness only and does not constitute formal legal advice. For formal proceedings or legal representation, consult a qualified advocate.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    features_html = (
        '<div class="lc-features-grid">'
        f'<div class="lc-feature-item"><div class="lc-card-icon-box">{get_icon_html("checkdoc")}</div><h3>Verified Legal Sources</h3><p>Direct citations and official source links returned with every query response.</p></div>'
        f'<div class="lc-feature-item"><div class="lc-card-icon-box">{get_icon_html("translate")}</div><h3>Plain-Language Clarity</h3><p>Legal acts and complex statutory sections explained in accessible, clear English.</p></div>'
        f'<div class="lc-feature-item"><div class="lc-card-icon-box">{get_icon_html("list")}</div><h3>Structured Guidance</h3><p>Clear recommended steps and actionable procedures for legal situations.</p></div>'
        '</div>'
    )
    st.markdown(features_html, unsafe_allow_html=True)
    render_footer()


def render_categories() -> None:
    # Full Category Navigation Bar (All categories accessible!)
    selected_cat_id = st.query_params.get("cat", CATEGORIES[0]["id"])
    
    st.markdown('<h1 class="lc-page-title" style="text-align:left; margin-bottom:16px;">Legal Categories</h1>', unsafe_allow_html=True)
    
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
        st.markdown('<h2 style="font-size:22px; margin-bottom:16px;">Common Questions</h2>', unsafe_allow_html=True)
        for faq in cat["faqs"]:
            with st.expander(faq["q"], expanded=False):
                st.write(faq["a"])

        st.markdown(
            f'<h2 style="font-size:22px; margin:32px 0 16px;">{html.escape(cat["stepper_title"])}</h2>',
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

    # Bottom CTA Button centered
    st.markdown('<div class="lc-bottom-cta-container">', unsafe_allow_html=True)
    if st.button(f"💬 Ask Legal Connect about {cat['name']}", type="primary", use_container_width=False):
        st.session_state.pending_question = cat["ask_prompt"]
        goto("chat")
    st.markdown('</div>', unsafe_allow_html=True)

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
            """
            <div class="lc-chat-empty-state">
              <div class="lc-empty-badge">⚖️ LEGALCONNECT ASSISTANT</div>
              <h2>Understand your legal rights in plain language.</h2>
              <p>Describe your real-world situation or legal problem below. LegalConnect searches verified Indian statutory sources across criminal, cyber, consumer, labour, and family protection laws to provide plain-language guidance.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="lc-empty-starters-label">OR SELECT A REAL-LIFE SITUATION TO EXPLORE:</div>',
            unsafe_allow_html=True,
        )
        starter_cols = st.columns(2)
        starters = [
            (
                "🛒 Defective Product & Seller Refusal",
                "I bought a phone recently and it stopped working. The seller refuses to help me. What can I do?",
            ),
            (
                "💼 Unpaid Salary & Withheld Pay",
                "My employer hasn't paid my salary for two months. What options might I have?",
            ),
            (
                "🔒 Personal Detail Misuse & Online Identity",
                "Someone is using my name and personal details online without my permission. What should I do?",
            ),
            (
                "🛡️ Safety Concerns & Domestic Protection",
                "My husband keeps threatening me and I am worried about my safety. What legal protection may be available?",
            ),
        ]
        for idx, (label, query) in enumerate(starters):
            with starter_cols[idx % 2]:
                if st.button(label, key=f"starter_q_{idx}", use_container_width=True, disabled=st.session_state.in_flight):
                    st.session_state.pending_question = query
                    st.rerun()

    for message in st.session_state.messages:
        if message["role"] == "user":
            render_user_message(message["content"])
        else:
            render_assistant_message(message)

    # Chat Input Form Bar - spans full container width matching scenario buttons & messages
    with st.form("chat_form", border=False, clear_on_submit=True):
        c_input, c_send = st.columns([0.86, 0.14], vertical_alignment="center")
        with c_input:
            follow_up = st.text_input(
                "Question",
                placeholder="Describe your legal situation or ask a question...",
                label_visibility="collapsed",
                disabled=st.session_state.in_flight,
            )
        with c_send:
            sent = st.form_submit_button(
                "Send ➤", type="primary", use_container_width=True, disabled=st.session_state.in_flight
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
        '<div class="lc-chat-disclaimer-note">⚖️ <strong>Legal Awareness Notice:</strong> LegalConnect provides legal awareness information, not formal legal advice. For formal proceedings or representation, consult a qualified advocate.</div>',
        unsafe_allow_html=True,
    )
