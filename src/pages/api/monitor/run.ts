import type { APIRoute } from 'astro';
import { runCycle } from '../../../server/monitoring/worker';
export const POST: APIRoute = async () => Response.json({ checks: (await runCycle()).length });
