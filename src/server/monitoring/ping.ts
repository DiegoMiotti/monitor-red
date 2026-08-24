import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import type { Check, Device } from './types';

const exec = promisify(execFile);
const isWindows = process.platform === 'win32';

export async function ping(device: Device): Promise<Check> {
  const timeout = Number(process.env.PING_TIMEOUT_SECONDS ?? 1);
  const args = isWindows ? ['-n', '1', '-w', String(timeout * 1000), device.ip] : ['-c', '1', '-W', String(timeout), device.ip];
  try {
    const { stdout } = await exec('ping', args, { timeout: (timeout + 2) * 1000 });
    const match = stdout.match(/(?:time[=<]|tiempo[=<])\s*([\d.,]+)\s*ms/i);
    return { ...device, status: 'UP', latencyMs: match ? Number(match[1].replace(',', '.')) : null, checkedAt: new Date() };
  } catch {
    return { ...device, status: 'DOWN', latencyMs: null, checkedAt: new Date() };
  }
}
