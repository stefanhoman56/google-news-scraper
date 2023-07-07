from summarizer import GoogleNewsSummarizer
import openai
import json

openai.api_key = ''

if __name__ == "__main__":
    articles = GoogleNewsSummarizer(500).run('AI', 5)
    file = open('result.json', 'w')
    json.dump(articles, file, indent=2)
    file.close()
