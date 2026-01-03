import { GoogleGenerativeAI } from '@google/generative-ai';
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

const apiKey = process.env.GEMINI_API_KEY;
const genAI = new GoogleGenerativeAI(apiKey || "");

const candidates = [
    "gemini-2.0-flash",
    "models/gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "models/gemini-2.0-flash-exp"
];

async function test() {
    for (const modelName of candidates) {
        console.log(`\nTesting model: ${modelName}...`);
        try {
            const model = genAI.getGenerativeModel({ model: modelName });
            const result = await model.generateContent("Say hello");
            console.log(`SUCCESS [${modelName}]:`, (await result.response).text());
            return;
        } catch (error) {
            console.log(`FAILED [${modelName}]:`, error.message ? error.message.split('\n')[0] : error);
        }
    }
}

test();
