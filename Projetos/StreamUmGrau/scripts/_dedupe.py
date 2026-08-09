import psycopg2

HOST = 'aws-0-sa-east-1.pooler.supabase.com'
PW = 'Family/310515umgrau'
USER = 'postgres.asanytdwhbsiujuppeth'

conn = psycopg2.connect(host=HOST, port=6543, user=USER, password=PW,
                        dbname='postgres', connect_timeout=10, sslmode='require')
conn.autocommit = True
cur = conn.cursor()

cur.execute("""
    with dup as (
        select id, titulo, tipo, popularidade,
               row_number() over (
                   partition by titulo, tipo
                   order by popularidade desc, criado_em desc
               ) as rn
        from public.midias
    )
    delete from public.midias m
    using dup d
    where m.id = d.id and d.rn > 1
""")
print('duplicatas removidas:', cur.rowcount)
cur.execute('select count(*) from public.midias')
print('total obras agora:', cur.fetchone()[0])
conn.close()
