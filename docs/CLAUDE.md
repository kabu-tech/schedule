# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a schedule aggregation system project in early planning stage. The project aims to collect and aggregate schedule information from multiple sources.

## Current Project State

- **Stage**: Documentation/Planning phase
- **Implementation**: No source code exists yet
- **Location**: `/Users/norimatsudaisuke/schedule/`

## Planned Data Sources

According to `docs/02_sources.md`, the system will aggregate data from:

1. **Official Websites** (必須/Required)
2. **Official X (Twitter)** (必須/Required) - RSS/Nitter approach for public posts
3. **Google Search + Gemini Extraction** - Search public pages and extract date/title info with Gemini
4. **Weverse** - API or scraping under consideration
5. **YouTube Community Feed** - RSS or HTML parsing
6. **News Articles** - Media sources to be determined

## Development Guidelines

Since this project has no implementation yet, when starting development:

1. **Technology Stack Decision**: First determine the programming language and framework based on the data sources and scraping/API requirements
2. **Project Setup**: Create appropriate configuration files (package.json, requirements.txt, etc.) based on chosen stack
3. **Architecture**: Design system to handle multiple data sources with different access methods (RSS, API, web scraping)

## Important Considerations

- The project involves aggregating data from various social media and web sources
- Multiple access methods will be needed (RSS feeds, APIs, web scraping)
- Japanese language support is required based on documentation

## Japanese Language Support (日本語対応)

**Status**: ✅ Fully Configured

### Configuration Files Created:
- `.vscode/settings.json` - VS Code Japanese encoding settings
- `src/config.py` - Japanese messages and prompt templates
- `src/utils/japanese.py` - Japanese text processing utilities
- `docs/japanese-setup.md` - Complete Japanese setup guide
- `.env.example` - Environment variables with Japanese locale settings
- `requirements.txt` - Updated with Japanese processing libraries

### Features:
- Japanese input/output fully supported
- Japanese date/time extraction (e.g., "2024年1月15日", "18時30分")
- Event type detection in Japanese
- Japanese prompt templates for AI interactions
- Text normalization (full-width/half-width conversion)
- Japanese calendar descriptions

### Usage:
All interactions can be conducted in Japanese. The system automatically processes:
- Japanese date formats
- Japanese event types (コンサート、リリース、テレビ出演 etc.)
- Japanese artist and venue names
- Japanese user interfaces and messages

When developing, use Japanese for:
- Comments and documentation
- User-facing messages
- Log outputs
- API responses