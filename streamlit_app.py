"""Guardian Fauna web interface, implemented in Streamlit as specified in the report."""

import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

from streamlit_ui.api_client import APIClient, APIClientError
from streamlit_ui.time_utils import event_time_to_utc


LOCAL_TIMEZONE = ZoneInfo("America/Sao_Paulo")
DEFAULT_API_URL = "https://gcyber.com.br/api/v1"


def api_base_url():
    configured = os.getenv("API_BASE_URL", "").strip()
    if configured:
        return configured
    try:
        return st.secrets.get("API_BASE_URL", DEFAULT_API_URL)
    except Exception:
        return DEFAULT_API_URL


def api(token=None):
    return APIClient(api_base_url(), token=token)


def display_error(error):
    if error.status_code == 401 and st.session_state.get("token"):
        st.session_state.clear()
        st.rerun()
    st.error(str(error))


def login_and_access_request():
    st.title("Guardian Fauna")
    st.write("Registro e consulta de apreensões com dados sensíveis cifrados.")
    sign_in, request_access = st.tabs(["Entrar", "Solicitar acesso"])

    with sign_in:
        with st.form("login_form"):
            email = st.text_input("E-mail institucional", key="login_email")
            password = st.text_input("Senha", type="password", key="login_password")
            submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
        if submitted:
            try:
                user = api().request("POST", "/auth/login", {"email": email, "senha": password})
                st.session_state["token"] = user["token"]
                st.session_state["user"] = {
                    "id": user["id"],
                    "nome": user["nome"],
                    "perfil": user["perfil_usuario"],
                    "orgao": user.get("orgao", ""),
                }
                st.rerun()
            except APIClientError as error:
                st.error(str(error))

    with request_access:
        if st.session_state.get("access_request_sent"):
            st.success("Solicitação enviada. O administrador do órgão precisa aprovar o acesso antes do primeiro login.")
            if st.button("Enviar outra solicitação"):
                st.session_state.pop("access_request_sent", None)
                st.rerun()
            return
        with st.form("access_request_form"):
            name = st.text_input("Nome completo")
            email = st.text_input("E-mail institucional")
            organization = st.text_input("Órgão ou posto de fiscalização")
            profile = st.selectbox("Perfil solicitado", ["Agente", "Coordenador"])
            justification = st.text_area("Por que você precisa de acesso?")
            password = st.text_input("Senha (mínimo de 10 caracteres)", type="password")
            confirm_password = st.text_input("Confirme a senha", type="password")
            submitted = st.form_submit_button("Enviar solicitação", type="primary", use_container_width=True)
        if submitted:
            if password != confirm_password:
                st.error("As senhas não coincidem.")
            else:
                try:
                    api().request("POST", "/solicitacoes", {
                        "nome": name,
                        "email": email,
                        "orgao": organization,
                        "perfilDesejado": profile,
                        "justificativa": justification,
                        "senha": password,
                    })
                    st.session_state["access_request_sent"] = True
                    st.rerun()
                except APIClientError as error:
                    st.error(str(error))


def logout():
    token = st.session_state.get("token")
    if token:
        try:
            api(token).request("POST", "/auth/logout")
        except APIClientError:
            pass
    st.session_state.clear()
    st.rerun()


def dashboard_page(client):
    st.title("Painel")
    try:
        summary = client.request("GET", "/dashboard")
    except APIClientError as error:
        display_error(error)
        return
    columns = st.columns(3)
    columns[0].metric("Operações ativas", summary.get("operacoes_ativas", 0))
    columns[1].metric("Apreensões registradas", summary.get("ocorrencias_registradas", 0))
    columns[2].metric("Abrigos cadastrados", summary.get("abrigos_cadastrados", 0))
    st.info("Protótipo acadêmico. A Cifra de Hill é didática e não protege informações reais de operação.")


def operations_page(client):
    st.title("Operações")
    st.caption("O código identifica a operação. O segredo é compartilhado com a equipe e não é armazenado.")
    with st.form("operation_form"):
        name = st.text_input("Nome da operação")
        code = st.text_input("Código (ex.: OP-2026-ASA)").upper().strip()
        start_date = st.date_input("Data de início")
        secret = st.text_input("Segredo compartilhado", type="password")
        submitted = st.form_submit_button("Cadastrar operação", type="primary")
    if submitted:
        try:
            result = client.request("POST", "/operacoes", {
                "nome": name,
                "codigo": code,
                "dataInicio": start_date.isoformat(),
                "segredoBase": secret,
            })
            st.success("Operação {} cadastrada.".format(result["codigo"]))
        except APIClientError as error:
            display_error(error)
    st.subheader("Operações disponíveis")
    try:
        rows = client.request("GET", "/operacoes")
        if rows:
            st.dataframe([
                {"Código": row["codigo"], "Nome": row["nome"], "Início": row["inicio"], "Status": row["status"]}
                for row in rows
            ], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma operação cadastrada.")
    except APIClientError as error:
        display_error(error)


def occurrence_page(client):
    st.title("Registrar apreensão")
    st.write("Informe a data e a hora em que a apreensão aconteceu. Esse instante participa da geração da chave.")
    try:
        operations = client.request("GET", "/operacoes")
    except APIClientError as error:
        display_error(error)
        return
    active = [row for row in operations if row.get("status") == "Ativa"]
    if not active:
        st.info("Ainda não há operação ativa. Peça ao coordenador que cadastre uma operação.")
        return

    now_local = datetime.now(LOCAL_TIMEZONE)
    with st.form("occurrence_form"):
        selected = st.selectbox(
            "Operação",
            active,
            format_func=lambda item: "{} — {}".format(item["codigo"], item["nome"]),
        )
        event_date = st.date_input("Data da apreensão", value=now_local.date(), format="DD/MM/YYYY")
        event_time = st.time_input("Horário da apreensão (São Paulo)", value=now_local.time().replace(microsecond=0), step=timedelta(seconds=1))
        secret = st.text_input("Segredo da operação", type="password")
        location = st.text_input("Local da apreensão")
        lat_col, lon_col = st.columns(2)
        latitude = lat_col.text_input("Latitude (graus decimais)", placeholder="-23.550520")
        longitude = lon_col.text_input("Longitude (graus decimais)", placeholder="-46.633308")
        agent = st.text_input("Agente responsável")
        details = st.text_area("Relato da apreensão", height=140)
        submitted = st.form_submit_button("Cifrar e registrar", type="primary", use_container_width=True)
    if submitted:
        try:
            event_timestamp = event_time_to_utc(event_date, event_time)
            coordinates = "{}, {}".format(latitude.strip(), longitude.strip())
            result = client.request("POST", "/ocorrencias", {
                "operacao_id": selected["codigo"],
                "segredo_agente": secret,
                "data_hora_apreensao": event_timestamp,
                "dados_sensiveis": {
                    "localizacao": location,
                    "coordenadas": coordinates,
                    "agente_responsavel": agent,
                    "detalhes": details,
                },
            })
            st.success("Apreensão cifrada e registrada. Código: {}".format(result["id"]))
            st.caption("Horário registrado em UTC: {}".format(result["timestamp"]))
        except ValueError as error:
            st.error(str(error))
        except APIClientError as error:
            display_error(error)


def history_page(client):
    st.title("Histórico de apreensões")
    st.write("Os campos sigilosos aparecem cifrados. Para ver os dados de um registro, informe o segredo da operação.")
    try:
        records = client.request("GET", "/ocorrencias")
    except APIClientError as error:
        display_error(error)
        return
    if not records:
        st.info("Nenhuma apreensão registrada.")
        return
    for record in records:
        title = "Registro {} · {} · {}".format(
            record["id"], record["operacao_id"], record["timestamp"]
        )
        with st.expander(title):
            st.caption("Conteúdo cifrado (hexadecimal)")
            st.code(record["bloco_cifrado"], language=None)
            secret_key = "secret_for_{}".format(record["id"])
            with st.form("decrypt_form_{}".format(record["id"])):
                secret = st.text_input("Segredo da operação", type="password", key=secret_key)
                submitted = st.form_submit_button("Decifrar este registro")
            if submitted:
                try:
                    result = client.request(
                        "POST",
                        "/ocorrencias/{}/decifrar".format(record["id"]),
                        {"segredo_operacao": secret},
                    )
                    st.session_state["plaintext_{}".format(record["id"])] = result
                    st.success("Dados apresentados nesta sessão.")
                except APIClientError as error:
                    display_error(error)
            plaintext = st.session_state.get("plaintext_{}".format(record["id"]))
            if plaintext:
                st.subheader("Detalhes da apreensão")
                st.write("**Local:** {}".format(plaintext.get("localizacao", "")))
                st.write("**Coordenadas:** {}".format(plaintext.get("coordenadas", "")))
                st.write("**Agente:** {}".format(plaintext.get("agente_responsavel", "")))
                st.write("**Relato:** {}".format(plaintext.get("detalhes", "")))


def access_requests_page(client):
    st.title("Solicitações de acesso")
    try:
        requests = client.request("GET", "/admin/solicitacoes")
    except APIClientError as error:
        display_error(error)
        return
    if not requests:
        st.info("Nenhuma solicitação pendente.")
        return
    for request in requests:
        with st.expander("{} — {}".format(request["nome"], request["orgao"])):
            st.write("**E-mail:** {}".format(request["email"]))
            st.write("**Perfil solicitado:** {}".format(request["perfil"]))
            st.write(request["justificativa"])
            approve, reject = st.columns(2)
            if approve.button("Aprovar", key="approve_{}".format(request["id"]), type="primary"):
                review_request(client, request["id"], "aprovar")
            if reject.button("Rejeitar", key="reject_{}".format(request["id"])):
                review_request(client, request["id"], "rejeitar")


def review_request(client, request_id, action):
    try:
        result = client.request("POST", "/admin/solicitacoes/{}".format(request_id), {"acao": action})
        st.success("Solicitação {}.".format(result["status"].lower()))
        st.rerun()
    except APIClientError as error:
        display_error(error)


def main():
    st.set_page_config(page_title="Guardian Fauna", page_icon="🦜", layout="wide")
    st.title("Guardian Fauna")
    st.caption("Registro de apreensões e consulta de informações cifradas")

    if not st.session_state.get("token") or not st.session_state.get("user"):
        login_and_access_request()
        st.divider()
        st.caption("Protótipo acadêmico. Não use dados reais sigilosos: a Cifra de Hill não é adequada para operações reais.")
        return

    user = st.session_state["user"]
    client = api(st.session_state["token"])
    with st.sidebar:
        st.subheader("Guardian Fauna")
        st.write(user.get("nome", "Usuário"))
        st.caption("{} · {}".format(user.get("perfil", ""), user.get("orgao", "")))
        pages = ["Painel", "Registrar apreensão", "Histórico"]
        if user.get("perfil") in ("Coordenador", "Admin"):
            pages.insert(1, "Operações")
        if user.get("perfil") == "Admin":
            pages.append("Solicitações de acesso")
        selected_page = st.radio("Navegação", pages, label_visibility="collapsed")
        st.button("Sair", on_click=logout, use_container_width=True)
        st.divider()
        st.caption("Uso acadêmico. Hill não deve proteger dados operacionais reais.")

    if selected_page == "Painel":
        dashboard_page(client)
    elif selected_page == "Operações":
        operations_page(client)
    elif selected_page == "Registrar apreensão":
        occurrence_page(client)
    elif selected_page == "Histórico":
        history_page(client)
    elif selected_page == "Solicitações de acesso":
        access_requests_page(client)


if __name__ == "__main__":
    main()
