from __future__ import annotations

import datetime as dt
import logging
import uuid
from pathlib import Path

import streamlit as st

from src.analytics import GA4Tracker
from src.landing_tracker import (
    normalize_channel,
    normalize_post_id,
    normalize_source_id,
    save_lead,
    track_cta,
    track_visit,
)


COPY = {
    "EN": {
        "hero_label": "Ask Before You Eat",
        "headline": "Ask first. Decide safer in 10 seconds.",
        "subcopy": "See evidence, check confidence, and show the right question before you order.",
        "cta_pilot": "Join pilot",
        "cta_scan": "Try first scan",
        "cta_pilot_toast": "Pilot interest tracked.",
        "cta_scan_toast": "First-scan intent tracked.",
        "value_title": "Evidence + Confidence + Confirm",
        "value_1": "Evidence: we show directly matched ingredient clues.",
        "value_2": "Confidence: we indicate certainty before action.",
        "value_3": "Confirm: we prepare staff-facing questions before final choice.",
        "safety_title": "Safety Notice",
        "safety_text": "No diagnosis, no prescription, no definitive medical judgment.",
        "emergency_text": "If emergency symptoms appear, use nearby map/call and contact 119 or 1330 immediately.",
        "lead_title": "Pilot waitlist",
        "lead_label": "Email",
        "lead_placeholder": "name@example.com",
        "lead_consent": "I agree to be contacted for pilot updates.",
        "lead_submit": "Submit",
        "lead_required": "Email is required.",
        "lead_need_consent": "Consent is required to submit.",
        "lead_success": "Thank you. Your pilot lead was saved.",
        "meta_channel": "Channel",
        "meta_date": "Tracking date",
    },
    "JP": {
        "hero_label": "Ask Before You Eat",
        "headline": "先に聞く。10秒でより安全な判断へ。",
        "subcopy": "根拠と確信度を確認し、注文前に店員へ見せる質問をすぐ提示します。",
        "cta_pilot": "パイロット参加",
        "cta_scan": "はじめてのスキャンを試す",
        "cta_pilot_toast": "パイロット参加意向を記録しました。",
        "cta_scan_toast": "初回スキャン意向を記録しました。",
        "value_title": "Evidence + Confidence + Confirm",
        "value_1": "Evidence: 一致した根拠を明示します。",
        "value_2": "Confidence: 行動前に確信度を表示します。",
        "value_3": "Confirm: 最終判断前に店員確認の質問を提示します。",
        "safety_title": "安全に関する注意",
        "safety_text": "診断・処方・医療的確定判断は行いません。",
        "emergency_text": "緊急症状がある場合は、地図/電話を利用し、119または1330へ連絡してください。",
        "lead_title": "パイロット待機リスト",
        "lead_label": "メール",
        "lead_placeholder": "name@example.com",
        "lead_consent": "パイロット関連の連絡を受け取ることに同意します。",
        "lead_submit": "送信",
        "lead_required": "メールアドレスを入力してください。",
        "lead_need_consent": "送信には同意が必要です。",
        "lead_success": "ありがとうございます。登録を保存しました。",
        "meta_channel": "チャネル",
        "meta_date": "計測日",
    },
}


def _legacy_query_params() -> dict[str, list[str]]:
    legacy_getter = getattr(st, "experimental_get_query_params", None)
    if not callable(legacy_getter):
        return {}
    raw_params = legacy_getter()
    if not isinstance(raw_params, dict):
        return {}

    normalized: dict[str, list[str]] = {}
    for key, value in raw_params.items():
        key_text = str(key)
        if isinstance(value, list):
            normalized[key_text] = [str(item) for item in value]
        else:
            normalized[key_text] = [str(value)]
    return normalized


def _get_query_param(key: str, default: str = "") -> str:
    if hasattr(st, "query_params"):
        value = st.query_params.get(key, default)
        if isinstance(value, list):
            return str(value[0]) if value else default
        return str(value)
    raw_params = _legacy_query_params()
    if key not in raw_params:
        return default
    values = raw_params.get(key) or [default]
    return str(values[0]) if values else default


def _resolve_date_token() -> str:
    query_date = _get_query_param("date", "")
    if len(query_date) == 8 and query_date.isdigit():
        return query_date
    return dt.datetime.now().strftime("%Y%m%d")


def _resolve_language() -> str:
    query_lang = _get_query_param("lang", "EN").upper()
    if query_lang in COPY:
        return query_lang
    return "EN"


def _setup_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def _ensure_session_id() -> str:
    if "landing_session_id" not in st.session_state:
        st.session_state["landing_session_id"] = str(uuid.uuid4())
    return str(st.session_state["landing_session_id"])


def _track_page_view_once(
    *,
    ga4: GA4Tracker,
    date_token: str,
    session_id: str,
    channel: str,
    language: str,
    source_id: str,
    post_id: str,
) -> None:
    if st.session_state.get("ga4_page_view_sent"):
        return
    ga4.track(
        date_token=date_token,
        event_name="page_view",
        client_id=session_id,
        channel=channel,
        language=language,
        params={
            "page_title": "askbeforeyoueat_landing",
            "source_id": source_id,
            "post_id": post_id,
        },
    )
    st.session_state["ga4_page_view_sent"] = True


def _track_cta_click(
    *,
    ga4: GA4Tracker,
    date_token: str,
    session_id: str,
    channel: str,
    language: str,
    cta_type: str,
    source_id: str,
    post_id: str,
) -> None:
    track_cta(
        date_token=date_token,
        session_id=session_id,
        channel=channel,
        cta_type=cta_type,
        language=language,
        source_id=source_id,
        post_id=post_id,
    )
    ga4.track(
        date_token=date_token,
        event_name="cta_click",
        client_id=session_id,
        channel=channel,
        language=language,
        params={
            "cta_type": cta_type,
            "source_id": source_id,
            "post_id": post_id,
        },
    )


def _render_style() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
html, body, [class*="css"] {
  font-family: "Space Grotesk", sans-serif;
  color: var(--text);
}
:root {
  --bg: #070d19;
  --surface: #0f1627;
  --text: #f4f7ff;
  --muted: #b7c4de;
  --primary: #ff5258;
  --accent: #29a57e;
  --card-bg: #f3efe6;
  --card-text: #2c2f36;
  --warning-bg: #fff1e7;
  --warning-text: #4a2a16;
}
.stApp {
  background:
    radial-gradient(55rem 35rem at 5% -10%, rgba(41, 165, 126, 0.25), transparent 45%),
    radial-gradient(45rem 30rem at 98% -15%, rgba(255, 82, 88, 0.18), transparent 50%),
    var(--bg);
}
.block-container {
  max-width: 980px;
  padding-top: 2rem;
  padding-bottom: 2rem;
}
.hero {
  background: linear-gradient(120deg, #0d5a47 0%, #1a8b6a 50%, #b8d8c9 100%);
  color: #fffdf9;
  padding: 2rem;
  border-radius: 18px;
  margin-bottom: 1.1rem;
  box-shadow: 0 10px 30px rgba(4, 14, 22, 0.35);
}
.badge {
  display: inline-block;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 999px;
  padding: 0.22rem 0.66rem;
  font-size: 0.85rem;
  margin-bottom: 0.8rem;
}
.value-card {
  background: var(--card-bg);
  color: var(--card-text);
  border: 1px solid #e1d8c6;
  border-radius: 14px;
  padding: 0.95rem 1.05rem;
  margin-bottom: 0.6rem;
  font-size: 1.02rem;
  line-height: 1.35;
}
.safety {
  border-left: 4px solid #cf4b1d;
  background: var(--warning-bg);
  color: var(--warning-text);
  padding: 0.95rem 1.05rem;
  border-radius: 10px;
  line-height: 1.45;
}
.lead-form {
  border: 1px solid #293147;
  border-radius: 12px;
  background: rgba(9, 14, 25, 0.45);
  padding: 0.75rem 0.95rem;
}
[data-testid="stForm"] {
  border: 1px solid #293147;
  border-radius: 12px;
  background: rgba(9, 14, 25, 0.45);
  padding: 0.75rem 0.95rem;
}
[data-testid="stSidebar"] {
  background: var(--surface);
}
div[data-testid="stCaptionContainer"] p {
  color: var(--muted);
}
</style>
""",
        unsafe_allow_html=True,
    )


def _render_hero(text: dict[str, str]) -> None:
    st.markdown(
        f"""
<section class="hero">
  <div class="badge">{text["hero_label"]}</div>
  <h1 style="margin:0 0 .5rem 0; color:#fff8ee;">{text["headline"]}</h1>
  <p style="margin:0; font-size:1.05rem;">{text["subcopy"]}</p>
</section>
""",
        unsafe_allow_html=True,
    )


def _render_cta_buttons(
    *,
    text: dict[str, str],
    ga4: GA4Tracker,
    date_token: str,
    session_id: str,
    channel: str,
    language: str,
    source_id: str,
    post_id: str,
) -> None:
    cta_col1, cta_col2 = st.columns(2)
    with cta_col1:
        if st.button(text["cta_pilot"], use_container_width=True, type="primary"):
            _track_cta_click(
                ga4=ga4,
                date_token=date_token,
                session_id=session_id,
                channel=channel,
                language=language,
                cta_type="pilot",
                source_id=source_id,
                post_id=post_id,
            )
            st.success(text["cta_pilot_toast"])
    with cta_col2:
        if st.button(text["cta_scan"], use_container_width=True):
            _track_cta_click(
                ga4=ga4,
                date_token=date_token,
                session_id=session_id,
                channel=channel,
                language=language,
                cta_type="first_scan",
                source_id=source_id,
                post_id=post_id,
            )
            st.success(text["cta_scan_toast"])


def _render_value_section(text: dict[str, str]) -> None:
    st.subheader(text["value_title"])
    st.markdown(f'<div class="value-card">{text["value_1"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="value-card">{text["value_2"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="value-card">{text["value_3"]}</div>', unsafe_allow_html=True)


def _render_safety_section(text: dict[str, str]) -> None:
    st.subheader(text["safety_title"])
    st.markdown(
        f'<div class="safety"><b>{text["safety_text"]}</b><br/>{text["emergency_text"]}</div>',
        unsafe_allow_html=True,
    )


def _render_lead_form(
    *,
    text: dict[str, str],
    ga4: GA4Tracker,
    date_token: str,
    session_id: str,
    channel: str,
    language: str,
    source_id: str,
    post_id: str,
) -> None:
    st.subheader(text["lead_title"])
    with st.form("pilot_lead_form", clear_on_submit=True):
        lead_email = st.text_input(text["lead_label"], placeholder=text["lead_placeholder"])
        consent = st.checkbox(text["lead_consent"])
        submit = st.form_submit_button(text["lead_submit"])
        if not submit:
            return
        if not lead_email.strip():
            st.error(text["lead_required"])
            return
        if not consent:
            st.error(text["lead_need_consent"])
            return

        save_lead(
            date_token=date_token,
            session_id=session_id,
            channel=channel,
            language=language,
            lead_email=lead_email.strip(),
            consent=True,
            source_id=source_id,
            post_id=post_id,
        )
        ga4.track(
            date_token=date_token,
            event_name="lead_submit",
            client_id=session_id,
            channel=channel,
            language=language,
            params={
                "consent": "1",
                "source_id": source_id,
                "post_id": post_id,
            },
        )
        st.success(text["lead_success"])


def _render_meta(text: dict[str, str], channel: str, date_token: str, source_id: str, post_id: str) -> None:
    meta_col1, meta_col2 = st.columns(2)
    meta_col1.caption(f'{text["meta_channel"]}: {channel}')
    meta_col2.caption(f'{text["meta_date"]}: {date_token} | src={source_id or "-"} | post={post_id or "-"}')


def main() -> None:
    log_path = Path(__file__).resolve().parents[1] / "logs" / "app.log"
    _setup_logging(log_path)

    st.set_page_config(page_title="Ask Before You Eat", page_icon="A", layout="centered")
    _render_style()

    ga4 = GA4Tracker.from_env()
    date_token = _resolve_date_token()
    channel = normalize_channel(_get_query_param("ch", "referral"))
    source_id = normalize_source_id(_get_query_param("src", ""))
    post_id = normalize_post_id(_get_query_param("post_id", ""))
    session_id = _ensure_session_id()

    default_lang = _resolve_language()
    lang = st.radio("Language", ["EN", "JP"], horizontal=True, index=0 if default_lang == "EN" else 1)
    text = COPY[lang]

    track_visit(
        date_token=date_token,
        session_id=session_id,
        channel=channel,
        source_id=source_id,
        post_id=post_id,
    )
    _track_page_view_once(
        ga4=ga4,
        date_token=date_token,
        session_id=session_id,
        channel=channel,
        language=lang,
        source_id=source_id,
        post_id=post_id,
    )

    _render_hero(text)
    _render_cta_buttons(
        text=text,
        ga4=ga4,
        date_token=date_token,
        session_id=session_id,
        channel=channel,
        language=lang,
        source_id=source_id,
        post_id=post_id,
    )
    _render_value_section(text)
    _render_safety_section(text)
    _render_lead_form(
        text=text,
        ga4=ga4,
        date_token=date_token,
        session_id=session_id,
        channel=channel,
        language=lang,
        source_id=source_id,
        post_id=post_id,
    )
    _render_meta(text, channel, date_token, source_id, post_id)
