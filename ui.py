"""
site.py
-------
Streamlit version of the "Filed" complaint-intake site, styled in the
austere editorial (ZARA-inspired) design language: black/white,
Helvetica + serif accent, zero border-radius, no gradients.

Run:
    pip install streamlit requests
    streamlit run site.py

Make sure the API is running first:
    uvicorn app:app --reload --port 8000
"""

import requests
import streamlit as st

API_URL = "http://localhost:8000/process-customer-message"

st.set_page_config(page_title="Filed — Say what happened.", page_icon="⬛", layout="wide")

# ---------------------------------------------------------------------------
# Design tokens, translated into CSS injected via markdown
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        --surface: #ffffff;
        --surface-raised: #f5f5f5;
        --surface-inverse: #000000;
        --text: #000000;
        --text-muted: #757575;
        --text-subtle: #555555;
        --text-inverse: #ffffff;
        --accent: #3860be;
        --font-display: 'Helvetica Now Text', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        --font-serif: 'Times New Roman', Georgia, serif;
    }

    html, body, [class*="css"] {
        font-family: var(--font-display);
    }

    .stApp {
        background-color: var(--surface);
    }

    /* Kill Streamlit's default chrome and top/bottom whitespace */
    #MainMenu, footer, header[data-testid="stHeader"] { display: none; }
    div[data-testid="stAppViewContainer"] > .main {
        padding-top: 0 !important;
    }
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 0.5rem !important;
        max-width: 1200px;
    }

    /* Robust full-bleed technique (works regardless of container width) */
    .full-bleed {
        width: 100vw;
        position: relative;
        left: 50%;
        right: 50%;
        margin-left: -50vw;
        margin-right: -50vw;
    }

    /* Top nav bar */
    .nav-bar {
        background-color: var(--surface-inverse);
        color: var(--text-inverse);
        padding: 0.7rem 1.6rem;
        margin-top: 0;
        margin-bottom: 2.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 0.78rem;
        font-weight: 600;
    }

    /* Hero headline */
    .eyebrow {
        font-size: 0.78rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--text-subtle);
        margin-bottom: 0.4rem;
    }
    .hero-headline {
        font-size: 3.2rem;
        font-weight: 300;
        text-transform: uppercase;
        letter-spacing: -0.02em;
        line-height: 1.05;
        margin: 0 0 0.6rem 0;
        color: var(--text);
    }
    .hero-serif {
        font-family: var(--font-serif);
        font-size: 1.5rem;
        color: var(--text-subtle);
        font-weight: 400;
        margin-bottom: 1rem;
    }
    .hero-body {
        font-size: 0.98rem;
        font-weight: 300;
        color: var(--text);
        max-width: 46ch;
        line-height: 1.6;
        margin-bottom: 1.6rem;
    }

    /* Form field labels */
    .field-label {
        font-size: 0.72rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--text-subtle);
        margin-bottom: 0.2rem;
    }

    /* Text area styled as underline field, no rounded corners */
    .stTextArea textarea {
        border: none !important;
        border-bottom: 1px solid #000000 !important;
        border-radius: 0 !important;
        background-color: var(--surface) !important;
        font-family: var(--font-display);
        font-weight: 300;
        font-size: 0.98rem;
        padding: 0.5rem 0 !important;
        color: black;
    }
    .stTextArea textarea:focus {
        box-shadow: none !important;
        outline: 1.5px solid var(--accent) !important;
        outline-offset: 2px;
    }

    /* Primary button: white fill, black border, sharp corners */
    div.stButton > button {
        background-color: var(--surface);
        color: var(--text);
        border: 1px solid #000000;
        border-radius: 0;
        padding: 0.6rem 1.6rem;
        font-size: 0.8rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        font-weight: 400;
        transition: background-color 0.2s ease, color 0.2s ease;
    }
    div.stButton > button:hover {
        background-color: #000000;
        color: #ffffff;
        border-color: #000000;
    }

    .form-note {
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-top: 0.6rem;
    }

    /* Answer panel: bordered box, no shadow, no radius */
    .answer-panel {
        border: 1px solid #000000;
        padding: 2rem;
        min-height: 320px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 1.1rem;
    }
    .answer-panel.empty {
        align-items: center;
        text-align: center;
        color: var(--text-muted);
    }
    .state-label {
        font-size: 0.72rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--text-muted);
    }
    .answer-row {
        border-bottom: 1px solid #dddddd;
        padding-bottom: 0.7rem;
    }
    .answer-row:last-of-type { border-bottom: none; padding-bottom: 0; }
    .answer-row .k {
        display: block;
        font-size: 0.7rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: 0.25rem;
    }
    .answer-row .v {
        display: block;
        font-size: 0.98rem;
        line-height: 1.5;
        color: var(--text);
        word-wrap: break-word;
        white-space: normal;
    }
    .answer-row .v.priority-High, .answer-row .v.priority-Critical {
        color: #a10c24; font-weight: 600;
    }
    .answer-response {
        font-family: var(--font-serif);
        font-size: 1.2rem;
        line-height: 1.55;
        color: var(--text);
        padding-top: 0.4rem;
        word-wrap: break-word;
        white-space: normal;
    }

    /* How-it-works grid */
    .grid-cell .num {
        font-family: var(--font-serif);
        font-size: 1.6rem;
        color: var(--text-muted);
    }
    .grid-cell .label {
        font-size: 0.72rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin: 0.3rem 0;
    }
    .grid-cell .subhead {
        font-size: 0.92rem;
        font-weight: 400;
        color: var(--text);
    }

    /* Inverse footer band */
    .inverse-band {
        background-color: #000000;
        color: #ffffff;
        padding: 3rem 2rem;
        text-align: center;
        margin-top: 3rem;
    }
    .inverse-band h2 {
        font-size: 2.2rem;
        font-weight: 300;
        text-transform: uppercase;
        margin-bottom: 0.6rem;
    }
    .inverse-band p { color: #dddddd; margin-bottom: 0; }

    .footer-legal {
        text-align: center;
        font-size: 0.75rem;
        color: #757575;
        padding: 1rem 0 0.5rem 0;
    }

    hr { border-color: #dddddd; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Nav bar (full-bleed)
# ---------------------------------------------------------------------------
st.markdown('<div class="nav-bar full-bleed">', unsafe_allow_html=True)
st.markdown(
    """
        <span>Filed</span>
        <span>File a complaint · How it works · Contact</span>
    """,
    unsafe_allow_html=True,
)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Hero: form (left) + answer panel (right)
# ---------------------------------------------------------------------------
if "result" not in st.session_state:
    st.session_state.result = None
if "loading" not in st.session_state:
    st.session_state.loading = False

left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown('<div class="eyebrow">Customer Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-headline">Say what<br>happened.</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-serif">We read every word before anyone else does.</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-body">Describe the issue in your own words. Our system reads it, '
        'works out what\'s actually going on, and tells you what happens next — in seconds, not days.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="field-label">Your message</div>', unsafe_allow_html=True)
    message = st.text_area(
        "message",
        label_visibility="collapsed",
        placeholder="I was charged twice for the same transaction and I need this resolved...",
        height=140,
    )
    submit = st.button("Submit")
    st.markdown(
        '<div class="form-note">Your message is read once, understood, and answered. '
        'Nothing is sold, nothing is shared.</div>',
        unsafe_allow_html=True,
    )

with right:
    panel_slot = st.empty()

    def render_empty():
        panel_slot.markdown(
            """
            <div class="answer-panel empty">
                <span class="state-label">Waiting</span>
                <p>Your answer will appear here once you submit a message.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def render_waiting():
        panel_slot.markdown(
            """
            <div class="answer-panel">
                <span class="state-label">Reading your message&hellip;</span>
                <p style="color:#757575;">This usually takes a few seconds.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def render_error(msg):
        panel_slot.markdown(
            f"""
            <div class="answer-panel">
                <span class="state-label">Something went wrong</span>
                <p style="color:#555555;">{msg}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def render_result(data):
        priority = data.get("priority", "Medium")
        panel_slot.markdown(
            f"""
            <div class="answer-panel">
                <span class="state-label">Your answer</span>
                <div class="answer-row">
                    <span class="k">Issue</span>
                    <span class="v">{data.get("issue_type", "—")}</span>
                </div>
                <div class="answer-row">
                    <span class="k">Priority</span>
                    <span class="v priority-{priority}">{priority}</span>
                </div>
                <div class="answer-row">
                    <span class="k">Routed to</span>
                    <span class="v">{data.get("routing", "—")}</span>
                </div>
                <div class="answer-row">
                    <span class="k">Next step</span>
                    <span class="v">{data.get("suggested_action", "—")}</span>
                </div>
                <div class="answer-row">
                    <span class="k">Why</span>
                    <span class="v">{data.get("explanation", "—")}</span>
                </div>
                <p class="answer-response">{data.get("response", "")}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if submit and message.strip():
        render_waiting()
        try:
            resp = requests.post(API_URL, json={"message": message}, timeout=60)
            resp.raise_for_status()
            render_result(resp.json())
        except requests.exceptions.ConnectionError:
            render_error(
                "We couldn't reach the system. Make sure the API is running "
                "(<code>uvicorn app:app --reload --port 8000</code>)."
            )
        except Exception as e:
            render_error(f"Unexpected error: {e}")
    elif submit:
        render_error("Please enter a message first.")
    else:
        render_empty()

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")

# ---------------------------------------------------------------------------
# Editorial band
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div style="max-width:720px; margin:2rem auto; text-align:center;">
        <h2 style="font-weight:300; text-transform:uppercase; font-size:1.6rem;">Every complaint, understood.</h2>
        <p style="font-family:'Times New Roman', Georgia, serif; font-size:1.5rem; color:#000; margin:1rem 0;">
            "Not a form you fill out and forget. A message that gets read, reasoned through, and answered."
        </p>
        <p style="color:#555555; font-size:0.95rem;">
            Behind the plain text box is a system trained to separate the urgent from the routine,
            the fraud from the fee dispute, and route each one to the right hands — instantly.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# How it works grid
# ---------------------------------------------------------------------------
c1, c2, c3 = st.columns(3, gap="large")
steps = [
    ("01", "Understand", "We read your message and work out what it's really about — even if it covers more than one issue."),
    ("02", "Decide", "We weigh urgency and set a priority, so critical issues never sit in a queue."),
    ("03", "Route", "Your message goes straight to the team built to handle it, with a clear next step attached."),
]
for col, (num, label, subhead) in zip([c1, c2, c3], steps):
    with col:
        st.markdown(
            f"""
            <div class="grid-cell">
                <div class="num">{num}</div>
                <div class="label">{label}</div>
                <div class="subhead">{subhead}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Inverse CTA band
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="inverse-band full-bleed">
        <h2>Read once. Handled right.</h2>
        <p>No hold music. No repeating yourself. Just an answer, and a clear next step.</p>
    </div>
    <p class="footer-legal">© 2026 Filed. This is a demonstration system for internal customer operations.</p>
    """,
    unsafe_allow_html=True,
)