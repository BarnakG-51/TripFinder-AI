# Trip Planner AI - Configuration Guide

## API Keys Setup

This app uses **Streamlit Secrets** to manage API keys securely.

### Quick Setup

1. **Copy the template:**
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

2. **Edit `.streamlit/secrets.toml` with your actual API keys:**
   ```toml
   TAVILY_API_KEY = "your_tavily_key_here"
   GOOGLE_MAPS_API_KEY = "your_google_maps_key_here"
   GROQ_API_KEY = "your_groq_key_here"
   ```

3. **Test your configuration:**
   ```bash
   python test_env.py
   ```

4. **Run the app:**
   ```bash
   ./run_app.sh
   ```

### Required API Keys

| Key | Service | Get It From |
|-----|---------|-------------|
| `TAVILY_API_KEY` | Web Search | https://tavily.com |
| `GOOGLE_MAPS_API_KEY` | Maps & Distance | https://console.cloud.google.com/apis/credentials |
| `GROQ_API_KEY` | LLM Planning | https://console.groq.com/keys |

### Security Notes

- ✅ `.streamlit/secrets.toml` is gitignored and won't be committed
- ✅ API keys are loaded only when the app starts
- ✅ Use `.streamlit/secrets.toml.example` as a template for new setups
- ❌ Never commit your actual `secrets.toml` file to git

### Troubleshooting

**"Missing API key" error:**
- Make sure `.streamlit/secrets.toml` exists
- Check that all three keys are present and have actual values (not placeholders)
- Run `python test_env.py` to verify

**Import errors:**
- Make sure you're using the virtual environment: `./run_app.sh`
- Install dependencies: `env/bin/python -m pip install -r requirements.txt`

---

## Migration from .env (Legacy)

If you were using `.env` files before, your API keys are now managed through **Streamlit Secrets**:

- **Old:** `.env` file in project root
- **New:** `.streamlit/secrets.toml` file

The functionality is the same, but Streamlit Secrets is the recommended approach for Streamlit apps.
