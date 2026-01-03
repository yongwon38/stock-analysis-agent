import fs from 'fs/promises';
import path from 'path';
import { AnalysisResult } from './gemini';
import { StockData } from './finance';

const DATA_DIR = path.join(process.cwd(), 'data');
export const DATA_FILE = path.join(DATA_DIR, 'analysis_results.json');

export interface StoredData {
    lastUpdated: string;
    results: {
        stock: StockData;
        analysis: AnalysisResult;
    }[];
}

export async function saveAnalysisResults(data: StoredData) {
    try {
        await fs.mkdir(DATA_DIR, { recursive: true });
        await fs.writeFile(DATA_FILE, JSON.stringify(data, null, 2));
    } catch (error) {
        console.error("Failed to save analysis results:", error);
    }
}

export async function getAnalysisResults(): Promise<StoredData | null> {
    try {
        const content = await fs.readFile(DATA_FILE, 'utf-8');
        return JSON.parse(content);
    } catch (error) {
        return null;
    }
}
