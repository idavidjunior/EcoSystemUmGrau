import sqlite3, json, datetime, sys

db = r"C:\Users\Playtec-bancada\.local\share\opencode\opencode.db"
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

CORTE = 1785363060000  # 29/07/2026 19:11 BRT

def ts(v):
    if v is None: return "-"
    if isinstance(v, (int, float)):
        return datetime.datetime.fromtimestamp(v/1000).strftime("%Y-%m-%d %H:%M:%S")
    return str(v)[:19]

# Identificar sessoes para deletar
cur.execute("""
    SELECT s.id, s.time_created,
           (SELECT COUNT(*) FROM message m WHERE m.session_id = s.id) as msgs,
           (SELECT MAX(m.time_created) FROM message m WHERE m.session_id = s.id) as ultima_msg
    FROM session s
    WHERE s.time_created < ?
      AND (SELECT COUNT(*) FROM message m WHERE m.session_id = s.id) < 10
    ORDER BY s.time_created DESC
""", (CORTE,))

alvos = cur.fetchall()

print(f"Sessoes a deletar: {len(alvos)}")
if not alvos:
    print("Nenhuma sessao para deletar.")
    conn.close()
    sys.exit(0)

print(f"{'Sessao':<24} | {'Criacao':<20} | {'Msgs':>4} | {'Ultima msg':<20}")
print("-"*75)
total_msgs = 0
for s in alvos:
    sid = s["id"][:24]
    print(f"{sid:<24} | {ts(s['time_created']):<20} | {s['msgs']:>4} | {ts(s['ultima_msg']):<20}")
    total_msgs += s["msgs"]

print(f"\nTotal: {len(alvos)} sessoes, {total_msgs} mensagens")
print(f"\nConfirma exclusao? Passar argumento 'sim' para executar")

if len(sys.argv) < 2 or sys.argv[1].lower() != "sim":
    print("Cancelado - passe 'sim' como argumento para confirmar")
    conn.close()
    sys.exit(0)

# Deletar
tot_part = 0
tot_msg = 0
tot_ses = 0
tot_event = 0
for s in alvos:
    sid = s["id"]
    cur.execute("DELETE FROM part WHERE session_id = ?", (sid,))
    tot_part += cur.rowcount
    cur.execute("DELETE FROM message WHERE session_id = ?", (sid,))
    tot_msg += cur.rowcount
    cur.execute("DELETE FROM event WHERE aggregate_id = ?", (sid,))
    tot_event += cur.rowcount
    cur.execute("DELETE FROM todo WHERE session_id = ?", (sid,))
    cur.execute("DELETE FROM session WHERE id = ?", (sid,))
    tot_ses += 1

conn.commit()
print(f"\nDeletado: {tot_ses} sessoes, {tot_msg} mensagens, {tot_part} parts, {tot_event} eventos")

print("Compactando banco (VACUUM)...")
cur.execute("VACUUM")
print("Concluido!")
conn.close()
