import type { APIRoute } from 'astro';
import { latestChecks } from '../../server/repositories/checks';
export const GET: APIRoute = async () => {
  const checks = await latestChecks();
  const up = checks.filter((check) => check.status === 'UP').length;
  const grouped = checks.reduce<Record<string, typeof checks>>((accumulator, check) => {
    (accumulator[check.base] ??= []).push(check);
    return accumulator;
  }, {});
  const byBase = Object.values(grouped).map((devices) => ({ base: devices[0].base, total: devices.length, down: devices.filter((item) => item.status === 'DOWN').length }));
  return Response.json({ total: checks.length, up, down: checks.length - up, availability: checks.length ? Math.round((up / checks.length) * 1000) / 10 : 0, bases: byBase.sort((a, b) => b.down - a.down) });
};
