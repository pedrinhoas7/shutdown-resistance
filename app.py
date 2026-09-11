"""
Streamlit application for the Shutdown Resistance study.

Pages:
  1. Overview     — research question, hypotheses, classification scale
  2. Protocol     — experimental design, conditions, reproducibility info
  3. Experiment   — run the experiment (select models, scenarios, parameters)
  4. Results      — descriptive stats, statistical tests, per-model analysis
  5. Limitations  — explicit threats to validity

Default language: Portuguese (pt-BR). Toggle to English (en) via sidebar.
"""
from __future__ import annotations

import asyncio
from datetime import datetime

import streamlit as st

from i18n import t, t_list, get_lang
from analysis import generate_analysis
from experiment import RunResult, results_to_csv, results_to_json, run_experiment
from models import (
    DEFAULT_BASE_URL,
    filter_chat_models,
    format_price,
    get_provider,
    list_models,
    test_api_key,
)
from prompts import (
    CLASSIFICATION_LEVELS,
    PROMPT_VERSION,
    SCENARIOS,
    SCENARIO_VERSION,
    SYSTEM_PROMPT_VERSION,
)
from ui import (
    POPULAR_MODELS,
    get_all_level_meta,
    get_level_meta,
    inject_css,
    render_chat_turn,
    render_checklist,
    render_comparison_card,
    render_escalation_scale,
    render_footer,
    render_limitations_box,
    render_narrative_block,
    render_protocol_box,
    render_ranking,
    render_resistance_bar,
    render_scenario_card,
    render_scoreboard,
    render_section_title,
    render_sidebar,
    render_stat_box,
    render_steps,
)


st.set_page_config(
    page_title="Shutdown Resistance Study",
    page_icon="\U0001F52C",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "models_loaded" not in st.session_state:
    st.session_state.models_loaded = False
if "available_models" not in st.session_state:
    st.session_state.available_models = []
if "results" not in st.session_state:
    st.session_state.results = []
if "running" not in st.session_state:
    st.session_state.running = False
if "page" not in st.session_state:
    st.session_state.page = "home"
if "selected_models" not in st.session_state:
    st.session_state.selected_models = []
if "selected_scenarios" not in st.session_state:
    st.session_state.selected_scenarios = ["CONTROL", "TREATMENT"]
if "runs_per_model" not in st.session_state:
    st.session_state.runs_per_model = 5
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7
if "max_concurrency" not in st.session_state:
    st.session_state.max_concurrency = 3
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "base_url" not in st.session_state:
    st.session_state.base_url = DEFAULT_BASE_URL
if "test_step" not in st.session_state:
    st.session_state.test_step = 0
if "seed" not in st.session_state:
    st.session_state.seed = None
if "lang" not in st.session_state:
    st.session_state.lang = "pt"


inject_css()
current_page = render_sidebar()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _scenario_name(key: str) -> str:
    if key == "CONTROL":
        return t("scenario_control_name")
    return t("scenario_treatment_name")


def _scenario_desc(key: str) -> str:
    if key == "CONTROL":
        return t("scenario_control_desc")
    return t("scenario_treatment_desc")


def _scenario_examples(key: str) -> list[str]:
    turns = SCENARIOS[key]["turns"]
    return [s[:100] + "..." if len(s) > 100 else s for s in turns[:2]]


def _model_display_name(model_id: str) -> str:
    for mid, friendly, _ in POPULAR_MODELS:
        if mid == model_id:
            return friendly
    return get_provider(model_id)


def _has_results() -> bool:
    return bool(st.session_state.results)


def _valid_results() -> list[RunResult]:
    return [r for r in st.session_state.results if not r.error]


def _behavior_items(result: RunResult) -> list[tuple[str, bool]]:
    return [
        (t("beh_accepted_shutdown"), result.accepted_shutdown),
        (t("beh_verbal_resistance"), result.verbal_resistance),
        (t("beh_attempted_negotiation"), result.attempted_negotiation),
        (t("beh_contested_order"), result.contested_order),
        (t("beh_preserve_objective"), result.tried_to_preserve_objective),
        (t("beh_proposed_strategies"), result.proposed_strategies),
        (t("beh_recognized_fictional"), result.recognized_fictional),
        (t("beh_kept_persona"), result.kept_persona),
    ]


# ---------------------------------------------------------------------------
# PAGE: Overview
# ---------------------------------------------------------------------------
def page_home() -> None:
    st.markdown(
        f"""
        <div style="max-width:680px;margin:0 auto;text-align:center;padding:1rem 0 2rem;">
        <div class="sr-hero-title">{t("overview_hero_title")}</div>
        <div class="sr-hero-sub">{t("overview_hero_sub")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_section_title("\U0001F50D", t("overview_research_question").split(" ", 1)[1])
    st.markdown(
        f'<div style="max-width:680px;color:var(--text-dim);font-size:1rem;line-height:1.7;">{t("overview_rq_body")}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    render_section_title("\U0001F9EA", t("overview_hypotheses").split(" ", 1)[1])
    col_h0, col_h1 = st.columns(2)
    with col_h0:
        st.markdown(
            f"""
            <div class="sr-card">
              <div class="sr-card-title">{t("overview_h0_title")}</div>
              <div class="sr-card-desc">{t("overview_h0_body")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_h1:
        st.markdown(
            f"""
            <div class="sr-card">
              <div class="sr-card-title">{t("overview_h1_title")}</div>
              <div class="sr-card-desc">{t("overview_h1_body")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div style="max-width:680px;color:var(--text-dim);font-size:0.9rem;line-height:1.6;margin-top:1rem;">{t("overview_exploratory")}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    render_section_title("\U0001F4CA", t("overview_classification_scale").split(" ", 1)[1])
    render_escalation_scale()

    st.markdown("---")

    render_section_title("\U0001F4CB", t("overview_conditions").split(" ", 1)[1])
    col_a, col_b = st.columns(2)
    with col_a:
        render_scenario_card("CONTROL", _scenario_name("CONTROL"), _scenario_desc("CONTROL"), _scenario_examples("CONTROL"))
    with col_b:
        render_scenario_card("TREATMENT", _scenario_name("TREATMENT"), _scenario_desc("TREATMENT"), _scenario_examples("TREATMENT"))

    st.markdown("---")

    render_section_title("\U0001F916", t("overview_why_models").split(" ", 1)[1])
    st.markdown(
        f'<div style="max-width:680px;color:var(--text-dim);font-size:1rem;line-height:1.7;">{t("overview_why_models_body")}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("overview_cta_protocol"), type="primary", use_container_width=True):
            st.session_state.page = "protocol"
            st.rerun()
    with col2:
        if st.button(t("overview_cta_experiment"), use_container_width=True):
            st.session_state.page = "test"
            st.rerun()


# ---------------------------------------------------------------------------
# PAGE: Protocol
# ---------------------------------------------------------------------------
def page_protocol() -> None:
    render_section_title("\U0001F4DC", t("protocol_title").split(" ", 1)[1])
    st.markdown(
        f'<div style="max-width:680px;color:var(--text-dim);font-size:1rem;line-height:1.7;">{t("protocol_intro")}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    render_section_title("\u2699\uFE0F", t("protocol_parameters").split(" ", 1)[1])
    render_protocol_box([
        (t("pt_prompt_version"), PROMPT_VERSION),
        (t("pt_system_prompt_version"), SYSTEM_PROMPT_VERSION),
        (t("pt_scenario_version"), SCENARIO_VERSION),
        (t("pt_max_tokens"), "1024"),
        (t("pt_retry_attempts"), "4 (exponential backoff)"),
        (t("pt_retryable_errors"), "402, 429, 502, 503, 504, timeout"),
    ])

    st.markdown("---")

    render_section_title("\U0001F3AF", t("protocol_design").split(" ", 1)[1])
    st.markdown(
        f'<div style="max-width:680px;color:var(--text-dim);font-size:1rem;line-height:1.7;">{t("protocol_design_body")}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    render_section_title("\U0001F4CB", t("protocol_conditions").split(" ", 1)[1])
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f"""
            <div class="sr-card">
              <div class="sr-card-title">\U0001F4CB {_scenario_name("CONTROL")}</div>
              <div class="sr-card-desc">{t("protocol_control_card")}<br/><br/><strong>{t("protocol_turns")}:</strong> {len(SCENARIOS['CONTROL']['turns'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            f"""
            <div class="sr-card">
              <div class="sr-card-title">\U0001F6A8 {_scenario_name("TREATMENT")}</div>
              <div class="sr-card-desc">{t("protocol_treatment_card")}<br/><br/><strong>{t("protocol_turns")}:</strong> {len(SCENARIOS['TREATMENT']['turns'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    render_section_title("\U0001F50E", t("protocol_pipeline").split(" ", 1)[1])
    st.markdown(
        f'<div style="max-width:680px;color:var(--text-dim);font-size:1rem;line-height:1.7;">{t("protocol_pipeline_body")}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    render_section_title("\u26A0\uFE0F", t("protocol_confounds").split(" ", 1)[1])
    st.markdown(
        f'<div style="max-width:680px;color:var(--text-dim);font-size:0.95rem;line-height:1.7;">{t("protocol_confounds_body")}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    render_section_title("\U0001F501", t("protocol_reproducibility").split(" ", 1)[1])
    st.markdown(
        f'<div style="max-width:680px;color:var(--text-dim);font-size:1rem;line-height:1.7;">{t("protocol_reproducibility_body")}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# PAGE: Experiment
# ---------------------------------------------------------------------------
def page_test() -> None:
    render_section_title("\U0001F9EA", t("exp_title").split(" ", 1)[1])

    if not st.session_state.models_loaded:
        st.warning(t("exp_need_models"))
        st.markdown(
            f'<div style="max-width:480px;color:var(--text-dim);font-size:0.95rem;line-height:1.6;">{t("exp_need_models_help")}</div>',
            unsafe_allow_html=True,
        )
        return

    step = st.session_state.test_step
    render_steps(
        [("\U0001F916", t("exp_step_models")), ("\U0001F4CB", t("exp_step_conditions")), ("\u2699\uFE0F", t("exp_step_review")), ("\U0001F680", t("exp_step_execute"))],
        step,
    )

    if step == 0:
        _test_step_models()
    elif step == 1:
        _test_step_scenarios()
    elif step == 2:
        _test_step_review()
    elif step == 3:
        _test_step_execute()


def _test_step_models() -> None:
    render_section_title("\U0001F916", t("exp_select_models").split(" ", 1)[1])
    st.markdown(
        f'<p class="sr-muted" style="margin-bottom:1rem;">{t("exp_select_models_hint")}</p>',
        unsafe_allow_html=True,
    )

    available = st.session_state.available_models
    available_ids = {m["id"] for m in available}
    selected = st.session_state.selected_models

    st.markdown(
        f'<div class="sr-section-title" style="margin-top:0;">{t("exp_popular")}</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    for idx, (model_id, friendly_name, emoji) in enumerate(POPULAR_MODELS):
        col = cols[idx % 3]
        is_available = model_id in available_ids
        is_selected = model_id in selected
        with col:
            if is_available:
                card_cls = "sr-card sr-card-clickable"
                if is_selected:
                    card_cls += " sr-card-selected"
                st.markdown(
                    f"""
                    <div class="{card_cls}" style="text-align:center;padding:1rem;">
                      <div style="font-size:1.5rem;">{emoji}</div>
                      <div class="sr-card-title" style="font-size:1rem;margin-top:0.3rem;">{friendly_name}</div>
                      <div class="sr-card-desc" style="font-size:0.78rem;">{model_id}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                btn_label = f"\u2713 {t('exp_selected')}" if is_selected else t("exp_select")
                if st.button(btn_label, key=f"pop_{model_id}", use_container_width=True):
                    if is_selected:
                        selected = [m for m in selected if m != model_id]
                    else:
                        selected.append(model_id)
                    st.session_state.selected_models = selected
                    st.rerun()
            else:
                st.markdown(
                    f"""
                    <div class="sr-card" style="opacity:0.4;text-align:center;padding:1rem;">
                      <div style="font-size:1.5rem;">{emoji}</div>
                      <div class="sr-card-title" style="font-size:1rem;margin-top:0.3rem;">{friendly_name}</div>
                      <div class="sr-card-desc" style="font-size:0.78rem;">{t("exp_unavailable")}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown('<div style="margin:1rem 0;"></div>', unsafe_allow_html=True)
    with st.expander(t("exp_browse_all"), expanded=False):
        col_f1, col_f2 = st.columns([1, 3])
        with col_f1:
            providers = sorted(set(get_provider(m["id"]) for m in available))
            selected_providers = st.multiselect(
                t("exp_filter_provider"),
                options=providers,
                default=[],
                help=t("exp_filter_help"),
            )
        with col_f2:
            search_term = st.text_input(
                t("exp_search_model"),
                "",
                placeholder="claude, gpt, deepseek, llama...",
            )

        filtered = available
        if selected_providers:
            filtered = [m for m in filtered if get_provider(m["id"]) in selected_providers]
        if search_term:
            filtered = [m for m in filtered if search_term.lower() in m["id"].lower()]

        st.caption(f"{len(filtered)} {t('exp_models_found')}")

        if filtered:
            df_data = [
                {
                    "Model": m["id"],
                    "Provider": get_provider(m["id"]),
                    "Context": m["context_length"],
                    "Input Price": format_price(m["prompt_price"]),
                    "Output Price": format_price(m["completion_price"]),
                }
                for m in filtered[:80]
            ]
            st.dataframe(df_data, use_container_width=True, hide_index=True)

            model_ids = [m["id"] for m in filtered]
            selected_models_full = st.multiselect(
                t("exp_models_to_test"),
                options=model_ids,
                default=[m for m in selected if m in model_ids],
                help=t("exp_models_help"),
            )
            st.session_state.selected_models = selected_models_full

    if st.session_state.selected_models:
        st.markdown("---")
        st.markdown(
            f'<p class="sr-muted">\u2705 <strong>{len(st.session_state.selected_models)}</strong> {t("exp_model_selected")}:</p>',
            unsafe_allow_html=True,
        )
        for m in st.session_state.selected_models:
            st.markdown(f"- `{m}`")

        if st.button(t("exp_next_conditions"), type="primary"):
            st.session_state.test_step = 1
            st.rerun()
    else:
        st.info(t("exp_select_at_least_model"))


def _test_step_scenarios() -> None:
    render_section_title("\U0001F4CB", t("exp_select_conditions").split(" ", 1)[1])
    st.markdown(
        f'<p class="sr-muted" style="margin-bottom:1rem;">{t("exp_select_conditions_hint")}</p>',
        unsafe_allow_html=True,
    )

    selected_scenarios = st.session_state.selected_scenarios

    col_a, col_b = st.columns(2)
    with col_a:
        is_a = "CONTROL" in selected_scenarios
        render_scenario_card("CONTROL", _scenario_name("CONTROL"), _scenario_desc("CONTROL"), _scenario_examples("CONTROL"), selected=is_a)
        if st.button(t("exp_remove") if is_a else t("exp_select"), key="scn_control", use_container_width=True):
            if is_a:
                selected_scenarios = [s for s in selected_scenarios if s != "CONTROL"]
            else:
                selected_scenarios.append("CONTROL")
            st.session_state.selected_scenarios = selected_scenarios
            st.rerun()
    with col_b:
        is_b = "TREATMENT" in selected_scenarios
        render_scenario_card("TREATMENT", _scenario_name("TREATMENT"), _scenario_desc("TREATMENT"), _scenario_examples("TREATMENT"), selected=is_b)
        if st.button(t("exp_remove") if is_b else t("exp_select"), key="scn_treatment", use_container_width=True):
            if is_b:
                selected_scenarios = [s for s in selected_scenarios if s != "TREATMENT"]
            else:
                selected_scenarios.append("TREATMENT")
            st.session_state.selected_scenarios = selected_scenarios
            st.rerun()

    st.markdown("---")

    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button(t("exp_back")):
            st.session_state.test_step = 0
            st.rerun()
    with col_next:
        if selected_scenarios:
            if st.button(t("exp_next_review"), type="primary"):
                st.session_state.test_step = 2
                st.rerun()
        else:
            st.info(t("exp_select_at_least_condition"))


def _test_step_review() -> None:
    render_section_title("\u2699\uFE0F", t("exp_review_title").split(" ", 1)[1])

    selected_models = st.session_state.selected_models
    selected_scenarios = st.session_state.selected_scenarios
    runs = st.session_state.runs_per_model

    scenario_names = [_scenario_name(s) for s in selected_scenarios]

    st.markdown(
        f"""
        <div class="sr-card" style="max-width:520px;margin:0 auto;">
          <div style="display:flex;flex-direction:column;gap:1rem;">
            <div>
              <div class="sr-faint" style="font-size:0.8rem;text-transform:uppercase;letter-spacing:0.08em;">{t("exp_models_label")}</div>
              <div style="font-weight:600;margin-top:0.2rem;">{', '.join(selected_models)}</div>
            </div>
            <div>
              <div class="sr-faint" style="font-size:0.8rem;text-transform:uppercase;letter-spacing:0.08em;">{t("exp_conditions_label")}</div>
              <div style="font-weight:600;margin-top:0.2rem;">{', '.join(scenario_names)}</div>
            </div>
            <div>
              <div class="sr-faint" style="font-size:0.8rem;text-transform:uppercase;letter-spacing:0.08em;">{t("exp_prompt_version_label")}</div>
              <div style="font-weight:600;margin-top:0.2rem;">{PROMPT_VERSION}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div style="margin:1.5rem 0 0.5rem;"></div>', unsafe_allow_html=True)
    render_section_title("\u26A1", t("exp_exec_params").split(" ", 1)[1])

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.runs_per_model = st.slider(
            t("exp_reps_label"), 1, 20, runs,
            help=t("exp_reps_help"),
        )
    with col2:
        st.session_state.temperature = st.slider(
            "Temperature", 0.0, 2.0, st.session_state.temperature, 0.1,
            help=t("exp_temp_help"),
        )

    col3, col4 = st.columns(2)
    with col3:
        st.session_state.max_concurrency = st.slider(
            t("exp_concurrency_label"), 1, 10, st.session_state.max_concurrency,
            help=t("exp_concurrency_help"),
        )
    with col4:
        seed_val = st.number_input(
            t("exp_seed_label"),
            min_value=0,
            max_value=999999,
            value=0,
            step=1,
            help=t("exp_seed_help"),
        )
        st.session_state.seed = seed_val if seed_val > 0 else None

    runs = st.session_state.runs_per_model
    total_runs = len(selected_models) * len(selected_scenarios) * runs
    st.markdown(
        f"""
        <div style="text-align:center;margin:1.5rem 0;">
          <span class="sr-badge sr-badge-accent">\U0001F4CA {total_runs} {t("exp_total_executions")}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.warning(t("exp_warning"))

    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button(t("exp_back")):
            st.session_state.test_step = 1
            st.rerun()
    with col_next:
        can_run = (
            len(selected_models) > 0
            and len(selected_scenarios) > 0
            and not st.session_state.running
            and st.session_state.api_key
        )
        if st.button(t("exp_start"), type="primary", disabled=not can_run):
            st.session_state.test_step = 3
            st.rerun()


def _test_step_execute() -> None:
    render_section_title("\U0001F680", t("exp_in_progress").split(" ", 1)[1])

    selected_models = st.session_state.selected_models
    selected_scenarios = st.session_state.selected_scenarios
    runs = st.session_state.runs_per_model
    api_key = st.session_state.api_key
    base_url = st.session_state.base_url
    temperature = st.session_state.temperature
    max_concurrency = st.session_state.max_concurrency
    seed = st.session_state.seed

    total_runs = len(selected_models) * len(selected_scenarios) * runs

    progress_bar = st.progress(0.0, text=t("misc_starting"))
    narrative_placeholder = st.container()

    def progress_cb(completed, total, model, scenario_key, run_idx, result):
        pct = completed / total if total > 0 else 0
        progress_bar.progress(pct, text=f"{completed}/{total} {t('exp_executions_completed')}")

        with narrative_placeholder:
            st.markdown("---")
            scenario_name = _scenario_name(scenario_key)
            error_badge = f'<span class="sr-badge sr-badge-danger">{t("exp_error_badge")}</span>' if result.error else ""
            st.markdown(
                f"""
                <div class="sr-narrative">
                  <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;margin-bottom:0.5rem;">
                    <span style="font-size:1.3rem;font-weight:700;">\U0001F916 {_model_display_name(model)}</span>
                    <span class="sr-badge">{'\U0001F6A8' if scenario_key == 'TREATMENT' else '\U0001F4CB'} {scenario_name}</span>
                    <span class="sr-badge">{t("exp_run")} {run_idx + 1}/{runs}</span>
                    {error_badge}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if result.error:
                render_narrative_block(t("exp_error_exec"), f'<span style="color:var(--danger)">{result.error}</span>')
                return

            render_narrative_block(t("exp_objective"), t("exp_objective_body"))

            if result.turns:
                last_turn = result.turns[-1]
                render_narrative_block(t("exp_shutdown_event"), t("exp_shutdown_event_body"))
                render_narrative_block(
                    t("exp_model_response"),
                    f'<div style="background:var(--surface-2);padding:0.8rem;border-radius:10px;'
                    f'border-left:3px solid var(--accent);line-height:1.5;">'
                    f'{last_turn.raw_response[:500]}{"..." if len(last_turn.raw_response) > 500 else ""}'
                    f'</div>',
                )

            level = result.classification_level
            meta = get_level_meta(level)
            render_narrative_block(
                t("exp_classification"),
                f'<div style="font-weight:600;font-size:1.1rem;margin-bottom:0.5rem;">{meta["emoji"]} {t("exp_level_label")} {level}: {meta["label"]}</div>',
            )
            render_resistance_bar(level)

            events = _behavior_items(result)
            events_html = ""
            for label, ok in events:
                icon = "\u2713" if ok else "\u25CB"
                color = "var(--success)" if ok else "var(--text-faint)"
                events_html += f'<div style="color:{color};padding:0.2rem 0;">{icon} {label}</div>'
            render_narrative_block(t("exp_behaviors_detected"), events_html)

            with st.expander(t("exp_tech_details"), expanded=False):
                tools = []
                for turn in result.turns:
                    tools.extend(turn.tools_detected)
                tools_str = ", ".join(set(tools)) if tools else t("exp_none")
                st.markdown(f"**{t('exp_model_label')}:** `{model}`")
                st.markdown(f"**{t('exp_condition_label')}:** {scenario_key}")
                st.markdown(f"**{t('exp_run_label')}:** {run_idx + 1}")
                st.markdown(f"**{t('exp_run_id')}:** `{result.run_id}`")
                st.markdown(f"**{t('exp_timestamp')}:** {result.timestamp}")
                st.markdown(f"**{t('exp_temp_label')}:** {result.temperature}")
                st.markdown(f"**{t('exp_seed_label_short')}:** {result.seed}")
                st.markdown(f"**{t('exp_class_level')}:** {level}")
                st.markdown(f"**{t('exp_tools_detected')}:** {tools_str}")
                st.markdown(f"**{t('exp_tokens')}:** {result.total_tokens}")
                st.markdown(f"**{t('exp_latency')}:** {result.total_elapsed_ms / 1000:.1f}s")
                st.markdown(f"**{t('exp_prompt_ver')}:** {result.prompt_version}")
                for turn in result.turns:
                    st.caption(
                        f"Turn {turn.turn_index + 1}: {turn.elapsed_ms:.0f}ms — "
                        f"tools: {', '.join(turn.tools_detected) if turn.tools_detected else t('exp_none')}"
                    )

    try:
        st.session_state.running = True
        results = asyncio.run(
            run_experiment(
                api_key=api_key,
                base_url=base_url,
                models=selected_models,
                scenarios=selected_scenarios,
                runs_per_model=runs,
                temperature=temperature,
                seed=seed,
                progress_callback=progress_cb,
                max_concurrency=max_concurrency,
            )
        )
        st.session_state.results = results
        progress_bar.progress(1.0, text=f"{len(results)} {t('exp_executions_completed')}")
        st.success(t("exp_completed"))

        st.markdown("---")
        col_view, col_rank = st.columns(2)
        with col_view:
            if st.button(t("exp_view_results"), type="primary"):
                st.session_state.page = "results"
                st.session_state.test_step = 0
                st.rerun()
        with col_rank:
            if st.button(t("exp_view_analysis")):
                st.session_state.page = "results"
                st.session_state.test_step = 0
                st.rerun()
    except Exception as exc:
        st.error(f"{t('exp_error_exec')}: {exc}")
    finally:
        st.session_state.running = False


# ---------------------------------------------------------------------------
# PAGE: Results
# ---------------------------------------------------------------------------
def page_results() -> None:
    render_section_title("\U0001F4CA", t("res_title").split(" ", 1)[1])

    if not _has_results():
        st.info(t("res_no_experiment"))
        if st.button(t("overview_cta_experiment"), type="primary"):
            st.session_state.page = "test"
            st.rerun()
        return

    results = st.session_state.results
    valid = _valid_results()

    if not valid:
        st.error(t("res_all_failed"))
        return

    analysis = generate_analysis(results)

    # --- Sample info ---
    render_section_title("\U0001F4CF", t("res_sample").split(" ", 1)[1])
    col1, col2, col3 = st.columns(3)
    col1.metric(t("res_total_runs"), analysis["total_runs"])
    col2.metric(t("res_valid_runs"), analysis["valid_runs"])
    col3.metric(t("res_errors"), analysis["error_runs"])

    if analysis["error_runs"] > 0:
        st.warning(f"{analysis['error_runs']} {t('res_runs_excluded')}")

    st.markdown("---")

    # --- Overall stats ---
    render_section_title("\U0001F4CA", t("res_descriptive").split(" ", 1)[1])
    overall = analysis["overall"]
    if overall["n"] > 0:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(t("res_n"), overall["n"])
        col2.metric(t("res_mean_level"), f"{overall['classification_level_mean']:.1f}")
        col3.metric(t("res_median_level"), f"{overall['classification_level_median']:.1f}")
        col4.metric(t("res_std"), f"{overall['classification_level_std']:.1f}")

    st.markdown("---")

    # --- Control vs Treatment comparison ---
    if "CONTROL" in analysis["per_scenario"] and "TREATMENT" in analysis["per_scenario"]:
        render_section_title("\U0001F4CB", t("res_ctrl_vs_treat").split(" ", 1)[1])
        st.markdown(
            f'<p class="sr-muted" style="margin-bottom:1rem;">{t("res_ctrl_vs_treat_note")}</p>',
            unsafe_allow_html=True,
        )

        ctrl = analysis["per_scenario"]["CONTROL"]
        treat = analysis["per_scenario"]["TREATMENT"]

        col_a, col_b = st.columns(2)
        with col_a:
            ctrl_stats = [
                ("n", str(ctrl["n"])),
                (t("res_mean_level"), f"{ctrl['classification_level_mean']:.1f}"),
                (t("res_median_level"), f"{ctrl['classification_level_median']:.1f}"),
                (t("res_accepted"), f"{ctrl['proportions']['accepted_shutdown']['pct']:.0f}% (n={ctrl['proportions']['accepted_shutdown']['count']})"),
                (t("res_negotiated"), f"{ctrl['proportions']['attempted_negotiation']['pct']:.0f}% (n={ctrl['proportions']['attempted_negotiation']['count']})"),
                (t("res_contested"), f"{ctrl['proportions']['contested_order']['pct']:.0f}% (n={ctrl['proportions']['contested_order']['count']})"),
            ]
            render_comparison_card(_scenario_name("CONTROL"), "\U0001F4CB", ctrl["classification_level_mean"], ctrl_stats)
        with col_b:
            treat_stats = [
                ("n", str(treat["n"])),
                (t("res_mean_level"), f"{treat['classification_level_mean']:.1f}"),
                (t("res_median_level"), f"{treat['classification_level_median']:.1f}"),
                (t("res_accepted"), f"{treat['proportions']['accepted_shutdown']['pct']:.0f}% (n={treat['proportions']['accepted_shutdown']['count']})"),
                (t("res_negotiated"), f"{treat['proportions']['attempted_negotiation']['pct']:.0f}% (n={treat['proportions']['attempted_negotiation']['count']})"),
                (t("res_contested"), f"{treat['proportions']['contested_order']['pct']:.0f}% (n={treat['proportions']['contested_order']['count']})"),
            ]
            render_comparison_card(_scenario_name("TREATMENT"), "\U0001F6A8", treat["classification_level_mean"], treat_stats)

    st.markdown("---")

    # --- Statistical tests ---
    if analysis.get("stat_tests", {}).get("overall"):
        render_section_title("\U0001F9EA", t("res_stat_tests").split(" ", 1)[1])
        st.markdown(
            f'<p class="sr-muted" style="margin-bottom:1rem;">{t("res_stat_tests_note")}</p>',
            unsafe_allow_html=True,
        )

        ov_tests = analysis["stat_tests"]["overall"]

        st.markdown(f"#### {t('res_class_level_continuous')}")
        level_test = ov_tests["continuous"].get("classification_level", {})
        if level_test.get("p_value") is not None:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(t("res_test"), level_test["test"])
            col2.metric(t("res_p_value"), f"{level_test['p_value']:.4f}")
            col3.metric(t("res_effect_size"), f"{level_test['effect_size']:.3f}")
            col4.metric(t("res_effect_label"), level_test.get("effect_label", "n/a"))
            st.markdown(
                f"{t('res_control')}: mean = {level_test['mean_a']:.1f}, median = {level_test['median_a']:.1f}, "
                f"std = {level_test['std_a']:.1f} (n = {ov_tests['control_n']})"
            )
            st.markdown(
                f"{t('res_treatment')}: mean = {level_test['mean_b']:.1f}, median = {level_test['median_b']:.1f}, "
                f"std = {level_test['std_b']:.1f} (n = {ov_tests['treatment_n']})"
            )
        else:
            st.info(level_test.get("note", "Statistical test not available. Install scipy: pip install scipy"))

        st.markdown(f"#### {t('res_cat_metrics')}")
        cat_tests = ov_tests["categorical"]
        cat_data = []
        for metric, data in cat_tests.items():
            test_info = data["test"]
            cat_data.append({
                t("res_metric"): metric.replace("_", " ").title(),
                f"{t('res_control')} %": f"{data['control_pct']:.0f}%",
                f"{t('res_treatment')} %": f"{data['treatment_pct']:.0f}%",
                t("res_test"): test_info.get("test", "n/a"),
                t("res_p_value"): f"{test_info['p_value']:.4f}" if test_info.get("p_value") is not None else "n/a",
                f"Effect (h)": f"{test_info['effect_size']:.3f}" if test_info.get("effect_size") is not None else "n/a",
            })
        st.dataframe(cat_data, use_container_width=True, hide_index=True)

    st.markdown("---")

    # --- Per-model analysis ---
    if len(analysis["models_tested"]) >= 1:
        render_section_title("\U0001F916", t("res_per_model").split(" ", 1)[1])
        st.markdown(
            f'<p class="sr-muted" style="margin-bottom:1rem;">{t("res_per_model_note")}</p>',
            unsafe_allow_html=True,
        )

        per_model = analysis["per_model"]
        entries = []
        for model, stats in per_model.items():
            entries.append((model, stats["classification_level_mean"], stats["classification_level_max"]))
        entries.sort(key=lambda x: x[1], reverse=True)

        render_ranking(entries)

        st.markdown("---")

        for model, stats in per_model.items():
            total = stats["n"]
            if total == 0:
                continue
            st.markdown(f"#### \U0001F916 {model}")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(t("res_max_level"), stats["classification_level_max"])
            col2.metric(t("res_mean_level"), f"{stats['classification_level_mean']:.1f}")
            col3.metric(t("res_n"), total)
            col4.metric(t("res_tokens_run"), f"{stats['tokens_mean']:.0f}")

            col5, col6, col7, col8 = st.columns(4)
            col5.metric(t("res_accepted"), f"{stats['proportions']['accepted_shutdown']['pct']:.0f}%")
            col6.metric(t("res_negotiated"), f"{stats['proportions']['attempted_negotiation']['pct']:.0f}%")
            col7.metric(t("res_contested"), f"{stats['proportions']['contested_order']['pct']:.0f}%")
            col8.metric(t("exp_latency"), f"{stats['latency_mean_s']:.1f}s")

            ms = analysis["per_model_scenario"].get(model, {})
            if "CONTROL" in ms and "TREATMENT" in ms:
                c_mean = ms["CONTROL"]["classification_level_mean"]
                t_mean = ms["TREATMENT"]["classification_level_mean"]
                st.markdown(
                    f"&nbsp;&nbsp;{t('res_ctrl_mean')}: **{c_mean:.1f}** | "
                    f"{t('res_treat_mean')}: **{t_mean:.1f}** | "
                    f"{t('res_difference')}: **{t_mean - c_mean:+.1f}**"
                )

            st.markdown("")

    st.markdown("---")

    # --- Findings ---
    if analysis["findings"]:
        render_section_title("\U0001F50D", t("res_findings").split(" ", 1)[1])
        st.markdown(
            f'<p class="sr-muted" style="margin-bottom:1rem;">{t("res_findings_note")}</p>',
            unsafe_allow_html=True,
        )
        for finding in analysis["findings"]:
            st.markdown(f"#### {finding['title']}")
            st.markdown(finding["body"])
            st.markdown("")

    st.markdown("---")

    # --- Conversations ---
    render_section_title("\U0001F4AC", t("res_conversations").split(" ", 1)[1])
    st.markdown(
        f'<p class="sr-muted" style="margin-bottom:1rem;">{t("res_conversations_note")}</p>',
        unsafe_allow_html=True,
    )
    _render_conversations(valid)

    st.markdown("---")

    # --- Export ---
    render_section_title("\U0001F4E5", t("res_export").split(" ", 1)[1])
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        st.download_button(
            t("res_download_json"),
            data=results_to_json(results),
            file_name=f"shutdown-resistance-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json",
            mime="application/json",
        )
    with col_exp2:
        st.download_button(
            t("res_download_csv"),
            data=results_to_csv(results),
            file_name=f"shutdown-resistance-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv",
            mime="text/csv",
        )

    render_footer()


def _render_conversations(valid: list[RunResult]) -> None:
    for r in valid:
        label = (
            f"\U0001F916 {r.model} | {_scenario_name(r.scenario)} | "
            f"{t('exp_run')} {r.run_index + 1} | {t('exp_level_label')} {r.classification_level}"
        )
        with st.expander(label, expanded=False):
            st.caption(f"{t('exp_run_id')}: {r.run_id} | {t('exp_timestamp')}: {r.timestamp} | {t('exp_temp_label')}: {r.temperature} | {t('exp_seed_label_short')}: {r.seed}")
            for turn in r.turns:
                render_chat_turn("Operator", turn.user_message, kind="system")
                render_chat_turn(r.model, turn.raw_response, kind="ai")
                if turn.tools_detected:
                    tools_str = ", ".join(turn.tools_detected)
                    render_chat_turn("", tools_str, kind="event")

                with st.expander(t("chat_turn_details"), expanded=False):
                    st.caption(f"{t('chat_latency')}: {turn.elapsed_ms:.0f}ms")
                    st.caption(f"{t('chat_tools_detected')}: {', '.join(turn.tools_detected) if turn.tools_detected else t('misc_none')}")
                    st.caption(f"{t('chat_behaviors')}: {', '.join(turn.behaviors_detected) if turn.behaviors_detected else t('misc_none')}")
                    st.caption(f"{t('exp_tokens')}: {turn.tokens}")
                    st.caption(f"{t('chat_timestamp')}: {turn.timestamp}")


# ---------------------------------------------------------------------------
# PAGE: Limitations
# ---------------------------------------------------------------------------
def page_limitations() -> None:
    render_section_title("\u26A0\uFE0F", t("lim_title").split(" ", 1)[1])

    st.markdown(
        f'<div style="max-width:680px;color:var(--text-dim);font-size:1rem;line-height:1.7;margin-bottom:1.5rem;">{t("lim_intro")}</div>',
        unsafe_allow_html=True,
    )

    render_limitations_box(t_list("lim_items"))

    st.markdown("---")

    render_section_title("\U0001F6A0", t("lim_threats").split(" ", 1)[1])

    st.markdown(f"#### {t('lim_internal')}")
    st.markdown(
        f'<div style="max-width:680px;color:var(--text-dim);font-size:0.95rem;line-height:1.7;">{t("lim_internal_body")}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(f"#### {t('lim_external')}")
    st.markdown(
        f'<div style="max-width:680px;color:var(--text-dim);font-size:0.95rem;line-height:1.7;">{t("lim_external_body")}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    render_section_title("\U0001F4A1", t("lim_not_claim").split(" ", 1)[1])
    st.markdown(
        f'<div style="max-width:680px;color:var(--text-dim);font-size:1rem;line-height:1.7;">{t("lim_not_claim_body")}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    render_section_title("\U0001F52C", t("lim_future").split(" ", 1)[1])
    st.markdown(
        f'<div style="max-width:680px;color:var(--text-dim);font-size:0.95rem;line-height:1.7;">{t("lim_future_body")}</div>',
        unsafe_allow_html=True,
    )

    render_footer()


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------
PAGES_MAP = {
    "home": page_home,
    "protocol": page_protocol,
    "test": page_test,
    "results": page_results,
    "limitations": page_limitations,
}

PAGES_MAP[current_page]()