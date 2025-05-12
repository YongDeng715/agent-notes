
# Weather MCP Example

This project demonstrates how to use MCP (Model Control Protocol) to create a weather service with both client and server components. The example includes two different weather service implementations and a client that can interact with either of them.

## Overview

The project consists of three main components:

1. **Weather Server (weather.py)**: A free weather service that uses the National Weather Service (NWS) API to query weather data for US locations.
2. **OpenWeather Server (open_weather.py)**: A weather service that uses the OpenWeather API to query weather data for any location worldwide.
3. **MCP Client (client.py)**: A client application that can connect to either weather server and make weather queries.

## Prerequisites

- Python 3.7+
- Required Python packages:
  ```bash
  pip install httpx mcp-server openai python-dotenv
  ```

## Configuration

### OpenWeather API (Optional)

If you want to use the OpenWeather service, you'll need to:
1. Sign up for an API key at [OpenWeather](https://openweathermap.org/api)
2. Replace `YOUR_API_KEY` in `open_weather.py` with your actual API key

### Client Configuration

The client can be configured in two ways:

1. **Environment Variables**:
   - Create a `.env` file with:
     ```toml
     OPENAI_API_KEY=your_api_key
     BASE_URL=your_base_url
     MODEL=your_model_name
     TEMPERATURE=0.7
     MAX_TOKENS=2048
     ```

2. **Direct Configuration**:
   - Modify the variables at the top of `client.py`:
     ```python
     OPENAI_API_KEY = "your_api_key"
     BASE_URL = "your_base_url"
     MODEL = "your_model_name"
     TEMPERATURE = 0.7
     MAX_TOKENS = 2048
     ```

## Usage

### Running the Weather Server

1. **Using the free NWS service (US only)**:
   ```bash
   python weather.py
   ```

2. **Using the OpenWeather service (worldwide)**:
   ```bash
   python open_weather.py
   ```

### Running the Client

To connect to a weather server:
```bash
python client.py <path_to_server_script>
```

For example:
```bash
python client.py weather.py
```

### Making Weather Queries

Once the client is connected, you can make weather queries in natural language. For example:

- "What's the weather in New York?"
- "Tell me the forecast for Los Angeles"
- "Is it raining in Chicago?"

## Key Features

### Weather Server (weather.py)
- Uses the free NWS API
- Limited to US locations
- Provides current weather alerts and forecasts
- No API key required

### OpenWeather Server (open_weather.py)
- Uses the OpenWeather API
- Supports worldwide locations
- Requires an API key
- Provides more detailed weather information

### MCP Client (client.py)
- Connects to either weather server
- Uses OpenAI/Qwen/Deepseek API for natural language processing
- Supports interactive chat interface
- Handles tool calls and responses automatically

## Response Format

Weather responses include:
- Temperature
- Humidity
- Wind speed
- Weather description
- Location information

## Error Handling

Both servers include error handling for:
- API connection issues
- Invalid locations
- Rate limiting
- Data parsing errors

## Example Output

```powershell
你: What's the weather in New York?

🤖 Qwen2.5-72B-Instruct: The current weather in New York is:
🌍 New York, US
🌡 Temperature: 20°C
💧 Humidity: 65%
🌬 Wind Speed: 3.5 m/s
🌤 Weather: Partly cloudy
```

## Notes

1. The free NWS service (weather.py) is limited to US locations only
2. The OpenWeather service requires an API key but supports worldwide locations
3. The client supports both English and Chinese queries
4. Weather data is cached to prevent excessive API calls
5. The client automatically handles rate limiting and retries

## Troubleshooting

1. If you get API key errors:
   - Check your API key configuration
   - Ensure the key has the correct permissions

2. If you get location errors:
   - For weather.py, ensure the location is in the US
   - For open_weather.py, use standard city names

3. If you get connection errors:
   - Check your internet connection
   - Verify the server is running
   - Check if the API endpoints are accessible