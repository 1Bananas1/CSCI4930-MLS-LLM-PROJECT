"""Scraper modules for FIFA data collection."""

from src.scrapers.player_scraper import (
    PlayerScraper,
    Player,
    Contract
)

__all__ = [
    'PlayerScraper',
    'Player',
    'Contract',
    'scrape_page'
]