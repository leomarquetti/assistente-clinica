"""Ponto de entrada da aplicação FastAPI com Swagger customizado e handlers seguros."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.limiter import limiter
from app.api.routes_mensagens import router
from app.domain.state_machine import StateTransitionError

API_DESCRIPTION = """
### ⚠️ AVISO DE MODO DE DEMONSTRAÇÃO E PRIVACIDADE (PORTFÓLIO)
Esta API opera em **modo de demonstração** com **IA simulada (baseada em regras)** e dados 100% fictícios.

- **Boas Práticas de Privacidade (Inspiradas na LGPD)**: Aplica mascaramento *best-effort* (heurístico/regex) de dados sensíveis antes de qualquer processamento ou log.
- **Segurança Clínica & Human-in-the-Loop**: O sistema **NÃO** responde dúvidas clínicas, **NÃO** diagnostica patologias e **NÃO** envia mensagens diretamente aos pacientes sem aprovação humana expressa.
- **Trilha de Auditoria**: Registros *append-only* com dados estritamente anonimizados.
- **Provedor Plugável**: Arquitetura desacoplada pronta para substituição por LLM real em ambiente controlado.
"""

app = FastAPI(
    title="Assistente de Atendimento para Clínicas (Modo Demo)",
    description=API_DESCRIPTION,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Acopla limitador de taxa ao estado da aplicação
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]


@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handler customizado para erros de validação da requisição.

    CRÍTICO PARA PRIVACIDADE: O FastAPI padrão ecoa o campo 'input' bruto do usuário,
    o que vazaria dados pessoais não validados na resposta HTTP 422.
    Este handler sanitiza os erros removendo o valor original de 'input'.
    """
    safe_errors: list[dict[str, Any]] = []
    for err in exc.errors():
        safe_error = {
            "type": err.get("type"),
            "loc": err.get("loc"),
            "msg": err.get("msg"),
        }
        safe_errors.append(safe_error)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": safe_errors},
    )


@app.exception_handler(StateTransitionError)
async def custom_state_transition_handler(
    request: Request, exc: StateTransitionError
) -> JSONResponse:
    """Converte erros de transição inválida da máquina de estados em HTTP 409 Conflict."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


# Registra rotas
app.include_router(router)


def custom_openapi() -> dict[str, Any]:
    """Customiza o schema OpenAPI para omitir o campo 'input' de ValidationError e declarar segurança."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        schemas = openapi_schema["components"]["schemas"]
        if "ValidationError" in schemas and "properties" in schemas["ValidationError"]:
            schemas["ValidationError"]["properties"].pop("input", None)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]
