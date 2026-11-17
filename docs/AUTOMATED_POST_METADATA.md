# Automated platform descriptions and hashtags

Every production package generates separate metadata for each destination from the approved script.

- **YouTube:** a searchable description, up to three focused hashtags, and a keyword tag list.
- **TikTok:** a shorter, platform-native caption and up to five focused hashtags.
- Both descriptions include the project's mandatory educational disclaimer.
- Hashtags are topic/category-derived, deduplicated and not represented as trending or guaranteed to improve reach.
- The metadata is saved as JSON plus copy-ready platform text files and is attached to the production manifest.
- Generated metadata remains subject to editorial review. A post cannot be treated as publication-ready merely because metadata generation passed.
- Long-form videos generate YouTube metadata only; short videos generate both YouTube Shorts and TikTok metadata.

The generator is deterministic and zero-cost. It does not scrape trends, use paid APIs, or promise engagement outcomes. Platform-specific limits and publishing requirements must be rechecked against current platform documentation before enabling upload automation.
