import { NextResponse } from 'next/server';
import { runBatchAnalysis } from '@/services/batch';

export async function GET() {
    try {
        const data = await runBatchAnalysis();
        return NextResponse.json({ success: true, data });
    } catch (error) {
        return NextResponse.json({ success: false, error: 'Failed to run analysis' }, { status: 500 });
    }
}
