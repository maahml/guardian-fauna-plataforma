"""Funções de data e hora usadas no formulário de ocorrências."""

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo


LOCAL_TIMEZONE = ZoneInfo("America/Sao_Paulo")


def event_time_to_utc(event_date, event_time):
    """Converte data e hora de São Paulo para o formato UTC esperado pela API."""
    if not isinstance(event_date, date) or isinstance(event_date, datetime):
        raise ValueError("Informe uma data válida para a apreensão.")
    if not isinstance(event_time, time):
        raise ValueError("Informe um horário válido para a apreensão.")
    local_event = datetime.combine(event_date, event_time).replace(tzinfo=LOCAL_TIMEZONE)
    utc_event = local_event.astimezone(timezone.utc)
    return utc_event.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
