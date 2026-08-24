import { Db, MongoClient } from 'mongodb';

let client: MongoClient | undefined;

export async function database(): Promise<Db> {
  const uri = import.meta.env.MONGODB_URI ?? process.env.MONGODB_URI;
  if (!uri) throw new Error('Falta MONGODB_URI en las variables de entorno.');
  client ??= new MongoClient(uri);
  await client.connect();
  return client.db(import.meta.env.MONGODB_DB_NAME ?? process.env.MONGODB_DB_NAME ?? 'monitor_red');
}
