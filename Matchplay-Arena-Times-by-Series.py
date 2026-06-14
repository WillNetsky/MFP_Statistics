import pandas as pd
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

ua = UserAgent()
#fallback='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/537.13
# (KHTML, like Gecko) Chrome/24.0.1290.1 Safari/537.13')
ua.update()

# Matchplay API URL
series_id = '1877'
series_url = 'https://matchplay.events/data/series/'+series_id+'/standings'

# Call the API
r = requests.get(series_url)
data = r.json()
tournaments = data['tournament_points']
tournament_ids = [tournament['tournament_id'] for tournament in data['tournament_points']]

tournaments = []
for tournament in tournament_ids:
    results_url = 'https://matchplay.events/data/tournaments/' + str(tournament) + '/results/csv'
    results = pd.read_csv(results_url)
    tournaments.append(results)
results = pd.concat(tournaments)

arenas = results[['Round','Set','Game 1']]

round_ids = arenas.Round.unique()

standings_url = 'https://matchplay.events/live/series/'+series_id

def get_soup(url, timeout=5):
    headers  = {'User-Agent':ua.random}
    try:
        response = requests.get(url,headers=headers)
    except:
        print("FAILED "+ url)
        return 0
    attempts = 0
    while(not response.ok):
            print((url+' failed with code: '+str(response.status_code)))
            if attempts > timeout:
                print(url+' failed with code: '+str(response.status_code))
                return BeautifulSoup('','lxml')
            response = requests.get(url)
            attempts += 1
    page = response.text
    soup = BeautifulSoup(page, 'lxml')
    return soup

standings_page = get_soup(standings_url)

tournament_live_ids = []
for week in standings_page.find('tr').find_all('a')[:len(tournament_ids)]:
    tournament_live_ids.append(week['href'].split('/')[-1])


# Selenium section
option = webdriver.ChromeOptions()
option.add_argument(' - incognito')
driver = webdriver.Chrome(ChromeDriverManager().install())

