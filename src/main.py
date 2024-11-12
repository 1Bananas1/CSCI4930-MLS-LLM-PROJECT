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

from scrapers.player_scraper import scrape_page
from config.leagues import leagues

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

def save_data(data: list, league_name: str) -> None:
    """Save scraped data to CSV and JSON files."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path('data')
    output_dir.mkdir(exist_ok=True)

    # headers
    df = pd.DataFrame(data)

    df.rename(columns={'pac':'Pace/Diving','sho':'Shooting/Handling','pas':'Passing/Kicking','dri':'Dribbling/Reflexes','def':'Defending/Pace','phy':'Physical/Positioning','ae':'Age','oa':'Overall Score','pt':'Potential Score','pi':'Player ID','hi':'Height','wi':'Weight','pf':'Preferred Foot','bo':'Best Overall',
                        'bp':'Best Position','gu':'Growth','jt':'Joined Team','le':'Loan End','vl':'Value','wg':'Wage','rc':'Release Clause','ta':'Total Attacking Score',
                        'cr':'Crossing','fi':'Finishing','he':'Heading Accuracy','sh':'Short Passing','vo':'Volleys','ts':'Total Skill','dr':'Dribbling','cu':'Curve',
                        'fr':'FK Accuracy','lo':'Long Passing','bl':'Ball Control','to':'Total Movement','ac':'Acceleration','sp':'Sprint Speed','ag':'Agility',
                        're':'Reactions','ba':'Balance','tp':'Total Power','so':'Shot Power','ju':'Jumping','st':'Stamina','sr':'Strength','ln':'Long Shots','te':'Total Mentality',
                        'ar':'Aggression','in':'Interceptions','po':'Attack Position','vi':'Vision','pe':'Penalties','cm':'Composure','td':'Total Defending','ma':'Defensive Awareness',
                        'sa':'Standing Tackle','sl':'Sliding tackle','tg':'Total Goalkeeping','gd':'GK Diving','gh':'GK Handling','gc':'GK Kicking','gp':'GK Positioning',
                        'gr':'GK Reflexes','tt':'Total Stats','bs':'Base Stats','wk':'Weak Foot','sk':'Skill Moves','aw':'Attacking Work Rate','dw':'Defensive Work Rate',
                        'ir':'International Reputation','bt':'Body Type','hc':'Real Face'},inplace=True)
    
    # Save as CSV
    
    csv_file = output_dir / f'fifa_players_{league_name}_{timestamp}.csv'
    df.to_csv(csv_file, index=False)
    logger.info(f"Data saved to CSV: {csv_file}")
    
    # Save as JSON
    json_file = output_dir / f'fifa_players_{league_name}_{timestamp}.json'
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

def scrape_league(driver: webdriver.Chrome, league_id: int) -> list:
    """Scrape all player data for a single league."""
    league_data = []
    offset = 0
    league_name = leagues[league_id]['name']
    
    logger.info(f"Starting scrape for {league_name}")
    
    while True:
        try:
            # Construct URL for current page
            base_url = (
                "https://sofifa.com/players?"
                "type=all&showCol[]=pi&showCol[]=ae&showCol[]=hi&showCol[]=wi&showCol[]=pf"
                "&showCol[]=oa&showCol[]=pt&showCol[]=bo&showCol[]=bp&showCol[]=gu&showCol[]=jt"
                "&showCol[]=le&showCol[]=vl&showCol[]=wg&showCol[]=rc&showCol[]=ta&showCol[]=cr"
                "&showCol[]=fi&showCol[]=he&showCol[]=sh&showCol[]=vo&showCol[]=ts&showCol[]=dr"
                "&showCol[]=cu&showCol[]=fr&showCol[]=lo&showCol[]=bl&showCol[]=to&showCol[]=ac"
                "&showCol[]=sp&showCol[]=ag&showCol[]=re&showCol[]=ba&showCol[]=tp&showCol[]=so"
                "&showCol[]=ju&showCol[]=st&showCol[]=sr&showCol[]=ln&showCol[]=te&showCol[]=ar"
                "&showCol[]=in&showCol[]=po&showCol[]=vi&showCol[]=pe&showCol[]=cm&showCol[]=td"
                "&showCol[]=ma&showCol[]=sa&showCol[]=sl&showCol[]=tg&showCol[]=gd&showCol[]=gh"
                "&showCol[]=gc&showCol[]=gp&showCol[]=gr&showCol[]=tt&showCol[]=bs&showCol[]=wk"
                "&showCol[]=sk&showCol[]=aw&showCol[]=dw&showCol[]=ir&showCol[]=bt&showCol[]=hc"
                "&showCol[]=pac&showCol[]=sho&showCol[]=pas&showCol[]=dri&showCol[]=def&showCol[]=phy"
                f"&lg={league_id}&offset={offset}"
            )
            
            logger.info(f"Scraping {league_name} - Page {offset//60 + 1}")
            
            # Load page and parse
            driver.get(base_url)
            driver.execute_script("window.stop();")
            time.sleep(2)  # Wait for content to load
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            page_data = scrape_page(soup, league_id)
            
            if not page_data:
                logger.warning(f"No data found on page {offset//60 + 1}")
                break
                
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
    
    logger.info(f"Completed scraping {league_name}. Total players: {len(league_data)}")
    return league_data

def main():
    """Main execution function."""
    logger.info("Starting FIFA player data scraper")
    
    chrome_options = setup_chrome_options()
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    try:
        for league_id in leagues.keys():
            try:
                league_data = scrape_league(driver, league_id)
                if league_data:
                    save_data(league_data, leagues[league_id]['name'])
            except Exception as e:
                logger.error(f"Error processing league {leagues[league_id]['name']}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}")
    
    finally:
        driver.quit()
        logger.info("Scraping completed")

if __name__ == "__main__":
    main()