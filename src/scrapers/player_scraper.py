from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
from bs4 import BeautifulSoup, Tag
from bs4.element import ResultSet
import time
from ratelimit import limits, sleep_and_retry
from config.leagues import leagues

logger = logging.getLogger(__name__)

@dataclass
class Contract:
    """Represents a player's contract information."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    @classmethod
    def from_text(cls, text: str) -> 'Contract':
        if not text:
            return cls()
        
        text = text.strip()
        if '~' in text:
            start, end = text.split('~')
            return cls(start.strip(), end.strip())
        return cls(end_date=text.strip())

class Player:
    """Represents a football player's data."""
    def __init__(self, name: str, positions: List[str], league_name: str, 
                 league_country: str, contract: Contract, attributes: Dict[str, str]):
        self.name = name
        self.positions = positions
        self.league_name = league_name
        self.league_country = league_country
        self.contract = contract
        self.attributes = attributes

    def to_dict(self) -> Dict[str, Any]:
        return {
            'Player': self.name,
            'Position': ', '.join(self.positions),
            'League': f"{self.league_name} ({self.league_country})",
            'Contract Start': self.contract.start_date,
            'Contract End': self.contract.end_date,
            **self.attributes
        }

class PlayerScraper:
    def __init__(self, soup: BeautifulSoup, league_id: int):
        self.soup = soup
        self.league_id = league_id
        self.players: List[Dict] = []

    def _get_player_name(self, row: Tag) -> Optional[str]:
        try:
            player_link = row.find('a', href=lambda href: href and "player" in href)
            if player_link:
                return player_link.get('data-tippy-content')
            return None
        except Exception as e:
            logger.warning(f"Error extracting player name: {e}")
            return None

    def _get_positions(self, row: Tag) -> List[str]:
        try:
            position_elements = row.find_all('span', class_='pos')
            return [pos.text.strip() for pos in position_elements if pos.text.strip()]
        except Exception as e:
            logger.warning(f"Error extracting positions: {e}")
            return []

    def _get_contract(self, row: Tag) -> Contract:
        try:
            contract_cell = row.find('div', class_='sub')
            if contract_cell:
                return Contract.from_text(contract_cell.text)
            return Contract()
        except Exception as e:
            logger.warning(f"Error extracting contract: {e}")
            return Contract()

    def _get_attributes(self, row: Tag) -> Dict[str, str]:
        attributes = {}
        try:
            for td in row.find_all('td'):
                data_col = td.get('data-col')
                if data_col:
                    attributes[data_col] = td.text.strip()
        except Exception as e:
            logger.warning(f"Error extracting attributes: {e}")
        return attributes

    def _is_valid_row(self, row: Tag) -> bool:
        return bool(
            row.find('a', href=lambda href: href and "player" in href) and
            row.find('span', class_='pos')
        )

    @sleep_and_retry
    @limits(calls=30, period=60)  # 30 calls per minute
    def scrape_page(self) -> List[Dict]:
        """Scrape all player data from the page."""
        try:
            table_rows: ResultSet = self.soup.find_all('tr')
            logger.info(f"Found {len(table_rows)} rows to process")
            
            for row in table_rows:
                if not self._is_valid_row(row):
                    continue

                try:
                    name = self._get_player_name(row)
                    if not name:
                        continue

                    player = Player(
                        name=name,
                        positions=self._get_positions(row),
                        league_name=leagues[self.league_id]['name'],
                        league_country=leagues[self.league_id]['country'],
                        contract=self._get_contract(row),
                        attributes=self._get_attributes(row)
                    )

                    self.players.append(player.to_dict())
                
                except Exception as e:
                    logger.error(f"Error processing player row: {e}")
                    continue

            logger.info(f"Successfully processed {len(self.players)} players")
            return self.players

        except Exception as e:
            logger.error(f"Fatal error in scrape_page: {e}")
            return []

def scrape_page(soup: BeautifulSoup, lg: int) -> List[Dict]:
    """Main function to scrape a page of player data."""
    scraper = PlayerScraper(soup, lg)
    return scraper.scrape_page()