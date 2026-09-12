# GitHub to Wix Integration

Use this when the design-system assets are published through GitHub Pages and embedded in Wix by URL.

## Publish

1. Push this repository to GitHub.
2. In GitHub, open Settings > Pages.
3. Set the source to the main branch and root folder.
4. After Pages publishes, your base URL will look like:

```text
https://YOUR-USER.github.io/melodia-design-system/
```

## Wix Embed Pattern

In Wix, add an HTML iframe and set the website address to a hosted component URL:

```text
https://YOUR-USER.github.io/melodia-design-system/wix/melodia-hero-embed.html?theme=dark&title=Melodia
```

Use query parameters to customize each instance. This keeps Wix connected directly to GitHub so fixes and design-system updates flow through one source.

## Component URLs

- `wix/melodia-hero-embed.html`
- `wix/melodia-passport-embed.html`
- `wix/badge-data-status.html`
- `wix/placeholder-data-missing.html`
- `wix/info-graph-metadata.html`
- `wix/tag-pcg-feature.html`
- `wix/layout-process-flow.html`
- `wix/chart-bar.html`
- `wix/card-performance.html`

Open `wix/index.html` after publishing for a small component catalog with example query strings.

## Review Notes

- The Melodia hero now has actual parallax layers, drifting constellations, twinkling stars, and `prefers-reduced-motion` support.
- Supporting embeds now support URL customization for repeated Wix use.
- Dynamic text is escaped before render so query-string content cannot inject HTML.
- Files remain self-contained, with Google Fonts loaded inside each embed for Wix portability.
