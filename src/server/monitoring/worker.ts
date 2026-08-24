import { database } from '../db';
import { loadInventory } from './inventory';
import { ping } from './ping';
import { processAlerts } from './alerts';

async function runCycle() {
  const devices = await loadInventory();
  const results = await Promise.all(devices.map(ping));
  const db = await database();
  await Promise.all([db.collection('checks').createIndex({ ip: 1, checkedAt: -1 }), db.collection('checks').createIndex({ checkedAt: -1 }), db.collection('active_alerts').createIndex({ target: 1 }, { unique: true })]);
  await db.collection('checks').insertMany(results);
  const retention = Number(process.env.RETENTION_DAYS ?? 30);
  await db.collection('checks').deleteMany({ checkedAt: { $lt: new Date(Date.now() - retention * 86_400_000) } });
  await processAlerts(results);
  console.info(`[${new Date().toISOString()}] UP ${results.filter((item) => item.status === 'UP').length} / DOWN ${results.filter((item) => item.status === 'DOWN').length}`);
  return results;
}

export { runCycle };

if (process.argv[1]?.endsWith('worker.ts') || process.argv[1]?.endsWith('worker.js')) {
  await runCycle();
  setInterval(() => void runCycle().catch(console.error), Number(process.env.MONITOR_INTERVAL_MS ?? 60_000));
}
