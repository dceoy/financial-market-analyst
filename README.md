# financial-market-analyst

Financial Market Analysis using LLMs

[![CI](https://github.com/dceoy/financial-market-analyst/actions/workflows/ci.yml/badge.svg)](https://github.com/dceoy/financial-market-analyst/actions/workflows/ci.yml)

## Overview

Automated market analysis system that uses Google Gemini to analyze economic news and send insights to Slack.

## Features

- **Automated Analysis**: Runs every 8 hours via GitHub Actions
- **Market Coverage**: Tracks indices (S&P 500, NASDAQ, Nikkei), commodities (oil, gold), and FX/macro indicators
- **Slack Integration**: Sends analysis directly to your Slack channel
- **Translation**: Supports multi-language output (default: Japanese)

## Setup

1. Configure GitHub Secrets:
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `SLACK_API_TOKEN`: Slack bot token
   - `SLACK_CHANNEL_ID`: Target Slack channel

2. Enable GitHub Actions in your repository

## Usage

### Automatic Analysis

The workflow runs automatically every 8 hours.

### Manual Trigger

1. Go to Actions → "Scheduled jobs"
2. Click "Run workflow"
3. Optionally provide a custom prompt

### Command Line

```bash
gemini /analyze_market
```
