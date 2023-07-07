import requests
from bs4 import BeautifulSoup
from google_news import GoogleNews
import openai

class GoogleNewsSummarizer:
    def __init__(self, summary_token_count) -> None:
        self.summary_word_count = summary_token_count

    def get_soup(self, url):
        headers = { 'User-Agent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/534.1 (KHTML, like Gecko) Chrome/6.0.422.0 Safari/534.1' }
        cookies = { 'CONSENT':'YES+cb.20230705-17-p0.it+FX+917; ' }
        response = requests.get(url, headers=headers, cookies=cookies)
        return BeautifulSoup(response.content, 'html.parser')
    
    def get_original_article_link(self, url):
        soup = self.get_soup(url)
        return soup.find('c-wiz').find('a').text
    
    def get_article_content(self, url):
        soup = self.get_soup(url)

        paragraphs = soup.find_all('p')

        filtered_paragraphs = [
            p.get_text() for p in paragraphs 
            if 'unwanted-class' not in p.get('class', []) and 'unwanted-id' not in p.get('id', '') 
            and not p.find_parent(['footer', 'header'])
            and not p.find(class_='unwanted-class')
            and not p.get('style') == 'display:none;'
            and 'Sign Up' not in p.get_text()  # Exclude text containing 'Sign Up'
            and 'Sign In' not in p.get_text()  # Exclude text containing 'Sign In'
            and 'Terms and Conditions' not in p.get_text()  # Exclude text containing 'Terms and Conditions'
            # Add more conditions as needed to exclude unwanted elements
        ]

        return '\n'.join(filtered_paragraphs)

    def search_articles(self, keywords, count):
        """{
            "title": "AI Agents that \u201cSelf-Reflect\u201d Perform Better in Changing Environments - Stanford HAI",
            "title_detail": {
                "type": "text/plain",
                "language": null,
                "base": "",
                "value": "AI Agents that \u201cSelf-Reflect\u201d Perform Better in Changing Environments - Stanford HAI"
            },
            "links": [
                {
                "rel": "alternate",
                "type": "text/html",
                "href": "https://news.google.com/rss/articles/CBMiWWh0dHBzOi8vaGFpLnN0YW5mb3JkLmVkdS9uZXdzL2FpLWFnZW50cy1zZWxmLXJlZmxlY3QtcGVyZm9ybS1iZXR0ZXItY2hhbmdpbmctZW52aXJvbm1lbnRz0gEA?oc=5"
                }
            ],
            "link": "https://news.google.com/rss/articles/CBMiWWh0dHBzOi8vaGFpLnN0YW5mb3JkLmVkdS9uZXdzL2FpLWFnZW50cy1zZWxmLXJlZmxlY3QtcGVyZm9ybS1iZXR0ZXItY2hhbmdpbmctZW52aXJvbm1lbnRz0gEA?oc=5",
            "id": "CBMiWWh0dHBzOi8vaGFpLnN0YW5mb3JkLmVkdS9uZXdzL2FpLWFnZW50cy1zZWxmLXJlZmxlY3QtcGVyZm9ybS1iZXR0ZXItY2hhbmdpbmctZW52aXJvbm1lbnRz0gEA",
            "guidislink": false,
            "published": "Thu, 06 Jul 2023 15:24:11 GMT",
            "published_parsed": [
                2023,
                7,
                6,
                15,
                24,
                11,
                3,
                187,
                0
            ],
            "summary": "<a href=\"https://news.google.com/rss/articles/CBMiWWh0dHBzOi8vaGFpLnN0YW5mb3JkLmVkdS9uZXdzL2FpLWFnZW50cy1zZWxmLXJlZmxlY3QtcGVyZm9ybS1iZXR0ZXItY2hhbmdpbmctZW52aXJvbm1lbnRz0gEA?oc=5\" target=\"_blank\">AI Agents that \u201cSelf-Reflect\u201d Perform Better in Changing Environments</a>&nbsp;&nbsp;<font color=\"#6f6f6f\">Stanford HAI</font>",
            "summary_detail": {
                "type": "text/html",
                "language": null,
                "base": "",
                "value": "<a href=\"https://news.google.com/rss/articles/CBMiWWh0dHBzOi8vaGFpLnN0YW5mb3JkLmVkdS9uZXdzL2FpLWFnZW50cy1zZWxmLXJlZmxlY3QtcGVyZm9ybS1iZXR0ZXItY2hhbmdpbmctZW52aXJvbm1lbnRz0gEA?oc=5\" target=\"_blank\">AI Agents that \u201cSelf-Reflect\u201d Perform Better in Changing Environments</a>&nbsp;&nbsp;<font color=\"#6f6f6f\">Stanford HAI</font>"
            },
            "source": {
                "href": "https://hai.stanford.edu",
                "title": "Stanford HAI"
            },
            "sub_articles": []
        }"""
        gn = GoogleNews()
        result = gn.search(keywords)
        return result['entries'][:count]
    
    def call_openai(self, prompt):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=(self.summary_word_count * 3) // 2,
            temperature=0.3,
        )

        result = completion["choices"][0]["message"]["content"]
        return result

    def get_summary(self, content):
        limit = self.summary_word_count * 5
        unit_length = 8000
        while len(content) > limit:
            prompt = f'Write summary less than {self.summary_word_count} words: \n\n' + content[:unit_length]
            content = self.call_openai(prompt) + '\n\n' + content[unit_length:]
        return content

    def run(self, keywords, count):
        articles = self.search_articles(keywords, count)
        result = []
        for index, article in enumerate(articles):
            original_link = self.get_original_article_link(article['link'])
            content = self.get_article_content(original_link)
            print("summary length is ", len(content))
            summary = self.get_summary(content)
            result.append({
                'title': article['title'],
                'summary': summary
            })
        return result
