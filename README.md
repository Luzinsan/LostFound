# Lost&Found

**Lost&Found** is a Telegram-based travel discovery bot that leverages advanced natural language processing (NLP) and aggregated data from trusted sources like Google Places, Wikipedia, and OpenStreetMap to deliver personalized travel recommendations. Each recommendation is enriched with historical insights, cultural details, and media references, ensuring users receive a comprehensive and engaging travel planning experience.

## Overview

Travelers often struggle to find destinations that truly match their unique interests. Lost&Found addresses this challenge by combining user preferences with data-driven insights to offer tailored travel suggestions directly through Telegram. Whether you're seeking historic landmarks, scenic nature spots, or vibrant urban experiences, Lost&Found transforms travel planning into an informed and enjoyable journey.

## Key Features

- **Personalized Recommendations:**  
  Utilizes NLP and semantic search techniques to analyze user input and deliver destination suggestions that align with individual interests.
  
- **Data Aggregation:**  
  Integrates data from multiple reliable sources including Google Places, Wikipedia, and OpenStreetMap, ensuring accuracy and depth.
  
- **Enriched Content:**  
  Provides detailed information such as historical background, cultural context, and media references for each recommended location.
  
- **User-Friendly Interface:**  
  Operates seamlessly within Telegram, offering intuitive commands and a conversational interaction model.

## Technology Stack

- **Backend:**  
  Developed using FastAPI or Flask for robust API creation and efficient data handling.
  
- **Data Storage:**  
  Utilizes PostgreSQL for structured data and Elasticsearch for high-performance full-text search capabilities.
  
- **Natural Language Processing:**  
  Implements libraries like spaCy, Transformers, and models such as BERT or Sentence-BERT for sentiment analysis and semantic search.
  
- **Telegram Bot Framework:**  
  Built using python-telegram-bot or Aiogram, providing a reliable and interactive user interface.

## Installation and Setup

### Prerequisites
- Python 3.11 or higher
- MongoDB ([Download & Install](https://www.mongodb.com/try/download/community))
- Redis ([Windows Subsystem for Linux](https://redis.io/docs/getting-started/installation/install-redis-on-windows/) or [Windows](https://github.com/microsoftarchive/redis/releases))
- uv package manager (recommended) or pip

### Windows Installation Guide

1. **Install Python**
   - Download Python 3.11+ from [official website](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   - Verify installation: `python --version`

2. **Install MongoDB**
   - Download MongoDB Community Server from [MongoDB website](https://www.mongodb.com/try/download/community)
   - Follow the installation wizard
   - Add MongoDB to PATH if not done automatically:
     - Copy path (typically `C:\Program Files\MongoDB\Server\6.0\bin`)
     - Add to System Environment Variables
   - Create data directory: `mkdir C:\data\db`
   - Start MongoDB: `mongod`

3. **Install Redis**
   Option 1 (Recommended) - Using WSL2:
   ```powershell
   # Install WSL2
   wsl --install

   # After restart, install Redis in WSL
   wsl
   sudo apt update
   sudo apt install redis-server
   sudo service redis-server start
   ```

   Option 2 - Windows Native:
   - Download Redis for Windows from [Github](https://github.com/microsoftarchive/redis/releases)
   - Extract to `C:\Redis`
   - Start Redis: `C:\Redis\redis-server.exe`

4. **Setup Project**
   ```powershell
   # Clone repository
   git clone <repository-url>
   cd LostFound

   # Install uv (recommended package manager)
   pip install uv

   # Create and activate virtual environment
   uv venv
   .venv\Scripts\activate

   # Install dependencies
   uv pip install -r requirements.txt
   ```

5. **Configure Environment**
   Create `.env` file in project root:
   ```env
   GOOGLE_PLACES_API=your_google_places_api_key
   OPENTRIPMAP_API_KEY=your_opentripmap_api_key
   TELEGRAM_BOT_API=your_telegram_bot_api_key
   CITIES=["Moscow", "Saint Petersburg"]
   ```

### Running the Project

1. **Start Services**
   ```powershell
   # Start MongoDB (in new terminal)
   mongod

   # Start Redis (in new terminal)
   # If using WSL:
   wsl
   sudo service redis-server start
   # If using Windows Redis:
   C:\Redis\redis-server.exe
   ```

2. **Start Celery Workers**
   ```powershell
   # Activate virtual environment if not activated
   .venv\Scripts\activate

   # Start Celery worker
   uv run celery -A parsers.tasks worker --loglevel=info -E
   ```

3. **Run the Application**
   ```powershell
   # In new terminal with activated venv
   uv run main.py
   ```

### Troubleshooting

1. **Redis Connection Issues**
   - Ensure Redis is running: `redis-cli ping` should return "PONG"
   - Check Redis port (default 6379) is not blocked by firewall
   - If using WSL, ensure WSL service is running

2. **MongoDB Connection Issues**
   - Verify MongoDB is running: `mongosh`
   - Check if data directory exists and has correct permissions
   - Default port is 27017

3. **Celery Worker Issues**
   - Ensure Redis is running and accessible
   - Check Celery version compatibility with Python version
   - Try running with `--pool=solo` flag if getting worker errors

### Notes

- For production deployment, consider using Windows Services or similar for automatic service startup
- Keep your API keys secure and never commit them to version control
- Monitor the logs in `celery` and application output for potential issues
- Consider using MongoDB Compass for database visualization and management

For more detailed information about the components:
- [MongoDB Documentation](https://www.mongodb.com/docs/)
- [Redis Documentation](https://redis.io/docs)
- [Celery Documentation](https://docs.celeryq.dev/en/stable/index.html)
