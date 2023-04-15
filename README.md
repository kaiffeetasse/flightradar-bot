# Flight Radar Bot 
This is a Telegram bot that uses the FlightRadar24 API to track flights in a given area and notify users when a new flight appears in their area of interest. 

## Features 
* Set your location by sending your current location via Telegram and the bot will set your radius of interest to 5km by default 
* The bot will scan for new flights within the given radius every 5 seconds and notify you if a new flight appears in your area of interest 
* You can view information about each flight such as aircraft type, altitude, speed, origin airport, and destination airport 
* You can view a map of your location with the size of the radius of interest
  
## Requirements 
* Python 3+ 
* Telegram API key  
* MySQL database
  
## Usage 
1. Install the necessary dependencies: `pip install -r requirements.txt` 
2. Set up environment variables in your .env file for Telegram API key and MySQL credentials in .env file (see example.env for reference)  
3. Run `python main.py` to start the bot

## Commands
* `/start` - Start the bot
* `/stop` - Stop the bot
* `/radius` - Set the radius of interest in kilometers