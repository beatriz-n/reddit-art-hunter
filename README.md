# Reddit Art Hunter

Aplicação local para organizar seu perfil artístico e acompanhar comunidades do Reddit que possam ter oportunidades relacionadas a comissões de arte.

O projeto tem uma interface em React + TypeScript, uma API em Python + FastAPI e PostgreSQL para persistência. A integração com o Reddit usa a Data API oficial, somente para leitura, e permanece desativada até que você configure credenciais e acesso apropriado. A integração com Ollama é opcional e usa um serviço local.

## Funcionalidades

- Perfil artístico com estilos, categorias, temas, serviços e faixas de preço.
- Galeria local para artes PNG, JPG, WEBP e GIF de até 15 MB.
- Cadastro de comunidades e filtros de busca.
- Consulta manual ao Reddit após configurar acesso aprovado à API.
- Registro local de posts selecionados e histórico de consultas.
- Análise de arte por Ollama quando houver um modelo local configurado.

## Requisitos

- Windows 10/11 com PowerShell
- Python 3.11 ou superior
- Node.js 20 ou superior e npm
- PostgreSQL local (necessário para migrations e recursos que salvam dados)
- Ollama e um modelo compatível (opcional)

## Configuração

1. Na pasta do projeto, copie o arquivo de exemplo:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Edite `.env` e ajuste `DATABASE_URL` para um banco criado especificamente para o Reddit Art Hunter. Exemplo:

   ```env
   DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/reddit_art_hunter
   ```

   Não use um banco de outro projeto. Crie primeiro o banco vazio no PostgreSQL. A aplicação não cria bancos nem executa migrations automaticamente.

3. Instale as dependências do backend e aplique as migrations no banco configurado:

   ```powershell
   cd backend
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -e ".[dev]"
   alembic upgrade head
   ```

4. Instale as dependências do frontend em outro terminal:

   ```powershell
   cd frontend
   npm install
   ```

## Executar localmente

Abra dois terminais PowerShell na pasta do projeto.

No primeiro, inicie a API:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

No segundo, inicie a interface:

```powershell
cd frontend
npm run dev
```

Abra o endereço local informado pelo Vite, normalmente <http://localhost:5173>. A API fica em <http://127.0.0.1:8000>, a documentação interativa em <http://127.0.0.1:8000/docs> e o endpoint de saúde em <http://127.0.0.1:8000/api/v1/health>.

## Integração com Reddit

O cadastro ou login no Reddit, por si só, não fornece ao projeto um token de API. A coleta exige credenciais de aplicativo e autorização de acesso válidas para o uso pretendido. Se o objetivo envolver encontrar clientes para comissões pagas, confirme com o Reddit se esse caso requer acesso comercial.

Depois de obter a autorização adequada, preencha no `.env`:

```env
REDDIT_ACCESS_TOKEN=seu_token
REDDIT_USER_AGENT=RedditArtHunter/0.1 (aplicativo local)
REDDIT_API_APPROVED=true
```

Reinicie a API e use **Buscar agora** no monitor de comunidades. O cliente faz consultas somente de leitura: não publica, não envia mensagens e não usa scraping. Configure o token apenas no `.env`, que está excluído do Git.

Consulte as [regras para desenvolvedores e uso comercial](https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data), os [termos da Data API](https://redditinc.com/policies/data-api-terms) e os [avisos oficiais de acesso à API](https://support.reddithelp.com/hc/en-us/articles/54353370049684-Changelog-October-8-2026). As regras de acesso podem mudar; confirme a situação atual diretamente com o Reddit.

## Integração com Ollama (opcional)

O Ollama deve estar instalado e rodando localmente em `http://localhost:11434`. O projeto não instala o Ollama nem baixa modelos automaticamente. Depois de instalar localmente um modelo compatível, preencha `OLLAMA_MODEL` no `.env`. Para embeddings de texto, configure também `OLLAMA_EMBEDDING_MODEL`. Reinicie a API após alterar as variáveis.

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=
OLLAMA_EMBEDDING_MODEL=
```

## Dados e privacidade

- O `.env` contém configurações privadas e não deve ser enviado ao GitHub.
- Artes e arquivos de trabalho são armazenados localmente em `data/` e não são incluídos no Git.
- Use credenciais e tokens somente no `.env`; não os inclua em issues, commits ou capturas de tela.
- A aplicação foi projetada para uso local e individual. Tornar o código público no GitHub não hospeda a aplicação nem torna os dados locais públicos.

## Verificações de desenvolvimento

No backend:

```powershell
cd backend
python -m pytest
```

No frontend:

```powershell
cd frontend
npm test
npm run build
```

## Estrutura

```text
backend/       API FastAPI, modelos SQLAlchemy, migrations Alembic e testes
frontend/      interface React + TypeScript
data/          arquivos de arte e dados locais (não versionados)
.env.example   modelo de configuração sem credenciais
```
