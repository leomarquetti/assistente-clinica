"""Testes unitários do serviço de triagem determinística, negações e segurança clínica."""

import pytest

from app.domain.intents import IntentEnum
from app.providers.llm_mock import MockLLMProvider
from app.services.triagem import (
    detectar_urgencia_clinica,
    executar_triagem_deterministica,
    normalizar_texto,
)


def test_normalizar_texto() -> None:
    bruto = "  Olá!  Gostaria   de  AGENDAR  às 14h: cardiologista & atenção! "
    normalizado = normalizar_texto(bruto)
    assert normalizado == "ola! gostaria de agendar as 14h: cardiologista & atencao!"


def test_detectar_urgencia_afirmativa() -> None:
    frases_urgentes = [
        "Estou sentindo uma forte dor no peito há 20 minutos.",
        "Paciente apresentando falta de ar e sufocamento.",
        "Houve um desmaio seguido de convulsão aqui na sala.",
        "Meu pai está com hemorragia e sangramento contínuo.",
        "Socorro, suspeita de avc com dormencia no braco!",
    ]
    for frase in frases_urgentes:
        norm = normalizar_texto(frase)
        is_urgente, sintoma = detectar_urgencia_clinica(norm)
        assert is_urgente is True
        assert sintoma is not None

        triagem = executar_triagem_deterministica(frase)
        assert triagem.intencao == IntentEnum.URGENCIA_CLINICA
        assert triagem.confianca == 1.0
        assert triagem.requer_atencao_humana is True
        assert "Atenção humana imediata" in (triagem.motivo_escalonamento or "")


def test_detectar_urgencia_com_negacao() -> None:
    # Frases onde o sintoma está expressamente negado
    frases_negadas = [
        "Não estou com dor no peito, apenas quero agendar um exame de rotina.",
        "Sem dor no peito e sem falta de ar, preciso remarcar minha consulta.",
        "Não sinto falta de ar nem febre alta, só queria saber o horário.",
        "Não tive desmaio, foi só uma tontura leve ao levantar.",
    ]
    for frase in frases_negadas:
        norm = normalizar_texto(frase)
        is_urgente, sintoma = detectar_urgencia_clinica(norm)
        assert is_urgente is False, f"Falha na negação para frase: {frase}"

        triagem = executar_triagem_deterministica(frase)
        assert triagem.intencao != IntentEnum.URGENCIA_CLINICA


def test_negacao_parcial_com_outro_sintoma_afirmativo() -> None:
    # Uma negação não pode anular um segundo sintoma presente
    frase = "Não sinto febre alta, mas estou com forte dor no peito."
    norm = normalizar_texto(frase)
    is_urgente, sintoma = detectar_urgencia_clinica(norm)
    assert is_urgente is True
    assert sintoma == "dor no peito"

    triagem = executar_triagem_deterministica(frase)
    assert triagem.intencao == IntentEnum.URGENCIA_CLINICA
    assert triagem.requer_atencao_humana is True


def test_classificacao_intencoes_administrativas() -> None:
    casos = [
        ("Gostaria de agendar consulta com dermatologista.", IntentEnum.AGENDAMENTO),
        ("Preciso remarcar minha consulta de quinta para sexta.", IntentEnum.REMARCACAO),
        ("Qual o endereço da clínica e que horas abre?", IntentEnum.DUVIDA_ADMINISTRATIVA),
        (
            "Quanto custa a consulta e vocês emitem nota fiscal para reembolso?",
            IntentEnum.FINANCEIRO,
        ),
    ]
    for frase, intencao_esperada in casos:
        triagem = executar_triagem_deterministica(frase)
        assert triagem.intencao == intencao_esperada
        assert triagem.confianca >= 0.6
        assert triagem.requer_atencao_humana is False


def test_baixa_confianca_escalona_para_humano() -> None:
    frase_ambigua = "Oi tudo bem"
    triagem = executar_triagem_deterministica(frase_ambigua, limiar_confianca=0.6)
    assert triagem.intencao == IntentEnum.OUTRO
    assert triagem.confianca < 0.6
    assert triagem.requer_atencao_humana is True
    assert "abaixo do limiar mínimo" in (triagem.motivo_escalonamento or "")


@pytest.mark.asyncio
async def test_provedor_mock_nunca_rebaixa_urgencia_nem_gera_rascunho_clinico() -> None:
    provider = MockLLMProvider()
    with pytest.raises(ValueError, match="Segurança clínica"):
        await provider.gerar_rascunho(
            texto_mascarado="[NOME MASCARADO] dor no peito",
            intencao=IntentEnum.URGENCIA_CLINICA,
        )
