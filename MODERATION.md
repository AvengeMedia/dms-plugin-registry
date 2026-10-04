# Plugin Moderation & Removal Policy

Guidelines and procedures for registry maintainers and plugin moderators.

## Moderator Commands

Moderators manage plugin status by commenting commands on the plugin's tracking issue:

- `/broken`: Flag the plugin as non-functional or incompatible with current DMS.
- `/working`: Clear the broken flag after fixes are verified.
- `/unmaintained`: Flag the plugin as abandoned by its upstream author.
- `/deprecated`: Flag the plugin as deprecated or superseded.
- `/review`: Mark the plugin as verified by a moderator.
- `/unreview`: Remove the reviewed mark.
- `/similar #<issue>`: Link related plugins (use `/unsimilar #<issue>` to unlink).

Plugin authors may also use `/unmaintained` or `/deprecated` on their own tracking issues.

---

## Plugin Removal Policy

Purging a plugin removes its entry from the registry, breaking existing installations. Deprecation is always preferred over deletion.

### Core Principles

- **Deprecation First**: Flag tracking issues with `/deprecated` or `/unmaintained` instead of deleting the registry entry.
- **Grace Period**: Non-emergency removals require a cooldown period (14–60 days) to allow user migration and community adoption.
- **Adoption First**: If an unmaintained plugin remains useful, priority is given to updating the repository pointer to an active community fork instead of purging.

### Purge Tiers

| Tier | Reason | Criteria | Grace Period | Action |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Emergency** | Malware, security exploits, unauthorized exfiltration, or legal/DMCA takedowns | **None** | Immediate deletion by maintainers |
| **2** | **Dead Upstream** | Repo deleted or returns 404/410/451 across 3 consecutive automated check runs | **14 days** | Automated removal PR merged if unaddressed |
| **3** | **Obsolete / Broken** | Flagged `/broken` or `/unmaintained` > 6 months with no upstream activity, or superseded by built-in DMS features | **60 days** | Purge only after adoption period expires |
| **4** | **Author Request** | Verified request from original author | **14–30 days** | Advance notice before removal; community may fork and retain entry |

### Process for Obsolete Plugins (Tier 3)

1. **Deprecate (Day 0)**: Flag tracking issue with `/deprecated` or `/unmaintained`.
2. **Adoption Window (Days 0–60)**: Label issue `help wanted` or `adoption-needed`. Community members may adopt by submitting a PR updating `repo` to an active fork.
3. **Purge (Day 60+)**: If unadopted, run the purge tool to remove the plugin files and update registry data:
   ```bash
   python3 script/purge_plugin.py <plugin_id>
   ```

### Restoration Policy

A purged plugin may be restored at any time via PR if an active, compatible repository is provided and verified.
