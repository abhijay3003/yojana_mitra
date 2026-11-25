"""P8 Missed-Call IVR (Exotel/Twilio webhook handler) and Indic TTS interface."""

from __future__ import annotations

from typing import Any, Dict

from agents.graph import YojanaMitraAgentGraph

IVR_LANG_MENU = {
    "1": ("te", "తెలుగు ఎంచుకోబడింది. దయచేసి మీ ప్రశ్నను అడగండి."),
    "2": ("hi", "हिन्दी चुनी गई है। कृपया अपना प्रश्न पूछें।"),
    "3": ("en", "English selected. Please speak your welfare scheme question after the beep."),
    "4": ("kn", "ಕನ್ನಡ ಆಯ್ಕೆಯಾಗಿದೆ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ."),
    "5": ("ta", "தமிழ் தேர்ந்தெடுக்கப்பட்டது. உங்கள் கேள்வியைக் கேளுங்கள்."),
}


def handle_ivr_webhook(
    digit: str = "1",
    transcript: str = "",
    profile: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Process Exotel/Twilio missed-call IVR callback -> language menu -> voice Q -> voice answer."""
    lang, prompt = IVR_LANG_MENU.get(digit, IVR_LANG_MENU["3"])
    if not transcript.strip():
        return {
            "stage": "LANGUAGE_MENU",
            "lang": lang,
            "tts_prompt": prompt,
            "twiml": f"<Response><Say language='{lang}-IN'>{prompt}</Say><Record maxLength='20'/></Response>",
        }

    agent = YojanaMitraAgentGraph()
    res = agent.run(transcript, profile=profile)
    spoken = res.get("answer") or res.get("scam_analysis", {}).get("verdict", "")
    return {
        "stage": "VOICE_ANSWER",
        "lang": res["lang"],
        "spoken_response": spoken,
        "twiml": f"<Response><Say language='{res['lang']}-IN'>{spoken}</Say></Response>",
        "sms_summary": spoken[:280],
        "latency_ms": res["latency_ms"],
    }
