"""Step 4: send a push notification to your phone and PC via ntfy.sh."""

import os
import urllib.request


def send_notification(title: str, message: str, click_url: str) -> None:
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not topic:
        raise SystemExit(
            "NTFY_TOPIC is not set. Add it under Settings > Secrets and variables > "
            "Actions > Secrets (the name must be exactly NTFY_TOPIC)."
        )
    if not click_url:
        print("  ! SITE_URL variable not set: the notification won't open the digest")
    print(f"  sending to ntfy topic '{topic[:4]}...' ")

    request = urllib.request.Request(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        method="POST",
        headers={
            # HTTP headers must be plain ASCII
            "Title": title.encode("ascii", "ignore").decode(),
            "Click": click_url,
            "Tags": "coffee,newspaper",
            "Priority": "default",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        print(f"  notification sent ({response.status})")
