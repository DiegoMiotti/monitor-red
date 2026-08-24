import { database } from '../db';
import type { Check } from '../monitoring/types';

export async function latestChecks(): Promise<Check[]> {
  const db = await database();
  return db.collection<Check>('checks').aggregate<Check>([
    { $sort: { checkedAt: -1 } },
    { $group: { _id: '$ip', check: { $first: '$$ROOT' } } },
    { $replaceRoot: { newRoot: '$check' } },
    { $sort: { base: 1, type: 1 } },
  ]).toArray();
}

export async function checkHistory(ip: string, hours: number) {
  const db = await database();
  return db.collection<Check>('checks').find({ ip, checkedAt: { $gte: new Date(Date.now() - hours * 3_600_000) } }, { projection: { checkedAt: 1, latencyMs: 1, status: 1 } }).sort({ checkedAt: 1 }).toArray();
}
