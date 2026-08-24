import sqlite3
import os
import subprocess
import csv
import datetime
from flask import Flask, render_template, request, jsonify
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# RUTAS ABSOLUTAS
BASE_DIR = "/home/soporte/monitor_red"
DB_FILE = os.path.join(BASE_DIR, "monitoreo.db")
CSV_FILE = os.path.join(BASE_DIR, "equipos.csv")

# --- LÓGICA DE PINGS ---
def ping_equipo(info):
    try:
        command = ['ping', '-c', '1', '-W', '1', info['ip']]
        subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
        return {**info, "estado": "UP"}
    except:
        return {**info, "estado": "DOWN"}

def get_data_raw():
    equipos_planos = []
    if not os.path.exists(CSV_FILE): return []
    with open(CSV_FILE, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = {k.strip(): v for k, v in row.items() if k}
            for tipo in ['Forti', 'DVR', 'TGO', 'Calle', 'Comedor', 'Jaula', 'Terceros']:
                ip = row.get(tipo)
                if ip and ip.strip() and ip.strip().lower() != 'nan':
                    equipos_planos.append({"ip": ip.strip(), "base": row.get('Base', 'Desconocida'), "tipo": tipo})
    with ThreadPoolExecutor(max_workers=40) as executor:
        return list(executor.map(ping_equipo, equipos_planos))

# --- RUTAS API ---
@app.route("/api/status")
def api_status():
    return jsonify({"equipos": get_data_raw(), "hora": datetime.datetime.now().strftime("%H:%M:%S")})

@app.route("/api/history")
def api_history():
    ip = request.args.get("ip")
    horas = request.args.get("horas", default=24, type=int)
    conn = sqlite3.connect(DB_FILE)
    # Importante: verifica si tu columna se llama 'status' o 'estado' en la DB
    query = "SELECT datetime(timestamp, 'localtime'), latency_ms FROM pings WHERE ip=? AND timestamp > datetime('now', '-%d hours') ORDER BY timestamp ASC" % horas
    res = conn.execute(query, (ip,)).fetchall()
    conn.close()
    return jsonify({"labels": [r[0] for r in res], "values": [r[1] for r in res]})

@app.route("/api/stats")
def api_stats():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # 1. Gráfico de Torta - Súper rápido (usando count total)
        total_pings = cursor.execute("SELECT COUNT(*) FROM pings").fetchone()[0] or 1
        pings_up = cursor.execute("SELECT COUNT(*) FROM pings WHERE estado = 'UP'").fetchone()[0]
        pings_down = total_pings - pings_up
        
        # 2. Top Inestables - Ahora agrupamos por BASE y TIPO para que sea legible
        # En lugar de solo IP, mostramos "Base - Tipo"
        inestables = cursor.execute("""
            SELECT base || ' - ' || tipo, COUNT(*) as fallas 
            FROM pings WHERE estado = 'DOWN' 
            GROUP BY base, tipo ORDER BY fallas DESC LIMIT 5
        """).fetchall()
        
        # 3. Top Lentos - Agrupamos por BASE y TIPO
        lentos = cursor.execute("""
            SELECT base || ' - ' || tipo, AVG(latency_ms) as promedio 
            FROM pings WHERE estado = 'UP' 
            GROUP BY base, tipo ORDER BY promedio DESC LIMIT 5
        """).fetchall()
        
        return jsonify({
            "pie": [pings_up, pings_down],
            "inestables": {
                "labels": [i[0] for i in inestables], 
                "values": [i[1] for i in inestables]
            },
            "lentos": {
                "labels": [l[0] for l in lentos], 
                "values": [round(l[1], 2) for l in lentos]
            }
        })
    finally:
        conn.close()

@app.route("/")
def index():
    return render_template("index.html")

# EL APP.RUN SIEMPRE DEBE IR AL FINAL DE TODO
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)