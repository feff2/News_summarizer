import feedparser



feed = feedparser.parse("https://lenta.ru/rss")
for entry in feed.entries:
    print(entry.title, entry.link, entry.published)

class RssScraper:
    def __init__(self, logger_name="rss_scraper"):
        self.logger = LoggerWrapper(logger_name)

    def scrape_site(self, url: str) -> dict[str, str]:
            try:
                self.logger.info("Переход на главную страницу {url}...")
                page.goto(url, timeout=120000, wait_until="domcontentloaded")   
                page.wait_for_selector("div.news_j0RKX a", timeout=30000)
                last_height = page.evaluate("document.body.scrollHeight")
                while True:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)
                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                
                anchors = page.query_selector_all("div.news_j0RKX a")

                links = set()
                for a in anchors:
                    href = a.get_attribute("href")
                    if href and re.search(r'/(text|incidents|longread|transport)/', href):
                        links.add(href)
                
                self.logger.debug(f"Найдено {len(links)} новостных статей")
                
                links_dict = {}

                for link in list(links)[:5]:
                    full_url = link if link.startswith('http') else f'{url}{link}'
                    try:
                        article = Article(full_url, language="ru")
                        article.download()
                        article.parse()

                        self.logger.debug("---")
                        self.logger.debug("Заголовок: " + article.title)
                        self.logger.debug("Текст: " + article.text[:500] + "...")
                        links[full_url] = f"Заголовок: {article.title}\nТекст: {article.text}"
                
                    except Exception as e:
                        self.logger.error(f"Не удалось обработать {full_url}: {e}")
                return links

            except Exception as e:
                self.logger.error(f"Ошибка при навигации или загрузке: {e}")
                page.screenshot(path="debug_screenshot.png")
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                self.logger.info("Файлы отладки сохранены.")
            finally:
                browser.close()
