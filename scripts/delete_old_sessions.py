import sqlite3, json, datetime

db = r"C:\Users\Playtec-bancada\.local\share\opencode\opencode.db"
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Sessoes criadas ANTES da correcao (19:11 BRT = 22:11 UTC de 29/07/2026)
# Manter: sessoes com 10+ mensagens (conversas do chat) e sessoes da correcao em diante
CORTE = 1785363060000  # 29/07/2026 19:11 BRT

# Identificar sessoes para deletar
cur.execute("""
    SELECT s.id, s.time_created, 
           (SELECT COUNT(*) FROM message m WHERE m.session_id = s.id) as msgs,
           (SELECT MIN(m.time_created) FROM message m WHERE m.session_id = s.id) as primeira_msg,
           (SELECT MAX(m.time_created) FROM message m WHERE m.session_id = s.id) as ultima_msg
    FROM session s
    WHERE s.time_created < ?
      AND (SELECT COUNT(*) FROM message m WHERE m.session_id = s.id) < 10
    ORDER BY s.time_created DESC
""", (CORTE,))

alvos = cur.fetchall()

print(f"Sessoes a deletar: {len(alvos)}")
print(f"{'Sessao':<24} | {'Criacao':<20} | {'Msgs':>4} | {'Ultima msg':<20}")
print("-"*75)
total_msgs = 0
for s in alvos:
    sid = s["id"][:24]
    criacao = datetime.datetime.fromtimestamp(s["time_created"]/1000).strftime("%Y-%m-%d %H:%M:%S") if s["time_created"] else "-"
    ultima = datetime.datetime.fromtimestamp(s["ultima_msg"]/1000).strftime("%Y-%m-%d %H:%M:%S") if s["ultima_msg"] else "-"
    print(f"{sid:<24} | {criacao:<20} | {s['msgs']:>4} | {ultima:<20}")
    total_msgs += s["msgs"]

print(f"\nTotal: {len(alvos)} sessoes, {total_msgs} mensagens")
print(f"\nDigite 'sim' para confirmar a exclusao ou qualquer outra coisa para cancelar")
resp = input().strip().lower()
if resp != "sim":
    print("Cancelado")
    conn.close()
    exit()

# Deletar parts, messages, depois sessions
tot_part = 0
tot_msg = 0
tot_ses = 0
for s in alvos:
    sid = s["id"]
    cur.execute("DELETE FROM part WHERE session_id = ?", (sid,))
    tot_part += cur.rowcount
    cur.execute("DELETE FROM message WHERE session_id = ?", (sid,))
    tot_msg += cur.rowcount
    # Tambem deletar eventos relacionados
    cur.execute("DELETE FROM event WHERE aggregate_id = ?", (sid,))
    cur.execute("DELETE FROM session WHERE id = ?", (sid,))
    tot_ses += 1

conn.commit()
print(f"\nDeletado: {tot_ses} sessoes, {tot_msg} mensagens, {tot_part} parts")

# Opcional: vacuum
print("Compactando banco (VACUUM)... pode levar alguns segundos")
cur.execute("VACUUM")
print("Concluido!")

conn.close()
