"""Testes unitários comparativos de persistência para MemoryStorage e SqliteStorage."""

import os
import uuid
from datetime import UTC, datetime

import pytest

from app.domain.intents import IntentEnum, StatusMensagemEnum
from app.domain.schemas import AuditoriaLogResponse, MensagemResponse
from app.storage.base import Storage
from app.storage.memory import MemoryStorage
from app.storage.sqlite import SqliteStorage


@pytest.fixture(params=["memory", "sqlite"])
def storage_instance(request: pytest.FixtureRequest, tmp_path: str) -> Storage:
    if request.param == "memory":
        return MemoryStorage()
    else:
        db_file = os.path.join(tmp_path, f"test_{uuid.uuid4().hex}.db")
        return SqliteStorage(db_file)


@pytest.mark.asyncio
async def test_salvar_e_obter_mensagem(storage_instance: Storage) -> None:
    agora = datetime.now(UTC)
    msg = MensagemResponse(
        id=str(uuid.uuid4()),
        texto_mascarado="[NOME MASCARADO] deseja consulta.",
        paciente_identificador_mascarado="[NOME MASCARADO]",
        intencao=IntentEnum.AGENDAMENTO,
        confianca=0.9,
        requer_atencao_humana=False,
        motivo_escalonamento=None,
        rascunho_resposta="Rascunho de agendamento...",
        status=StatusMensagemEnum.AGUARDANDO_APROVACAO,
        criado_em=agora,
        atualizado_em=agora,
    )

    await storage_instance.salvar_mensagem(msg)
    recuperada = await storage_instance.obter_mensagem(msg.id)

    assert recuperada is not None
    assert recuperada.id == msg.id
    assert recuperada.texto_mascarado == msg.texto_mascarado
    assert recuperada.intencao == IntentEnum.AGENDAMENTO
    assert recuperada.confianca == 0.9
    assert recuperada.status == StatusMensagemEnum.AGUARDANDO_APROVACAO


@pytest.mark.asyncio
async def test_atualizar_mensagem(storage_instance: Storage) -> None:
    agora = datetime.now(UTC)
    msg = MensagemResponse(
        id=str(uuid.uuid4()),
        texto_mascarado="Solicitação de remarcação.",
        paciente_identificador_mascarado=None,
        intencao=IntentEnum.REMARCACAO,
        confianca=0.88,
        requer_atencao_humana=False,
        motivo_escalonamento=None,
        rascunho_resposta="Rascunho remarcar...",
        status=StatusMensagemEnum.AGUARDANDO_APROVACAO,
        criado_em=agora,
        atualizado_em=agora,
    )
    await storage_instance.salvar_mensagem(msg)

    # Atualiza status e texto aprovado
    msg.status = StatusMensagemEnum.APROVADA
    msg.texto_aprovado = "Remarcação confirmada."
    msg.aprovado_por = "atendente_teste"
    msg.observacoes = "Sem custo adicional."
    await storage_instance.atualizar_mensagem(msg)

    atualizada = await storage_instance.obter_mensagem(msg.id)
    assert atualizada is not None
    assert atualizada.status == StatusMensagemEnum.APROVADA
    assert atualizada.texto_aprovado == "Remarcação confirmada."
    assert atualizada.aprovado_por == "atendente_teste"
    assert atualizada.observacoes == "Sem custo adicional."


@pytest.mark.asyncio
async def test_auditoria_append_only(storage_instance: Storage) -> None:
    reg1 = AuditoriaLogResponse(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(UTC),
        mensagem_id="msg-1",
        acao="MENSAGEM_RECEBIDA",
        operador="sistema",
        detalhes={"step": 1},
    )
    reg2 = AuditoriaLogResponse(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(UTC),
        mensagem_id="msg-1",
        acao="TRIAGEM_CONCLUIDA",
        operador="sistema",
        detalhes={"step": 2},
    )

    await storage_instance.registrar_auditoria(reg1)
    await storage_instance.registrar_auditoria(reg2)

    registros = await storage_instance.listar_auditoria()
    assert len(registros) == 2
    # Ordenação decrescente por timestamp (mais recente primeiro)
    assert registros[0].acao == "TRIAGEM_CONCLUIDA"
    assert registros[1].acao == "MENSAGEM_RECEBIDA"
    assert registros[0].detalhes == {"step": 2}


@pytest.mark.asyncio
async def test_limpar_dados(storage_instance: Storage) -> None:
    msg = MensagemResponse(
        id=str(uuid.uuid4()),
        texto_mascarado="Teste limpeza.",
        paciente_identificador_mascarado=None,
        intencao=IntentEnum.OUTRO,
        confianca=0.5,
        requer_atencao_humana=True,
        motivo_escalonamento="Teste",
        rascunho_resposta=None,
        status=StatusMensagemEnum.REQUER_ATENCAO_HUMANA,
        criado_em=datetime.now(UTC),
        atualizado_em=datetime.now(UTC),
    )
    await storage_instance.salvar_mensagem(msg)
    await storage_instance.limpar_dados()

    assert await storage_instance.obter_mensagem(msg.id) is None
    assert len(await storage_instance.listar_auditoria()) == 0
