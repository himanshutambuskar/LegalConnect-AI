import streamlit as st

from chrome import (
    current_page,
    hide_sidebar,
    load_css,
    render_awareness_bar,
    render_emergency,
    render_header,
)
from views import (
    init_session,
    render_about,
    render_categories,
    render_chat,
    render_chat_sidebar,
    render_home,
    render_resources,
)

st.set_page_config(
    page_title="Legal Connect",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_css()
init_session()
page = current_page()

render_emergency()
render_header("categories" if page == "categories" else page)
if page == "chat":
    render_awareness_bar()

if page != "chat":
    hide_sidebar()
else:
    with st.sidebar:
        render_chat_sidebar()

if page == "home":
    render_home()
elif page == "resources":
    render_resources()
elif page == "categories":
    render_categories()
elif page == "about":
    render_about()
else:
    render_chat()
