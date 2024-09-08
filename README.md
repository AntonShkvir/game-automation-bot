# Game Automation Bot

## Description

Game Automation Bot is a Telegram bot designed to automate game sessions for earning coins in games like **MEMEFI** and **BLUM**. Users can submit their data, and the bot will create asynchronous sessions that automatically collect coins on their behalf. The bot also provides a user-friendly interface for managing and tracking these sessions.

## Key Features

- **Automated Sessions**: The bot creates and runs game sessions for users to earn cryptocurrency automatically.
- **Asynchronous Execution**: Game sessions run asynchronously, allowing multiple sessions to operate at once without delays.
- **User-Friendly Interface**: The bot provides a simple interface for users to start, stop, and manage their active game sessions.
- **Game Support**: Currently supports:
  - **MEMEFI**
  - **BLUM**

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/AntonShkvir/game-automation-bot.git
    ```

2. **Navigate to the project directory:**
    ```bash
    cd game-automation-bot
    ```

3. **Create a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
    ```

   Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5. **Set up the configuration:**
    In `config.py` file replace `"your_api_token"` with your actual Telegram bot API token:
    ```python
    API_TOKEN = "your_api_token"
    ```
   Ensure the token is correct, as it will be used to authenticate your bot.

6. **Run the bot:**
    ```bash
    python main.py
    ```

## Usage

1. **Submit Game Data**: Users submit the required game data for the bot to create a session.
2. **Start Session**: The bot will create an asynchronous session to collect coins for the user.
3. **Manage Sessions**: Users can stop, restart, or check the status of their sessions using the bot's interface.
