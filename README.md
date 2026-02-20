# YouTube RAG Search Engine

Semantic search over YouTube video transcripts with a Streamlit UI. The app fetches or transcribes audio, chunks text with timestamps, embeds it via LangFlow, and returns time-accurate clips.

## Highlights
- Search YouTube or paste a direct video link
- Automatic transcription with Whisper (WhisperX optional)
- Timestamped chunks stored in AstraDB via LangFlow
- Semantic search with clickable, time-based results

## How It Works
1. Find videos (search or direct link)
2. Download audio and transcribe (Whisper, fallback to captions)
3. Chunk transcripts with timestamps
4. Upload embeddings to AstraDB through LangFlow
5. Query and display matching clips in Streamlit

## Tech Stack
- Streamlit for the UI
- Whisper / WhisperX for transcription
- yt-dlp for audio download
- LangFlow HTTP API for embeddings and retrieval
- AstraDB as the vector store

## Quickstart
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure LangFlow/AstraDB settings in `app.py`:
   - `HOST`
   - `UPLOAD_FLOW_ID`
   - `QUERY_FLOW_ID`
   - `API_KEY`
3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Configuration
Update the constants in `app.py` to match your LangFlow deployment.

| Setting | Description |
| --- | --- |
| `HOST` | LangFlow host (e.g., ngrok URL) |
| `UPLOAD_FLOW_ID` | Flow used to embed and store chunks |
| `QUERY_FLOW_ID` | Flow used to query stored chunks |
| `API_KEY` | Auth key for LangFlow (if enabled) |
| `CHUNK_SIZE` | Max characters per chunk |

## Project Structure
- `app.py` Streamlit UI and LangFlow integration
- `transcribe_videos.py` YouTube download, transcription, and chunking
- `requirements.txt` Python dependencies

## Notes
- `ffmpeg` is required by `yt-dlp` for audio extraction.
- WhisperX is optional and used when installed.
- Do not commit real API keys to public repositories.

## License
No license specified.
