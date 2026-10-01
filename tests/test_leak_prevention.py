"""Teste estrito de prevenção de vazamento de dados pessoais (PII).

Garante que o texto original com dados pessoais sensíveis NUNCA aparece:
1. No corpo de respostas de erro de validação (HTTP 422 - handler customizado de RequestValidationError).
2. Nas respostas da API pública (HTTP 201/200).
3. Na entidade persistida no Storage.
4. Na trilha de auditoria append-only.
5. No texto aprovado ou nas observações pós-intervenção humana.
"""

from fastapi.testclient import TestClient


def test_request_validation_error_nao_ecoa_input_sensivel(client: TestClient) -> None:
    # Payload inválido (texto com menos de 3 caracteres) contendo dados sensíveis
    dado_sensivel = "CPF_SECRETO_52998224725"
    payload_invalido = {
        "texto": "oi",  # Falha min_length=3
        "paciente_identificador": dado_sensivel,
    }

    response = client.post("/mensagens", json=payload_invalido)
    assert response.status_code == 422

    corpo_resposta = response.text
    # Garante que o input bruto foi removido e não vazou no erro
    assert dado_sensivel not in corpo_resposta
    assert '"input":' not in corpo_resposta


def test_garantia_de_nao_vazamento_end_to_end(
    client: TestClient,
    headers_atendente: dict[str, str],
    headers_gestor: dict[str, str],
) -> None:
    # Conjunto de dados pessoais fictícios a serem rastreados (Ana Souza Teste)
    pii_sensivel = [
        "52998224725",
        "11987654321",
        "paciente.sensivel@clinicaexemplo.com",
        "Ana Souza Teste",
        "01310-100",
        "12.345.678-9",
        "12/05/1978",
    ]

    mensagem_bruta = (
        "Olá, me chamo Ana Souza Teste, nascida em 12/05/1978, moro no CEP 01310-100, "
        "meu RG é 12.345.678-9 e meu CPF de teste é 52998224725. Meu email é paciente.sensivel@clinicaexemplo.com "
        "e meu whats é 11987654321. Gostaria de agendar uma consulta."
    )
    paciente_id_bruto = "Ana Souza Teste 52998224725"

    # 1. Envio da mensagem via API
    resp_post = client.post(
        "/mensagens",
        json={"texto": mensagem_bruta, "paciente_identificador": paciente_id_bruto},
    )
    assert resp_post.status_code == 201
    dados_resposta = resp_post.text
    msg_id = resp_post.json()["id"]

    # Verifica se algum PII vazou na resposta da API
    for pii in pii_sensivel:
        assert pii not in dados_resposta, f"Vazamento de '{pii}' detectado na resposta da API!"

    # 2. Inspeciona o registro gravado no Storage através do endpoint autenticado
    msg_no_storage = client.get(f"/mensagens/{msg_id}", headers=headers_atendente).text
    for pii in pii_sensivel:
        assert pii not in msg_no_storage, f"Vazamento de '{pii}' detectado no Storage!"

    # 3. Inspeciona os registros na Auditoria append-only
    resp_auditoria = client.get("/auditoria", headers=headers_gestor)
    assert resp_auditoria.status_code == 200
    auditoria_completa = resp_auditoria.text
    for pii in pii_sensivel:
        assert pii not in auditoria_completa, f"Vazamento de '{pii}' detectado na Auditoria!"

    # 4. Aprova com tentativa de inserir PII no texto aprovado e observações
    resp_aprov = client.post(
        f"/mensagens/{msg_id}/aprovar",
        json={
            "texto_aprovado": "Consulta confirmada para Ana Souza Teste tel 11987654321.",
            "aprovado_por": "atendente_seguranca",
            "observacoes": "Confirmado CPF de teste 52998224725 e email paciente.sensivel@clinicaexemplo.com.",
        },
        headers=headers_atendente,
    )
    assert resp_aprov.status_code == 200
    texto_aprovado_resp = resp_aprov.text
    for pii in pii_sensivel:
        assert pii not in texto_aprovado_resp, f"Vazamento de '{pii}' detectado pós-aprovação!"

    # 5. Verifica novamente a auditoria após a aprovação
    auditoria_pos_aprov = client.get("/auditoria", headers=headers_gestor).text
    for pii in pii_sensivel:
        assert pii not in auditoria_pos_aprov, (
            f"Vazamento de '{pii}' detectado na Auditoria após aprovação!"
        )
