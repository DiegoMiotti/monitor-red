import { readFile } from 'node:fs/promises';
import type { Device, DeviceType } from './types';

const types: DeviceType[] = ['Forti', 'DVR', 'TGO', 'Calle', 'Comedor', 'Jaula', 'Terceros', 'Redmi Note 10', 'Motorola'];

export async function loadInventory(path = process.env.EQUIPMENT_CSV_PATH ?? 'templates/equipos.csv'): Promise<Device[]> {
  const [headerLine, ...lines] = (await readFile(path, 'utf8')).replace(/^\uFEFF/, '').trim().split(/\r?\n/);
  const header = headerLine.split(',').map((value) => value.trim());
  return lines.flatMap((line) => {
    const row = line.split(',').map((value) => value.trim());
    const get = (name: string) => row[header.indexOf(name)] ?? '';
    return types.flatMap((type) => {
      const ip = get(type);
      return ip && ip.toLowerCase() !== 'nan' ? [{ ip, base: get('Base') || 'Desconocida', type, location: get('Ubicacion') || undefined }] : [];
    });
  });
}
