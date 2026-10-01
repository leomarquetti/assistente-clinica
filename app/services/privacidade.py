"""Módulo de privacidade e higienização de dados pessoais.

Aplica boas práticas de privacidade com mascaramento best-effort (heurístico e regex),
assegurando que nenhum dado pessoal sensível (CPF com dígitos verificadores válidos,
telefones com DDD, e-mails, CEP, RG, datas de nascimento e nomes declarados)
seja enviado a provedores de IA ou persistido em texto claro.
"""

import re
from re import Pattern


def validar_digitos_cpf(cpf_numeros: str) -> bool:
    """Valida se uma sequência de 11 dígitos possui dígitos verificadores válidos de CPF.

    Utilizado para distinguir deterministicamente entre um CPF desformatado e um
    número de telefone celular brasileiro (ambos possuem 11 dígitos).
    """
    if len(cpf_numeros) != 11 or not cpf_numeros.isdigit():
        return False

    # CPFs com todos os dígitos iguais são inválidos
    if cpf_numeros == cpf_numeros[0] * 11:
        return False

    # Primeiro dígito verificador
    soma_1 = sum(int(cpf_numeros[i]) * (10 - i) for i in range(9))
    resto_1 = soma_1 % 11
    digito_1 = 0 if resto_1 < 2 else 11 - resto_1

    if int(cpf_numeros[9]) != digito_1:
        return False

    # Segundo dígito verificador
    soma_2 = sum(int(cpf_numeros[i]) * (11 - i) for i in range(10))
    resto_2 = soma_2 % 11
    digito_2 = 0 if resto_2 < 2 else 11 - resto_2

    return int(cpf_numeros[10]) == digito_2


# Expressões regulares pré-compiladas
REGEX_EMAIL: Pattern[str] = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# CEP formatado ou antecedido de menção a CEP
REGEX_CEP: Pattern[str] = re.compile(
    r"\b\d{5}-\d{3}\b|\bcep[:\s]+(?:\d{8}|\d{5}-\d{3})\b",
    re.IGNORECASE,
)

# RG formatado (comum em SP, RJ, etc: XX.XXX.XXX-X ou similar)
REGEX_RG: Pattern[str] = re.compile(
    r"\b\d{1,2}\.\d{3}\.\d{3}-[\dxX]\b|\brg[:\s]+(?:\d{7,9}-?[\dxX]|\d{7,9})\b",
    re.IGNORECASE,
)

# Data de nascimento (DD/MM/AAAA)
REGEX_DATA_NASCIMENTO: Pattern[str] = re.compile(
    r"\b(?:0[1-9]|[12][0-9]|3[01])/(?:0[1-9]|1[0-2])/(?:19\d{2}|20\d{2})\b"
)

# CPF formatado (XXX.XXX.XXX-XX)
REGEX_CPF_FORMATADO: Pattern[str] = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")

# Padrão genérico de 11 dígitos contínuos (para desambiguação entre CPF e celular com DDD)
REGEX_11_DIGITOS: Pattern[str] = re.compile(r"\b\d{11}\b")

# Telefone brasileiro com DDD (formatado ou com espaços/hífen, ou celular com 9)
REGEX_TELEFONE: Pattern[str] = re.compile(
    r"(?:\+?55\s?)?(?:\(?\b[1-9]{2}\)?\s?)?(?:9\s?\d{4}[-.\s]?\d{4}|[2-5]\d{3}[-.\s]?\d{4})\b"
)

# Introduções comuns a nomes próprios de pacientes
REGEX_NOME_INTRODUZIDO: Pattern[str] = re.compile(
    r"(\b(?:me chamo|sou\s+(?:o|a)|meu nome [eé]|aqui [eé]\s+(?:o|a)|paciente|sr\.?|sra\.?|dr\.?|dra\.?)\s+)"
    r"([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s+(?:de|da|do|dos|das|e)?\s*[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)*)",
    re.IGNORECASE,
)

# Nomes próprios compostos com 2 ou mais palavras capitalizadas
REGEX_NOME_COMPOSTO: Pattern[str] = re.compile(
    r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s+(?:de|da|do|dos|das|e)\s+|\s+)"
    r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s+(?:de|da|do|dos|das|e)\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+|\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)*\b"
)


def _substituir_cpfs_e_telefones(texto: str) -> str:
    """Substitui CPFs formatados e desambigua números de 11 dígitos entre CPF e telefone."""

    # 1. Substituir CPFs explicitamente formatados (XXX.XXX.XXX-XX) se dígitos forem válidos
    def repl_cpf_formatado(match: re.Match[str]) -> str:
        raw = match.group(0)
        digits = re.sub(r"\D", "", raw)
        if validar_digitos_cpf(digits):
            return "[CPF MASCARADO]"
        return raw

    texto = REGEX_CPF_FORMATADO.sub(repl_cpf_formatado, texto)

    # 2. Desambiguação de sequências de 11 dígitos contínuos
    def repl_11_digitos(match: re.Match[str]) -> str:
        digits = match.group(0)
        if validar_digitos_cpf(digits):
            return "[CPF MASCARADO]"
        # Se não é CPF válido, mas começa com DDD brasileiro (11 a 99) e dígito 9 (celular)
        ddd = int(digits[:2])
        if 11 <= ddd <= 99 and digits[2] == "9":
            return "[TELEFONE MASCARADO]"
        return digits

    texto = REGEX_11_DIGITOS.sub(repl_11_digitos, texto)

    # 3. Substituir demais padrões de telefone
    texto = REGEX_TELEFONE.sub("[TELEFONE MASCARADO]", texto)

    return texto


def mascarar_dados_pessoais(texto: str | None) -> str:
    """Aplica mascaramento best-effort de PII em um texto.

    Cobre:
    - E-mails
    - CEPs
    - RGs
    - Datas de nascimento (DD/MM/AAAA)
    - CPFs (com validação de dígitos verificadores)
    - Telefones (celulares e fixos)
    - Nomes próprios (introduzidos ou compostos)
    """
    if not texto:
        return ""

    resultado = texto

    # E-mails
    resultado = REGEX_EMAIL.sub("[EMAIL MASCARADO]", resultado)

    # CEPs
    resultado = REGEX_CEP.sub("[CEP MASCARADO]", resultado)

    # RGs
    resultado = REGEX_RG.sub("[RG MASCARADO]", resultado)

    # Datas de Nascimento
    resultado = REGEX_DATA_NASCIMENTO.sub("[DATA MASCARADA]", resultado)

    # CPFs e Telefones (com validação de dígito de CPF)
    resultado = _substituir_cpfs_e_telefones(resultado)

    # Nomes introduzidos expressamente (mantendo a preposição/verbo introdutório)
    def repl_nome_introduzido(match: re.Match[str]) -> str:
        introducao = match.group(1)
        return f"{introducao}[NOME MASCARADO]"

    resultado = REGEX_NOME_INTRODUZIDO.sub(repl_nome_introduzido, resultado)

    # Nomes próprios compostos remanescentes (ex.: em identificadores ou textos livres)
    resultado = REGEX_NOME_COMPOSTO.sub("[NOME MASCARADO]", resultado)

    return resultado
