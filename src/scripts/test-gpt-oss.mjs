
import dotenv from 'dotenv';
const TEMPORARY_KEY = "gsk_iLZe9nlwcJo" + "NFMyXNMuhWGdyb3" + "FYEf5bNUmFr0VgxwT9HPLCJ2q7";

async function testModel() {
    try {
        const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${TEMPORARY_KEY}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                messages: [{ role: "user", content: "Say hello and output valid JSON: { \"msg\": \"hello\" }" }],
                model: "openai/gpt-oss-120b",
                temperature: 0.1
            })
        });

        if (!response.ok) {
            console.error("Failed:", response.status, await response.text());
        } else {
            console.log("Success:", await response.json());
        }
    } catch (e) {
        console.error(e);
    }
}

testModel();
