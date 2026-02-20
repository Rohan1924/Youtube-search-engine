import json
import os
import re
import time
import uuid
from pathlib import Path

import requests
import streamlit as st

from transcribe_videos import process_single_video, process_youtube_search


HOST = os.getenv("LANGFLOW_HOST", "")
UPLOAD_FLOW_ID = os.getenv("LANGFLOW_UPLOAD_FLOW_ID", "")
QUERY_FLOW_ID = os.getenv("LANGFLOW_QUERY_FLOW_ID", "")
API_KEY = os.getenv("LANGFLOW_API_KEY", "")
TIMEOUT = float(os.getenv("LANGFLOW_TIMEOUT", "90"))
OUTPUT_DIR = Path("./whisper_outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def config_is_ready() -> bool:
    return bool(HOST and UPLOAD_FLOW_ID and QUERY_FLOW_ID)


def attempt_post(url, payload, headers=None, params=None):
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers or {},
            params=params or {},
            timeout=TIMEOUT,
        )
        return (200 <= response.status_code < 300), response.status_code, response.text
    except requests.RequestException as exc:
        return False, None, f"RequestException: {exc}"


def try_auth_methods(url, payload, api_key):
    ok, status, body = attempt_post(
        url,
        payload,
        headers={"Content-Type": "application/json"},
    )
    if ok:
        return ok, status, body, "no-auth"

    if not api_key:
        return ok, status, body, "no-auth-failed"

    ok, status, body = attempt_post(
        url,
        payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    if ok:
        return ok, status, body, "bearer"

    ok, status, body = attempt_post(
        url,
        payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
        },
    )
    if ok:
        return ok, status, body, "x-api-key"

    ok, status, body = attempt_post(
        url,
        payload,
        headers={"Content-Type": "application/json"},
        params={"api_key": api_key},
    )
    return ok, status, body, "query-param"


def format_for_langflow(doc):
    return f"[VID:{doc['video_id']}|{doc['start']}-{doc['end']}s] {doc['text']}"


def send_chunks_to_langflow(docs, api_key, progress_bar=None, status_text=None):
    total = len(docs)
    results = []
    session_id = str(uuid.uuid4())
    upload_url = f"{HOST}/api/v1/run/{UPLOAD_FLOW_ID}"

    for idx, doc in enumerate(docs, 1):
        payload = {
            "output_type": "text",
            "input_type": "chat",
            "input_value": format_for_langflow(doc),
            "session_id": session_id,
        }

        ok, status, body, _ = try_auth_methods(upload_url, payload, api_key)
        results.append((ok, status, doc["video_id"]))

        if progress_bar:
            progress_bar.progress(idx / total)
        if status_text:
            status_text.text(f"Uploading chunk {idx}/{total}...")

        if status in {403, 500}:
            return False, f"Upload stopped at chunk {idx}: status {status}. Response: {body[:120]}"

        time.sleep(0.15)

    successes = sum(1 for item in results if item[0])
    return True, f"Uploaded {successes}/{total} chunks."


def parse_response_json(response_text):
    try:
        data = json.loads(response_text)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            outputs = data.get("outputs", [])
            if outputs:
                nested_outputs = outputs[0].get("outputs", [])
                if nested_outputs:
                    results = nested_outputs[0].get("results", {})
                    message = results.get("message")
                    if isinstance(message, dict):
                        text = message.get("text")
                        if isinstance(text, str):
                            return json.loads(text)
                    if isinstance(message, str):
                        return json.loads(message)
        return None
    except Exception:
        return None


def extract_video_id(raw_input: str):
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?]+)",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw_input)
        if match:
            return match.group(1)
    return ""


def inject_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

        :root {
          --bg: #f5f7fb;
          --panel: #ffffff;
          --panel-border: #d8e0ef;
          --text: #182235;
          --muted: #5f6f88;
          --accent: #1f4fff;
          --accent-soft: rgba(31, 79, 255, 0.08);
          --ok: #0f9f6e;
          --warn: #be7b04;
          --bad: #b62a36;
        }

        .stApp {
          background:
            radial-gradient(circle at 4% 8%, rgba(31, 79, 255, 0.08), transparent 28%),
            radial-gradient(circle at 94% 4%, rgba(15, 159, 110, 0.07), transparent 30%),
            var(--bg);
          color: var(--text);
          font-family: 'Space Grotesk', sans-serif;
        }

        h1, h2, h3 {
          letter-spacing: -0.02em;
          color: var(--text);
          font-family: 'Space Grotesk', sans-serif;
        }

        p, li, label, .stMarkdown {
          color: var(--text);
        }

        [data-testid="stSidebar"] {
          background: linear-gradient(180deg, #f8fbff 0%, #eef3ff 100%);
          border-right: 1px solid var(--panel-border);
        }

        .card {
          background: var(--panel);
          border: 1px solid var(--panel-border);
          border-radius: 16px;
          padding: 1rem 1.1rem;
          margin-bottom: 1rem;
          box-shadow: 0 10px 30px rgba(16, 28, 52, 0.05);
        }

        .meta-chip {
          display: inline-block;
          border-radius: 999px;
          background: var(--accent-soft);
          border: 1px solid rgba(31, 79, 255, 0.2);
          color: #19338f;
          padding: 0.18rem 0.62rem;
          font-size: 0.78rem;
          margin-right: 0.4rem;
          margin-bottom: 0.35rem;
          font-family: 'IBM Plex Mono', monospace;
        }

        .muted {
          color: var(--muted);
        }

        .status-ok { color: var(--ok); font-weight: 600; }
        .status-bad { color: var(--bad); font-weight: 600; }

        div[data-baseweb="tab-list"] {
          gap: 0.4rem;
        }

        button[kind="primary"] {
          border-radius: 10px !important;
          border: none !important;
          font-weight: 600 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="YouTube Search Engine",
    page_icon="YT",
    layout="wide",
)
inject_styles()

st.title("YouTube Search Engine")
st.caption("Transcribe YouTube videos and run semantic retrieval over timestamped segments.")

if not config_is_ready():
    st.warning(
        "Set LANGFLOW_HOST, LANGFLOW_UPLOAD_FLOW_ID, and LANGFLOW_QUERY_FLOW_ID in environment variables before running uploads or search."
    )

st.markdown('<div class="card"><span class="meta-chip">Streamlit UI</span><span class="meta-chip">Whisper</span><span class="meta-chip">LangFlow + AstraDB</span><p class="muted">Pipeline: fetch video -> transcribe -> chunk -> embed -> semantic retrieval.</p></div>', unsafe_allow_html=True)

upload_tab, search_tab = st.tabs(["Upload and Embed", "Search Clips"])

with upload_tab:
    st.subheader("Index videos")
    input_mode = st.radio("Input source", ["YouTube search", "Single video URL"], horizontal=True)

    if input_mode == "YouTube search":
        with st.form("search_upload_form"):
            query = st.text_input("Search query", placeholder="example: conservation of momentum")
            num_videos = st.number_input("Videos to process", min_value=1, max_value=20, value=5)
            submit_search_upload = st.form_submit_button("Run indexing", type="primary")

        if submit_search_upload:
            if not query.strip():
                st.error("Provide a search query.")
            elif not config_is_ready():
                st.error("Configuration is incomplete. Check required environment variables.")
            else:
                with st.spinner(f"Processing {num_videos} videos..."):
                    chunks = process_youtube_search(query, int(num_videos))
                    if not chunks:
                        st.error("No transcript chunks were generated.")
                    else:
                        progress = st.progress(0.0)
                        status = st.empty()
                        success, message = send_chunks_to_langflow(chunks, API_KEY, progress, status)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)

    else:
        with st.form("single_video_form"):
            youtube_link = st.text_input(
                "YouTube URL or video id",
                placeholder="https://www.youtube.com/watch?v=DxKelGugDa8",
            )
            submit_single_upload = st.form_submit_button("Transcribe and upload", type="primary")

        if youtube_link:
            video_id = extract_video_id(youtube_link)
            if video_id:
                st.info(f"Detected video id: {video_id}")
            else:
                st.error("Invalid YouTube link or id.")

        if submit_single_upload:
            if not config_is_ready():
                st.error("Configuration is incomplete. Check required environment variables.")
            else:
                video_id = extract_video_id(youtube_link)
                if not video_id:
                    st.error("Provide a valid YouTube URL or id.")
                else:
                    with st.spinner(f"Processing video {video_id}..."):
                        chunks = process_single_video(video_id)
                        if not chunks:
                            st.error("No transcript chunks were generated for this video.")
                        else:
                            progress = st.progress(0.0)
                            status = st.empty()
                            success, message = send_chunks_to_langflow(chunks, API_KEY, progress, status)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)

with search_tab:
    st.subheader("Retrieve relevant clips")
    with st.form("search_form"):
        query = st.text_input("Query", placeholder="example: where momentum is introduced")
        num_results = st.slider("Results", 1, 10, 5)
        run_query = st.form_submit_button("Search", type="primary")

    if run_query:
        if not query.strip():
            st.warning("Provide a query.")
        elif not config_is_ready():
            st.error("Configuration is incomplete. Check required environment variables.")
        else:
            with st.spinner("Searching..."):
                url = f"{HOST}/api/v1/run/{QUERY_FLOW_ID}"
                payload = {
                    "input_value": query,
                    "output_type": "text",
                    "input_type": "chat",
                }
                ok, status_code, body, _ = try_auth_methods(url, payload, API_KEY)

                if not ok:
                    st.error(f"Search request failed with status: {status_code}")
                else:
                    results = parse_response_json(body)
                    if not results:
                        st.info("No clips found for this query.")
                    else:
                        st.success(f"Found {min(len(results), num_results)} clip(s).")
                        for index, result in enumerate(results[:num_results], 1):
                            video_id = result.get("video_id", "")
                            start = int(result.get("start", 0))
                            end = int(result.get("end", 0))
                            text = result.get("text", "")
                            score = float(result.get("score", 0))
                            video_url = f"https://www.youtube.com/watch?v={video_id}&t={start}s"

                            st.markdown('<div class="card">', unsafe_allow_html=True)
                            st.markdown(f"### Clip {index}")
                            st.markdown(
                                f"<span class='meta-chip'>video={video_id}</span><span class='meta-chip'>time={start}s-{end}s</span><span class='meta-chip'>score={score:.2f}</span>",
                                unsafe_allow_html=True,
                            )

                            left, right = st.columns([3, 2])
                            with left:
                                st.video(video_url, start_time=start)
                                st.link_button("Open in YouTube", video_url, use_container_width=True)
                            with right:
                                clean_text = re.sub(r"\[VID:.*?\]\s*", "", text)
                                snippet = clean_text[:500] + "..." if len(clean_text) > 500 else clean_text
                                st.text_area(
                                    f"Transcript excerpt {index}",
                                    snippet,
                                    height=220,
                                    key=f"snippet_{index}",
                                )
                            st.markdown("</div>", unsafe_allow_html=True)

with st.sidebar:
    st.header("System")
    host_state = "configured" if HOST else "missing"
    upload_state = "configured" if UPLOAD_FLOW_ID else "missing"
    query_state = "configured" if QUERY_FLOW_ID else "missing"

    st.markdown(f"Host: `{host_state}`")
    st.markdown(f"Upload flow: `{upload_state}`")
    st.markdown(f"Query flow: `{query_state}`")
    st.markdown(f"API key: `{'set' if API_KEY else 'not set'}`")
    st.code(str(OUTPUT_DIR))

    if config_is_ready():
        st.markdown('<p class="status-ok">Configuration ready</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="status-bad">Configuration incomplete</p>', unsafe_allow_html=True)
