import datetime
import urllib3
import json
import logging
import pandas as pd
import requests
import socket
from bs4 import BeautifulSoup

urllib3.disable_warnings()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

BASE_URL = "https://ctftime.org/stats"
BASE_IP = "109.233.61.11"


def fronting(*args, **kwargs):
    return [
        [
            socket.AddressFamily.AF_INET,
            socket.SocketKind.SOCK_STREAM,
            6,
            "",
            (BASE_IP, 443),
        ]
    ]


socket.getaddrinfo = fronting

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0"
}


def getCountryMap(save=None):
    url = f"{BASE_URL}/US"
    r = requests.get(url, headers=headers, verify=False)
    soup = BeautifulSoup(r.text, "lxml")
    countries = soup.find_all("ul", {"class": "dropdown-menu"})[3].find_all("li")[1:]
    maper = lambda x: (x.a.attrs["href"].split("/")[-1], x.text)
    countries = dict(map(maper, countries)) | {"idk": "idk"}
    # countries = dict(sorted(countries.items(), key=lambda item: item[1]))
    if save:
        with open(save, "w") as fp:
            json.dump(countries, fp, indent=4)
    return countries


def parsePage(team):
    tds = team.find_all("td")
    rank = tds[0].text
    team_name = tds[2].text
    team_id = tds[2].a.attrs["href"].split("/")[-1]
    country = tds[3].img.attrs["alt"] if tds[3].img else "idk"
    score = tds[4].text
    events = tds[5].text
    return rank, team_name, team_id, country, score, events


def getTeamInfo(YEAR, page=20):
    for i in range(page):
        url = f"{BASE_URL}/{YEAR}?page={i+1}"
        logging.debug(f"GET {url}")
        r = requests.get(url, headers=headers, verify=False)
        if r.status_code != 200:
            logging.warning(f"Can't reach {url}")
            return
        soup = BeautifulSoup(r.text, "lxml")
        for team in soup.find_all("tr")[1:51]:
            yield parsePage(team)


def saveRank(YEAR, csvFile=None, page=20):
    df = pd.DataFrame(columns=["rank", "Name", "team_id", "country", "score", "events"])
    for i, data in enumerate(getTeamInfo(YEAR, page)):
        df.loc[i] = data
    convert_dict = {"rank": int, "team_id": int, "score": float, "events": int}
    df = df.astype(convert_dict)
    countries = getCountryMap()
    df.replace({"country": countries}, inplace=True)
    if csvFile:
        df.to_csv(csvFile, index=False)
        logging.info(f"Saved {csvFile}!")
    return df


if __name__ == "__main__":
    current_time = datetime.datetime.now()
    year = current_time.year
    if current_time.month == 1 and current_time.day < 14:
        year -= 1
    csvFile = f"CTFTIME_{year}.csv"
    saveRank(year, csvFile)
    # getCountryMap(f"countries.json")
