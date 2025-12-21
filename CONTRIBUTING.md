# Contributing

## Table of Contents

- [Contributing a Plugin](#contributing-a-plugin)
- [Contributing a Theme](#contributing-a-theme)

---

# Contributing a Plugin

Thank you for contributing to the Dank Material Shell Plugins registry!

## How to Add Your Plugin

1. **Fork this repository**

2. **Create a new JSON file** in the `plugins/` directory following this naming convention:
   ```
   plugins/{github-username}-{plugin-name}.json
   ```
   - Use lowercase letters
   - Separate words with hyphens
   - Examples: `daniel-42-z-powerusage.json`, `rochacbruno-worldclock.json`

3. **Fill in your plugin information** using the schema below:

```json
{
    "id": "pluginId",
    "name": "PluginName",
    "capabilities": ["dankbar-widget"],
    "category": "monitoring",
    "repo": "https://github.com/yourusername/your-plugin-repo",
    "path": "optional/path/in/monorepo",
    "author": "Your Name",
    "description": "Brief description of what your plugin does",
    "dependencies": ["dependency1", "dependency2"],
    "compositors": ["niri", "hyprland"],
    "distro": ["any"],
    "screenshot": "https://url/to/screenshot.png"
}
```

### Field Descriptions

- **id** (required): Unique identifier in camelCase format (e.g., `worldClock`, `powerUsageMonitor`)
  - **Must start with a lowercase letter**
  - **Can only contain letters and digits** (no underscores, hyphens, or spaces)
  - **Must exactly match the `id` field in your repository's `plugin.json` file**
- **name** (required): Display name of your plugin (e.g., `World Clock`, `Power Usage Monitor`)
  - **Must exactly match the `name` field in your repository's `plugin.json` file**
- **capabilities** (required): Array of capabilities, e.g., `["dankbar-widget"]`
- **category** (required): One of: `monitoring`, `utilities`, `appearance`, `system`, etc.
- **repo** (required): Full GitHub URL to your plugin repository
- **path** (optional): If your plugin is in a monorepo, specify the subdirectory path
- **author** (required): Your name or GitHub username
- **description** (required): Clear, concise description of the plugin's purpose
- **dependencies** (required): Array of dependencies, use `[]` if none
- **compositors** (required): Supported Wayland compositors: `["niri", "hyprland"]`, etc.
- **distro** (required): Supported distributions: `["any"]`, `["fedora"]`, `["arch"]`, etc.
- **screenshot** (optional): Direct URL to a screenshot image

4. **Validate your plugin locally** before submitting:

   Run the following validation commands to ensure your plugin meets all requirements:

   ```bash
   # Install dependencies
   pip install jinja2 requests

   # Validate JSON schema and required fields
   python3 .github/generate.py --validate

   # Validate links, paths, IDs, and names
   python3 .github/validate_links.py
   ```

   These validations check:
   - Valid JSON syntax (no trailing commas)
   - All required fields are present
   - Arrays use proper formatting
   - URLs are complete and accessible
   - Screenshot URLs are reachable
   - Repository URLs are valid
   - Plugin paths exist (for monorepo plugins)
   - **`id` field is in camelCase format and matches your repository's `plugin.json`**
   - **`name` field matches your repository's `plugin.json`**

5. **Submit a Pull Request**
   - Commit your JSON file
   - Push to your fork
   - Create a PR to this repository
   - Include a brief description of your plugin in the PR

## Guidelines

- Keep descriptions concise and informative
- Ensure your repository has proper documentation
- Test that your plugin works with the specified compositors and distros
- Include a screenshot when possible to showcase your plugin
- **IMPORTANT**: The `id` and `name` fields in your registry JSON file **must exactly match** the corresponding fields in your plugin repository's `plugin.json` file
  - For regular plugins: Must match `{repo}/plugin.json`
  - For monorepo plugins: Must match `{repo}/{path}/plugin.json`
- **IMPORTANT**: The `id` field must be in camelCase format (starts with lowercase, only letters/digits)

## Questions?

If you have questions about the contribution process, please open an issue in this repository.

---

# Contributing a Theme

Thank you for contributing a theme to the Dank Material Shell registry!

## How to Add Your Theme

1. **Fork this repository**

2. **Create a new folder** in the `themes/` directory:
   ```
   themes/{theme-name}/theme.json
   ```
   - Use lowercase letters and hyphens
   - Examples: `tokyonight`, `gruvbox-dark`, `catppuccin-mocha`

3. **Create your theme.json** with the following schema:

```json
{
  "id": "themeId",
  "name": "Theme Name",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "Brief description of your theme",
  "dark": {
    "primary": "#hex",
    "primaryText": "#hex",
    "primaryContainer": "#hex",
    "secondary": "#hex",
    "surface": "#hex",
    "surfaceText": "#hex",
    "surfaceVariant": "#hex",
    "surfaceVariantText": "#hex",
    "surfaceTint": "#hex",
    "background": "#hex",
    "backgroundText": "#hex",
    "outline": "#hex",
    "surfaceContainer": "#hex",
    "surfaceContainerHigh": "#hex",
    "error": "#hex",
    "warning": "#hex",
    "info": "#hex"
  },
  "light": {
    "primary": "#hex",
    "primaryText": "#hex",
    "primaryContainer": "#hex",
    "secondary": "#hex",
    "surface": "#hex",
    "surfaceText": "#hex",
    "surfaceVariant": "#hex",
    "surfaceVariantText": "#hex",
    "surfaceTint": "#hex",
    "background": "#hex",
    "backgroundText": "#hex",
    "outline": "#hex",
    "surfaceContainer": "#hex",
    "surfaceContainerHigh": "#hex",
    "error": "#hex",
    "warning": "#hex",
    "info": "#hex"
  }
}
```

### Field Descriptions

**Metadata:**
- **id** (required): Unique identifier in camelCase (e.g., `tokyoNight`, `gruvboxDark`)
- **name** (required): Display name of your theme
- **version** (required): Semver version (e.g., `1.0.0`)
- **author** (required): Your name or username
- **description** (required): Brief description of the theme

**Color Fields (required for both dark and light):**
- **primary**: Primary accent color
- **primaryText**: Text color on primary backgrounds
- **primaryContainer**: Container using primary color
- **secondary**: Secondary accent color
- **surface**: Main surface/card background
- **surfaceText**: Text on surfaces
- **surfaceVariant**: Alternative surface color
- **surfaceVariantText**: Text on variant surfaces
- **surfaceTint**: Tint overlay color
- **background**: App background color
- **backgroundText**: Text on background
- **outline**: Border/divider color
- **surfaceContainer**: Container background
- **surfaceContainerHigh**: Elevated container background
- **error**: Error state color
- **warning**: Warning state color
- **info**: Info state color

4. **Validate your theme locally**:

   ```bash
   pip install jinja2
   python3 .github/validate_themes.py
   python3 .github/generate.py --validate
   ```

5. **Submit a Pull Request**
   - Commit only your `theme.json` file (previews are auto-generated)
   - Push to your fork and create a PR
   - A preview will be generated and posted as a comment on your PR
   - After merge, the preview SVG will be committed automatically

## Guidelines

- All color values must be 6-digit hex codes (e.g., `#7aa2f7`)
- Both `dark` and `light` variants are required
- The `id` must be camelCase (starts lowercase, alphanumeric only)
- Version must follow semver format (`X.Y.Z`)
- Keep descriptions concise
- Test your colors for readability and contrast
