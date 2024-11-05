import pandas as pd
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options 

player_data = []

leagues = {
    13: {'country': 'England', 'name': 'Premier League'},
    16: {'country': 'France', 'name': 'Ligue 1'},
    19: {'country': 'Germany', 'name': 'Bundesliga'},
    31: {'country': 'Italy', 'name': 'Serie A'},
    53: {'country': 'Spain', 'name': 'La Liga'},
    4: {'country': 'Belgium', 'name': 'Pro League'},
    7: {'country': 'Brazil', 'name': 'Série A'},
    10: {'country': 'Netherlands', 'name': 'Eredivisie'},
    14: {'country': 'England', 'name': 'Championship'},
    17: {'country': 'France', 'name': 'Ligue 2'},
    20: {'country': 'Germany', 'name': '2. Bundesliga'},
    32: {'country': 'Italy', 'name': 'Serie B'},
    39: {'country': 'United States', 'name': 'Major League Soccer'},
    41: {'country': 'Norway', 'name': 'Eliteserien'},
    50: {'country': 'Scotland', 'name': 'Premiership'},
    54: {'country': 'Spain', 'name': 'La Liga 2'},
    56: {'country': 'Sweden', 'name': 'Allsvenskan'},
    60: {'country': 'England', 'name': 'League One'},
    61: {'country': 'England', 'name': 'League Two'},
    63: {'country': 'Greece', 'name': 'Super League'},
    64: {'country': 'Hungary', 'name': 'Nemzeti Bajnokság I'},
    65: {'country': 'Republic of Ireland', 'name': 'Premier Division'},
    66: {'country': 'Poland', 'name': 'Ekstraklasa'},
    68: {'country': 'Türkiye', 'name': 'Süper Lig'},
    80: {'country': 'Austria', 'name': 'Bundesliga'},
    83: {'country': 'Korea Republic', 'name': 'K League 1'},
    189: {'country': 'Switzerland', 'name': 'Super League'},
    308: {'country': 'Portugal', 'name': 'Primeira Liga'},
    313: {'country': 'Azerbaijan', 'name': 'Premyer Liqa'},
    317: {'country': 'Croatia', 'name': 'Hrvatska nogometna liga'},
    318: {'country': 'Cyprus', 'name': '1. Division'},
    319: {'country': 'Czechia', 'name': 'První liga'},
    322: {'country': 'Finland', 'name': 'Veikkausliiga'},
    330: {'country': 'Romania', 'name': 'Liga I'},
    332: {'country': 'Ukraine', 'name': 'Premier League'},
    335: {'country': 'Chile', 'name': 'Primera Division'},
    336: {'country': 'Colombia', 'name': 'Categoría Primera A'},
    337: {'country': 'Paraguay', 'name': 'División Profesional'},
    338: {'country': 'Uruguay', 'name': 'Primera División'},
    350: {'country': 'Saudi Arabia', 'name': 'Pro League'},
    351: {'country': 'Australia', 'name': 'A-League Men'},
    353: {'country': 'Argentina', 'name': 'Liga Profesional de Fútbol'},
    2012: {'country': 'China PR', 'name': 'Super League'},
    2013: {'country': 'United Arab Emirates', 'name': 'Pro League'},
    2017: {'country': 'Bolivia', 'name': 'División de Fútbol Profesional'},
    2018: {'country': 'Ecuador', 'name': 'Serie A'},
    2019: {'country': 'Venezuela', 'name': 'Primera Division'},
    2020: {'country': 'Peru', 'name': 'Liga 1'},
    2076: {'country': 'Germany', 'name': '3. Liga'},
    2149: {'country': 'India', 'name': 'Super League'}
}


chromeOptions = Options()
arguments = [
    "--disable-extensions",
    "--disable-notifications",
    "--disable-infobars",
    "--disable-popup-blocking",
    "--incognito",
    "--blink-settings=imagesEnabled=false"
]

for arg in arguments:
    chromeOptions.add_argument(arg)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chromeOptions)








