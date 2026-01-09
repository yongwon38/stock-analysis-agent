import fs from 'fs';
import path from 'path';

// Manual Env Load
const envPath = path.resolve(process.cwd(), '.env.local');
if (fs.existsSync(envPath)) {
    const envConfig = fs.readFileSync(envPath, 'utf8');
    envConfig.split('\n').forEach(line => {
        const [key, value] = line.split('=');
        if (key && value) process.env[key.trim()] = value.trim();
    });
}

const GROQ_API_KEY = process.env.GROQ_API_KEY;

async function callGroq(messages) {
    if (!GROQ_API_KEY) throw new Error("GROQ_API_KEY not configured");

    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${GROQ_API_KEY}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            messages: messages,
            model: "openai/gpt-oss-120b",
            temperature: 0.1,
            response_format: { type: "json_object" }
        })
    });

    if (!response.ok) {
        const err = await response.text();
        throw new Error(`Groq API Error: ${response.status} ${err}`);
    }

    const json = await response.json();
    return json.choices[0]?.message?.content || "";
}

async function runTest() {
    console.log("Starting Multi-Agent Debug...");
    const dummyContext = JSON.stringify({ symbol: "AAPL", price: 150 });

    // Real Prompt Snippet
    const PRICE_AGENT_SYSTEM = `
당신은 주가 기술적 분석 전문가입니다.
제공된 주가 데이터를 분석하여 JSON 형식으로 출력하세요.
모든 텍스트는 한국어로 작성하세요.

## 분석 항목
1. 추세 분석 (단기/중기, 이평선)
2. 기술적 지표 (RSI, 모멘텀)
3. 지지/저항 라인
4. 변동성 평가

## 출력 형식 (JSON)
{
  "current_price": number,
  "trend": {
    "short_term": "상승/하락/횡보",
    "medium_term": "상승/하락/횡보",
    "trend_strength": "강함/보통/약함"
  },
  "technical_indicators": {
    "rsi": number,
    "rsi_signal": "과매수/중립/과매도",
    "macd_signal": "매수/중립/매도"
  },
  "support_resistance": {
    "support_levels": [number],
    "resistance_levels": [number]
  },
  "volatility": "높음/보통/낮음",
  "technical_score": number (1-10),
  "summary": "기술적 분석 요약 (2-3문장)"
}
`;

    try {
        console.time("Parallel");
        // Simulate 4 agents in parallel with REAL prompts
        await Promise.all([
            callGroq([{ role: "system", content: PRICE_AGENT_SYSTEM }, { role: "user", content: dummyContext }]),
            callGroq([{ role: "system", content: PRICE_AGENT_SYSTEM }, { role: "user", content: dummyContext }]),
            callGroq([{ role: "system", content: PRICE_AGENT_SYSTEM }, { role: "user", content: dummyContext }]),
            callGroq([{ role: "system", content: PRICE_AGENT_SYSTEM }, { role: "user", content: dummyContext }])
        ]);
        console.timeEnd("Parallel");
        console.log("Parallel Success!");
    } catch (e) {
        console.timeEnd("Parallel");
        console.error("Parallel Failed:", e.message);
    }

    try {
        console.time("CheckJSON");
        const raw = await callGroq([{ role: "system", content: PRICE_AGENT_SYSTEM }, { role: "user", content: dummyContext }]);
        console.timeEnd("CheckJSON");
        console.log("RAW OUTPUT:", raw);

        try {
            const parsed = JSON.parse(raw);
            console.log("JSON Parse Success!", parsed);
        } catch (e) {
            console.error("JSON PARSE FAILED:", e.message);
        }

    } catch (e) {
        console.error("Groq Call Failed:", e.message);
    }
}

runTest();
