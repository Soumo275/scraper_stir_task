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
from dotenv import load_dotenv
import os

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
    chrome_options.add_argument(f'--proxy-server={proxy_url}')  # ScraperAPI as the proxy server
    driver = webdriver.Chrome(options=chrome_options)
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
        
        driver = get_driver_with_proxy()
        driver.maximize_window()
        driver.get("https://twitter.com/i/flow/login")

        # Log in
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "text"))
        )
        username_field.send_keys(TWITTER_USERNAME)
        username_field.send_keys(Keys.RETURN)

        extra_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "text"))
        )
        extra_field.send_keys(TWITTER_NAME)
        extra_field.send_keys(Keys.RETURN)

        password_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_field.send_keys(TWITTER_PASSWORD)
        password_field.send_keys(Keys.RETURN)

        WebDriverWait(driver, 20).until(
            EC.url_contains('home')
        )
        print("Login successful!")

        # Extract trends
        trends = []
        for i in range(1, 5):
            trend = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, f'/html/body/div[1]/div/div/div[2]/main/div/div/div/div[2]/div/div[2]/div/div/div/div[4]/section/div/div/div[{i + 2}]/div/div/div/div[2]')
                )
            ).text
            trends.append(trend)

        print("Trends:", trends)

        # Retrieve IP address used via ScraperAPI
        response = requests.get(proxy_url)
        ip_address = response.json().get('origin', 'Unknown') if response.status_code == 200 else "Unknown"
        print("IP address used by ScraperAPI:", ip_address)

        # Capture end time
        end_time = datetime.datetime.now()
        print(f"Script ended at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Save data to MongoDB
        document = {
            "trend1": trends[0],
            "trend2": trends[1],
            "trend3": trends[2],
            "trend4": trends[3],
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
            "trend1": latest_entry.get("trend1", "N/A"),
            "trend2": latest_entry.get("trend2", "N/A"),
            "trend3": latest_entry.get("trend3", "N/A"),
            "trend4": latest_entry.get("trend4", "N/A"),
            "start_time": latest_entry.get("start_time", "N/A"),
            "end_time": latest_entry.get("end_time", "N/A"),
            "ip_address": latest_entry.get("ip_address", "N/A"),
        }
        return jsonify(response_data)
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
