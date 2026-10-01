"""Serviço determinístico de triagem, detecção de urgência clínica e classificação de intenções."""

import re
import unicodedata
from typing import NamedTuple

from app.domain.intents import IntentEnum


def normalizar_texto(texto: str) -> str:
    """Normaliza texto removendo acentos, convertendo para minúsculas e simplificando espaços."""
    if not texto:
        return ""
    # Decomposição de caracteres e remoção de marcas de acentuação
    nfkd = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Minúsculas e substituição de quebras de linha/múltiplos espaços por espaço simples
    limpo = sem_acento.lower()
    return re.sub(r"\s+", " ", limpo).strip()


# Termos e sintomas clínicos de urgência (em forma normalizada sem acento)
SINTOMAS_URGENTES: list[str] = [
    "dor no peito",
    "dor toracica",
    "aperto no peito",
    "falta de ar",
    "dificuldade para respirar",
    "dificuldade de respirar",
    "sufocamento",
    "sangramento",
    "hemorragia",
    "febre alta",
    "desmaio",
    "desmaiei",
    "perda de consciencia",
    "perdi a consciencia",
    "convulsao",
    "convulsoes",
    "convulsionando",
    "intoxicacao",
    "envenenamento",
    "infarto",
    "avc",
    "derrame",
    "paralisia facial",
    "dormencia no braco",
    "emergencia",
    "socorro",
]

# Padrões que indicam negação explícita imediatamente antes de um sintoma (incluindo conectivos como 'nem')
PREFIXOS_NEGACAO: list[str] = [
    r"nao\s+estou\s+com",
    r"nao\s+sinto",
    r"nao\s+tenho",
    r"nao\s+apresento",
    r"nao\s+tive",
    r"nao\s+e",
    r"nao\s+ha",
    r"sem",
    r"livre\s+de",
    r"descarto",
    r"nem\s+estou\s+com",
    r"nem\s+sinto",
    r"nem\s+tenho",
    r"nem\s+apresento",
    r"nem\s+tive",
    r"nem",
]


def _sintoma_esta_negado(texto_normalizado: str, sintoma: str) -> bool:
    """Verifica se todas as ocorrências do sintoma no texto são precedidas por negação."""
    padrao_sintoma = re.escape(sintoma)
    padrao_negacao = r"(?:" + "|".join(PREFIXOS_NEGACAO) + r")\s+" + padrao_sintoma

    ocorrencias_totais = len(re.findall(r"\b" + padrao_sintoma + r"\b", texto_normalizado))
    ocorrencias_negadas = len(re.findall(r"\b" + padrao_negacao + r"\b", texto_normalizado))

    # Considera negado se todas as ocorrências estiverem sob negação direta ou correlata ('nem')
    return ocorrencias_totais > 0 and ocorrencias_totais == ocorrencias_negadas


def detectar_urgencia_clinica(texto_normalizado: str) -> tuple[bool, str | None]:
    """Detecta deterministicamente se há sintomas ou termos de urgência clínica ativos (não negados).

    Retorna: (is_urgente, sintoma_detectado)
    """
    for sintoma in SINTOMAS_URGENTES:
        if re.search(r"\b" + re.escape(sintoma) + r"\b", texto_normalizado):
            if not _sintoma_esta_negado(texto_normalizado, sintoma):
                return True, sintoma
    return False, None


# Dicionários de palavras-chave para classificação de intenção no modo baseado em regras
KEYWORDS_REMARCACAO = [
    "remarcar",
    "reagendar",
    "mudar data",
    "trocar data",
    "mudar horario",
    "trocar horario",
    "cancelar",
    "desmarcar",
    "adiar",
]

KEYWORDS_AGENDAMENTO = [
    "agendar",
    "marcar",
    "consulta",
    "exame",
    "vaga",
    "horario disponivel",
    "disponibilidade",
    "doutor",
    "doutora",
    "medico",
    "medica",
    "especialista",
    "oftalmologista",
    "cardiologista",
    "dermatologista",
    "clinico geral",
]

KEYWORDS_DUVIDA_ADM = [
    "endereco",
    "localizacao",
    "onde fica",
    "estacionamento",
    "horario de funcionamento",
    "que horas abre",
    "que horas fecha",
    "convenio",
    "plano de saude",
    "atende unimed",
    "atende bradesco",
    "atende sulamerica",
]

KEYWORDS_FINANCEIRO = [
    "valor",
    "preco",
    "quanto custa",
    "forma de pagamento",
    "pagamento",
    "pix",
    "cartao",
    "parcelamento",
    "recibo",
    "nota fiscal",
    "reembolso",
    "orcamento",
]


class ResultadoTriagem(NamedTuple):
    intencao: IntentEnum
    confianca: float
    requer_atencao_humana: bool
    motivo_escalonamento: str | None


def executar_triagem_deterministica(texto: str, limiar_confianca: float = 0.6) -> ResultadoTriagem:
    """Executa a triagem determinística com normalização, detecção de urgência e negação.

    REGRA FUNDAMENTAL: A detecção de urgência é prioritária, determinística e
    NUNCA pode ser rebaixada por qualquer provedor subsequente.
    """
    texto_norm = normalizar_texto(texto)

    # 1. Checagem Determinística de Urgência
    is_urgente, sintoma = detectar_urgencia_clinica(texto_norm)
    if is_urgente:
        return ResultadoTriagem(
            intencao=IntentEnum.URGENCIA_CLINICA,
            confianca=1.0,
            requer_atencao_humana=True,
            motivo_escalonamento=f"Detectado sintoma ou emergência clínica ('{sintoma}'). "
            "Atenção humana imediata necessária; rascunho de resposta bloqueado.",
        )

    # 2. Classificação de Intenção Administrativa
    # Remarcação tem prioridade léxica sobre agendamento simples
    if any(k in texto_norm for k in KEYWORDS_REMARCACAO):
        intencao = IntentEnum.REMARCACAO
        confianca = 0.90
    elif any(k in texto_norm for k in KEYWORDS_FINANCEIRO):
        intencao = IntentEnum.FINANCEIRO
        confianca = 0.88
    elif any(k in texto_norm for k in KEYWORDS_DUVIDA_ADM):
        intencao = IntentEnum.DUVIDA_ADMINISTRATIVA
        confianca = 0.85
    elif any(k in texto_norm for k in KEYWORDS_AGENDAMENTO):
        intencao = IntentEnum.AGENDAMENTO
        confianca = 0.85
    else:
        intencao = IntentEnum.OUTRO
        # Mensagens genéricas ou curtas têm baixa confiança
        confianca = 0.35

    # 3. Verificação de Limiar de Confiança
    if confianca < limiar_confianca:
        return ResultadoTriagem(
            intencao=intencao,
            confianca=confianca,
            requer_atencao_humana=True,
            motivo_escalonamento=f"Confiança de classificação ({confianca:.2f}) abaixo "
            f"do limiar mínimo ({limiar_confianca:.2f}). Encaminhado para análise manual.",
        )

    return ResultadoTriagem(
        intencao=intencao,
        confianca=confianca,
        requer_atencao_humana=False,
        motivo_escalonamento=None,
    )
