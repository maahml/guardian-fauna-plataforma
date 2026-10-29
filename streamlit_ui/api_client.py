"""Cliente HTTP da interface para a API Python do Guardian Fauna."""

import requests


class APIClientError(Exception):
    """Erro da API apresentado sem incluir credenciais da requisição."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class APIClient:
    def __init__(self, base_url, token=None, timeout=20):
        self.base_url = (base_url or "").rstrip("/")
        self.token = token
        self.timeout = timeout
        if not self.base_url:
            raise ValueError("Configure a URL da API do Guardian Fauna.")

    def request(self, method, path, payload=None):
        url = self.base_url + "/" + (path or "").lstrip("/")
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise APIClientError("Não foi possível conectar à API. Tente novamente.") from exc

        if not response.ok:
            message = "A solicitação não foi concluída. Tente novamente."
            try:
                body = response.json()
                if isinstance(body, dict) and isinstance(body.get("message"), str):
                    message = body["message"]
            except ValueError:
                pass
            if response.status_code == 401:
                message = "Sua sessão expirou. Entre novamente."
            raise APIClientError(message, response.status_code)

        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError:
            raise APIClientError("A API retornou uma resposta inválida.")
