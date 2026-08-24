# Monitor Red

Monitor Red es una plataforma de observabilidad de conectividad para sedes y sus equipos de red. Esta versión inicia la migración del monitor Python/Flask a una arquitectura modular basada en **Astro + Node.js + MongoDB**.

## Objetivo de la migración

- Interfaz moderna, responsive y rápida con Astro.
- API tipada del lado servidor para dashboard, historial y métricas.
- Servicio de sondeo independiente para ejecutar pings sin bloquear la web.
- Persistencia en MongoDB, preparada para índices, retención y crecimiento.
- Configuración sensible exclusivamente mediante variables de entorno.

## Arquitectura

```
Browser (Astro UI) -> /api/* (Astro server) -> MongoDB
                                          ^
                                          |
                                monitor worker (Node.js)
                                          |
                                     ICMP / ping
```

El worker lee el inventario desde `EQUIPMENT_CSV_PATH` (por defecto el CSV histórico), ejecuta los chequeos y guarda una muestra por equipo en MongoDB. La aplicación web sólo consulta datos persistidos: no lanza pings al abrir el dashboard.

## Requisitos

- Node.js 20 o superior
- MongoDB 7 o superior (local, Docker o Atlas)

## Inicio rápido

```bash
cp .env.example .env
npm install
npm run dev
```

En otra terminal, iniciar el worker:

```bash
npm run monitor
```

El dashboard queda disponible en `http://localhost:4321`.

## Variables de entorno

Copiar `.env.example` a `.env` y completar `MONGODB_URI`. Nunca incluir contraseñas SMTP ni URIs con credenciales en el repositorio.

| Variable | Descripción | Valor por defecto |
| --- | --- | --- |
| `MONGODB_URI` | Cadena de conexión de MongoDB | — |
| `MONGODB_DB_NAME` | Base de datos de la aplicación | `monitor_red` |
| `EQUIPMENT_CSV_PATH` | Inventario CSV legado a importar/leer | `templates/equipos.csv` |
| `MONITOR_INTERVAL_MS` | Frecuencia del ciclo de chequeo | `60000` |
| `PING_TIMEOUT_SECONDS` | Tiempo máximo por ping | `1` |
| `RETENTION_DAYS` | Días de historial conservado | `30` |
| `SMTP_*` / `ALERT_EMAIL_TO` | Credenciales SMTP y destinatario de alertas | — |

## Estructura

```
src/
  pages/              Dashboard y endpoints API de Astro
  components/         Componentes visuales reutilizables
  server/
    monitoring/       Parser CSV, ping y worker
    repositories/     Acceso a MongoDB
    services/         Casos de uso y métricas
```

## Endpoints

- `GET /api/status`: último estado registrado de cada equipo.
- `GET /api/history?ip=…&hours=24`: serie de latencia.
- `GET /api/stats?hours=24`: disponibilidad, equipos inestables y lentos.
- `POST /api/monitor/run`: ejecuta un ciclo manual (útil para entornos controlados).

## Migración desde la versión anterior

Los archivos Python y el CSV se mantienen como referencia durante la transición. El CSV actual puede seguir siendo el inventario de entrada, pero el historial SQLite se reemplaza por las colecciones MongoDB `checks` y `active_alerts`. Las credenciales expuestas en el código legado deben revocarse y moverse a un gestor de secretos antes de cualquier despliegue.

## Scripts

- `npm run dev`: desarrollo web.
- `npm run build`: compila la aplicación para producción.
- `npm run preview`: prueba el build.
- `npm run monitor`: inicia el worker de monitoreo.
- `npm run check`: validación de tipos y Astro.
