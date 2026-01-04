export async function register() {
    // Batch scheduler disabled per user request for full real-time architecture
    // if (process.env.NEXT_RUNTIME === 'nodejs') {
    //     const { initScheduler } = await import('@/services/scheduler');
    //     initScheduler();
    // }
}
