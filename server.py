import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from urllib.parse import parse_qs, urlparse
import json
import pandas as pd
from datetime import datetime
import uuid
import os
from typing import Callable, Any
from wsgiref.simple_server import make_server
import random

nltk.download('vader_lexicon', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('stopwords', quiet=True)

adj_noun_pairs_count = {}
sia = SentimentIntensityAnalyzer()
stop_words = set(stopwords.words('english'))

reviews = pd.read_csv('data/reviews.csv').to_dict('records')

VALID_LOCATIONS = [
    "Albuquerque, New Mexico",
    "Carlsbad, California",
    "Chula Vista, California",
    "Colorado Springs, Colorado",
    "Denver, Colorado",
    "El Cajon, California",
    "El Paso, Texas",
    "Escondido, California",
    "Fresno, California",
    "La Mesa, California",
    "Las Vegas, Nevada",
    "Los Angeles, California",
    "Oceanside, California",
    "Phoenix, Arizona",
    "Sacramento, California",
    "Salt Lake City, Utah",
    "Salt Lake City, Utah",
    "San Diego, California",
    "Tucson, Arizona"
]

class ReviewAnalyzerServer:
    def __init__(self) -> None:
        # This method is a placeholder for future initialization logic
        pass

    def analyze_sentiment(self, review_body):
        sentiment_scores = sia.polarity_scores(review_body)
        return sentiment_scores

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]) -> bytes:
        """
        The environ parameter is a dictionary containing some useful
        HTTP request information such as: REQUEST_METHOD, CONTENT_LENGTH, QUERY_STRING,
        PATH_INFO, CONTENT_TYPE, etc.
        """

        if environ["REQUEST_METHOD"] == "GET":
            # Create the response body from the reviews and convert to a JSON byte string
            def analyze_sentiment(r):
                return {
                    'neg': round(random.uniform(0, 10), 2),
                    'new': round(random.uniform(0, 10), 2),
                    'pos': round(random.uniform(0, 10), 2),
                    'compound': round(random.uniform(0, 10), 2),
                }

            def transformResponseItems(rs):
                for i in rs:
                    i['sentiment'] = analyze_sentiment(i)
                return rs
            
            response_body = json.dumps(transformResponseItems(reviews), indent=2).encode("utf-8")
            
            # Write your code here
            query_string = environ["QUERY_STRING"]
            q = parse_qs(query_string)
            # queries = query_string.split('&')
            # query_dict = {} if not query_string else dict([i.split('=') for i in queries])
            # print(query_dict)

            filtered_review = transformResponseItems(reviews)


            for k, v in q.items():
                if k == 'start_date':
                    filtered_review = list(filter(lambda r: datetime.strptime(r['Timestamp'], "%Y-%m-%d %H:%M:%S") >= datetime.strptime(v[0], "%Y-%m-%d"), filtered_review))
                elif k == 'end_date':
                    filtered_review = list(filter(lambda r: datetime.strptime(r['Timestamp'], "%Y-%m-%d %H:%M:%S") <= datetime.strptime(v[0], "%Y-%m-%d"), filtered_review))
                else:
                    # check if valid location
                    if k == 'location' and v[0] not in VALID_LOCATIONS:
                        response_body = json.dumps({'error': 'invalid location'}, indent=2).encode("utf-8")  
                        start_response("400 Bad Request", [
                            ("Content-Type", "application/json"),
                            ("Content-Length", str(len(response_body)))
                            ])
                        return [response_body]

                    filtered_review = list(filter(lambda r: r[k.capitalize()] == v[0], reviews))

                
            sorted_reviews = sorted(filtered_review, key=lambda x: x['sentiment']['compound'], reverse=True)
            response_body = json.dumps(sorted_reviews, indent=2).encode("utf-8")


            

            # Set the appropriate response headers
            start_response("200 OK", [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response_body)))
             ])
            
            return [response_body]


        if environ["REQUEST_METHOD"] == "POST":
            # Write your code here
            try:
                content_length = int(environ.get("CONTENT_LENGTH", 0))
            except ValueError:
                content_length = 0

            body = environ["wsgi.input"].read(content_length).decode('utf-8')
            q = parse_qs(body)

            location = q.get('Location', [None])[0]
            review_body = q.get('ReviewBody', [None])[0]

            if location is None or location not in VALID_LOCATIONS:
                response_body = json.dumps({'error': 'invalid location'}, indent=2).encode("utf-8")  
                start_response("400 Bad Request", [
                    ("Content-Type", "application/json"),
                    ("Content-Length", str(len(response_body)))
                ])
                return [response_body]

            if review_body is None:
                response_body = json.dumps({'error': 'body can not be empty'}, indent=2).encode("utf-8")  
                start_response("400 Bad Request", [
                    ("Content-Type", "application/json"),
                    ("Content-Length", str(len(response_body)))
                ])
                return [response_body]


            r = {
                "ReviewId": str(uuid.uuid4()),
                "ReviewBody": review_body,
                "Location": location,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            response_body = json.dumps(r, indent=2).encode("utf-8")
            start_response("201 Created", [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response_body)))
             ])

            return [response_body]

if __name__ == "__main__":
    app = ReviewAnalyzerServer()
    port = os.environ.get('PORT', 8000)
    with make_server("", port, app) as httpd:
        print(f"Listening on port {port}...")
        httpd.serve_forever()