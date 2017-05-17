import json
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import datetime
import os

'''
This is used by flask, returns json {'title': title, 'link': link, 'content': ''}.
'''
today = datetime.date.today()

# Configure the connection to the database
client = MongoClient(os.environ['MongoDB_URI'])
# client = MongoClient('localhost', 27017)
db = client['kenya-news']  # Select the database
collection = db.news


def get_tuko():
    print('starting')
    tuko = requests.get('https://www.tuko.co.ke')
    soup = BeautifulSoup(tuko.text, 'html.parser')
    tuko = []
    for link in soup.select('a.news__link', limit=6):
        news_title = '{}({})'.format(link.get_text(), link.get('href'))
        print(news_title)
        tuko_link = requests.get(link.get('href'))
        soup_link = BeautifulSoup(tuko_link.text, 'html.parser')
        article_date = soup_link.find("meta", property="og:updated_time")['content']
        news_dict = {
            'source': 'tuko',
            'title': link.get_text(),
            'link': link.get('href'),
            'content': [link_inner.get_text().strip(' ,.-') for link_inner in
                        soup_link.select('p.align-left > strong', limit=3) if
                        link_inner.get_text() != 'READ ALSO: '],
            'date': article_date,
            'date_added': datetime.datetime.utcnow()
        }
        collection.update({'link': link.get('href')}, news_dict, upsert=True)
        tuko.append(news_dict)
    return tuko


def get_capital():
    capital_url = 'http://www.capitalfm.co.ke/news/{}/{:02}'.format(today.year, today.month)
    capital = requests.get(capital_url)
    soup = BeautifulSoup(capital.text, 'html.parser')
    capital = []
    for article in soup.select('div.entry-information'):
        article_link = article.a
        link = article_link['href']
        title = article_link.get_text()
        summary = article.p.get_text().split('-')[1].strip()
        capital_link = requests.get(link)
        soup_link = BeautifulSoup(capital_link.text, 'html.parser')
        print(title, link)
        article_date = soup_link.find("meta", property="article:published_time")['content']
        news_dict = {
            'source': 'capital',
            'title': title,
            'link': link,
            'content': [summary],
            'date': article_date,
            'date_added': datetime.datetime.utcnow()
        }
        collection.update({'link': link}, news_dict, upsert=True)
        capital.append(news_dict)
    return capital


def get_standard():
    standard = requests.get('https://www.standardmedia.co.ke/')
    soup = BeautifulSoup(standard.text, 'html.parser')
    standard = []
    for link in soup.select('.col-xs-8.zero a', limit=11):
        if link.get_text():
            news_title = '{}({})'.format(link.get_text().strip(), link.get('href'))
            print(news_title)
            standard_link = requests.get(link.get('href'))
            soup_link = BeautifulSoup(standard_link.text, 'html.parser')
            article_date = 0
            content = ''
            try:
                data = json.loads(soup_link.find('script', type='application/ld+json').text.replace("\\", r"\\"))
                article_date = data['dateModified']
                content = data['description']
            except ValueError:
                print('Invalid json detected')
            news_dict = {
                'source': 'standard',
                'title': link.get_text().strip(),
                'link': link.get('href'),
                'content': content,
                'date': article_date,
                'date_added': datetime.datetime.utcnow()
            }
            collection.update({'link': link.get('href')}, news_dict, upsert=True)
            standard.append(news_dict)
    return standard


def get_nation():
    nation = requests.get('http://www.nation.co.ke/news')
    soup = BeautifulSoup(nation.text, 'html.parser')
    top_teaser = soup.select('.story-teaser.top-teaser > h1 > a')
    medium_teasers = soup.select('.story-teaser.medium-teaser > h2 > a', limit=4)
    tiny_teasers = soup.select('.story-teaser.tiny-teaser > a:nth-of-type(2)')
    nation_stories = top_teaser + medium_teasers + tiny_teasers
    nation = []
    for link in nation_stories:
        complete_link = 'http://www.nation.co.ke{}'.format(link.get('href'))
        news_title = '{}({})'.format(link.get_text(), complete_link)
        print(news_title)
        nation_link = requests.get(complete_link)
        soup_link = BeautifulSoup(nation_link.text, 'html.parser')
        article_date = soup_link.find("meta", property="og:article:modified_time")['content']
        news_dict = {
            'source': 'nation',
            'title': link.get_text(),
            'link': complete_link,
            'content': [link_inner.get_text().strip() for link_inner in
                        soup_link.select('section.summary > div > ul li')],
            'date': article_date,
            'date_added': datetime.datetime.utcnow()
        }
        collection.update({'link': complete_link}, news_dict, upsert=True)
        nation.append(news_dict)
    return nation


def get_the_star():
    star = requests.get('http://www.the-star.co.ke/')
    soup = BeautifulSoup(star.text, 'html.parser')
    top_stories = soup.select('.field.field-name-title > h1 > a', limit=7)
    medium_stories = soup.select('h1.field-content > a', limit=10)
    star_stories = top_stories + medium_stories
    star = []
    for link in star_stories:
        complete_link = 'http://www.the-star.co.ke{}'.format(link.get('href'))
        news_title = '{}({})'.format(link.get_text(), complete_link)
        print(news_title)
        star_link = requests.get(complete_link)
        soup_link = BeautifulSoup(star_link.text, 'html.parser')
        news_dict = {
            'source': 'star',
            'title': link.get_text(),
            'link': complete_link,
            'content': [link_inner.get_text() for link_inner in soup_link.select('.field.field-name-body p', limit=2)],
            'date': datetime.datetime.utcnow(),
            'date_added': datetime.datetime.utcnow()
        }
        collection.update({'link': complete_link}, news_dict, upsert=True)
        star.append(news_dict)
    return star


def get_news():
    get_tuko()
    get_capital()
    get_standard()
    get_nation()
    # get_the_star()
