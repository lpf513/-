from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AudioCue:
    key: str
    source_url: str
    license: str


FREE_AUDIO_CUES = {
    "merge": AudioCue("merge", "https://freesound.org/people/LloydEvans09/sounds/185748/", "CC BY 4.0"),
    "chain": AudioCue("chain", "https://freesound.org/people/Benboncan/sounds/60084/", "CC BY 4.0"),
    "win": AudioCue("win", "https://freesound.org/people/unadamlar/sounds/474179/", "CC0/CC BY (check page)"),
    "fail": AudioCue("fail", "https://freesound.org/people/SamsterBirdies/sounds/554114/", "CC BY 4.0"),
    "button": AudioCue("button", "https://freesound.org/people/InspectorJ/sounds/403018/", "CC BY 4.0"),
}


class AudioManager:
    """Minimal audio manager.

    In this repo we keep URL-based cue mapping for free/public assets.
    Runtime playback can be wired to pygame/simpleaudio in app shell.
    """

    def __init__(self) -> None:
        self.play_log: list[str] = []

    def play(self, cue: str) -> None:
        if cue not in FREE_AUDIO_CUES:
            return
        self.play_log.append(cue)
