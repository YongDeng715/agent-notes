import os
import sys
from x_config.twitter_api import init_twitter, post_tweet

def x_post_tool(text: str) -> str:
    """Tool to post a tweet using Twitter API. Returns tweet ID or error message."""
    api = init_twitter()
    if not api:
        return "[Error] Failed to initialize Twitter API."
    tweet_id = post_tweet(api, text)
    return tweet_id or "[Error] Failed to post tweet."

def mock_draw_tool(description: str, params: dict) -> str:
    """Mock image generation tool. Returns a fake image URL based on description."""
    import hashlib
    hash_str = hashlib.md5(description.encode('utf-8')).hexdigest()[:8]
    return f"http://fakeimg.com/{hash_str}.png"
