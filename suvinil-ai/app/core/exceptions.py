"""Exceções customizadas e handlers para a API"""
from fastapi import HTTPException, status
from typing import Any, Optional


class SuvinilException(HTTPException):
    """Classe base para exceções customizadas da aplicação"""
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[dict[str, str]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundException(SuvinilException):
    """Recurso não encontrado (404)"""
    def __init__(self, resource: str = "Recurso", resource_id: Optional[str] = None):
        detail = f"{resource} não encontrado"
        if resource_id:
            detail += f" (ID: {resource_id})"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedException(SuvinilException):
    """Não autorizado (401)"""
    def __init__(self, detail: str = "Credenciais inválidas"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(SuvinilException):
    """Acesso negado (403)"""
    def __init__(self, detail: str = "Você não tem permissão para acessar este recurso"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BadRequestException(SuvinilException):
    """Requisição inválida (400)"""
    def __init__(self, detail: str = "Requisição inválida"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ConflictException(SuvinilException):
    """Conflito (409) - recurso já existe"""
    def __init__(self, resource: str = "Recurso", detail: Optional[str] = None):
        if not detail:
            detail = f"{resource} já existe"
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class InternalServerException(SuvinilException):
    """Erro interno do servidor (500)"""
    def __init__(self, detail: str = "Erro interno do servidor"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


# Exceções específicas do domínio
class PaintNotFoundException(NotFoundException):
    """Tinta não encontrada"""
    def __init__(self, paint_id: Optional[int] = None):
        super().__init__(resource="Tinta", resource_id=str(paint_id) if paint_id else None)


class UserNotFoundException(NotFoundException):
    """Usuário não encontrado"""
    def __init__(self, user_id: Optional[int] = None):
        super().__init__(resource="Usuário", resource_id=str(user_id) if user_id else None)


class UserAlreadyExistsException(ConflictException):
    """Usuário já existe (email/username duplicado)"""
    def __init__(self, field: str = "email"):
        detail = f"Usuário com este {field} já está cadastrado"
        super().__init__(resource="Usuário", detail=detail)


class InactiveUserException(BadRequestException):
    """Usuário inativo"""
    def __init__(self):
        super().__init__(detail="Usuário inativo")


class AIServiceException(InternalServerException):
    """Erro no serviço de IA"""
    def __init__(self, detail: str = "Erro ao processar solicitação de IA"):
        super().__init__(detail=detail)
