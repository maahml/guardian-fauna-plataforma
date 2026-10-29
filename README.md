# Guardian Fauna

Sistema para apoiar equipes de fiscalização no registro de operações, ocorrências, abrigos e comunicação segura sobre a fauna silvestre. O projeto reúne uma interface web, uma API e componentes de apoio ao armazenamento protegido dos registros.

## Telas do sistema

As imagens abaixo são capturas da interface do Guardian Fauna e mostram os principais fluxos disponíveis.

| Acesso e painel | Operações |
|---|---|
| **Login**<br>![Tela de login](screenshots/01-login.png) | **Solicitar acesso**<br>![Solicitação de acesso](screenshots/02-solicitar-acesso.png) |
| **Solicitação enviada**<br>![Confirmação da solicitação](screenshots/03-solicitacao-enviada.png) | **Painel do coordenador**<br>![Painel operacional](screenshots/04-dashboard-coordenador.png) |
| **Operações cadastradas**<br>![Lista de operações](screenshots/05-operacoes.png) | **Nova operação**<br>![Cadastro de operação](screenshots/06-nova-operacao.png) |
| **Ocorrências cifradas**<br>![Histórico de ocorrências cifradas](screenshots/07-historico-ocorrencias-cifradas.png) | **Decifrar histórico**<br>![Janela para decifrar o histórico](screenshots/08-modal-decifrar-historico.png) |
| **Histórico decifrado**<br>![Histórico com dados decifrados](screenshots/09-historico-dados-decifrados.png) | **Registrar ocorrência**<br>![Formulário de ocorrência](screenshots/10-registrar-ocorrencia.png) |
| **Detalhe cifrado**<br>![Detalhes cifrados da ocorrência](screenshots/11-detalhe-ocorrencia-cifrada.png) | **Decifrar ocorrência**<br>![Janela para decifrar ocorrência](screenshots/12-modal-decifrar-ocorrencia.png) |
| **Detalhe visualizado**<br>![Detalhes decifrados da ocorrência](screenshots/13-detalhe-ocorrencia-visualizada.png) | **Abrigos e CETAS**<br>![Lista de abrigos](screenshots/14-abrigos-cetas.png) |
| **Cadastrar abrigo**<br>![Formulário de abrigo](screenshots/15-cadastrar-abrigo.png) | **Mensageria cifrada**<br>![Mensagens cifradas](screenshots/16-mensageria-cifrada.png) |
| **Mensageria visualizada**<br>![Mensagens decifradas](screenshots/17-mensageria-decifrada.png) |  |

## Estrutura

- `frontend/`: aplicação web em React e Vite.
- `backend/`: API, persistência, validação e rotinas de proteção de dados.
- `streamlit_app.py` e `streamlit_ui/`: interface auxiliar em Streamlit.
- `tests/`: testes automatizados do projeto.

## Execução

Consulte os arquivos de configuração de cada parte para instalar as dependências e definir as variáveis de ambiente. Use `frontend/.env.example` como modelo para configurar a URL da API. Não coloque credenciais reais em arquivos versionados.
