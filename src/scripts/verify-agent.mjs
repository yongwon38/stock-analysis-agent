import dotenv from 'dotenv';
// Mock environment if needed, or rely on .env.local being loaded if I run with dotenv
// We will manually load env vars for the script
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

// Import provider directly (we can't import typescript modules easily in node script without ts-node)
// So we will just hit the API directly in this script to mock the agent behavior 
// OR we can try to use the compiled output if accessible. 
// Easier: Just Re-implement the key test here to verify the Model + Prompt combo works.

const GROQ_API_KEY = process.env.GROQ_API_KEY;

async function testAgent() {
    console.log("Testing Groq Multi-Agent Prompt...");
    if (!GROQ_API_KEY) {
        console.error("No GROQ_API_KEY found.");
        return;
    }

    const SYSTEM_PROMPT = `
당신은 주가 기술적 분석 전문가입니다. 
다음 데이터를 분석하여 JSON으로 출력하세요.
{ "score": number, "summary": "Korean text" }
    `;

    const USER_CONTEXT = JSON.stringify({
        symbol: "AAPL",
        price: 150,
        history: [140, 142, 145, 148, 150]
    });

    try {
        const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${GROQ_API_KEY}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                messages: [
                    { role: "system", content: SYSTEM_PROMPT },
                    { role: "user", content: USER_CONTEXT }
                ],
                model: "openai/gpt-oss-120b",
                temperature: 0.1,
                response_format: { type: "json_object" }
            })
        });

        if (!response.ok) {
            console.error("API Failed:", await response.text());
        } else {
            const json = await response.json();
            console.log("Success! Output:", json.choices[0].message.content);
        }
    } catch (e) {
        console.error("Error:", e);
    }
}

testAgent();
