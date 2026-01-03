import cron from 'node-cron';
import { runBatchAnalysis } from './batch';

export function initScheduler() {
    // Run at 5:00 PM (Korea Time)
    // 0 17 * * *
    const schedule = '0 17 * * *';

    console.log(`Initializing Scheduler... [${schedule}]`);

    cron.schedule(schedule, async () => {
        console.log("Running scheduled batch analysis...");
        await runBatchAnalysis();
    });
}
