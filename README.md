# YouTube Search Engine

A clean Streamlit application for indexing YouTube transcripts and retrieving timestamped clips with semantic search.

[Demo Video](https://github.com/Rohan1924/Youtube-search-engine)

## Screenshots

Add your screenshots to `assets/screenshots/` with these names:

- `home.png`
- `upload.png`
- `search-results.png`

Then they will render here:

![Home](assets/screenshots/home.png)
![Upload Pipeline](assets/screenshots/upload.png)
![Search Results](assets/screenshots/search-results.png)

## Demo

- Upload your demo video to `assets/demo/demo.mp4` and commit it if size is acceptable.
- If the file is large, upload to YouTube/Drive and replace the link below.

[Watch Demo](https://github.com/Rohan1924/Youtube-search-engine)

## What it does

- Downloads video audio using `yt-dlp`
- Transcribes with Whisper (fallback to YouTube captions)
- Chunks transcript text with timestamps
- Sends chunks to a LangFlow embedding pipeline (AstraDB-backed)
- Runs semantic retrieval and returns relevant clips with direct playback links

## Project structure

- `app.py`: Streamlit UI, indexing workflow, and retrieval workflow
- `transcribe_videos.py`: YouTube fetch + transcription + chunking pipeline
- `requirements.txt`: runtime dependencies
- `assets/screenshots/`: README screenshots
- `assets/demo/`: demo video file(s)
- `whisper_outputs/`: generated transcript chunk files

## Quick start

1. Clone and install dependencies.

```bash
git clone https://github.com/Rohan1924/Youtube-search-engine.git
cd Youtube-search-engine
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment variables.

```bash
cp .env.example .env
```

Set the values in `.env` (or export directly in your shell):

- `LANGFLOW_HOST`
- `LANGFLOW_UPLOAD_FLOW_ID`
- `LANGFLOW_QUERY_FLOW_ID`
- `LANGFLOW_API_KEY` (optional, if your LangFlow instance requires auth)
- `LANGFLOW_TIMEOUT` (optional, default `90`)

3. Run the app.

```bash
streamlit run app.py
```

## Configuration notes

- App startup requires `LANGFLOW_HOST`, `LANGFLOW_UPLOAD_FLOW_ID`, and `LANGFLOW_QUERY_FLOW_ID`.
- Authentication supports Bearer token, `x-api-key`, and `api_key` query fallback.
- Whisper output JSON files are written to `./whisper_outputs`.

## Usage

1. Open **Upload and Embed**.
2. Choose either a YouTube search query or a single video URL.
3. Run indexing to push transcript chunks into your vector pipeline.
4. Open **Search Clips** and ask natural-language queries.
5. Play the returned timestamped clips directly in the UI.

## Security

Do not commit real API keys. Use environment variables or local `.env` only.

## License

Add a license file if you plan to distribute or accept contributions.
