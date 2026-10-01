"""Rotas da API para gerenciamento de mensagens, aprovação, auditoria e saúde."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Security, status

from app.api.auth import require_atendente, require_gestor
from app.api.deps import get_pipeline_service, get_storage
from app.api.limiter import limiter
from app.config import settings
from app.domain.intents import RoleEnum
from app.domain.schemas import (
    AprovacaoRequest,
    AuditoriaLogResponse,
    HealthCheckResponse,
    MensagemCriar,
    MensagemResponse,
    RejeicaoRequest,
)
from app.domain.state_machine import StateTransitionError
from app.services.pipeline import PipelineService
from app.storage.base import Storage

router = APIRouter()


@router.post(
    "/mensagens",
    response_model=MensagemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Receber mensagem de paciente fictício",
    description="Recebe mensagem, aplica mascaramento preventivo, realiza triagem determinística e sugere rascunho.",
)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def criar_mensagem(
    request: Request,
    payload: MensagemCriar,
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> MensagemResponse:
    """Recebe mensagem bruta, anonimiza dados pessoais e executa triagem."""
    return await pipeline.processar_mensagem(payload)


@router.get(
    "/mensagens/{mensagem_id}",
    response_model=MensagemResponse,
    summary="Consultar mensagem processada (Equipe de Atendimento)",
    description="Retorna os detalhes de uma mensagem processada e rascunho sugerido. Protegido para atendentes e gestores. O identificador é um UUIDv4 aleatório para impedir ataques de enumeração.",
)
async def obter_mensagem(
    mensagem_id: str,
    role: RoleEnum = Security(require_atendente),
    storage: Storage = Depends(get_storage),
) -> MensagemResponse:
    """Busca mensagem por UUIDv4 autenticado."""
    mensagem = await storage.obter_mensagem(mensagem_id)
    if not mensagem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mensagem com id '{mensagem_id}' não encontrada.",
        )
    return mensagem


@router.post(
    "/mensagens/{mensagem_id}/aprovar",
    response_model=MensagemResponse,
    summary="Aprovar rascunho de resposta (Ação Humana)",
    description="Requer autenticação com papel 'atendente' ou 'gestor'. Valida máquina de estados (409 em transições inválidas).",
)
async def aprovar_mensagem(
    mensagem_id: str,
    payload: AprovacaoRequest,
    role: RoleEnum = Security(require_atendente),
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> MensagemResponse:
    """Aprova ou edita o rascunho para envio, validando a transição de estado."""
    try:
        return await pipeline.aprovar_mensagem(
            mensagem_id=mensagem_id,
            requisicao=payload,
            operador_autenticado=f"{role.value}:{payload.aprovado_por}",
        )
    except KeyError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mensagem com id '{mensagem_id}' não encontrada.",
        ) from err
    except StateTransitionError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err


@router.post(
    "/mensagens/{mensagem_id}/rejeitar",
    response_model=MensagemResponse,
    summary="Rejeitar ou descartar mensagem",
    description="Requer autenticação com papel 'atendente' ou 'gestor'. Valida máquina de estados (409 em transições inválidas).",
)
async def rejeitar_mensagem(
    mensagem_id: str,
    payload: RejeicaoRequest,
    role: RoleEnum = Security(require_atendente),
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> MensagemResponse:
    """Rejeita ou descarta a mensagem."""
    try:
        return await pipeline.rejeitar_mensagem(
            mensagem_id=mensagem_id,
            requisicao=payload,
            operador_autenticado=f"{role.value}:{payload.rejeitado_por}",
        )
    except KeyError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mensagem com id '{mensagem_id}' não encontrada.",
        ) from err
    except StateTransitionError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err


@router.get(
    "/auditoria",
    response_model=list[AuditoriaLogResponse],
    summary="Consultar trilha de auditoria append-only",
    description="Requer autenticação estrita com papel 'gestor'. Retorna eventos sem dados sensíveis em texto claro.",
)
async def listar_auditoria(
    limite: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    role: RoleEnum = Security(require_gestor),
    storage: Storage = Depends(get_storage),
) -> list[AuditoriaLogResponse]:
    """Lista eventos cronológicos de auditoria."""
    return await storage.listar_auditoria(limite=limite, offset=offset)


@router.get(
    "/saude",
    response_model=HealthCheckResponse,
    summary="Verificação de integridade e metadados",
    description="Informa o status do serviço, modo demo ativo e provedor configurado.",
)
async def verificar_saude() -> HealthCheckResponse:
    """Retorna o status operacional da aplicação."""
    return HealthCheckResponse(
        status="ok",
        app_mode=settings.APP_MODE,
        llm_provider=settings.LLM_PROVIDER,
        storage=settings.STORAGE,
        aviso="Modo de demonstração ativo com IA simulada (baseada em regras). "
        "Não utilizar para decisões médicas reais.",
    )
