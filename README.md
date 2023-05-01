# Flight Radar Bot

This is a Telegram bot that uses the FlightRadar24 API to track flights in a given area and notify users when a new
flight appears in their area of interest. You can use this bot by adding [@flights_24_bot](https://t.me/flights_24_bot)
to your Telegram chat or host it yourself.

## Features

* Set your location by sending your current location via Telegram and the bot will set your radius of interest to 5km by
  default
* The bot will scan for new flights within the given radius every 5 seconds and notify you if a new flight appears in
  your area of interest
* You can view information about each flight such as aircraft type, altitude, speed, origin airport, and destination
  airport
* You can view a map of your location with the size of the radius of interest

## Requirements

* Python 3+
* Telegram API key
* MySQL database

## Usage

0. Set up environment variables in your .env file for Telegram API key and MySQL credentials in .env file (see
   example.env for reference)

### Docker

You can run the bot using Docker. The Dockerfile is set up to use the environment variables in the .env file.

1. Build the image: `docker build -t flight-radar-bot .`
2. Run the container: `docker run -d --name flight-radar-bot flight-radar-bot`

### Docker Compose

You can also run the bot using Docker Compose. The Dockerfile is set up to use the environment variables in the .env
file.

1. Run `docker-compose up -d`

### Local

1. Install the necessary dependencies: `pip install -r requirements.txt`
2. Run `python main.py` to start the bot

## Commands

* `/start` - Start the bot
* `/stop` - Stop the bot
* `/radius` - Set the radius of interest in kilometers
* `/altitude` - Set the altitude bounds for aircraft detection
* `/altmin` - Set the min altitude for aircraft detection
* `/altmax` - Set the max altitude for aircraft detection
* `/track` - Track aircraft by aircraft registration

## Credits

Thanks to [FlightRadar24](https://www.flightradar24.com/) for providing the API and komoot for
the [static map library](https://github.com/komoot/staticmap).