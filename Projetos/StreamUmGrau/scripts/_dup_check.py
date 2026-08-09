import psycopg2

HOST = 'aws-0-sa-east-1.pooler.supabase.com'
PW = 'Family/310515umgrau'
USER = 'postgres.asanytdwhbsiujuppeth'

conn = psycopg2.connect(host=HOST, port=6543, user=USER, password=PW,
                        dbname='postgres', connect_timeout=10, sslmode='require')
conn.autocommit = True
cur = conn.cursor()

cur.execute("""
    select titulo, tipo, count(*)
    from public.midias
    group by titulo, tipo
    having count(*) > 1
    order by count(*) desc
""")
rows = cur.fetchall()
print('duplicatas por titulo+tipo:', len(rows))
for t, tipo, n in rows[:10]:
    print(f'  {n}x {t} ({tipo})')
conn.close()
