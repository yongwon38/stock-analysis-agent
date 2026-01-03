# Stock Analysis Agent (Predictive Income Generator)

**Live Demo:** [https://predictive-income-generator.vercel.app/](https://predictive-income-generator.vercel.app/)

## Project Overview
This project is an **AI-powered Stock Analysis Agent** designed to automate the collection and analysis of stock market data. It serves as a personal investment assistant, providing daily insights into your favorite US and Korean stocks without manual research.

## Key Features

### 🤖 AI-Driven Analysis
-   **Investment Recommendations**: Uses Google's **Gemini 2.0 Flash** model to analyze market data and generate "BUY", "SELL", or "HOLD" signals.
-   **Sentiment Analysis**: Scans recent news headlines to calculate a sentiment score (0-100), giving you a quick sense of market mood.
-   **Detailed Summaries**: Provides a markdown-formatted summary of the analysis, highlighting key factors and potential risks.

### 📊 Real-Time & Historical Data
-   **Market Data**: Integrates with standard finance APIs to fetch real-time prices, PE ratios, and EPS.
-   **Interactive Charts**: Visualizes 1-year price history with interactive tooltips for identifying trends.
-   **Multi-Market Support**: Seamlessly handles both US stocks (e.g., AAPL, TSLA) and Korean stocks (e.g., Samsung Electronics, NAVER).

### ⚡ Automated Workflows
-   **Daily Batch Processing**: Automatically runs a batch analysis job every day at 8:00 AM and 5:00 PM KST to ensure data is fresh before market open/close.
-   **Production Ready**: Deployed on Vercel with a robust Next.js frontend and server-side automation.

## Technology Stack
-   **Frontend**: Next.js (App Router), TailwindCSS for premium "Dark Mode" aesthetics.
-   **AI Core**: Google Gemini API (`gemini-2.0-flash`).
-   **Data Engine**: `yahoo-finance2` for market data fetching.
-   **Visualization**: `recharts` for dynamic stock charts.
-   **Scheduler**: `node-cron` for automated background tasks.

## Why This Project?
Investing requires constant vigilance. This agent removes the repetitive work of checking multiple sources by aggregating price, news, and AI insights into a single, clean dashboard. It allows users to make informed decisions faster by presenting complex data in a simple, digestible format.

---

*This project is for educational and informational purposes only. Always do your own research before investing.*
