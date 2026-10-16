# Short-Form Video Detection Rules

An automated, open dataset of Android View IDs, Accessibility selectors, and heuristic rules for detecting short-form video players (YouTube Shorts, Instagram Reels).

This repository is maintained autonomously to track changes across host app updates and layout refactors, providing reliable selectors for digital wellbeing, screen time, and focus apps.

---

## 🎯 Purpose

Modern social media platforms frequently update their layout hierarchies, rotate obfuscated resource IDs, and alter container structures. 

This dataset provides:
1. **Positive Selectors:** Reliable view IDs and content descriptions associated with short-form video players.
2. **Negative Exclusions:** Safeguards that prevent false positives when users are viewing comments, live streams, or regular feed content.
3. **Direct Message (DM) Exemptions:** Structural rules distinguishing algorithmic reels from videos shared privately between friends in chat.
4. **Audit Metadata:** Timestamps (`last_checked_epoch` and `last_updated_epoch`) to allow client applications to evaluate freshness and enforce safe offline fallbacks.

---

## 📦 Dataset Endpoint

The dataset is published as standard JSON and can be fetched directly via GitHub Raw:

```
https://raw.githubusercontent.com/<owner>/<repo>/main/rules/rules.json
```

---

## 📋 Schema Specification

```json
{
  "schema_version": 1,
  "last_checked_epoch": 1729092286008,
  "last_updated_epoch": 1729092286008,
  "stale_after_days": 30,
  "apps": [
    {
      "package_name": "com.google.android.youtube",
      "feature": "shorts",
      "version": 1,
      "positive_rules": {
        "view_ids": [
          "com.google.android.youtube:id/reel_player_page_container",
          "com.google.android.youtube:id/reel_progress_bar",
          "com.google.android.youtube:id/reel_recycler"
        ],
        "content_descriptions": []
      },
      "negative_rules": {
        "view_ids": [
          "com.google.android.youtube:id/immersive_live_player",
          "com.google.android.youtube:id/live_chat_content",
          "com.google.android.youtube:id/live_chat_text_field_bar"
        ],
        "texts": [
          "Live chat",
          "Video player"
        ]
      }
    },
    {
      "package_name": "com.instagram.android",
      "feature": "reels",
      "version": 1,
      "positive_rules": {
        "view_ids": [
          "com.instagram.android:id/clips_video_container",
          "com.instagram.android:id/clips_viewer_camera_button",
          "com.instagram.android:id/clips_viewer_view_pager",
          "com.instagram.android:id/reels_touchable_background"
        ],
        "content_descriptions": []
      },
      "negative_rules": {
        "view_ids": [
          "com.instagram.android:id/layout_comment_thread_edittext",
          "com.instagram.android:id/row_comment_container"
        ],
        "texts": []
      },
      "dm_exemption": {
        "required_view_ids": [
          "com.instagram.android:id/sender_username_or_fullname",
          "com.instagram.android:id/reply_bar_edittext"
        ],
        "forbidden_view_ids": [
          "com.instagram.android:id/suggested_title"
        ]
      }
    }
  ]
}
```

### Field Definitions

| Field | Type | Description |
|---|---|---|
| `schema_version` | Integer | Version number of the dataset schema. |
| `last_checked_epoch` | Long (ms) | Timestamp when the upstream sources were last checked by CI. |
| `last_updated_epoch` | Long (ms) | Timestamp when an actual change was detected and written to the rules. |
| `stale_after_days` | Integer | Recommended threshold after which clients should failover to native heuristics. |
| `positive_rules.view_ids` | Array[String] | Resource IDs confirming active short-form video playback. |
| `negative_rules.view_ids` | Array[String] | Resource IDs that immediately disqualify a match (e.g. comment drawers, live chats). |
| `negative_rules.texts` | Array[String] | Visible UI strings that disqualify a match. |
| `dm_exemption` | Object | Rules to exempt privately sent videos inside direct message threads. |

---

## 🤖 Automated Updates

A GitHub Actions workflow runs daily at `04:00 UTC`:
- Polls public accessibility parser updates.
- Validates changes against baseline resilient selectors and edge-case exemption filters.
- Re-indexes `last_checked_epoch` and records updates only when definitions change.

---

## 📄 License

This dataset is released under the [MIT License](LICENSE) / Public Domain.

---

## ⚙️ CI/CD Setup

To enable automated daily synchronization in GitHub Actions:
1. Navigate to **Settings > Secrets and variables > Actions** in this repository.
2. Under **Repository secrets**, click **New repository secret**.
3. Name: `UPSTREAM_CONFIG_URL`
4. Secret: *(URL of the upstream accessibility config to track and sanitize)*
