from flask import Flask, jsonify, render_template
from pymongo import MongoClient
import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from selenium.webdriver.chrome.options import Options
import os
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from dotenv import load_dotenv

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

# Configure Selenium with a ScraperAPI proxy
def get_driver_with_proxy():
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--no-sandbox')  # Ensures sandboxing does not interfere
    chrome_options.add_argument('--disable-gpu')  # Necessary for headless mode
    chrome_options.add_argument('--disable-dev-shm-usage')  # Resolves issues with resource limits in cloud
    chrome_options.add_argument(f'--proxy-server={proxy_url}')
    chrome_options.add_argument('--disable-extensions')  # Disable extensions to save memory
    chrome_options.add_argument('--disable-software-rasterizer')  # Disable software rasterizer

    # Use the default Chromium path in the Docker image
    chrome_options.binary_location = "/usr/bin/chromium"

    # Use webdriver_manager to install the correct version of ChromeDriver
    chromedriver_path = "/usr/bin/chromedriver"

    # Create the Service object
    service = Service(chromedriver_path)

    # Initialize the WebDriver with the service and options
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run-scraper", methods=["GET"])
def run_scraper():
    try:
        # Capture start time
        start_time = datetime.datetime.now()
        print(f"Script started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Initialize the WebDriver with the proxy configuration
        driver = get_driver_with_proxy()
        driver.get("https://twitter.com/i/flow/login")

        # Log in to Twitter
        username_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "text"))
        )
        username_field.send_keys(TWITTER_USERNAME)
        username_field.send_keys(Keys.RETURN)

        time.sleep(2)  # Reduced sleep time to save memory

        # Handle username field if it asks for additional input
        try:
            username_field = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
            username_field.send_keys(TWITTER_NAME)
            username_field.send_keys(Keys.RETURN)
        except Exception as e:
            print("No username input required")

        # Enter the password
        password_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_field.send_keys(TWITTER_PASSWORD)
        password_field.send_keys(Keys.RETURN)

        # Wait for the home page to load
        WebDriverWait(driver, 20).until(
            EC.url_contains('home')
        )
        print("Login successful!")

        # Extract trends
        trends = []
        trend_xpath = [
            '/html/body/div[1]/div/div/div[2]/main/div/div/div/div[2]/div/div[2]/div/div/div/div[4]/section/div/div/div[3]/div/div/div/div[2]',
            '/html/body/div[1]/div/div/div[2]/main/div/div/div/div[2]/div/div[2]/div/div/div/div[4]/section/div/div/div[4]/div/div/div/div[2]',
            '/html/body/div[1]/div/div/div[2]/main/div/div/div/div[2]/div/div[2]/div/div/div/div[4]/section/div/div/div[5]/div/div/div/div[2]',
            '/html/body/div[1]/div/div/div[2]/main/div/div/div/div[2]/div/div[2]/div/div/div/div[4]/section/div/div/div[6]/div/div/div/div[2]'
        ]

        for xpath in trend_xpath:
            trend = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            ).text
            trends.append(trend)

        # Log the trends
        print(f"Trends: {trends}")

        # Retrieve IP address used via ScraperAPI
        ip_address = "Unknown"
        try:
            response = requests.get(proxy_url)
            # Log the raw response content for debugging
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

        driver.quit()

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
