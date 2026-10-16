#!/usr/bin/env python3
"""
Short-Form Video Detection Rules Synchronizer
Maintains an automated, validated dataset of Android Accessibility View IDs
and heuristic selectors for detecting short-form video players (YouTube Shorts, Instagram Reels).
"""

import json
import os
import sys
import time
import urllib.request

ENV_VAR_NAME = "UPSTREAM_CONFIG_URL"
RULES_FILE = "rules/rules.json"
TARGET_PACKAGES = {"com.instagram.android", "com.google.android.youtube"}

def fetch_upstream(upstream_url):
    req = urllib.request.Request(
        upstream_url,
        headers={"User-Agent": "ShortVideoRulesSync/1.0", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def load_local_rules():
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Notice: Could not parse existing local rules: {e}", file=sys.stderr)
    return None

def main():
    current_time_epoch = int(time.time() * 1000)
    local_data = load_local_rules()
    upstream_url = os.environ.get(ENV_VAR_NAME, "").strip()

    if not upstream_url:
        print(f"Notice: '{ENV_VAR_NAME}' environment variable is not set.", file=sys.stderr)
        print("Skipping upstream fetch. Existing local rules are preserved.", file=sys.stderr)
        if local_data is None:
            local_data = {
                "schema_version": 1,
                "last_checked_epoch": current_time_epoch,
                "last_updated_epoch": current_time_epoch,
                "stale_after_days": 30,
                "apps": []
            }
            os.makedirs(os.path.dirname(RULES_FILE), exist_ok=True)
            with open(RULES_FILE, "w", encoding="utf-8") as f:
                json.dump(local_data, f, indent=2)
        sys.exit(0)
    
    try:
        upstream = fetch_upstream(upstream_url)
    except Exception as e:
        print(f"Warning: Failed to fetch upstream ({e}). Preserving local rules.", file=sys.stderr)
        sys.exit(0)

    transformed_apps = []
    for app in upstream.get("in_app_usage_parsers", []):
        pkg = app.get("app_id")
        if pkg not in TARGET_PACKAGES:
            continue
            
        for parser in app.get("parsers", []):
            name = parser.get("name")
            if name not in ("reels", "shorts"):
                continue

            pos_view_ids = []
            pos_content_desc = []
            for r in parser.get("validation_rules", []):
                if r.get("type") == "view_id_match":
                    pos_view_ids.extend(r.get("values", []))
                elif r.get("type") == "content_description_match":
                    pos_content_desc.extend(r.get("values", []))

            neg_view_ids = []
            neg_texts = []
            for r in parser.get("negative_validation_rules", []):
                if r.get("type") == "view_id_match":
                    neg_view_ids.extend(r.get("values", []))
                elif r.get("type") == "text_match":
                    neg_texts.extend(r.get("values", []))

            transformed_apps.append({
                "package_name": pkg,
                "feature": name,
                "version": parser.get("version", 1),
                "positive_rules": {
                    "view_ids": sorted(list(set(pos_view_ids))),
                    "content_descriptions": sorted(list(set(pos_content_desc)))
                },
                "negative_rules": {
                    "view_ids": sorted(list(set(neg_view_ids))),
                    "texts": sorted(list(set(neg_texts)))
                }
            })

    # Curated baseline additions from open-source reverse-engineering analysis
    BASELINE_RULES = {
        "com.google.android.youtube": {
            "pos_view_ids": [
                "com.google.android.youtube:id/reel_player_page_container",
                "com.google.android.youtube:id/reel_progress_bar"
            ],
            "neg_view_ids": [],
            "neg_texts": []
        },
        "com.instagram.android": {
            "pos_view_ids": [
                "com.instagram.android:id/clips_viewer_camera_button"
            ],
            "neg_view_ids": [
                "com.instagram.android:id/layout_comment_thread_edittext",
                "com.instagram.android:id/row_comment_container"
            ],
            "neg_texts": []
        }
    }

    for app in transformed_apps:
        pkg = app["package_name"]
        if pkg in BASELINE_RULES:
            base = BASELINE_RULES[pkg]
            app["positive_rules"]["view_ids"] = sorted(list(set(app["positive_rules"]["view_ids"] + base["pos_view_ids"])))
            app["negative_rules"]["view_ids"] = sorted(list(set(app["negative_rules"]["view_ids"] + base["neg_view_ids"])))

    # Direct Message (DM) chat exemption configuration for Instagram
    for app in transformed_apps:
        if app["package_name"] == "com.instagram.android":
            app["dm_exemption"] = {
                "required_view_ids": [
                    "com.instagram.android:id/sender_username_or_fullname",
                    "com.instagram.android:id/reply_bar_edittext"
                ],
                "forbidden_view_ids": [
                    "com.instagram.android:id/suggested_title"
                ]
            }

    # Evaluate diff against existing local records
    is_changed = True
    last_updated_epoch = current_time_epoch
    if local_data and "apps" in local_data:
        if json.dumps(local_data["apps"], sort_keys=True) == json.dumps(transformed_apps, sort_keys=True):
            is_changed = False
            last_updated_epoch = local_data.get("last_updated_epoch", current_time_epoch)

    output_payload = {
        "schema_version": 1,
        "last_checked_epoch": current_time_epoch,
        "last_updated_epoch": last_updated_epoch,
        "stale_after_days": 30,
        "apps": transformed_apps
    }

    os.makedirs(os.path.dirname(RULES_FILE), exist_ok=True)
    with open(RULES_FILE, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    print(f"Sync complete. Changed: {is_changed}, Last Checked: {current_time_epoch}")

if __name__ == "__main__":
    main()
