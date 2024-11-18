import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import logging
from datetime import datetime
import json
from typing import List, Dict, Optional

from scrapers.player_scraper import scrape_page
from config.leagues import leagues

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_fifa_versions(driver: webdriver.Chrome) -> Dict[int, str]:
    """
    Get all available FIFA version codes from the roster dropdown.
    Returns a dictionary mapping years to their latest version codes.
    """
    try:
        # Go to the main page first
        driver.get("https://sofifa.com")
        time.sleep(5)  # Wait for page to load

        # Click on any dropdown/button if needed to show roster versions
        roster_button = driver.find_element(By.NAME, "roster")
        roster_button.click()
        time.sleep(2)  # Wait for dropdown to fully load
        
        # Parse the roster dropdown
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        roster_select = soup.find('select', {'name': 'roster'})
        
        if not roster_select:
            logger.error("Could not find roster selection dropdown")
            driver.save_screenshot("error_page.png")  # Save screenshot for debugging
            logger.info("Page source:")
            logger.info(soup.prettify()[:500])  # Log first 500 chars of page source
            return {}
            
        versions = {}
        logger.info("Found roster options:")
        for option in roster_select.find_all('option'):
            # Get both value and text
            value = option.get('value', '')
            text = option.text.strip()
            logger.info(f"Found option: {text} -> {value}")
            
            if value and '/?' in value and 'r=' in value and 'set=true' in value:
                # Extract version code using regex to be more robust
                import re
                version_match = re.search(r'r=(\d+)&', value)
                if version_match:
                    version_code = version_match.group(1)
                    try:
                        date = datetime.strptime(text, '%b %d, %Y')
                        year = date.year
                        
                        # Keep only the latest version (highest number) for each year
                        if year not in versions or int(version_code) > int(versions[year]):
                            versions[year] = version_code
                            logger.info(f"Added/Updated version for {year}: {version_code}")
                    except ValueError as e:
                        logger.warning(f"Could not parse date from '{text}': {e}")
                        continue
                else:
                    logger.warning(f"Could not extract version code from value: {value}")
        
        if not versions:
            logger.error("No versions found! Page source:")
            logger.error(soup.prettify()[:1000])  # Log more of the page source for debugging
            return {}
            
        logger.info("Successfully found versions:")
        for year, code in sorted(versions.items()):
            logger.info(f"FIFA {year}: {code}")
            
        return versions
        
    except Exception as e:
        logger.error(f"Error getting FIFA versions: {e}")
        import traceback
        logger.error(traceback.format_exc())  # Print full stack trace
        return {}
    
def setup_chrome_options() -> Options:
    """Configure Chrome options for scraping."""
    chrome_options = Options()
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    return chrome_options

def save_data(data: List[Dict], league_name: str, year: int = None) -> None:
    """Save scraped data to CSV and JSON files."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path('data')
    output_dir.mkdir(exist_ok=True)
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Add year to filename if provided
    year_suffix = f"_{year}" if year is not None else ""

    df.rename(columns={'pac':'Pace/Diving','sho':'Shooting/Handling','pas':'Passing/Kicking','dri':'Dribbling/Reflexes','def':'Defending/Pace','phy':'Physical/Positioning',
                    'ae':'Age','oa':'Overall Score','pt':'Potential Score','pi':'Player ID','hi':'Height','wi':'Weight','pf':'Preferred Foot','bo':'Best Overall',
                    'bp':'Best Position','gu':'Growth','jt':'Joined Team','le':'Loan End','vl':'Value','wg':'Wage','rc':'Release Clause','ta':'Total Attacking Score',
                    'cr':'Crossing','fi':'Finishing','he':'Heading Accuracy','sh':'Short Passing','vo':'Volleys','ts':'Total Skill','dr':'Dribbling','cu':'Curve',
                    'fr':'FK Accuracy','lo':'Long Passing','bl':'Ball Control','to':'Total Movement','ac':'Acceleration','sp':'Sprint Speed','ag':'Agility',
                    're':'Reactions','ba':'Balance','tp':'Total Power','so':'Shot Power','ju':'Jumping','st':'Stamina','sr':'Strength','ln':'Long Shots','te':'Total Mentality',
                    'ar':'Aggression','in':'Interceptions','po':'Attack Position','vi':'Vision','pe':'Penalties','cm':'Composure','td':'Total Defending','ma':'Defensive Awareness',
                    'sa':'Standing Tackle','sl':'Sliding tackle','tg':'Total Goalkeeping','gd':'GK Diving','gh':'GK Handling','gc':'GK Kicking','gp':'GK Positioning',
                    'gr':'GK Reflexes','tt':'Total Stats','bs':'Base Stats','wk':'Weak Foot','sk':'Skill Moves','aw':'Attacking Work Rate','dw':'Defensive Work Rate',
                    'ir':'International Reputation','bt':'Body Type','hc':'Real Face'}, inplace=True)
    
    # Save as CSV
    csv_file = output_dir / f'fifa_players_{league_name}_{year_suffix}_{timestamp}.csv'
    df.to_csv(csv_file, index=False)
    logger.info(f"Data saved to CSV: {csv_file}")
    
    # Save as JSON
    json_file = output_dir / f'fifa_players_{league_name}_{year_suffix}_{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Data saved to JSON: {json_file}")

def has_next_page(driver) -> bool:
    """Check if there is a next page available."""
    try:
        next_button = driver.find_elements(By.LINK_TEXT, "Next")
        return bool(next_button)
    except Exception as e:
        logger.warning(f"Error checking for next page: {e}")
        return False

def scrape_league(driver: webdriver.Chrome, league_id: int, year: int, version_code: str) -> List[Dict]:
    """Scrape all player data for a single league and year."""
    league_data = []
    offset = 0
    league_name = leagues[league_id]['name']
    
    logger.info(f"Starting scrape for {league_name} - FIFA {year}")
    
    while True:
        try:
            base_url = (
                f"https://sofifa.com/players?r={version_code}&set=true"
                "&type=all"
                "&showCol[]=pi&showCol[]=ae&showCol[]=hi&showCol[]=wi&showCol[]=pf"
                "&showCol[]=oa&showCol[]=pt&showCol[]=bo&showCol[]=bp&showCol[]=gu"
                "&showCol[]=jt&showCol[]=le&showCol[]=vl&showCol[]=wg&showCol[]=rc"
                "&showCol[]=ta&showCol[]=cr&showCol[]=fi&showCol[]=he&showCol[]=sh"
                "&showCol[]=vo&showCol[]=ts&showCol[]=dr&showCol[]=cu&showCol[]=fr"
                "&showCol[]=lo&showCol[]=bl&showCol[]=to&showCol[]=ac&showCol[]=sp"
                "&showCol[]=ag&showCol[]=re&showCol[]=ba&showCol[]=tp&showCol[]=so"
                "&showCol[]=ju&showCol[]=st&showCol[]=sr&showCol[]=ln&showCol[]=te"
                "&showCol[]=ar&showCol[]=in&showCol[]=po&showCol[]=vi&showCol[]=pe"
                "&showCol[]=cm&showCol[]=td&showCol[]=ma&showCol[]=sa&showCol[]=sl"
                "&showCol[]=tg&showCol[]=gd&showCol[]=gh&showCol[]=gc&showCol[]=gp"
                "&showCol[]=gr&showCol[]=tt&showCol[]=bs&showCol[]=wk&showCol[]=sk"
                "&showCol[]=aw&showCol[]=dw&showCol[]=ir&showCol[]=bt&showCol[]=hc"
                "&showCol[]=pac&showCol[]=sho&showCol[]=pas&showCol[]=dri"
                "&showCol[]=def&showCol[]=phy"
                "&showCol[]=traits&showCol[]=playstyles"
                "&showCol[]=playstyles_plus&showCol[]=acceleration_type"
                f"&lg={league_id}&offset={offset}"
            )
            
            logger.info(f"Scraping {league_name} - FIFA {year} - Page {offset//60 + 1}")
            
            driver.get(base_url)
            driver.execute_script("window.stop();")
            time.sleep(2)  # Wait for content to load
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            page_data = scrape_page(soup, league_id)
            
            if not page_data:
                logger.warning(f"No data found on page {offset//60 + 1}")
                break
                
            # Add year to each player's data
            for player in page_data:
                player['Year'] = year
                player['FIFA_Version'] = f"FIFA {year}" if year != 2024 else "FC 25"
                
            league_data.extend(page_data)
            logger.info(f"Found {len(page_data)} players on current page")
            
            if not has_next_page(driver):
                logger.info("Reached last page")
                break
                
            offset += 60
            driver.delete_all_cookies()
            
        except Exception as e:
            logger.error(f"Error scraping page: {e}")
            break
    
    logger.info(f"Completed scraping {league_name} - Year {year}. Total players: {len(league_data)}")
    return league_data

def main():
    """Main execution function."""
    logger.info("Starting FIFA player data scraper")
    
    # Hardcoded versions for testing
    hardcoded_versions = {
        2015: "150059",
        2016: "160058",
        2017: "170099",
        2018: "180067"
    }
    
    chrome_options = setup_chrome_options()
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    try:
        logger.info("Using hardcoded FIFA versions:")
        for year, code in sorted(hardcoded_versions.items()):
            logger.info(f"FIFA {year}: Version code {code}")
        
        total_players = 0
        for league_id in leagues.keys():
            league_name = leagues[league_id]['name']
            logger.info(f"Processing league: {league_name}")
            
            for year, version_code in sorted(hardcoded_versions.items()):
                try:
                    year_data = scrape_league(driver, league_id, year, version_code)
                    
                    if year_data:
                        save_data(year_data, league_name, year)
                        total_players += len(year_data)
                    
                    time.sleep(5)
                    
                except Exception as e:
                    logger.error(f"Error processing FIFA {year} for {league_name}: {e}")
                    continue
                    
            logger.info(f"Completed processing {league_name}")
            
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}")
    
    finally:
        driver.quit()
        logger.info(f"Scraping completed. Total players scraped: {total_players}")

if __name__ == "__main__":
    main()