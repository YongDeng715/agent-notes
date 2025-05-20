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
