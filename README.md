# financial-market-analyst

Automated financial market analysis via Gemini CLI, plus a Codex-based market brief workflow, delivered to Slack via GitHub Actions.

[![CI](https://github.com/dceoy/financial-market-analyst/actions/workflows/ci.yml/badge.svg)](https://github.com/dceoy/financial-market-analyst/actions/workflows/ci.yml)

## Overview

This repository wires Google Gemini CLI prompts and OpenAI Codex CLI skills into GitHub Actions workflows. It runs scheduled market analysis, formats results, and posts them to Slack.

## Key Features

- **Scheduled analysis**: Runs every 8 hours via `scheduler.yml`.
- **Manual runs**: Dispatch workflows with custom prompts.
- **Slack delivery**: Posts Gemini/Codex outputs to a configured Slack channel.
- **Structured market scope**: Indices, commodities, and macro/FX coverage baked into the prompt.
- **Codex market brief skill**: Short-horizon, JST-timestamped brief for equities, commodities, and macro/FX.

## How It Works

### Gemini CLI flow

- Prompt definition: `.gemini/commands/analyze_market.toml`
- Workflow: `.github/workflows/gemini-cli-to-slack.yml`
- Schedule and defaults: `.github/workflows/scheduler.yml`

The scheduler passes the `/analyze_market` command, asks for a Japanese translation, and writes the output to `./slack_message.txt` before posting to Slack.

### Codex CLI flow

- Skill definition: `.codex/skills/market-brief/SKILL.md`
- Codex configuration: `.codex/config.toml`
- Workflow: `.github/workflows/codex-cli-to-slack.yml`

The default prompt is `$market-brief`, which triggers the skill to produce a 24‑hour tactical brief with strict short-line formatting and JST timestamps.

## Required Secrets

### Gemini workflows

- `GEMINI_API_KEY`: Gemini API key
- `SLACK_API_TOKEN`: Slack bot token
- `SLACK_CHANNEL_ID`: Slack channel ID

### Codex workflows

- `CODEX_API_KEY`: OpenAI API key for Codex CLI
- `SLACK_API_TOKEN`: Slack bot token
- `SLACK_CHANNEL_ID`: Slack channel ID

## Usage

### Scheduled analysis

The scheduler runs every 8 hours:

- Cron: `0 */8 * * *`
- Workflow: “Scheduled jobs”

### Manual Gemini run

1. Go to Actions → “Scheduled jobs”.
2. Click “Run workflow”.
3. Optionally override the default prompt.

### Manual Codex run

1. Go to Actions → “Codex CLI with Slack notification”.
2. Click “Run workflow”.
3. Optionally override the prompt (default: `$market-brief`).

### Local CLI use

```bash
gemini /analyze_market
```

## Development

### Lint workflows

```bash
actionlint .github/workflows/*.yml
```

### Validate TOML

```bash
taplo fmt --check .gemini/commands/*.toml
```

## CI/CD

The CI workflow runs linting and release tasks from `.github/workflows/ci.yml`.
