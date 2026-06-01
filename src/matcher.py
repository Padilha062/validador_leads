from thefuzz import fuzz


def _normalize(text: str) -> str:
    return " ".join(str(text).lower().split())


def calculate_match_score(lead_name: str, profile: dict) -> float:
    profile_name = str(profile.get("name", "")).strip()

    text_score = 0.0
    if profile_name:
        ratio = fuzz.partial_ratio(_normalize(lead_name), _normalize(profile_name))
        text_score = (ratio / 100.0) * 6.0

    picture_url = str(profile.get("profilePictureUrl", "")).strip()
    bonus_picture = 2.0 if picture_url.startswith(("http://", "https://")) else 0.0

    status = str(profile.get("status", "")).strip()
    bonus_status = 2.0 if status else 0.0

    return round(min(text_score + bonus_picture + bonus_status, 10.0), 2)
