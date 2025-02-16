# Yahoo Auction Discord Bot

This project is a Discord bot designed to monitor Yahoo Auctions and alert users on a Discord server about new listings. The bot uses Hikari for Discord interactions and includes features for translating Japanese listings to make them more accessible to international users.

## Features

- Monitor Yahoo Auctions for new listings
- Automatic translation of Japanese listings
- Discord notifications for new items
- Configurable check intervals
- SQLite database for storing alerts and tracking listings

## Installation

Before you start the installation process, ensure you have Python 3.8 or above installed on your system. You can download Python from [here](https://www.python.org/downloads/).

Follow these steps to install the project:

1. Clone this repository to your local machine:

```bash
git clone https://github.com/annaelmoussa/yahoo-auction-alert-discord-bot.git
```

2. Navigate to the project directory:

```bash
cd yahoo-auction-alert-discord-bot
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Dependencies

The project uses several key Python packages:

- hikari & hikari-lightbulb: For Discord bot functionality
- beautifulsoup4: For web scraping
- dataset: For database operations
- easygoogletranslate: For translation services
- python-dotenv: For environment variable management
- requests: For HTTP requests
- SQLAlchemy: For database ORM

## Setting Up the Environment Variables

Create a `.env` file in the root directory of the project with the following variables:

```bash
BOT_TOKEN=your-discord-token
CHECK_INTERVAL=60
ENABLE_GET_AUCTION=true
```

- `BOT_TOKEN`: Your Discord bot token (required)
- `CHECK_INTERVAL`: Time in seconds between auction checks (default: 60)
- `ENABLE_GET_AUCTION`: Enable/disable the auction monitoring feature (default: true)

## Running the Bot

Start the bot by running:

```bash
python main.py
```

The bot will begin monitoring auctions and sending notifications to your configured Discord channel.

## Project Structure

- `main.py`: Main bot implementation and Discord commands
- `get.py`: Yahoo Auction interaction and monitoring logic
- `alerts.db`: SQLite database for storing alerts and tracking listings
- `.env`: Configuration file for bot settings

## Important Notes

1. This bot relies on web scraping to fetch auction data. Changes to the auction site's structure may affect functionality.
2. Translation services are provided through the easygoogletranslate package, which may have rate limits or occasional instability.
3. Keep your Discord token secure and never share it publicly.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

If you encounter any issues or have questions, please open an issue on this GitHub repository. We will try our best to assist you.

This readme was written (mostly) by ChatGPT because I'm lazy.
