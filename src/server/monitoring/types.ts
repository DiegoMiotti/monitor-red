export type DeviceType = 'Forti' | 'DVR' | 'TGO' | 'Calle' | 'Comedor' | 'Jaula' | 'Terceros' | 'Redmi Note 10' | 'Motorola';
export type CheckStatus = 'UP' | 'DOWN';

export interface Device { ip: string; base: string; type: DeviceType; location?: string }
export interface Check extends Device { status: CheckStatus; latencyMs: number | null; checkedAt: Date }
