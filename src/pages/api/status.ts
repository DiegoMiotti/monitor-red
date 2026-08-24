import type { APIRoute } from 'astro';
import { latestChecks } from '../../server/repositories/checks';
export const GET: APIRoute = async () => Response.json({ devices: await latestChecks(), updatedAt: new Date().toISOString() });
