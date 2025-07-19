import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import time

#get data from url with standings
standings_url = "https://www.hockey-reference.com/leagues/NHL_2025.html"
data = requests.get(standings_url)
time.sleep(2)

#get beginning table
soup = BeautifulSoup(data.text,features="lxml")
all_matches = []
team_urls = []
team_names = []
for x in range(0,2,1):
    starting_table = soup.select('table', class_=['sortable','stats_table','now_sortable'])[x]
    
    #get team links and team name from table
    links = starting_table.find_all('a')
    for link in links:
        href = link.get("href")
        if href and '/teams/' in href:
            full_url = f"https://www.hockey-reference.com{href}"
            name = link.text.strip()  # Get visible text of link
            team_urls.append(full_url)
            team_names.append(name)

for x in range(0,len(team_urls),1): 
    #get team url 
    team_url = team_urls[x]
    team_name = team_names[x]

    data = requests.get(team_url)
    time.sleep(2)

    #get link from header
    soup = BeautifulSoup(data.text,features="lxml")
    header = soup.select('div[data-template="Partials/Teams/Summary"]')[0]
    links = header.find_all('a')
    links = [l.get("href") for l in links]
    schedule_link = [l for l in links if '_games' in l]
    schedule_link = [f"https://www.hockey-reference.com{schedule_link[0]}"][0]

    #get link for game specific stats
    soup_game = BeautifulSoup(data.text,features="lxml")
    links = soup.find_all('a')
    links = [l.get("href") for l in links]
    links = [l for l in links if l and '_gamelog' in l]
    gamelog_link = [f"https://www.hockey-reference.com{links[0]}"][0] 
    
    years = list(range(2025,2021,-1))
    for year in years:
        data = requests.get(schedule_link)
        time.sleep(2)
        soup = BeautifulSoup(data.text,features="lxml")

        #match dataframe
        matches = pd.read_html(StringIO(data.text), match="Regular Season")[0]

        #adjust cols
        cols = matches.columns.tolist()
        cols[cols.index("Unnamed: 6")] = 'Result'
        cols[cols.index('Unnamed: 2')] = "Venue"
        matches.columns = cols
        matches = matches.drop(['Unnamed: 7','OL','Streak','Att.','LOG','Notes'], axis=1)

        data = requests.get(gamelog_link)
        soup_game = BeautifulSoup(data.text,features="lxml")
        time.sleep(2)

        #shooting dataframe
        shooting = pd.read_html(StringIO(data.text), match= "Regular Season")[0]
        if isinstance(shooting.columns, pd.MultiIndex):
            shooting.columns = shooting.columns.droplevel()

        #rename columns to make data clearer
        cols = shooting.columns.tolist()
        cols[cols.index('SOG')] = 'SOG_For'
        cols[cols.index('PIM')] = 'PIM_For'
        cols[cols.index('PPG')] = 'PPG_For'
        cols[cols.index('PPO')] = 'PPO_For'
        cols[cols.index('SOG')] = 'SOG_Against'
        cols[cols.index('PIM')] = 'PIM_Against'
        cols[cols.index('PPG')] = 'PPG_Against'
        cols[cols.index('PPO')] = 'PPO_Against'
        shooting.columns = cols

        #combine dataframes together
        try:
            team_data = matches.merge(shooting[["Date", "SOG_For","SOG_Against","PIM_For","PIM_Against","OT","PPG_For","PPG_Against","PPO_For","PPO_Against"]], on = "Date")
        except ValueError:
            continue

        #add season and team data
        team_data["Season"]= f"{year-1}-{year}"
        team_data["Team"] = team_name
        team_data["Venue"] = team_data["Venue"].replace('@', 'Away')
        team_data["Venue"] = team_data["Venue"].fillna('Home')

        all_matches.append(team_data)
        time.sleep(2)

        print(f"Successfully read {team_name} {year-1}-{year} stats")

        #get next schedule link
        link = soup.select_one('a.button2.prev')
        if link and link.has_attr('href'):
            schedule_link = f"https://www.hockey-reference.com{link['href']}"
        else:
            break

        #get next gamelog link
        link = soup_game.select_one('a.button2.prev')
        if link and link.has_attr('href'):
            gamelog_link = f"https://www.hockey-reference.com{link['href']}"
        else:
            break 

#get single dataframe
match_df = pd.concat(all_matches)
match_df.columns = [c.lower() for c in match_df.columns]
match_df.to_csv("matches.csv")
print("All matches read and input into a csv file")