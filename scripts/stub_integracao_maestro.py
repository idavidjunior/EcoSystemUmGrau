"""stub_integracao_maestro.py — Modelo de como integrar componentes na FASE 2.

NAO aplicar ainda. Este arquivo e so um exemplo de referencia pra quando
fase 1 terminar e fase 2 comecar.

Exemplo: scripts/system_guardian.py antes e depois.

ANTES (atual, sem maestro):
    def start_tts_service():
        if not _pode_iniciar('tts_service.py'):
            return False
        if is_tts_service_up():
            return False
        proc = subprocess.Popen([...])
        ...

DEPOIS (fase 2, com maestro):
    def start_tts_service():
        from maestro_client import consultar_maestro, fallback_degraded
        decisao = consultar_maestro('pode_iniciar', script='tts_service.py')
        if decisao.get('status') == 'offline':
            # maestro nao respondeu, modo degraded: agir mas alertar
            if not fallback_degraded('guardian', 'start_tts_service'):
                return False
        elif not decisao.get('pode'):
            # maestro mandou esperar (cooldown ou ja_vivo)
            log.debug(f'Maestro bloqueou start_tts: {decisao.get(\"motivo\")}')
            return False
        proc = subprocess.Popen([...])
        # avisa maestro que nasceu
        if maestro_disponivel():
            consultar_maestro('registrar', script='tts_service.py',
                            pid=proc.pid, owner='guardian')
        ...

A fase 1 NAO precisa deste stub. Componentes continuam como estao.
Maestro so observa. Apos 1-3 dias validando, fase 2 substitui as
duas checagens locais (_pode_iniciar + is_X_up) pela consulta ao maestro.
"""
# Este arquivo nao tem codigo real, e so documentacao.
