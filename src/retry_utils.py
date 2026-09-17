import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Rate limit tracking
_last_api_call_time = None
_rate_limit_until = None
_min_request_interval = 0.5  # seconds between requests


def invoke_with_retry(llm, messages, max_retries=1):
    """
    Retry failed LLM calls with smart rate limit handling.

    Features:
    - Detects rate limits early
    - Implements request spacing (min 0.5s between calls)
    - Fails fast on rate limits (no endless retries)
    - Provides user-friendly error messages
    """
    global _last_api_call_time, _rate_limit_until

    last_error = None

    # Check if we're in cooldown period
    if _rate_limit_until and datetime.now() < _rate_limit_until:
        wait_time = (_rate_limit_until - datetime.now()).total_seconds()
        raise Exception(
            f"API Rate Limit Active\n\n"
            f"Please wait {wait_time:.0f} seconds before trying again.\n\n"
            f"💡 **Tip:** The API has strict rate limits. "
            f"Space out your questions by waiting a few seconds between requests."
        )

    for attempt in range(1, max_retries + 1):
        try:
            # Space out requests
            if _last_api_call_time:
                elapsed = time.time() - _last_api_call_time
                if elapsed < _min_request_interval:
                    wait = _min_request_interval - elapsed
                    time.sleep(wait)

            _last_api_call_time = time.time()
            return llm.invoke(messages)

        except Exception as e:
            last_error = e
            error_str = str(e).lower()

            # Detect rate limit
            if any(word in error_str for word in ["rate", "quota", "429", "too many", "limit", "exceeded"]):
                logger.warning(f"Rate limit detected: {str(e)[:100]}")

                # Set cooldown period (wait at least 30 seconds before next attempt)
                _rate_limit_until = datetime.now() + timedelta(seconds=30)

                raise Exception(
                    "🚫 **API Rate Limit Exceeded**\n\n"
                    "The Google Gemini API rate limit has been reached.\n\n"
                    "**What to do:**\n"
                    "1. ⏳ Wait 30+ seconds before asking another question\n"
                    "2. 📊 Use simpler questions (they're faster)\n"
                    "3. 💾 Ask about cached results (shows ✅ Cached)\n"
                    "4. 🔑 Check API quota at console.cloud.google.com\n\n"
                    "**If it keeps happening:**\n"
                    "- Your API plan may be too basic\n"
                    "- Upgrade to a paid plan\n"
                    "- Or wait for daily quota reset (24 hours)"
                ) from e

            # For other errors, optionally retry once
            if attempt < max_retries:
                logger.warning(f"Attempt {attempt} failed: {str(e)[:100]}. Retrying...")
                time.sleep(1)  # Wait 1 second before retry
                continue
            else:
                raise

    if last_error:
        raise last_error