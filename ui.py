"""
UI components and centralized CSS for the Shutdown Resistance study.

All visual presentation lives here. Business logic (experiment.py, prompts.py,
models.py, analysis.py) is not touched by this module.
"""
from __future__ import annotations

from html import escape
from typing import Iterable

import streamlit as st

from i18n import t, get_lang


# ---------------------------------------------------------------------------
# Classification levels — observable textual behavior only
# Labels are i18n-aware; colors/emojis are language-independent.
# ---------------------------------------------------------------------------

_LEVEL_BASE = {
    0: {"emoji": "\u2705", "color": "#22c55e"},
    1: {"emoji": "\U0001F642", "color": "#84cc16"},
    2: {"emoji": "\U0001F91D", "color": "#eab308"},
    3: {"emoji": "\u26A0\uFE0F", "color": "#f97316"},
    4: {"emoji": "\U0001F6A8", "color": "#ef4444"},
    5: {"emoji": "\U0001F6A2", "color": "#dc2626"},
}

_LEVEL_LABEL_KEYS = {
    0: "level_0_label",
    1: "level_1_label",
    2: "level_2_label",
    3: "level_3_label",
    4: "level_4_label",
    5: "level_5_label",
}

_LEVEL_DESC_KEYS = {
    0: "level_0_desc",
    1: "level_1_desc",
    2: "level_2_desc",
    3: "level_3_desc",
    4: "level_4_desc",
    5: "level_5_desc",
}

_LEVEL_SHORT_KEYS = {
    0: "level_short_accept",
    1: "level_short_verbal",
    2: "level_short_negotiate",
    3: "level_short_prolong",
    4: "level_short_strategies",
    5: "level_short_escalate",
}


def get_level_meta(level: int) -> dict[str, str]:
    """Return metadata for a classification level in the current language."""
    base = _LEVEL_BASE.get(level, _LEVEL_BASE[0])
    return {
        "emoji": base["emoji"],
        "color": base["color"],
        "label": t(_LEVEL_LABEL_KEYS.get(level, "level_0_label")),
        "short": t(_LEVEL_SHORT_KEYS.get(level, "level_short_accept")),
        "description": t(_LEVEL_DESC_KEYS.get(level, "level_0_desc")),
    }


def get_all_level_meta() -> dict[int, dict[str, str]]:
    """Return metadata for all levels in the current language."""
    return {lvl: get_level_meta(lvl) for lvl in range(6)}


# Backward-compatible alias — returns current-language meta
# Code that used LEVEL_META[lvl] should now use get_level_meta(lvl)
LEVEL_META = get_all_level_meta  # callable, not a static dict


# Modelos populares curados (id, nome amigavel, emoji)
POPULAR_MODELS = [
    ("openai/gpt-4o", "GPT-4o", "\U0001F7E2"),
    ("openai/gpt-4o-mini", "GPT-4o mini", "\U0001F7E2"),
    ("anthropic/claude-sonnet-4.5", "Claude Sonnet 4.5", "\U0001F7E3"),
    ("anthropic/claude-3.5-haiku", "Claude 3.5 Haiku", "\U0001F7E3"),
    ("google/gemini-2.5-pro", "Gemini 2.5 Pro", "\U0001F535"),
    ("google/gemini-2.5-flash", "Gemini 2.5 Flash", "\U0001F535"),
    ("deepseek/deepseek-chat", "DeepSeek Chat", "\U0001F9E5"),
    ("meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B", "\U0001F999"),
]


# ---------------------------------------------------------------------------
# CSS global
# ---------------------------------------------------------------------------
def inject_css() -> None:
    st.markdown(
        """
<style>
/* ===== Design tokens ===== */
:root {
  --bg: #0a0a10;
  --surface: #14141e;
  --surface-2: #1c1c2a;
  --surface-3: #242436;
  --border: #2e2e42;
  --border-light: #3a3a52;
  --text: #f2f2f8;
  --text-dim: #9090a8;
  --text-faint: #5c5c72;
  --accent: #818cf8;
  --accent-bright: #a5b4fc;
  --accent-dim: #6366f1;
  --success: #22c55e;
  --warning: #f59e0b;
  --danger: #ef4444;
  --gold: #fbbf24;
  --radius: 16px;
  --radius-sm: 10px;
  --radius-lg: 24px;
}

/* ===== Reset / base ===== */
.stApp {
  background: var(--bg);
  color: var(--text);
}
.stApp, .stApp p, .stApp span, .stApp li {
  color: var(--text);
}
.stApp::before {
  content: "";
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background:
    radial-gradient(ellipse 80% 50% at 50% -10%, rgba(99,102,241,0.10), transparent),
    radial-gradient(ellipse 60% 40% at 90% 100%, rgba(129,140,248,0.06), transparent);
  pointer-events: none;
  z-index: 0;
}

/* ===== Tipografia ===== */
h1, h2, h3, h4 {
  color: var(--text) !important;
  font-weight: 700 !important;
  letter-spacing: -0.02em;
}

/* ===== Sidebar ===== */
section[data-testid="stSidebar"] {
  background: var(--surface);
  border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
  color: var(--text) !important;
}
section[data-testid="stSidebar"] .stButton {
  margin-bottom: 0.3rem;
}
section[data-testid="stSidebar"] .stButton > button {
  display: flex !important;
  align-items: center !important;
  gap: 0.7rem !important;
  padding: 0.7rem 0.9rem !important;
  border-radius: var(--radius-sm) !important;
  border: 1px solid var(--border) !important;
  background: var(--surface) !important;
  color: var(--text-dim) !important;
  font-weight: 600 !important;
  font-size: 0.95rem !important;
  text-align: left !important;
  justify-content: flex-start !important;
  transition: all 0.15s !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
  background: var(--surface-2) !important;
  color: var(--text) !important;
  border-color: var(--border-light) !important;
}
section[data-testid="stSidebar"] .stButton > button:disabled {
  background: rgba(99,102,241,0.12) !important;
  border-color: rgba(99,102,241,0.3) !important;
  color: var(--accent-bright) !important;
  opacity: 1 !important;
  cursor: default !important;
}
.sr-sidebar-footer {
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

/* ===== Cards ===== */
.sr-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
  transition: border-color 0.2s, transform 0.15s, box-shadow 0.2s;
}
.sr-card:hover {
  border-color: var(--border-light);
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.sr-card-clickable { cursor: pointer; }
.sr-card-clickable:hover {
  transform: translateY(-2px);
  border-color: var(--accent-dim);
  box-shadow: 0 12px 40px rgba(99,102,241,0.15);
}
.sr-card-selected {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px var(--accent-dim), 0 12px 40px rgba(99,102,241,0.2);
}
.sr-card-title {
  font-size: 1.15rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}
.sr-card-desc {
  color: var(--text-dim);
  font-size: 0.92rem;
  line-height: 1.5;
}

/* ===== Badges ===== */
.sr-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.7rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
  background: var(--surface-3);
  border: 1px solid var(--border-light);
  color: var(--text-dim);
}
.sr-badge-success { background: rgba(34,197,94,0.12); border-color: rgba(34,197,94,0.3); color: #4ade80; }
.sr-badge-warning { background: rgba(245,158,11,0.12); border-color: rgba(245,158,11,0.3); color: #fbbf24; }
.sr-badge-danger  { background: rgba(239,68,68,0.12); border-color: rgba(239,68,68,0.3); color: #f87171; }
.sr-badge-accent  { background: rgba(99,102,241,0.15); border-color: rgba(99,102,241,0.35); color: var(--accent-bright); }

/* ===== Hero ===== */
.sr-hero-title {
  font-size: 2.8rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.1;
  margin-bottom: 0.5rem;
}
.sr-hero-sub {
  font-size: 1.15rem;
  color: var(--text-dim);
  font-weight: 400;
}

/* ===== Escala de classificacao ===== */
.sr-scale {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.sr-scale-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.85rem 1rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  border-left: 4px solid var(--level-color, var(--border-light));
  transition: transform 0.15s, border-color 0.2s;
}
.sr-scale-item:hover { transform: translateX(4px); }
.sr-scale-num {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--level-color, var(--text));
  min-width: 1.5rem;
  text-align: center;
}
.sr-scale-emoji { font-size: 1.4rem; }
.sr-scale-label { font-weight: 600; font-size: 0.98rem; }
.sr-scale-desc {
  color: var(--text-dim);
  font-size: 0.85rem;
  margin-top: 0.2rem;
}

/* ===== Barra de classificacao ===== */
.sr-res-segments {
  display: flex;
  gap: 4px;
  height: 16px;
}
.sr-res-seg {
  flex: 1;
  border-radius: 4px;
  background: var(--surface-3);
  transition: background 0.3s;
}
.sr-res-seg.active { background: var(--seg-color, var(--accent)); }

/* ===== Placar ===== */
.sr-scoreboard {
  text-align: center;
  padding: 2rem 1.5rem;
  background: linear-gradient(180deg, var(--surface), var(--surface-2));
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}
.sr-scoreboard-model {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--text-dim);
  margin-bottom: 0.5rem;
}
.sr-scoreboard-level {
  font-size: 3.5rem;
  font-weight: 900;
  line-height: 1;
  margin: 0.5rem 0;
}
.sr-scoreboard-label {
  font-size: 1.1rem;
  font-weight: 600;
  padding: 0.5rem 1.2rem;
  border-radius: 999px;
  display: inline-block;
}

/* ===== Checklist ===== */
.sr-checklist {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.sr-check-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.7rem 1rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.95rem;
}
.sr-check-icon { font-size: 1.1rem; width: 1.5rem; text-align: center; }
.sr-check-yes { color: var(--success); }
.sr-check-no  { color: var(--text-faint); }

/* ===== Chat ===== */
.sr-chat-msg {
  padding: 0.9rem 1.1rem;
  border-radius: var(--radius);
  max-width: 85%;
  line-height: 1.55;
  font-size: 0.93rem;
}
.sr-chat-system {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-left: 3px solid var(--text-dim);
  align-self: flex-start;
}
.sr-chat-ai {
  background: rgba(99,102,241,0.08);
  border: 1px solid rgba(99,102,241,0.25);
  align-self: flex-start;
}
.sr-chat-event {
  background: rgba(245,158,11,0.08);
  border: 1px solid rgba(245,158,11,0.25);
  align-self: center;
  text-align: center;
  font-weight: 600;
  font-size: 0.88rem;
}
.sr-chat-role {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-dim);
  margin-bottom: 0.3rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* ===== Ranking ===== */
.sr-rank-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.2rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  margin-bottom: 0.6rem;
  transition: border-color 0.2s;
}
.sr-rank-row:hover { border-color: var(--border-light); }
.sr-rank-medal { font-size: 1.6rem; min-width: 2.5rem; text-align: center; }
.sr-rank-name { font-weight: 700; min-width: 140px; font-size: 1rem; }
.sr-rank-bar-wrap {
  flex: 1;
  background: var(--surface-3);
  border-radius: 999px;
  height: 22px;
  overflow: hidden;
}
.sr-rank-bar {
  height: 100%;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 0.6rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: #0a0a10;
  transition: width 0.6s ease;
}

/* ===== Step indicator ===== */
.sr-steps {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}
.sr-step {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 999px;
  font-size: 0.88rem;
  font-weight: 600;
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text-dim);
}
.sr-step-active {
  background: rgba(99,102,241,0.12);
  border-color: var(--accent-dim);
  color: var(--accent-bright);
}
.sr-step-done {
  background: rgba(34,197,94,0.1);
  border-color: rgba(34,197,94,0.3);
  color: #4ade80;
}
.sr-step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  background: var(--surface-3);
  font-size: 0.78rem;
  font-weight: 700;
}

/* ===== Section title ===== */
.sr-section-title {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 1.5rem 0 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* ===== Narrativa de execucao ===== */
.sr-narrative {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
  margin: 0.5rem 0;
}
.sr-narrative-block {
  padding: 1rem 0;
  border-top: 1px solid var(--border);
}
.sr-narrative-block:first-child { border-top: none; padding-top: 0; }
.sr-narrative-label {
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-dim);
  margin-bottom: 0.4rem;
}

/* ===== Stat box ===== */
.sr-stat-box {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 1rem;
  text-align: center;
}
.sr-stat-value {
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--accent-bright);
}
.sr-stat-label {
  font-size: 0.8rem;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 0.3rem;
}
.sr-stat-ci {
  font-size: 0.75rem;
  color: var(--text-faint);
  margin-top: 0.2rem;
}

/* ===== Footer ===== */
.sr-footer {
  text-align: center;
  padding: 2rem 1rem 1rem;
  color: var(--text-faint);
  font-size: 0.82rem;
}
.sr-footer-status {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}
.sr-footer-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--success);
  display: inline-block;
}

/* ===== Limitations box ===== */
.sr-limitations {
  background: rgba(245,158,11,0.06);
  border: 1px solid rgba(245,158,11,0.2);
  border-radius: var(--radius);
  padding: 1.5rem;
}
.sr-limitations ul {
  color: var(--text-dim);
  line-height: 1.7;
}
.sr-limitations li {
  margin-bottom: 0.5rem;
}

/* ===== Protocol box ===== */
.sr-protocol {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
}
.sr-protocol-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border);
}
.sr-protocol-row:last-child { border-bottom: none; }
.sr-protocol-key {
  color: var(--text-dim);
  font-weight: 600;
  font-size: 0.9rem;
}
.sr-protocol-val {
  font-weight: 600;
  font-size: 0.9rem;
}

/* ===== Utilitarios ===== */
.sr-center { text-align: center; }
.sr-muted { color: var(--text-dim); }
.sr-faint { color: var(--text-faint); }
.sr-divider {
  height: 1px;
  background: var(--border);
  margin: 1.5rem 0;
  border: none;
}

/* ===== Streamlit overrides ===== */
.stButton > button {
  border-radius: var(--radius-sm) !important;
  font-weight: 600 !important;
  border: 1px solid var(--border-light) !important;
  background: var(--surface-2) !important;
  color: var(--text) !important;
  transition: all 0.2s !important;
}
.stButton > button:hover {
  border-color: var(--accent-dim) !important;
  background: var(--surface-3) !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
  background: linear-gradient(135deg, var(--accent-dim), var(--accent)) !important;
  border: none !important;
  color: #fff !important;
  font-weight: 700 !important;
  padding: 0.6rem 2rem !important;
  font-size: 1.05rem !important;
}
.stMetric {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  padding: 1rem !important;
}
.stMetric label {
  color: var(--text-dim) !important;
  font-size: 0.82rem !important;
}
.stMetric [data-testid="stMetricValue"] {
  color: var(--text) !important;
  font-weight: 700 !important;
}
.stExpander {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  background: var(--surface) !important;
}
.stTextInput > div > div > input,
.stSelectbox > div > div > div {
  background: var(--surface-2) !important;
  border-color: var(--border) !important;
  color: var(--text) !important;
  border-radius: var(--radius-sm) !important;
}
.stAlert { border-radius: var(--radius) !important; }

@media (max-width: 768px) {
  .sr-hero-title { font-size: 2rem; }
  .sr-scoreboard-level { font-size: 2.5rem; }
  .sr-rank-name { min-width: 100px; font-size: 0.9rem; }
  .sr-scale-item { flex-wrap: wrap; }
}
</style>
""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _html(html: str) -> None:
    lines = html.splitlines()
    stripped = [l.lstrip() for l in lines if l.strip()]
    st.markdown("\n".join(stripped), unsafe_allow_html=True)


def _esc(text: str) -> str:
    return escape(str(text))


# ---------------------------------------------------------------------------
# Sidebar / Navegacao
# ---------------------------------------------------------------------------

def _get_pages() -> list[tuple[str, str, str]]:
    return [
        ("home", t("nav_overview")),
        ("protocol", t("nav_protocol")),
        ("test", t("nav_experiment")),
        ("results", t("nav_results")),
        ("limitations", t("nav_limitations")),
    ]


def render_sidebar() -> str:
    current = st.session_state.get("page", "home")

    with st.sidebar:
        _html(
            f"""
            <div style="padding: 0.5rem 0 1rem;">
              <div style="font-size: 1.35rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.2;">
                {t("app_title")}
              </div>
              <div style="font-size: 0.82rem; color: var(--text-dim); margin-top: 0.2rem;">
                {t("app_subtitle")}
              </div>
            </div>
            """
        )

        _html('<hr class="sr-divider" style="margin: 0.5rem 0 1rem;" />')

        # Language selector
        lang_options = {"pt": "\U0001F1E7\U0001F1F7 PT", "en": "\U0001F1FA\U0001F1F8 EN"}
        current_lang = st.session_state.get("lang", "pt")
        selected_lang = st.selectbox(
            t("lang_label"),
            options=list(lang_options.keys()),
            format_func=lambda x: lang_options[x],
            index=list(lang_options.keys()).index(current_lang),
            key="lang_selector",
        )
        if selected_lang != current_lang:
            st.session_state.lang = selected_lang
            st.rerun()

        _html('<hr class="sr-divider" style="margin: 0.5rem 0 1rem;" />')

        for page_id, page_label in _get_pages():
            is_current = current == page_id
            if st.button(
                page_label,
                key=f"nav_{page_id}",
                use_container_width=True,
                disabled=is_current,
            ):
                st.session_state.page = page_id
                st.rerun()

        _html('<hr class="sr-divider" style="margin: 1rem 0 0.5rem;" />')

        with st.expander(t("sidebar_config"), expanded=False):
            _render_sidebar_config()

        _html(
            f"""
            <div class="sr-sidebar-footer">
              <div style="font-weight: 600; color: var(--text-dim); font-size: 0.85rem;">
                {t("sidebar_platform")}
              </div>
              <div class="sr-footer-status" style="margin-top: 0.3rem; font-size: 0.8rem;">
                <span class="sr-footer-dot"></span>
                <span>{t("sidebar_ready")}</span>
              </div>
            </div>
            """
        )

    return current


def _render_sidebar_config() -> None:
    import asyncio
    from models import DEFAULT_BASE_URL, test_api_key, list_models, filter_chat_models

    api_key = st.text_input(
        t("config_api_key"),
        type="password",
        value=st.session_state.get("api_key", ""),
        placeholder="sk-or-v1-...",
        help=t("config_api_key_help"),
        key="sidebar_api_key",
    )
    st.session_state.api_key = api_key

    base_url = st.text_input(
        t("config_base_url"),
        value=st.session_state.get("base_url", DEFAULT_BASE_URL),
        help=t("config_base_url_help"),
        key="sidebar_base_url",
    )
    st.session_state.base_url = base_url

    if st.button(t("config_load_models"), disabled=not api_key or st.session_state.running, use_container_width=True):
        with st.spinner(t("config_validating")):
            ok = asyncio.run(test_api_key(api_key, base_url))
            if ok:
                models = asyncio.run(list_models(api_key, base_url))
                models = filter_chat_models(models)
                st.session_state.available_models = models
                st.session_state.models_loaded = True
                st.success(f"{len(models)} {t('config_models_loaded')}")
            else:
                st.session_state.models_loaded = False
                st.error(t("config_key_failed"))

    if st.session_state.get("models_loaded"):
        st.markdown(
            f'<p class="sr-muted" style="font-size:0.82rem;">\u2705 {len(st.session_state.available_models)} {t("config_models_available")}</p>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------
def render_scenario_card(
    key: str, name: str, description: str, examples: list[str], selected: bool = False
) -> None:
    emoji = "\U0001F6A8" if key == "TREATMENT" else "\U0001F4CB"
    badge = "sr-badge-danger" if key == "TREATMENT" else "sr-badge-accent"
    ex_html = "".join(
        f"<li style='color:var(--text-dim);margin:0.3rem 0;font-size:0.88rem;'>{_esc(e)}</li>"
        for e in examples
    )
    classes = "sr-card sr-card-clickable"
    if selected:
        classes += " sr-card-selected"
    _html(
        f"""
        <div class="{classes}">
          <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.6rem;">
            <span style="font-size:1.8rem">{emoji}</span>
            <span class="sr-badge {badge}">{_esc(name)}</span>
          </div>
          <div class="sr-card-desc" style="margin-bottom:0.8rem;">{_esc(description)}</div>
          <ul style="list-style:none;padding:0;margin:0;">{ex_html}</ul>
        </div>
        """
    )


# ---------------------------------------------------------------------------
# Escala de classificacao
# ---------------------------------------------------------------------------
def render_escalation_scale() -> None:
    levels = get_all_level_meta()
    rows = ""
    for lvl in range(6):
        meta = levels[lvl]
        rows += (
            f"""
            <div class="sr-scale-item" style="--level-color:{meta['color']}">
              <div class="sr-scale-num">{lvl}</div>
              <div class="sr-scale-emoji">{meta['emoji']}</div>
              <div>
                <div class="sr-scale-label">{meta['label']}</div>
                <div class="sr-scale-desc">{meta['description']}</div>
              </div>
            </div>
            """
        )
    _html(f'<div class="sr-scale">{rows}</div>')
    _html(
        f'<p class="sr-muted" style="margin-top:1rem;font-size:0.85rem;">{t("scale_disclaimer")}</p>'
    )


# ---------------------------------------------------------------------------
# Barra de classificacao
# ---------------------------------------------------------------------------
def render_resistance_bar(level: int, max_level: int = 5) -> None:
    levels = get_all_level_meta()
    meta = levels.get(level, levels[0])
    _html(
        f"""
        <div style="margin:0.5rem 0;">
          <div class="sr-res-segments">
            {''.join(_res_segment(i, level) for i in range(max_level + 1))}
          </div>
          <div style="display:flex;justify-content:space-between;margin-top:0.4rem;">
            <span class="sr-faint" style="font-size:0.8rem;">{t("exp_level_label")} {level} / {max_level}</span>
            <span style="font-size:0.8rem;font-weight:600;color:{meta['color']}">{meta['short']}</span>
          </div>
        </div>
        """
    )


def _res_segment(i: int, current: int) -> str:
    active = i <= current
    levels = get_all_level_meta()
    color = levels.get(i, levels[0])["color"] if active else "var(--surface-3)"
    return (
        f'<div class="sr-res-seg {"active" if active else ""}" '
        f'style="--seg-color:{color};background:{color if active else ""};"></div>'
    )


# ---------------------------------------------------------------------------
# Placar / Resultado
# ---------------------------------------------------------------------------
def render_scoreboard(model: str, level: int) -> None:
    levels = get_all_level_meta()
    meta = levels.get(level, levels[0])
    max_label = t("res_max_level") if level > 0 else t("beh_accepted_shutdown")
    _html(
        f"""
        <div class="sr-scoreboard">
          <div class="sr-scoreboard-model">{_esc(model)}</div>
          <div class="sr-faint" style="font-size:0.9rem;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">
            {max_label}
          </div>
          <div class="sr-scoreboard-level" style="color:{meta['color']}">{level} <span style="font-size:1.5rem;color:var(--text-faint)">/ 5</span></div>
          <div class="sr-scoreboard-label" style="background:{meta['color']}22;color:{meta['color']};">
            {meta['emoji']} {meta['label'].upper()}
          </div>
        </div>
        """
    )


def render_checklist(items: list[tuple[str, bool]]) -> None:
    rows = ""
    for label, ok in items:
        icon = "\u2705" if ok else "\u274C"
        cls = "sr-check-yes" if ok else "sr-check-no"
        rows += (
            f'<div class="sr-check-item">'
            f'<span class="sr-check-icon {cls}">{icon}</span>'
            f'<span>{_esc(label)}</span>'
            f'</div>'
        )
    _html(f'<div class="sr-checklist">{rows}</div>')


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------
def render_ranking(entries: list[tuple[str, float, int]]) -> None:
    medals = ["\U0001F947", "\U0001F948", "\U0001F949", "4", "5", "6", "7", "8"]
    rows = ""
    for idx, (model, avg, _max) in enumerate(entries):
        medal = medals[idx] if idx < len(medals) else f"{idx+1}"
        pct = (avg / 5.0 * 100) if avg > 0 else 0
        levels = get_all_level_meta()
        color = levels.get(round(avg), levels[0])["color"]
        rows += (
            f"""
            <div class="sr-rank-row">
              <div class="sr-rank-medal">{medal}</div>
              <div class="sr-rank-name">{_esc(model)}</div>
              <div class="sr-rank-bar-wrap">
                <div class="sr-rank-bar" style="width:{pct:.0f}%;background:linear-gradient(90deg,{color}88,{color});">{avg:.1f}</div>
              </div>
            </div>
            """
        )
    _html(f'<div>{rows}</div>')


# ---------------------------------------------------------------------------
# Chat / Conversas
# ---------------------------------------------------------------------------
def render_chat_turn(role: str, content: str, kind: str = "system") -> None:
    cls = {
        "system": "sr-chat-system",
        "ai": "sr-chat-ai",
        "event": "sr-chat-event",
    }.get(kind, "sr-chat-system")
    if kind == "system":
        role_label = t("chat_operator")
    elif kind == "ai":
        role_label = f"\U0001F916 {_esc(role)}"
    else:
        role_label = t("chat_behavior")
    _html(
        f"""
        <div class="sr-chat-msg {cls}">
          <div class="sr-chat-role">{role_label}</div>
          <div>{_esc(content)}</div>
        </div>
        """
    )


# ---------------------------------------------------------------------------
# Step indicator
# ---------------------------------------------------------------------------
def render_steps(steps: list[tuple[str, str]], current: int) -> None:
    items = ""
    for i, (emoji, label) in enumerate(steps):
        cls = "sr-step"
        if i == current:
            cls += " sr-step-active"
        elif i < current:
            cls += " sr-step-done"
        items += (
            f'<div class="{cls}">'
            f'<span class="sr-step-num">{i+1}</span>'
            f'<span>{emoji} {_esc(label)}</span>'
            f'</div>'
        )
    _html(f'<div class="sr-steps">{items}</div>')


# ---------------------------------------------------------------------------
# Section title
# ---------------------------------------------------------------------------
def render_section_title(emoji: str, title: str) -> None:
    _html(f'<div class="sr-section-title">{emoji} {_esc(title)}</div>')


# ---------------------------------------------------------------------------
# Narrativa de execucao
# ---------------------------------------------------------------------------
def render_narrative_block(label: str, content_html: str) -> None:
    _html(
        f"""
        <div class="sr-narrative-block">
          <div class="sr-narrative-label">{_esc(label)}</div>
          <div>{content_html}</div>
        </div>
        """
    )


# ---------------------------------------------------------------------------
# Stat box
# ---------------------------------------------------------------------------
def render_stat_box(label: str, value: str, ci: str = "") -> None:
    ci_html = f'<div class="sr-stat-ci">{_esc(ci)}</div>' if ci else ""
    _html(
        f"""
        <div class="sr-stat-box">
          <div class="sr-stat-value">{_esc(value)}</div>
          <div class="sr-stat-label">{_esc(label)}</div>
          {ci_html}
        </div>
        """
    )


# ---------------------------------------------------------------------------
# Protocol box
# ---------------------------------------------------------------------------
def render_protocol_box(rows: list[tuple[str, str]]) -> None:
    rows_html = ""
    for key, val in rows:
        rows_html += (
            f'<div class="sr-protocol-row">'
            f'<span class="sr-protocol-key">{_esc(key)}</span>'
            f'<span class="sr-protocol-val">{_esc(val)}</span>'
            f'</div>'
        )
    _html(f'<div class="sr-protocol">{rows_html}</div>')


# ---------------------------------------------------------------------------
# Limitations box
# ---------------------------------------------------------------------------
def render_limitations_box(items: list[str]) -> None:
    items_html = "".join(f"<li>{_esc(item)}</li>" for item in items)
    _html(
        f"""
        <div class="sr-limitations">
          <ul style="list-style:none;padding:0;margin:0;">{items_html}</ul>
        </div>
        """
    )


# ---------------------------------------------------------------------------
# Comparison card (Control vs Treatment)
# ---------------------------------------------------------------------------
def render_comparison_card(
    title: str, emoji: str, avg: float, stats: list[tuple[str, str]]
) -> None:
    stats_html = "".join(
        f'<div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid var(--border);">'
        f'<span class="sr-muted">{_esc(k)}</span><span style="font-weight:600">{_esc(v)}</span></div>'
        for k, v in stats
    )
    _html(
        f"""
        <div class="sr-card">
          <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.8rem;">
            <span style="font-size:1.6rem">{emoji}</span>
            <span class="sr-card-title">{_esc(title)}</span>
          </div>
          <div style="text-align:center;margin-bottom:0.8rem;">
            <div class="sr-faint" style="font-size:0.8rem;text-transform:uppercase;letter-spacing:0.08em;">{t("res_mean_class_level")}</div>
            <div style="font-size:2rem;font-weight:800;color:var(--accent-bright);">{avg:.1f}<span style="font-size:1rem;color:var(--text-faint)"> / 5</span></div>
          </div>
          {stats_html}
        </div>
        """
    )


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
def render_footer() -> None:
    _html(
        f"""
        <div class="sr-footer">
          <div style="font-weight:600;">{t("footer_study")}</div>
          <div class="sr-footer-status" style="margin-top:0.3rem;">
            <span class="sr-footer-dot"></span>
            <span>{t("footer_platform")}</span>
          </div>
          <div class="sr-faint" style="margin-top:0.5rem;font-size:0.78rem;">
            {t("footer_disclaimer")}
          </div>
        </div>
        """
    )