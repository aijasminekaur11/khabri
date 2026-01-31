#!/usr/bin/env python3
"""
Weekly Health Check Runner
Khabri - News Intelligence System

Checks if all configured news sources are accessible
Sends a health report via Telegram

Usage:
    python health_check_runner.py check
    python health_check_runner.py notify
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path

import aiohttp
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('HealthCheck')

# Temp files
HEALTH_REPORT_FILE = '/tmp/health_report.json'

# Config file path
CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'sources.yaml'


def load_sources():
    """Load sources from config file"""
    if not CONFIG_PATH.exists():
        logger.error(f"Config file not found: {CONFIG_PATH}")
        return []

    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)

    sources = []

    # News sources
    for source in config.get('news_sources', []):
        if source.get('enabled', True):
            sources.append({
                'name': source['name'],
                'url': source['url'],
                'type': 'news'
            })

    # RSS feeds
    for source in config.get('rss_feeds', []):
        if source.get('enabled', True):
            sources.append({
                'name': source['name'],
                'url': source['url'],
                'type': 'rss'
            })

    # Competitors
    for source in config.get('competitors', []):
        if source.get('enabled', True):
            sources.append({
                'name': source['name'],
                'url': source['url'],
                'type': 'competitor'
            })

    return sources


async def check_source(session, source):
    """Check if a source is accessible"""
    try:
        async with session.get(
            source['url'],
            timeout=aiohttp.ClientTimeout(total=15),
            allow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; KhabriBot/1.0)'}
        ) as response:
            if response.status == 200:
                return {
                    'name': source['name'],
                    'url': source['url'],
                    'type': source['type'],
                    'status': 'healthy',
                    'http_status': response.status,
                    'error': None
                }
            else:
                return {
                    'name': source['name'],
                    'url': source['url'],
                    'type': source['type'],
                    'status': 'unhealthy',
                    'http_status': response.status,
                    'error': f'HTTP {response.status}'
                }
    except asyncio.TimeoutError:
        return {
            'name': source['name'],
            'url': source['url'],
            'type': source['type'],
            'status': 'timeout',
            'http_status': None,
            'error': 'Connection timeout (15s)'
        }
    except Exception as e:
        return {
            'name': source['name'],
            'url': source['url'],
            'type': source['type'],
            'status': 'error',
            'http_status': None,
            'error': str(e)[:100]
        }


async def run_health_check():
    """Run health check on all sources"""
    logger.info("🩺 Running health check...")

    sources = load_sources()
    logger.info(f"Checking {len(sources)} sources...")

    results = []

    async with aiohttp.ClientSession() as session:
        tasks = [check_source(session, source) for source in sources]
        results = await asyncio.gather(*tasks)

    # Categorize results
    healthy = [r for r in results if r['status'] == 'healthy']
    unhealthy = [r for r in results if r['status'] in ('unhealthy', 'timeout', 'error')]

    report = {
        'timestamp': datetime.now().isoformat(),
        'total': len(results),
        'healthy_count': len(healthy),
        'unhealthy_count': len(unhealthy),
        'healthy': healthy,
        'unhealthy': unhealthy,
        'all_results': results
    }

    logger.info(f"Results: {len(healthy)}/{len(results)} healthy")

    # Save report
    with open(HEALTH_REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)

    return report


async def send_health_report():
    """Send health report via Telegram"""
    logger.info("Sending health report...")

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        logger.error("Telegram credentials not set!")
        sys.exit(1)

    if not os.path.exists(HEALTH_REPORT_FILE):
        logger.error("No health report found. Run 'check' first.")
        sys.exit(1)

    with open(HEALTH_REPORT_FILE, 'r') as f:
        report = json.load(f)

    # Format message
    message = format_health_report(report)

    # Send via Telegram
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    async with aiohttp.ClientSession() as session:
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                logger.info("Health report sent!")
            else:
                error = await response.text()
                logger.error(f"Telegram send failed: {error}")
                sys.exit(1)


def format_health_report(report):
    """Format health report message"""
    now = datetime.now()
    date_str = now.strftime('%A, %b %d, %Y')

    healthy_count = report['healthy_count']
    total = report['total']
    unhealthy = report['unhealthy']

    lines = [
        "🩺 <b>WEEKLY HEALTH REPORT</b>",
        f"📅 {date_str}",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        ""
    ]

    # Overall status
    if len(unhealthy) == 0:
        lines.append(f"✅ <b>ALL HEALTHY:</b> {healthy_count}/{total} sources")
        lines.append("")
        lines.append("All news sources are responding normally.")
    else:
        lines.append(f"✅ HEALTHY: {healthy_count}/{total}")
        lines.append(f"🔴 ISSUES: {len(unhealthy)}/{total}")
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        lines.append("🔴 <b>PROBLEM SOURCES:</b>")
        lines.append("")

        for item in unhealthy:
            status_emoji = "❌" if item['status'] == 'error' else "⚠️"
            lines.append(f"{status_emoji} <b>{item['name']}</b>")
            lines.append(f"   Type: {item['type']}")
            lines.append(f"   Error: {item['error']}")
            lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    # By category
    healthy_list = report['healthy']
    news_healthy = len([h for h in healthy_list if h['type'] == 'news'])
    rss_healthy = len([h for h in healthy_list if h['type'] == 'rss'])
    competitor_healthy = len([h for h in healthy_list if h['type'] == 'competitor'])

    lines.append("📊 <b>BY CATEGORY:</b>")
    lines.append(f"   📰 News sites: {news_healthy} healthy")
    lines.append(f"   📡 RSS feeds: {rss_healthy} healthy")
    lines.append(f"   🏢 Competitors: {competitor_healthy} healthy")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"⏰ <i>Next check: Next Monday 7:30 AM IST</i>")
    lines.append("🤖 <i>Powered by Khabri</i>")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python health_check_runner.py [check|notify]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'check':
        asyncio.run(run_health_check())
    elif command == 'notify':
        asyncio.run(send_health_report())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
