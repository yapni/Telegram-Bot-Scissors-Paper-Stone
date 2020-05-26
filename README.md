# Telegram Bot: Scissors Paper Stone
A beginner's creation of a telegram bot that allows users to play a game of "Scissors, Paper, Stone".

This bot is currently deployed using Heroku's free plan. Add the bot to your telegram: https://t.me/letsPlaySPS_bot

The following describes how to run your own "Scissors, Paper, Stone" bot.

## Requirements

This bot uses [**python-telegram-bot**](https://github.com/python-telegram-bot/python-telegram-bot) (tested with version 12.7) as a Python interface for the [Telegram Bot API](https://core.telegram.org/bots/api).

## Installation

1. Clone this repository

2. Install dependencies: 

   ```shell
   $ pip install -r requirements.txt
   ```

## Usage

1. Register your bot and obtain an authorization token via [BotFather](https://core.telegram.org/bots/#6-botfather)

2. Set the environment variables required in your shell:
   - `TELEGRAM_SPS_BOT_TOKEN`: Authorization token obtained from BotFather.
   - `TELEGRAM_SPS_BOT_MODE`: Set to "dev" for development mode (running locally) or "prod" to production mode (Heroku deployment) .
   - `TELEGRAM_SPS_BOT_PORT` : Port number to listen for the web hook. Required if deployed in Heroku and running in production mode. Set to 8443 by default.
   - `TELEGRAM_SPS_BOT_HEROKU_NAME`: Heroku app name. Required if running in production mode.

3. Run the main script:

   ```shell
   $ python3 main.py
   ```

4. Add the bot to a Telegram group. Enter "/help" and follow the instructions given by the bot.