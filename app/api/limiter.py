"""Instância de rate limiting para proteção contra abusos e DoS."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Limitador baseado no endereço IP do cliente
limiter = Limiter(key_func=get_remote_address)
