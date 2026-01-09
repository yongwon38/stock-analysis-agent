import { GoogleGenerativeAI } from '@google/generative-ai';

// Env Config
const GROQ_API_KEY = process.env.GROQ_API_KEY;
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;

// Export Helpers for debug page
export function getEffectiveGeminiKey() { return GEMINI_API_KEY; }
export function getEffectiveGroqKey() { return GROQ_API_KEY; }

// Initialize Gemini
const genAI = new GoogleGenerativeAI(GEMINI_API_KEY || "");

/**
 * Call Groq API (Primary)
 * Model: openai/gpt-oss-120b
 */
export async function callGroq(messages: any[]): Promise<string> {
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
            response_format: { type: "json_object" } // Force JSON
        })
    });

    if (!response.ok) {
        const err = await response.text();
        throw new Error(`Groq API Error: ${response.status} ${err}`);
    }

    const json = await response.json();
    return json.choices[0]?.message?.content || "";
}

/**
 * Call Gemini API (Fallback)
 * Model: gemini-2.0-flash-lite
 */
export async function callGemini(prompt: string): Promise<string> {
    const model = genAI.getGenerativeModel({
        model: "gemini-2.0-flash-lite",
        generationConfig: { responseMimeType: "application/json" } // Force JSON
    });

    try {
        const result = await model.generateContent(prompt);
        return (await result.response).text();
    } catch (e: any) {
        throw e;
    }
}

/**
 * Robust Provider Chain
 * Tries Groq -> Gemini -> throws Error
 */
export async function generateWithFallback(systemPrompt: string, userContent: string): Promise<any> {
    const messages = [
        { role: "system", content: systemPrompt },
        { role: "user", content: userContent }
    ];
    const fullPrompt = `${systemPrompt}\n\nUser Input:\n${userContent}`;

    try {
        const text = await callGroq(messages);
        return JSON.parse(text);
    } catch (groqE: any) {
        console.warn(`[Groq Fail] ${groqE.message}. Switching to Gemini...`);
        try {
            const text = await callGemini(fullPrompt);
            return JSON.parse(text);
        } catch (geminiE: any) {
            console.error(`[Gemini Fail] ${geminiE.message}`);
            throw new Error(`All AI Providers Failed`);
        }
    }
}
