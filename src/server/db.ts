import { Db, MongoClient } from 'mongodb';

let client: MongoClient | undefined;

export async function database(): Promise<Db> {
  const env = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env ?? process.env;
  const uri = env.MONGODB_URI;
  if (!uri) throw new Error('Falta MONGODB_URI en las variables de entorno.');
  client ??= new MongoClient(uri);
  await client.connect();
  return client.db(env.MONGODB_DB_NAME ?? 'monitor_red');
}
