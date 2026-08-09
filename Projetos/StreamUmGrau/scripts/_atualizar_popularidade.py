import psycopg2, re, sys

HOST = 'aws-0-sa-east-1.pooler.supabase.com'
PW = 'Family/310515umgrau'
USER = 'postgres.asanytdwhbsiujuppeth'

conn = psycopg2.connect(host=HOST, port=6543, user=USER, password=PW,
                        dbname='postgres', connect_timeout=10, sslmode='require')
conn.autocommit = True
cur = conn.cursor()

sql = open(r'database\seed_tmdb.sql', encoding='utf-8').read()
body = sql.split('values')[1].split('on conflict')[0]

pat = re.compile(
    r"\(\s*'((?:[^']|'')*)'\s*,\s*'([^']*)'\s*,\s*'((?:[^']|'')*)'\s*,\s*'((?:[^']|'')*)'\s*,\s*'((?:[^']|'')*)'\s*,\s*'((?:[^']|'')*)'\s*,\s*(\d+)\s*,\s*'([^']*)'\s*,\s*(\d+)\s*,\s*(\d+)\s*\)"
)
linhas = pat.findall(body)
print('linhas parseadas:', len(linhas))

atualizadas = 0
inseridas = 0
for t, tipo, cat, sin, capa, banner, ano, idio, idade, pop in linhas:
    t2 = t.replace("''", "'")
    cur.execute('update public.midias set popularidade=%s where titulo=%s and tipo=%s',
                (int(pop), t2, tipo))
    if cur.rowcount:
        atualizadas += cur.rowcount
        continue
    cur.execute(
        "insert into public.midias (titulo, tipo, categoria, sinopse, capa_url, banner_url, ano, idioma_tipo, classificacao_etaria, popularidade)"
        " values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) on conflict (id) do nothing",
        (t2, tipo, cat, sin, capa, banner, int(ano), idio, int(idade), int(pop)))
    inseridas += 1

print('atualizadas:', atualizadas, '| inseridas:', inseridas)
cur.execute('select count(*) from public.midias')
print('total obras:', cur.fetchone()[0])
conn.close()
