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
    try:
        with sync_playwright() as p:
            # Launch the browser with full-screen settings
            browser = p.chromium.launch(headless=True, args=["--start-maximized"])
            context = browser.new_context(
                viewport=None  # Sets the browser to fullscreen mode
            )
            page = context.new_page()

            # Navigate to Twitter login page
            print("Navigating to Twitter login page...")
            page.goto("https://twitter.com/i/flow/login", timeout=90000)

            # Log in to Twitter
            print("Entering username...")
            page.fill("input[name=\"text\"]", TWITTER_USERNAME)
            page.press("input[name=\"text\"]", "Enter")
            time.sleep(2)

            # Handle additional username input if required
            try:
                page.fill("input[name=\"text\"]", TWITTER_NAME)
                page.press("input[name=\"text\"]", "Enter")
                time.sleep(2)
                print("Additional username input handled.")
            except Exception:
                print("No additional username input required.")

            print("Entering password...")
            page.fill("input[name=\"password\"]", TWITTER_PASSWORD)
            page.press("input[name=\"password\"]", "Enter")

            try:
                page.fill("input[name=\"text\"]", TWITTER_USERNAME)
                page.press("input[name=\"text\"]", "Enter")
                time.sleep(2)
                print("Additional email input handled.")
            except Exception:
                print("No additional email input required.")

            print("Login successful!")

            # Wait for the home page to load
            print("Waiting for home page to load...")
            try:
                page.wait_for_selector('xpath=//a[contains(@href, "/home")]', timeout=120000)
                print("Home page loaded successfully!")
            except Exception as e:
                print(f"Error during waiting for selector: {e}")
                with open("debug_page.html", "w") as file:
                    file.write(page.content())
                raise

            # Debug: Capture screenshot and HTML
            page.screenshot(path="debug_screenshot.png")
            html_content = page.content()
            with open("debug_page.html", "w") as file:
                file.write(html_content)

            print("Extracting individual trends...")
            trends = {}
            try:
                trends["trend1"] = page.locator(
                    'xpath=/html/body/div[1]/div/div/div[2]/main/div/div/div/div[2]/div/div[2]/div/div/div/div[4]/section/div/div/div[3]/div/div/div/div[2]'
                ).inner_text()
            except Exception:
                trends["trend1"] = "Error fetching trend1"
            
            try:
                trends["trend2"] = page.locator(
                    'xpath=/html/body/div[1]/div/div/div[2]/main/div/div/div/div[2]/div/div[2]/div/div/div/div[4]/section/div/div/div[4]/div/div/div/div[2]'
                ).inner_text()
            except Exception:
                trends["trend2"] = "Error fetching trend2"
            
            try:
                trends["trend3"] = page.locator(
                    'xpath=/html/body/div[1]/div/div/div[2]/main/div/div/div/div[2]/div/div[2]/div/div/div/div[4]/section/div/div/div[5]/div/div/div/div[2]'
                ).inner_text()
            except Exception:
                trends["trend3"] = "Error fetching trend3"
            
            try:
                trends["trend4"] = page.locator(
                    'xpath=/html/body/div[1]/div/div/div[2]/main/div/div/div/div[2]/div/div[2]/div/div/div/div[4]/section/div/div/div[6]/div/div/div/div[2]'
                ).inner_text()
            except Exception:
                trends["trend4"] = "Error fetching trend4"
            
            print(f"Extracted trends: {trends}")

            # Close the browser
            browser.close()
            return trends

    except Exception as e:
        print(f"Error during scraping: {e}")
        return []

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
            response = requests.get(proxy_url, timeout=10)
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
