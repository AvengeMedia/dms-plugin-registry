### Type of Change

- [ ] New plugin
- [ ] Update existing plugin
- [ ] Plugin removal
- [ ] New theme
- [ ] Update existing theme
- [ ] Misc / Maintenance (Nix, workflows, docs, etc.)

---

### New Plugin Checklist

<!-- If submitting a new plugin, complete this checklist. If updating an existing plugin/theme, removing a plugin, or submitting misc changes, please delete this section. -->

> [!IMPORTANT]
> Non-compliant submissions may be closed by maintainers without explanation.

- [ ] I have read and followed [CONTRIBUTING.md](../CONTRIBUTING.md).
- [ ] This plugin does not duplicate an existing plugin, OR it meets the [duplication guidelines](../CONTRIBUTING.md#guidelines) (unmaintained original / major improvements / upstream contacted first).
- [ ] The `id` in the JSON is in camelCase and exactly matches `plugin.json` in the plugin repository.
- [ ] I have validated locally (`python3 .github/generate.py --validate` and `python3 .github/validate_links.py`).
- [ ] I understand that non-compliant submissions may be rejected or closed without explanation.

---

### Plugin Removal Checklist

<!-- If submitting a plugin removal, complete this checklist. Otherwise, please delete this section. -->

- [ ] I have read and followed the [Plugin Removal Policy](../MODERATION.md#plugin-removal-policy).
- [ ] I have specified the removal tier (Tier 1/2/3/4) and justified it in the description below.
- [ ] If Tier 3, the required 60-day deprecation/adoption period has elapsed on the tracking issue.

---

### Description

<!-- Brief summary of changes. For new plugins, describe what it does. For successors/forks, link the unaddressed upstream issue/PR. For plugin removals, state the tier, reason, and link to the relevant issue. -->

