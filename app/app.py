from flask import Flask, jsonify, render_template
from pymongo import MongoClient
import datetime
import os
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import requests

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Load sensitive information from environment variables
MONGO_URI = os.getenv("MONGO_URI")
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")
TWITTER_NAME = os.getenv("TWITTER_NAME")

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client["twitter_trends"]
collection = db["trend_data"]

# ScraperAPI configuration
proxy_url = f'https://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url=https://httpbin.org/ip'

# Function to scrape Twitter trends using Playwright
def scrape_twitter():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Navigate to Twitter login page
        page.goto("https://twitter.com/i/flow/login")

        # Log in to Twitter
        page.fill("input[name=\"text\"]", TWITTER_USERNAME)
        page.press("input[name=\"text\"]", "Enter")
        time.sleep(2)

        # Handle additional username input if required
        try:
            page.fill("input[name=\"text\"]", TWITTER_NAME)
            page.press("input[name=\"text\"]", "Enter")
            time.sleep(2)
        except Exception:
            print("No additional username input required")

        # Enter the password
        page.fill("input[name=\"password\"]", TWITTER_PASSWORD)
        page.press("input[name=\"password\"]", "Enter")

        # Wait for the home page to load
        page.wait_for_url("**/home")
        print("Login successful!")

        # Extract trends
        trends = []
        trend_selectors = [
            "xpath=/html/body/div[1]/div/div/div[2]/main/div/div/div/div[2]/div/div[2]/div/div/div/div[4]/section/div/div/div[3]/div/div/div/div[2]",
            "xpath=/html/body/div[1]/div/div/div[2]/main/div/div/div/div[2]/div/div[2]/div/div/div/div[4]/section/div/div/div[4]/div/div/div/div[2]",
            "xpath=/html/body/div[1]/div/div/div[2]/main/div/div/div/div[2]/div/div[2]/div/div/div/div[4]/section/div/div/div[5]/div/div/div/div[2]",
            "xpath=/html/body/div[1]/div/div/div[2]/main/div/div/div/div[2]/div/div[2]/div/div/div/div[4]/section/div/div/div[6]/div/div/div/div[2]",
        ]

        for selector in trend_selectors:
            try:
                trend = page.locator(selector).text_content()
                trends.append(trend)
            except Exception as e:
                print(f"Failed to fetch trend: {e}")

        # Close the browser
        browser.close()

        return trends

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run-scraper", methods=["GET"])
def run_scraper():
    try:
        # Capture start time
        start_time = datetime.datetime.now()
        print(f"Script started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Scrape Twitter trends
        trends = scrape_twitter()
        print(f"Trends: {trends}")

        # Retrieve IP address used via ScraperAPI
        ip_address = "Unknown"
        try:
            response = requests.get(proxy_url)
            print("ScraperAPI Response Content:", response.text)

            if response.status_code == 200:
                ip_address = response.json().get('origin', 'Unknown')
            else:
                ip_address = "Error: Failed to retrieve IP"
        except Exception as e:
            print(f"Error occurred while fetching IP address from ScraperAPI: {str(e)}")

        print("IP address used by ScraperAPI:", ip_address)

        # Capture end time
        end_time = datetime.datetime.now()
        print(f"Script ended at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Save data to MongoDB
        document = {
            "trends": trends,
            "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S'),
            "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S'),
            "ip_address": ip_address
        }

        collection.insert_one(document)
        print("Data saved to MongoDB:", document)

        # Fetch the latest entry from the database
        latest_entry = collection.find_one(sort=[("_id", -1)])
        if not latest_entry:
            return jsonify({"error": "No data found in MongoDB."}), 404

        response_data = {
            "unique_id": str(latest_entry.get("_id", "N/A")),
            "trends": latest_entry.get("trends", "N/A"),
            "start_time": latest_entry.get("start_time", "N/A"),
            "end_time": latest_entry.get("end_time", "N/A"),
            "ip_address": latest_entry.get("ip_address", "N/A"),
        }

        print(f"Latest MongoDB Entry: {response_data}")

        return jsonify(response_data)

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
