from youtube_transcript_api import YouTubeTranscriptApi


def get_combined_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
        combined_text = " ".join(entry['text'] for entry in transcript)
        return combined_text
    except Exception as ex:
        print(f"[Error] Fetching YouTube transcript: {ex}")
        return ""
