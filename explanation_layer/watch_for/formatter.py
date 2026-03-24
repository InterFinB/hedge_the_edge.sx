def format_watch_for_items(items, max_items=3):

    if not items:
        return []

    # sort by priority first
    items = sorted(
        items,
        key=lambda x: x.get("priority", 0),
        reverse=True,
    )

    grouped = {}

    for item in items:

        asset = item.get("asset")
        message = item.get("message")

        if not message:
            continue

        key = asset if asset else message

        if key not in grouped:
            grouped[key] = {
                "asset": asset,
                "messages": [],
                "priority": item.get("priority", 0),
            }

        grouped[key]["messages"].append(message)

    merged = []

    for g in grouped.values():

        asset = g["asset"]
        messages = g["messages"]

        if asset:

            # remove "Watch X:" prefix duplicates
            cleaned = []

            for m in messages:

                if m.startswith(f"Watch {asset}:"):
                    m = m[len(f"Watch {asset}:") :].strip()

                cleaned.append(m)

            text = f"Watch {asset}: " + " ".join(cleaned)

        else:

            text = " ".join(messages)

        merged.append(
            (
                g["priority"],
                text,
            )
        )

    # sort again by priority
    merged = sorted(
        merged,
        key=lambda x: x[0],
        reverse=True,
    )

    bullets = [m[1] for m in merged[:max_items]]

    return bullets