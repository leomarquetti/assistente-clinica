"""Testes unitários exaustivos do serviço de privacidade e mascaramento best-effort."""

from app.services.privacidade import (
    mascarar_dados_pessoais,
    validar_digitos_cpf,
)


def test_validar_digitos_cpf_sucesso() -> None:
    # 52998224725 é um CPF com dígitos verificadores matematicamente válidos
    assert validar_digitos_cpf("52998224725") is True
    # 11144477735 é válido
    assert validar_digitos_cpf("11144477735") is True


def test_validar_digitos_cpf_falhas() -> None:
    # Dígitos repetidos
    assert validar_digitos_cpf("11111111111") is False
    assert validar_digitos_cpf("00000000000") is False
    # Tamanho incorreto
    assert validar_digitos_cpf("1234567890") is False
    assert validar_digitos_cpf("123456789012") is False
    # Dígito verificador incorreto
    assert validar_digitos_cpf("12345678900") is False
    # Não numérico
    assert validar_digitos_cpf("1234567890a") is False


def test_mascarar_cpf_formatado() -> None:
    texto = "Meu documento é 111.444.777-35 para o cadastro."
    resultado = mascarar_dados_pessoais(texto)
    assert "111.444.777-35" not in resultado
    assert "[CPF MASCARADO]" in resultado


def test_distinguir_cpf_desformatado_de_telefone_celular() -> None:
    # CPF válido desformatado de 11 dígitos
    texto_cpf = "Segue o número 52998224725 para verificação."
    resultado_cpf = mascarar_dados_pessoais(texto_cpf)
    assert "52998224725" not in resultado_cpf
    assert "[CPF MASCARADO]" in resultado_cpf

    # Número de celular com DDD 11 e 9 dígitos (total 11 dígitos, não é CPF válido)
    texto_tel = "Pode me chamar no whats 11987654321 hoje."
    resultado_tel = mascarar_dados_pessoais(texto_tel)
    assert "11987654321" not in resultado_tel
    assert "[TELEFONE MASCARADO]" in resultado_tel


def test_mascarar_telefones_diversos_formatos() -> None:
    exemplos = [
        "Ligue para (11) 98765-4321 por favor.",
        "Contato: +55 21 99999-8888.",
        "Telefone fixo da empresa: (11) 3333-4444.",
        "Me ligue no 19 98888-7777 urgente.",
    ]
    for texto in exemplos:
        resultado = mascarar_dados_pessoais(texto)
        assert "[TELEFONE MASCARADO]" in resultado


def test_mascarar_emails() -> None:
    texto = "Envie o comprovante para paciente.ficticio@exemplo.com.br ou teste@gmail.com."
    resultado = mascarar_dados_pessoais(texto)
    assert "paciente.ficticio@exemplo.com.br" not in resultado
    assert "teste@gmail.com" not in resultado
    assert "[EMAIL MASCARADO]" in resultado


def test_mascarar_cep() -> None:
    texto = "Moro na rua das Flores, CEP 01310-100 próximo ao metrô."
    resultado = mascarar_dados_pessoais(texto)
    assert "01310-100" not in resultado
    assert "[CEP MASCARADO]" in resultado

    texto_desformatado = "Meu cep: 01310100."
    resultado_desformatado = mascarar_dados_pessoais(texto_desformatado)
    assert "01310100" not in resultado_desformatado
    assert "[CEP MASCARADO]" in resultado_desformatado


def test_mascarar_rg() -> None:
    texto = "Meu RG é 12.345.678-9 expedido pela SSP."
    resultado = mascarar_dados_pessoais(texto)
    assert "12.345.678-9" not in resultado
    assert "[RG MASCARADO]" in resultado


def test_mascarar_data_nascimento() -> None:
    texto = "Nasci em 15/08/1990 e gostaria de agendar um retorno."
    resultado = mascarar_dados_pessoais(texto)
    assert "15/08/1990" not in resultado
    assert "[DATA MASCARADA]" in resultado


def test_mascarar_nomes_declarados() -> None:
    textos = [
        (
            "Olá, me chamo Carlos Alberto de Souza e quero marcar consulta.",
            "Carlos Alberto de Souza",
        ),
        ("Boa tarde, sou a Maria Eduarda Santos.", "Maria Eduarda Santos"),
        ("Oi, meu nome é Fernanda Lima.", "Fernanda Lima"),
    ]
    for texto, nome in textos:
        resultado = mascarar_dados_pessoais(texto)
        assert nome not in resultado
        assert "[NOME MASCARADO]" in resultado


def test_mascarar_texto_vazio_ou_nulo() -> None:
    assert mascarar_dados_pessoais(None) == ""
    assert mascarar_dados_pessoais("") == ""
