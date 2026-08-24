import type { APIRoute } from 'astro';
import { checkHistory } from '../../server/repositories/checks';
export const GET: APIRoute = async ({ url }) => {
  const ip = url.searchParams.get('ip');
  const hours = Math.min(Math.max(Number(url.searchParams.get('hours') ?? 24), 1), 24 * 30);
  if (!ip) return Response.json({ error: 'El parámetro ip es obligatorio.' }, { status: 400 });
  return Response.json(await checkHistory(ip, hours));
};
