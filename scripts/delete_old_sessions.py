import sqlite3, datetime, sys

db = r"C:\Users\Playtec-bancada\.local\share\opencode\opencode.db"
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Deleter sessoes antes de 29/07/2026 00:00 BRT
inicio_hoje = int(datetime.datetime(2026, 7, 29, 3, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)

def ts(v):
    if v is None: return "-"
    if isinstance(v, (int, float)):
        return datetime.datetime.fromtimestamp(v/1000).strftime("%Y-%m-%d %H:%M")
    return str(v)[:16]

cur.execute("""
    SELECT s.id, s.time_created,
           (SELECT COUNT(*) FROM message m WHERE m.session_id = s.id) as total_msgs,
           (SELECT COUNT(*) FROM part p WHERE p.session_id = s.id) as total_parts,
           (SELECT COUNT(*) FROM event e WHERE e.aggregate_id = s.id) as total_events
    FROM session s
    WHERE s.time_created < ?
    ORDER BY s.time_created
""", (inicio_hoje,))

alvos = cur.fetchall()
total_msg = sum(r["total_msgs"] for r in alvos)
total_part = sum(r["total_parts"] for r in alvos)
total_event = sum(r["total_events"] for r in alvos)

print(f"Sessoes a deletar: {len(alvos)}")
print(f"Mensagens: {total_msg} | Parts: {total_part} | Eventos: {total_event}")
print()
print(f"{'Sessao':<24} | {'Data':<16} | {'Msgs':>4} | {'Parts':>5} | {'Events':>6}")
print("-"*70)
for s in alvos[:30]:
    print(f"{s['id'][:24]:<24} | {ts(s['time_created']):<16} | {s['total_msgs']:>4} | {s['total_parts']:>5} | {s['total_events']:>6}")
if len(alvos) > 30:
    print(f"... e mais {len(alvos)-30} sessoes")

print(f"\nTotal: {len(alvos)} sessoes, {total_msg} mensagens, {total_part} parts, {total_event} eventos")
if len(sys.argv) < 2 or sys.argv[1].lower() != "sim":
    print("\nExecute com argumento 'sim' para confirmar a exclusao")
    conn.close()
    sys.exit(0)

# Deletar
d_msg = d_part = d_event = d_ses = 0
for s in alvos:
    sid = s["id"]
    cur.execute("DELETE FROM part WHERE session_id = ?", (sid,))
    d_part += cur.rowcount
    cur.execute("DELETE FROM message WHERE session_id = ?", (sid,))
    d_msg += cur.rowcount
    cur.execute("DELETE FROM event WHERE aggregate_id = ?", (sid,))
    d_event += cur.rowcount
    cur.execute("DELETE FROM todo WHERE session_id = ?", (sid,))
    cur.execute("DELETE FROM session WHERE id = ?", (sid,))
    d_ses += 1

conn.commit()
print(f"\nDeletado: {d_ses} sessoes, {d_msg} mensagens, {d_part} parts, {d_event} eventos")

print("Compactando banco...")
cur.execute("VACUUM")
print("Concluido!")
conn.close()
