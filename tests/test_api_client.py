import unittest
from unittest.mock import Mock, patch

import requests

from streamlit_ui.api_client import APIClient, APIClientError


class APIClientTests(unittest.TestCase):
    @patch("streamlit_ui.api_client.requests.request")
    def test_request_sends_session_token_and_json_body(self, request):
        response = Mock()
        response.status_code = 201
        response.json.return_value = {"id": "8"}
        response.raise_for_status.return_value = None
        request.return_value = response
        client = APIClient("https://example.org/api/v1", token="session-token")

        result = client.request("POST", "/ocorrencias", {"x": 1})

        self.assertEqual(result, {"id": "8"})
        self.assertEqual(request.call_args.kwargs["headers"]["Authorization"], "Bearer session-token")
        self.assertEqual(request.call_args.kwargs["json"], {"x": 1})

    @patch("streamlit_ui.api_client.requests.request")
    def test_api_error_is_exposed_as_a_clear_message(self, request):
        response = Mock()
        response.ok = False
        response.status_code = 403
        response.json.return_value = {"message": "Segredo incorreto."}
        response.raise_for_status.side_effect = requests.HTTPError(response=response)
        request.return_value = response
        client = APIClient("https://example.org/api/v1")

        with self.assertRaisesRegex(APIClientError, "Segredo incorreto"):
            client.request("POST", "/ocorrencias/1/decifrar", {"segredo_operacao": "x"})


if __name__ == "__main__":
    unittest.main()
