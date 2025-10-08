import requests
from bs4 import BeautifulSoup
from datetime import datetime
from src.shared.logger import LoggerWrapper
from src.jobs.settings import settings


class RssScraper:
    def __init__(self):

        self.logger = LoggerWrapper("rss_scraper")
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    def _fetch_page(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ошибка при загрузке {url}: {e}")
            return None

    def _parse_article_page(self, article_url, pub_date_str):
        self.logger.info(f"Парсинг статьи: {article_url}")
        response = self._fetch_page(article_url)
        if not response:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        title_tag = soup.find('h1', class_='topic-body__title')
        title = title_tag.get_text(strip=True) if title_tag else ""

        content_paragraphs = soup.find_all('p', class_='topic-body__content-text')
        text = "\n".join([p.get_text(strip=True) for p in content_paragraphs])
        
        if not text:
            text_div = soup.find('div', class_='topic-body__content')
            if text_div:
                text = text_div.get_text(strip=True, separator='\n')

        try:
            published_at = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
        except ValueError:
            published_at = datetime.now()

        return {
            'published_at': published_at.isoformat(),
            'content': f"{title}\n\n{text}",
            'url': article_url
        }

    def scrape_feed(self, urls, limit=None):
        articles_by_source = {}
        for url in urls:
            articles_by_source[url] = []

            self.logger.info(f"Запускаем парсинг RSS: {url}")
            response = self._fetch_page(url)
            if not response:
                return []

            soup = BeautifulSoup(response.content, 'lxml-xml')
            
            items = soup.find_all('item')
            
            if limit:
                items = items[:limit]
                self.logger.info(f"Найдено {len(items)} новостей (установлен лимит).")
            else:
                self.logger.info(f"Найдено {len(items)} новостей в RSS.")


            for item in items:
                article_url = item.link.text
                pub_date_str = item.pubDate.text
                
                if article_url:
                    article_data = self._parse_article_page(article_url, pub_date_str)
                    if article_data:
                        articles_by_source[url].append(article_data)
            
        return articles_by_source

if __name__ == "__main__":
    scraper = RssScraper()
    
    articles = scraper.scrape_feed(settings.RSS_URLS, limit=3)
    
    print("\n\n--- ✨ Итоговый результат ---")
    if articles:
        print(articles)
    else:
        print("Не удалось получить данные о статьях.")