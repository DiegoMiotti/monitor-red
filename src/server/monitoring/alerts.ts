import nodemailer from 'nodemailer';
import { database } from '../db';
import type { Check } from './types';

type Alert = { target: string; startedAt: Date; lastSentAt?: Date };

async function notify(subject: string, text: string) {
  const { SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, ALERT_EMAIL_TO } = process.env;
  if (!SMTP_HOST || !SMTP_USER || !SMTP_PASS || !ALERT_EMAIL_TO) return false;
  await nodemailer.createTransport({ host: SMTP_HOST, port: Number(SMTP_PORT ?? 465), secure: Number(SMTP_PORT ?? 465) === 465, auth: { user: SMTP_USER, pass: SMTP_PASS } }).sendMail({ from: SMTP_USER, to: ALERT_EMAIL_TO, subject, text });
  return true;
}

export async function processAlerts(checks: Check[]) {
  const db = await database(); const alerts = db.collection<Alert>('active_alerts');
  const grouped = checks.reduce<Record<string, Check[]>>((accumulator, check) => { (accumulator[check.base] ??= []).push(check); return accumulator; }, {});
  for (const [base, devices] of Object.entries(grouped)) {
    const street = devices.find((device) => device.type === 'Calle');
    const target = devices.every((device) => device.status === 'DOWN') ? `BASE_${base}` : street?.status === 'DOWN' ? `CALLE_${base}` : undefined;
    for (const candidate of [`BASE_${base}`, `CALLE_${base}`]) {
      const current = await alerts.findOne({ target: candidate });
      if (candidate !== target && current) {
        if (current.lastSentAt) await notify(`[RESTABLECIDO] ${candidate}`, `El servicio en ${candidate} volvió a la normalidad.`);
        await alerts.deleteOne({ target: candidate });
      }
    }
    if (!target) continue;
    const active = await alerts.findOne({ target }); const now = new Date();
    if (!active) { await alerts.insertOne({ target, startedAt: now }); continue; }
    const elapsed = now.getTime() - active.startedAt.getTime(); const sinceLast = active.lastSentAt ? now.getTime() - active.lastSentAt.getTime() : Infinity;
    if ((elapsed >= 600_000 && !active.lastSentAt) || (active.lastSentAt && sinceLast >= 3_600_000)) {
      const kind = active.lastSentAt ? 'RECORDATORIO' : 'ALERTA';
      if (await notify(`[${kind}] Falla persistente - ${target}`, `Equipo: ${target}\nInicio: ${active.startedAt.toISOString()}\nDuración: ${Math.floor(elapsed / 60_000)} min.`)) await alerts.updateOne({ target }, { $set: { lastSentAt: now } });
    }
  }
}
