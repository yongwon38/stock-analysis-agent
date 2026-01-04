import { GoogleGenerativeAI } from '@google/generative-ai';
import { getEffectiveGeminiKey, getEffectiveGroqKey } from '@/lib/ai';

export const dynamic = 'force-dynamic';

export default async function DebugPage() {
    const geminiKey = getEffectiveGeminiKey();
    const groqKey = getEffectiveGroqKey();

    let geminiStatus = "Checking...";
    let groqStatus = "Checking...";

    // Test Gemini
    try {
        if (!geminiKey) throw new Error("Key Missing");
        const genAI = new GoogleGenerativeAI(geminiKey);
        const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });
        await model.generateContent("Test");
        geminiStatus = "OK (Connected)";
    } catch (e: any) {
        geminiStatus = `FAILED: ${e.message}`;
    }

    // Test Groq
    try {
        if (!groqKey) throw new Error("Key Missing");
        const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${groqKey}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                messages: [{ role: "user", content: "Test" }],
                model: "llama-3.3-70b-versatile",
                max_tokens: 1
            })
        });
        if (response.ok) {
            groqStatus = "OK (Connected)";
        } else {
            groqStatus = `FAILED: ${response.status} ${await response.text()}`;
        }
    } catch (e: any) {
        groqStatus = `FAILED: ${e.message}`;
    }

    return (
        <div className="min-h-screen bg-black text-green-400 p-8 font-mono">
            <h1 className="text-2xl font-bold mb-8 border-b border-green-800 pb-2">System Diagnostics</h1>

            <div className="grid gap-6">
                <div className="border border-green-800 p-4 rounded">
                    <h2 className="text-xl mb-4 text-white">Environment Variables</h2>
                    <ul className="space-y-2">
                        <li>
                            GEMINI_API_KEY: <span className={geminiKey ? "text-green-500" : "text-red-500"}>{geminiKey ? `Present (${geminiKey.substring(0, 4)}...)` : "MISSING"}</span>
                        </li>
                        <li>
                            GROQ_API_KEY: <span className={groqKey ? "text-green-500" : "text-red-500"}>{groqKey ? `Present (${groqKey.substring(0, 4)}...)` : "MISSING"}</span>
                        </li>
                    </ul>
                </div>

                <div className="border border-green-800 p-4 rounded">
                    <h2 className="text-xl mb-4 text-white">Connectivity Test</h2>
                    <ul className="space-y-2">
                        <li>Gemini Test: <span className={geminiStatus.includes("OK") ? "text-green-500" : "text-red-500"}>{geminiStatus}</span></li>
                        <li>Groq Test: <span className={groqStatus.includes("OK") ? "text-green-500" : "text-red-500"}>{groqStatus}</span></li>
                    </ul>
                </div>

                <div className="border border-green-800 p-4 rounded text-xs text-slate-500">
                    <p>Current Time: {new Date().toISOString()}</p>
                    <p>Node Env: {process.env.NODE_ENV}</p>
                    <p>Vercel Env: {process.env.VERCEL_ENV || 'Unknown'}</p>
                </div>

                <div className="mt-4 p-4 border border-yellow-900/50 text-yellow-600 rounded text-sm">
                    <h3 className="font-bold mb-2 text-yellow-500">Why are keys MISSING?</h3>
                    <ul className="list-disc list-inside space-y-1">
                        <li>Vercel variables are <strong>snapshot</strong> at build time.</li>
                        <li>If you added keys <em>after</em> the last deployment, they are not visible yet.</li>
                        <li><strong>Solution:</strong> This page update triggered a new build. If you still see MISSING, double-check that the keys are in the <strong>Production</strong> environment settings in Vercel.</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}
