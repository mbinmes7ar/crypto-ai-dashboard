import streamlit as st
import requests
import os
from datetime import datetime
from anthropic import Anthropic

# Page config
st.set_page_config(
    page_title="Crypto AI Dashboard",
    page_icon="🤖",
    layout="wide"
)

# Title
st.title("🤖 Crypto AI Briefing Dashboard")
st.caption(f"Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")

# Update button
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("🔄 Update Now", use_container_width=True):
        st.rerun()

# Get API keys from secrets
try:
    COINGECKO_KEY = st.secrets["COINGECKO_API_KEY"]
    CRYPTOPANIC_KEY = st.secrets["CRYPTOPANIC_API_KEY"]
    ANTHROPIC_KEY = st.secrets["ANTHROPIC_API_KEY"]
except:
    st.error("⚠️ API keys not configured. Go to Settings → Secrets to add your keys.")
    st.stop()

# Function to get crypto prices
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_crypto_prices():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum",
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        headers = {"x-cg-demo-api-key": COINGECKO_KEY}
        response = requests.get(url, params=params, headers=headers)
        return response.json()
    except Exception as e:
        st.error(f"Error fetching prices: {e}")
        return None

# Function to get crypto news
@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_crypto_news():
    try:
        url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_KEY}&public=true"
        response = requests.get(url)
        data = response.json()
        return data.get('results', [])[:5]  # Get top 5 news
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return []

# Function to get AI analysis
def get_ai_analysis(price_data, news_data):
    try:
        client = Anthropic(api_key=ANTHROPIC_KEY)
        
        prompt = f"""Analyze this cryptocurrency market data and provide a brief summary:

Price Data:
- Bitcoin: ${price_data['bitcoin']['usd']:,.2f} (24h change: {price_data['bitcoin']['usd_24h_change']:.2f}%)
- Ethereum: ${price_data['ethereum']['usd']:,.2f} (24h change: {price_data['ethereum']['usd_24h_change']:.2f}%)

Recent News Headlines:
{chr(10).join([f"- {news['title']}" for news in news_data[:3]])}

Provide a concise analysis in 3-4 sentences covering:
1. Key market movements
2. Notable trends
3. What to watch for

Be objective and data-driven."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text
    except Exception as e:
        return f"Unable to generate AI analysis: {e}"

# Get data
with st.spinner("Fetching latest data..."):
    prices = get_crypto_prices()
    news = get_crypto_news()

if prices:
    # Price cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        btc_change = prices['bitcoin']['usd_24h_change']
        st.metric(
            "Bitcoin (BTC)",
            f"${prices['bitcoin']['usd']:,.0f}",
            f"{btc_change:.2f}%",
            delta_color="normal"
        )
    
    with col2:
        eth_change = prices['ethereum']['usd_24h_change']
        st.metric(
            "Ethereum (ETH)",
            f"${prices['ethereum']['usd']:,.0f}",
            f"{eth_change:.2f}%",
            delta_color="normal"
        )
    
    with col3:
        # Calculate simple market sentiment
        avg_change = (btc_change + eth_change) / 2
        if avg_change > 2:
            sentiment = "Greed 😎"
        elif avg_change > 0:
            sentiment = "Optimistic 🙂"
        elif avg_change > -2:
            sentiment = "Cautious 😐"
        else:
            sentiment = "Fear 😰"
        
        st.metric("Market Sentiment", sentiment, f"{avg_change:.2f}%")
    
    # AI Analysis Section
    st.markdown("---")
    st.subheader("🧠 AI Market Analysis")
    
    with st.spinner("Generating AI analysis..."):
        analysis = get_ai_analysis(prices, news)
        st.write(analysis)
    
    # News Section
    st.markdown("---")
    st.subheader("📰 Latest Crypto News")
    
    if news:
        for item in news:
            with st.container():
                st.markdown(f"**{item['title']}**")
                st.caption(f"{item['source']['title']} • {item['published_at']}")
                st.markdown("---")
    else:
        st.info("No news available at the moment.")

else:
    st.error("Unable to fetch cryptocurrency data. Please check your API keys.")

# Footer
st.markdown("---")
st.caption("Data provided by CoinGecko • News from CryptoPanic • AI Analysis by Claude")