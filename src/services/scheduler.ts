import cron from 'node-cron';
import { runBatchAnalysis } from './batch';

export function initScheduler() {
    // Run at 8:00 AM and 5:00 PM (Korea/Japan Time approx, assuming server is in KST or UTC adjusted)
    // 0 8,17 * * *
    const schedule = '0 8,17 * * *';

    console.log(`Initializing Scheduler... [${schedule}]`);

    cron.schedule(schedule, async () => {
        console.log("Running scheduled batch analysis...");
        await runBatchAnalysis();
    });
}
