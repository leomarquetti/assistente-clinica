"""Implementação de persistência relacional em SQLite local para demonstração."""

import asyncio
import json
import sqlite3
from datetime import datetime
from typing import Any

from app.domain.intents import IntentEnum, StatusMensagemEnum
from app.domain.schemas import AuditoriaLogResponse, MensagemResponse
from app.storage.base import Storage


class SqliteStorage(Storage):
    """Armazenamento persistente local em SQLite com tabelas relacionais e thread-safety."""

    def __init__(self, db_path: str = "clinic_demo.db"):
        self.db_path = db_path
        self._lock = asyncio.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Cria as tabelas de mensagens e auditoria append-only caso não existam."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS mensagens (
                    id TEXT PRIMARY KEY,
                    texto_mascarado TEXT NOT NULL,
                    paciente_identificador_mascarado TEXT,
                    intencao TEXT NOT NULL,
                    confianca REAL NOT NULL,
                    requer_atencao_humana INTEGER NOT NULL,
                    motivo_escalonamento TEXT,
                    rascunho_resposta TEXT,
                    status TEXT NOT NULL,
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL,
                    texto_aprovado TEXT,
                    aprovado_por TEXT,
                    observacoes TEXT
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auditoria (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    mensagem_id TEXT,
                    acao TEXT NOT NULL,
                    operador TEXT NOT NULL,
                    detalhes TEXT NOT NULL
                )
                """
            )
            conn.commit()

    async def salvar_mensagem(self, mensagem: MensagemResponse) -> None:
        async with self._lock:
            await asyncio.to_thread(self._salvar_mensagem_sync, mensagem)

    def _salvar_mensagem_sync(self, mensagem: MensagemResponse) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO mensagens (
                    id, texto_mascarado, paciente_identificador_mascarado,
                    intencao, confianca, requer_atencao_humana, motivo_escalonamento,
                    rascunho_resposta, status, criado_em, atualizado_em,
                    texto_aprovado, aprovado_por, observacoes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mensagem.id,
                    mensagem.texto_mascarado,
                    mensagem.paciente_identificador_mascarado,
                    mensagem.intencao.value,
                    mensagem.confianca,
                    1 if mensagem.requer_atencao_humana else 0,
                    mensagem.motivo_escalonamento,
                    mensagem.rascunho_resposta,
                    mensagem.status.value,
                    mensagem.criado_em.isoformat(),
                    mensagem.atualizado_em.isoformat(),
                    mensagem.texto_aprovado,
                    mensagem.aprovado_por,
                    mensagem.observacoes,
                ),
            )
            conn.commit()

    async def obter_mensagem(self, mensagem_id: str) -> MensagemResponse | None:
        async with self._lock:
            return await asyncio.to_thread(self._obter_mensagem_sync, mensagem_id)

    def _obter_mensagem_sync(self, mensagem_id: str) -> MensagemResponse | None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM mensagens WHERE id = ?", (mensagem_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_mensagem(row)

    async def atualizar_mensagem(self, mensagem: MensagemResponse) -> None:
        async with self._lock:
            await asyncio.to_thread(self._atualizar_mensagem_sync, mensagem)

    def _atualizar_mensagem_sync(self, mensagem: MensagemResponse) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE mensagens SET
                    status = ?,
                    atualizado_em = ?,
                    texto_aprovado = ?,
                    aprovado_por = ?,
                    observacoes = ?
                WHERE id = ?
                """,
                (
                    mensagem.status.value,
                    mensagem.atualizado_em.isoformat(),
                    mensagem.texto_aprovado,
                    mensagem.aprovado_por,
                    mensagem.observacoes,
                    mensagem.id,
                ),
            )
            if cursor.rowcount == 0:
                raise KeyError(f"Mensagem {mensagem.id} não encontrada para atualização.")
            conn.commit()

    async def registrar_auditoria(self, registro: AuditoriaLogResponse) -> None:
        async with self._lock:
            await asyncio.to_thread(self._registrar_auditoria_sync, registro)

    def _registrar_auditoria_sync(self, registro: AuditoriaLogResponse) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO auditoria (id, timestamp, mensagem_id, acao, operador, detalhes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    registro.id,
                    registro.timestamp.isoformat(),
                    registro.mensagem_id,
                    registro.acao,
                    registro.operador,
                    json.dumps(registro.detalhes, ensure_ascii=False),
                ),
            )
            conn.commit()

    async def listar_auditoria(
        self, limite: int = 50, offset: int = 0
    ) -> list[AuditoriaLogResponse]:
        async with self._lock:
            return await asyncio.to_thread(self._listar_auditoria_sync, limite, offset)

    def _listar_auditoria_sync(self, limite: int, offset: int) -> list[AuditoriaLogResponse]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM auditoria ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limite, offset),
            )
            rows = cursor.fetchall()
            return [
                AuditoriaLogResponse(
                    id=row["id"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    mensagem_id=row["mensagem_id"],
                    acao=row["acao"],
                    operador=row["operador"],
                    detalhes=json.loads(row["detalhes"]),
                )
                for row in rows
            ]

    async def limpar_dados(self) -> None:
        async with self._lock:
            await asyncio.to_thread(self._limpar_dados_sync)

    def _limpar_dados_sync(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM mensagens")
            cursor.execute("DELETE FROM auditoria")
            conn.commit()

    def _row_to_mensagem(self, row: Any) -> MensagemResponse:
        return MensagemResponse(
            id=row["id"],
            texto_mascarado=row["texto_mascarado"],
            paciente_identificador_mascarado=row["paciente_identificador_mascarado"],
            intencao=IntentEnum(row["intencao"]),
            confianca=float(row["confianca"]),
            requer_atencao_humana=bool(row["requer_atencao_humana"]),
            motivo_escalonamento=row["motivo_escalonamento"],
            rascunho_resposta=row["rascunho_resposta"],
            status=StatusMensagemEnum(row["status"]),
            criado_em=datetime.fromisoformat(row["criado_em"]),
            atualizado_em=datetime.fromisoformat(row["atualizado_em"]),
            texto_aprovado=row["texto_aprovado"],
            aprovado_por=row["aprovado_por"],
            observacoes=row["observacoes"],
        )
