import fs from 'fs';
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

const apiKey = process.env.GEMINI_API_KEY;
const baseUrl = `https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`;

async function listAllModels() {
    let url = baseUrl;
    let allModels = [];

    try {
        while (url) {
            console.log("Fetching: " + url); // Debug url
            const response = await fetch(url);
            const data = await response.json();

            if (data.models) {
                allModels = allModels.concat(data.models);
            }

            if (data.nextPageToken) {
                url = `${baseUrl}&pageToken=${data.nextPageToken}`;
            } else {
                url = null;
            }
        }

        const modelNames = allModels
            .filter(m => m.supportedGenerationMethods && m.supportedGenerationMethods.includes('generateContent'))
            .map(m => m.name);

        fs.writeFileSync('available_models.txt', modelNames.join('\n'));
        console.log(`Saved ${modelNames.length} models to available_models.txt`);

    } catch (error) {
        console.error("Error listing models:", error);
    }
}

listAllModels();
