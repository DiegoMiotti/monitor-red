import re  # Asegurate de que esta línea esté al principio del archivo
import sqlite3, subprocess, time, csv, os, datetime
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = "/home/soporte/monitor_red"
CSV_FILE = os.path.join(BASE_DIR, "equipos.csv")
DB_FILE = os.path.join(BASE_DIR, "monitoreo.db")
def get_db_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("CREATE TABLE IF NOT EXISTS pings (id INTEGER PRIMARY KEY AUTOINCREMENT, ip TEXT, base TEXT, tipo TEXT, latency_ms REAL, estado TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS alertas_activas (target TEXT PRIMARY KEY, tipo_alerta TEXT, inicio_falla TEXT, ultimo_envio TEXT)")
    conn.close()

def ping_equipo(info):
    try:
        # -c 3: tira 3 pings
        # -i 0.2: espera solo 0.2s entre pings (para que sea rápido)
        # -W 1: espera 1 segundo la respuesta final
        salida = subprocess.check_output(
            ['ping', '-c', '3', '-i', '0.2', '-W', '1', '-n', info['ip']], 
            stderr=subprocess.STDOUT, 
            universal_newlines=True
        )
        
        # Buscamos el tiempo del último ping exitoso en la salida
        match = re.search(r"time=([\d.]+)", salida)
        
        if match:
            ms = float(match.group(1))
            return {**info, "estado": "UP", "ms": ms}
        else:
            return {**info, "estado": "DOWN", "ms": 500.0}
            
    except Exception:
        return {**info, "estado": "DOWN", "ms": 500.0}
        
def procesar_alertas(resultados):
    conn = get_db_connection()
    cursor = conn.cursor()
    ahora = datetime.datetime.now()
    ahora_str = ahora.strftime('%Y-%m-%d %H:%M:%S')
    
    bases = {}
    for r in resultados:
        if r['base'] not in bases: bases[r['base']] = []
        bases[r['base']].append(r)

    for nombre_base, equipos in bases.items():
        todos_down = all(e['estado'] == 'DOWN' for e in equipos)
        calle = next((e for e in equipos if e['tipo'] == 'Calle'), None)
        
        target_falla = None
        if todos_down: target_falla = f"BASE_{nombre_base}"
        elif calle and calle['estado'] == 'DOWN': target_falla = f"CALLE_{nombre_base}"

        # --- GESTIÓN DE FALLAS ---
        if target_falla:
            cursor.execute("SELECT inicio_falla, ultimo_envio FROM alertas_activas WHERE target=?", (target_falla,))
            row = cursor.fetchone()
            
            if not row:
                cursor.execute("INSERT INTO alertas_activas (target, inicio_falla) VALUES (?, ?)", (target_falla, ahora_str))
                print(f"DEBUG: [{target_falla}] Falla detectada. Iniciando cronómetro.")
            else:
                inicio = datetime.datetime.strptime(row[0][:19], '%Y-%m-%d %H:%M:%S')
                minutos_caido = (ahora - inicio).total_seconds() / 60
                
                ultimo_envio_str = row[1]
                
                # La versión local no envía correos; solo conserva el estado de la falla.

        # --- GESTIÓN DE RECUPERACIONES ---
        posibles = [f"BASE_{nombre_base}", f"CALLE_{nombre_base}"]
        for t in posibles:
            if t != target_falla:
                cursor.execute("SELECT ultimo_envio FROM alertas_activas WHERE target=?", (t,))
                res_alert = cursor.fetchone()
                if res_alert:
                    cursor.execute("DELETE FROM alertas_activas WHERE target=?", (t,))
    
    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    init_db()
    print(">>> SERVICIO MONITOR INICIADO (Versión Final SSL + Auto-Limpieza) <<<")
    while True:
        try:
            # --- 1. LIMPIEZA AUTOMÁTICA (Mantiene solo los últimos 30 días) ---
            conn_limpieza = get_db_connection()
            conn_limpieza.execute("DELETE FROM pings WHERE timestamp < datetime('now', '-30 days');")
            conn_limpieza.commit()
            conn_limpieza.close()

            # --- 2. LECTURA DE EQUIPOS ---
            equipos = []
            with open(CSV_FILE, newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    base = row.get('Base', 'Desconocida')
                    for t in ['Forti','DVR','TGO','Calle','Comedor','Jaula','Terceros']:
                        ip = row.get(t)
                        if ip and ip.strip() and ip.strip().lower() != 'nan':
                            equipos.append({"ip":ip.strip(), "base":base, "tipo":t})
            
            # --- 3. EJECUCIÓN DE PINGS ---
            with ThreadPoolExecutor(max_workers=40) as ex:
                res = list(ex.map(ping_equipo, equipos))
            
            # --- 4. GUARDADO DE RESULTADOS ---
            conn = get_db_connection()
            for r in res:
                conn.execute("INSERT INTO pings (ip, base, tipo, latency_ms, estado) VALUES (?,?,?,?,?)", (r['ip'], r['base'], r['tipo'], r['ms'], r['estado']))
            conn.commit()
            conn.close()

            # --- 5. PROCESAMIENTO DE ALERTAS ---
            procesar_alertas(res)
            
            print(f"Ciclo OK: UP {sum(1 for x in res if x['estado']=='UP')} | DOWN {sum(1 for x in res if x['estado']=='DOWN')} - {datetime.datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"ERROR en ciclo: {e}")
            
        time.sleep(60)
