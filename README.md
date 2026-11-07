# Reddit Art Hunter

Base local do projeto: frontend React + TypeScript, API FastAPI, PostgreSQL com SQLAlchemy/Alembic. A Fase 4 inclui cadastro de subreddits, filtros, histórico e coleta manual somente pela API oficial.

## Requisitos

- Python 3.11 ou superior
- Node.js 20 ou superior e npm
- PostgreSQL local (opcional para iniciar a API; necessário para migrations e funcionalidades que persistam dados)

## Iniciar no Windows (PowerShell)

1. Na pasta raiz do projeto, copie `.env.example` para `.env` e ajuste `DATABASE_URL` para um banco que você criar. O backend fica em `backend/`. Nenhum banco ou migration é criado automaticamente.
2. Backend:

   ```powershell
   cd backend
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -e ".[dev]"
   uvicorn app.main:app --reload
   ```

   A API estará em `http://127.0.0.1:8000`; documentação em `/docs`; saúde em `/api/v1/health`.
   O `.env` pode ficar na raiz ou em `backend/`. A configuração de banco só é usada ao inicializar sessões ou rodar Alembic.
3. Frontend, em outro terminal:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

   Abra o endereço exibido pelo Vite. O proxy encaminha `/api` para o backend local.

### Esta instalação

O `.env` da raiz já está configurado com a conexão local informada. Para preservar o Bookverse, o Reddit Art Hunter usa um banco separado chamado `reddit_art_hunter`; as migrations até a Fase 4 já foram aplicadas nesse banco vazio. O banco `bookverse` não foi alterado.

Os serviços já estão iniciados nesta sessão:

- Interface: <http://127.0.0.1:5173>
- API: <http://127.0.0.1:8000>
- Documentação da API: <http://127.0.0.1:8000/docs>

Para iniciar novamente depois de fechar os serviços, abra dois terminais PowerShell na pasta do projeto. No primeiro, execute `cd backend`, `.\.venv\Scripts\Activate.ps1` e `uvicorn app.main:app --reload`. No segundo, execute `cd frontend` e `npm run dev -- --host 127.0.0.1`. Não é necessário repetir a migration.

Na página **Meu perfil artístico**, cadastre estilos, categorias e temas, envie artes (PNG/JPG/WEBP/GIF até 15 MB) e registre seus serviços e faixas de preço. Os arquivos ficam em `data/artworks/`; remova artes pela própria galeria. Em **Monitor de comunidades**, cadastre subreddits e filtros; uma busca manual só fica habilitada após preencher as credenciais e aprovação.

## Banco de dados

Crie manualmente um banco vazio, por exemplo `reddit_art_hunter`, e configure uma URL no formato:

```text
postgresql+psycopg://usuario:senha@localhost:5432/reddit_art_hunter
```

Depois de ajustar `DATABASE_URL` e confirmar que aponta para o banco correto, rode `alembic upgrade head` em `backend/`. A migração `0004` adiciona comunidades, posts selecionados e histórico de consultas. O comando nunca é executado automaticamente. Não é necessário instalar pgvector nesta fase.

## Verificações

No backend: `python -m pytest`. No frontend: `npm test` (Vitest) e `npm run build`.

## Limites desta fase

O projeto não instala Ollama nem baixa modelos automaticamente. O runtime Ollama foi instalado nesta máquina na Fase 3; nenhum modelo foi baixado. Depois de escolher um modelo multimodal que caiba no seu hardware, defina `OLLAMA_MODEL`; para embeddings de texto, defina `OLLAMA_EMBEDDING_MODEL` e reinicie a API. A página do perfil mostra o estado da conexão e permite analisar cada arte. As respostas estruturadas e o modelo usado ficam registrados no banco.

Ollama deve continuar local em `http://localhost:11434`; a API rejeita endereços remotos. Só são usados modelos já instalados. A integração de embeddings nesta fase recebe texto; a análise visual produz descrições que poderão ser comparadas com embeddings textuais em uma etapa posterior. A extensão pgvector e a escolha dos modelos ainda não foram feitas.

### Reddit Data API

O sistema é local e de usuário único. Para consultar a Data API, o Reddit ainda exige cadastro do aplicativo e acesso autorizado para o caso de uso. Se o uso envolver encontrar clientes para comissões pagas, confirme com o Reddit se exige autorização comercial. Após obter o acesso apropriado, configure `REDDIT_ACCESS_TOKEN`, `REDDIT_USER_AGENT` identificável e `REDDIT_API_APPROVED=true` no `.env`, reinicie a API e use **Buscar agora**. O cliente faz apenas leitura via OAuth; não usa scraping, não publica e não envia mensagens. A aplicação armazena apenas título, corpo, permalink e datas essenciais, sem nome do autor. Consulte as [regras para desenvolvedores e uso comercial](https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data) e os [Data API Terms](https://redditinc.com/policies/data-api-terms).

Na tela **Monitor de comunidades**, você já pode cadastrar comunidades e filtros. A coleta fica bloqueada até o Reddit aprovar o acesso apropriado e você configurar o token. Nota: o Reddit anunciou que não aceita novos pedidos de acesso à API pública a partir de 31 de outubro de 2026; apps públicos existentes estão sendo migrados ao Developer Platform. Confira o [aviso oficial e o cronograma](https://support.reddithelp.com/hc/en-us/articles/54353370049684-Changelog-October-8-2026). O login no Developer Platform não fornece credenciais para um script externo como este; veja a [FAQ oficial](https://developers.reddit.com/docs/guides/faq).

Para instalar o runtime Ollama no Windows, use o instalador oficial e confira os requisitos de GPU antes de escolher modelos: [instruções oficiais para Windows](https://docs.ollama.com/windows). O runtime precisa de pelo menos 4 GB de espaço; os modelos exigem espaço adicional e não são baixados pelo projeto.
