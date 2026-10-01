"""Testes de integração dos endpoints HTTP da API FastAPI."""

from fastapi.testclient import TestClient


def test_endpoint_saude(client: TestClient) -> None:
    response = client.get("/saude")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app_mode"] == "demo"
    assert data["llm_provider"] == "mock"
    assert data["storage"] == "memory"
    assert "Modo de demonstração" in data["aviso"]


def test_criar_e_obter_mensagem(client: TestClient, headers_atendente: dict[str, str]) -> None:
    payload = {
        "texto": "Olá! Gostaria de agendar consulta para amanhã. Meu contato é 11987654321.",
        "paciente_identificador": "P-1024",
    }
    # Criar mensagem (público)
    post_resp = client.post("/mensagens", json=payload)
    assert post_resp.status_code == 201
    dados = post_resp.json()
    msg_id = dados["id"]

    assert dados["intencao"] == "agendamento"
    assert dados["status"] == "aguardando_aprovacao"
    assert "11987654321" not in dados["texto_mascarado"]
    assert "[TELEFONE MASCARADO]" in dados["texto_mascarado"]
    assert dados["rascunho_resposta"] is not None

    # Tenta obter mensagem sem autenticação -> 401 Unauthorized
    sem_auth = client.get(f"/mensagens/{msg_id}")
    assert sem_auth.status_code == 401

    # Obter mensagem com chave de atendente -> 200 OK
    get_resp = client.get(f"/mensagens/{msg_id}", headers=headers_atendente)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == msg_id


def test_obter_mensagem_inexistente(client: TestClient, headers_atendente: dict[str, str]) -> None:
    response = client.get("/mensagens/id-inexistente-12345", headers=headers_atendente)
    assert response.status_code == 404
    assert "não encontrada" in response.json()["detail"]


def test_fluxo_aprovacao_autenticada_e_conflito_409(
    client: TestClient, headers_atendente: dict[str, str]
) -> None:
    # 1. Cria mensagem
    post_resp = client.post(
        "/mensagens",
        json={"texto": "Gostaria de agendar cardiologista para sexta-feira."},
    )
    msg_id = post_resp.json()["id"]

    # 2. Tenta aprovar sem autenticação (401)
    sem_auth = client.post(f"/mensagens/{msg_id}/aprovar", json={"aprovado_por": "ana"})
    assert sem_auth.status_code == 401

    # 3. Tenta aprovar com chave inválida (401)
    chave_invalida = client.post(
        f"/mensagens/{msg_id}/aprovar",
        json={"aprovado_por": "ana"},
        headers={"X-API-Key": "chave-errada"},
    )
    assert chave_invalida.status_code == 401

    # 4. Aprova com chave válida de atendente (200)
    aprovar_resp = client.post(
        f"/mensagens/{msg_id}/aprovar",
        json={
            "texto_aprovado": "Consulta confirmada para sexta-feira às 10h.",
            "aprovado_por": "atendente_ana",
            "observacoes": "Preferência por Dr. Silva.",
        },
        headers=headers_atendente,
    )
    assert aprovar_resp.status_code == 200
    assert aprovar_resp.json()["status"] == "aprovada"
    assert aprovar_resp.json()["aprovado_por"] == "atendente_ana"

    # 5. Tentativa de aprovar mensagem já aprovada deve resultar em HTTP 409 Conflict
    reaprovacao_resp = client.post(
        f"/mensagens/{msg_id}/aprovar",
        json={"aprovado_por": "atendente_ana"},
        headers=headers_atendente,
    )
    assert reaprovacao_resp.status_code == 409
    assert "Transição inválida" in reaprovacao_resp.json()["detail"]


def test_fluxo_rejeicao_mensagem(client: TestClient, headers_atendente: dict[str, str]) -> None:
    # Cria mensagem
    post_resp = client.post("/mensagens", json={"texto": "Gostaria de remarcar."})
    msg_id = post_resp.json()["id"]

    # Rejeita mensagem
    rejeita_resp = client.post(
        f"/mensagens/{msg_id}/rejeitar",
        json={"motivo": "Spam recebido.", "rejeitado_por": "atendente_lucas"},
        headers=headers_atendente,
    )
    assert rejeita_resp.status_code == 200
    assert rejeita_resp.json()["status"] == "rejeitada"

    # Tentativa de aprovar mensagem rejeitada deve falhar com 409 Conflict
    aprov_resp = client.post(
        f"/mensagens/{msg_id}/aprovar",
        json={"aprovado_por": "atendente_lucas"},
        headers=headers_atendente,
    )
    assert aprov_resp.status_code == 409


def test_permissao_auditoria_apenas_gestor(
    client: TestClient,
    headers_atendente: dict[str, str],
    headers_gestor: dict[str, str],
) -> None:
    # 1. Sem autenticação -> 401
    resp_anon = client.get("/auditoria")
    assert resp_anon.status_code == 401

    # 2. Com chave de atendente -> 403 Forbidden (apenas gestor)
    resp_atendente = client.get("/auditoria", headers=headers_atendente)
    assert resp_atendente.status_code == 403
    assert "restrito ao papel de 'gestor'" in resp_atendente.json()["detail"]

    # 3. Com chave de gestor -> 200 OK
    resp_gestor = client.get("/auditoria", headers=headers_gestor)
    assert resp_gestor.status_code == 200
    assert isinstance(resp_gestor.json(), list)
