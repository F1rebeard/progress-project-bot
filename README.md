# Progress Project Bot

A Telegram bot for tracking CrossFit workout progress, managing user profiles, and providing personalized workout plans.

## Features

- **User Registration**: Register and create a user profile with personal information
- **Profile Management**: Track and update your fitness profile
- **Workout Calendar**: View and plan workouts on a calendar
- **Workout of the Day**: Get daily workout suggestions
- **Exercise Tracking**: Record and track exercise results with various measurement units
- **Performance Standards**: Compare your results with standards based on user level and gender
- **Subscription Management**: Handle user subscriptions and payments with different plans (Standard, With Curator, Full Start Program, One Month Start) and statuses (Active, Frozen, Expired)
- **Personalized Workouts**: Get workouts tailored to your fitness level (First, Second, Minkaifa, Competition, Start)
- **Biometric Tracking**: Monitor your biometric data
- **Curator System**: Get guidance from fitness curators/coaches

## Tech Stack

- **Python 3.12+**
- **Telegram Bot API**: Using aiogram 3.17+ and aiogram-dialog 2.3+
- **Database**: PostgreSQL with SQLAlchemy ORM and Alembic for migrations
- **Containerization**: Docker and Docker Compose
- **Code Quality**: Ruff, isort, pre-commit hooks

## Installation

### Prerequisites

- Python 3.12 or higher
- Docker and Docker Compose
- PostgreSQL (or use the provided Docker setup)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/progress-project-bot.git
   cd progress-project-bot
   ```

2. Create a `.env` file in the project root with the following variables:
   ```
   DATABASE_URL=postgresql+asyncpg://admin:admin@localhost:5432/progress_db
   DEBUG=True
   ADMIN_IDS=[your_telegram_id]
   BOT_TOKEN=your_telegram_bot_token
   ```

3. Start the PostgreSQL database:
   ```bash
   docker-compose up -d
   ```

4. Install dependencies:
   ```bash
   pip install -e .
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Start the bot:
   ```bash
   python -m src.main
   ```

## Usage

1. Start a chat with your bot on Telegram
2. Use the `/progress` command to begin
3. Follow the registration process to set up your profile
4. Use the main menu to navigate between different features:
   - View your profile
   - Check the workout of the day
   - View your workout calendar
   - Record exercise results
   - Manage your subscription

## Project Structure

```
progress-project-bot/
├── src/
│   ├── bot/                  # Bot-related code
│   │   ├── handlers/         # Message and command handlers
│   │   └── keyboards/        # Telegram keyboard layouts
│   ├── constants/            # Application constants
│   ├── dao/                  # Data Access Objects
│   ├── database/             # Database configuration
│   │   ├── migrations/       # Alembic migrations
│   │   └── models/           # SQLAlchemy models
│   ├── middleware/           # Middleware components
│   ├── schemas/              # Pydantic schemas
│   ├── utils/                # Utility functions
│   ├── config.py             # Application configuration
│   ├── logger.py             # Logging setup
│   └── main.py               # Application entry point
├── tests/                    # Test directory
├── alembic.ini               # Alembic configuration
├── docker-compose.yaml       # Docker Compose configuration
├── pyproject.toml            # Project metadata and dependencies
└── README.md                 # Project documentation
```

## Development

### Setting Up Development Environment

1. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

2. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Running Tests

```bash
pytest
```

### Code Quality

The project uses:
- Ruff for linting and formatting
- isort for import sorting
- pre-commit hooks for automated checks

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
