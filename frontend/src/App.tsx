import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  createService, createStyle, deleteArtwork, deleteService, deleteStyle, getApiHealth,
  analyzeArtwork, embedText, getAIStatus, getArtworkAnalyses, listArtworks, listServices, listStyles, updateArtwork,
  updateService, uploadArtwork, createSubreddit, deleteSubreddit, getMonitorStatus, listMonitoredPosts,
  listSearchRuns, listSubreddits, scanSubreddit, type AIStatus, type ArtStyle, type Artwork,
  type ArtworkAnalysis, type CommissionService, type Health,
} from "./api";

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [artworks, setArtworks] = useState<Artwork[]>([]);
  const [styles, setStyles] = useState<ArtStyle[]>([]);
  const [services, setServices] = useState<CommissionService[]>([]);
  const [aiStatus, setAIStatus] = useState<AIStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    setHealth(null);
    try {
      const apiHealth = await getApiHealth();
      setHealth(apiHealth);
      try { setAIStatus(await getAIStatus()); }
      catch { setAIStatus(null); }
      const [artItems, styleItems, serviceItems] = await Promise.all([
        listArtworks(), listStyles(), listServices(),
      ]);
      setArtworks(artItems);
      setStyles(styleItems);
      setServices(serviceItems);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível carregar o perfil.");
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  async function runAction(action: () => Promise<unknown>, message: string) {
    setError(""); setNotice("");
    try { await action(); await refresh(); setNotice(message); }
    catch (err) { setError(err instanceof Error ? err.message : "A operação falhou."); }
  }

  async function runAnalysis(artworkId: string): Promise<ArtworkAnalysis | null> {
    setError(""); setNotice("");
    try {
      const result = await analyzeArtwork(artworkId);
      setNotice("Análise local concluída e salva.");
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : "A análise local falhou.");
      return null;
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#top"><span className="brand-glyph">✦</span><span>ART HUNTER<small>LOCAL STUDIO</small></span></a>
        <p className="nav-caption">SEU ESPAÇO</p>
        <a className="nav-item active" href="#portfolio"><span>▦</span> Meu portfólio</a>
        <a className="nav-item" href="#classifications"><span>⌘</span> Estilos e temas</a>
        <a className="nav-item" href="#services"><span>◇</span> Serviços</a>
        <div className="sidebar-bottom"><span className={`connection-dot ${health ? "connected" : ""}`} />{health ? "API conectada" : "Aguardando conexão"}<small>FASE 2 · PERFIL ARTÍSTICO</small></div>
      </aside>

      <section className="workspace" id="top">
        <header className="topbar"><div><span className="crumb">REDDIT ART HUNTER</span><span className="crumb-sep">/</span><span className="crumb current">PERFIL ARTÍSTICO</span></div><div className="local-badge"><span /> SEUS ARQUIVOS FICAM NO COMPUTADOR</div></header>
        <div className="content">
          <div className="page-heading"><div><p className="eyebrow">FASE 02 <span>·</span> SUA IDENTIDADE CRIATIVA</p><h1>Meu perfil artístico</h1><p className="subheading">Organize suas referências e deixe claro o tipo de trabalho que você oferece.</p></div><div className="stat-pill"><strong>{artworks.length}</strong><span>ARTES NO PORTFÓLIO</span></div></div>

          {error && <div className="alert error-alert" role="alert"><span>!</span><div><strong>Não foi possível carregar os dados</strong><p>{error}{!health && " Inicie a API e confira a conexão com o PostgreSQL."}</p></div><button onClick={() => void refresh()}>Tentar novamente</button></div>}
          {notice && <div className="alert success-alert" role="status">✓ &nbsp;{notice}<button aria-label="Fechar aviso" onClick={() => setNotice("")}>×</button></div>}

          <AISetupCard status={aiStatus} />
          <SubredditMonitor />

          <section className="section-block" id="portfolio">
            <div className="section-title"><div><p className="eyebrow">BIBLIOTECA VISUAL</p><h2>Suas artes</h2></div><span className="section-count">{artworks.length.toString().padStart(2, "0")} itens</span></div>
            <UploadPanel styles={styles} onUpload={(file, title, description, ids) => runAction(() => uploadArtwork(file, title, description, ids), "Arte adicionada ao portfólio.")} />
            {loading ? <div className="empty-state">Carregando seu perfil…</div> : artworks.length ? <div className="art-grid">{artworks.map((art) => <ArtworkCard key={art.id} artwork={art} styles={styles} canAnalyze={Boolean(aiStatus?.reachable && aiStatus.model_installed)} onAnalyze={() => runAnalysis(art.id)} onSave={(value) => runAction(() => updateArtwork(art.id, value), "Alterações salvas.")} onDelete={() => runAction(() => deleteArtwork(art.id), "Arte removida do portfólio.")} />)}</div> : <div className="empty-state"><span>✧</span><strong>Sua galeria começa com uma arte.</strong><p>Adicione imagens representativas do estilo de comissão que você deseja receber.</p></div>}
          </section>

          <div className="two-column">
            <section className="section-block panel" id="classifications"><div className="section-title"><div><p className="eyebrow">ORGANIZAÇÃO</p><h2>Estilos e temas</h2></div></div><StyleManager styles={styles} onCreate={(value) => runAction(() => createStyle(value), "Classificação criada.")} onDelete={(id) => runAction(() => deleteStyle(id), "Classificação removida.")} /></section>
            <section className="section-block panel" id="services"><div className="section-title"><div><p className="eyebrow">O QUE VOCÊ OFERECE</p><h2>Serviços e preços</h2></div></div><ServiceManager services={services} onCreate={(value) => runAction(() => createService(value), "Serviço cadastrado.")} onUpdate={(id, value) => runAction(() => updateService(id, value), "Serviço atualizado.")} onDelete={(id) => runAction(() => deleteService(id), "Serviço removido.")} /></section>
          </div>
          <footer><span>REDDIT ART HUNTER <b>·</b> PRIVADO E LOCAL</span><span>{health?.service ?? "API offline"}</span></footer>
        </div>
      </section>
    </main>
  );
}

function SubredditMonitor() {
  const [communities, setCommunities] = useState<import("./api").Subreddit[]>([]);
  const [posts, setPosts] = useState<import("./api").MonitoredPost[]>([]);
  const [runs, setRuns] = useState<import("./api").SearchRun[]>([]);
  const [status, setStatus] = useState<import("./api").MonitorStatus | null>(null);
  const [name, setName] = useState("");
  const [include, setInclude] = useState("");
  const [exclude, setExclude] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const refresh = useCallback(async () => {
    try {
      const [communityData, postData, runData, monitorStatus] = await Promise.all([
        listSubreddits(), listMonitoredPosts(), listSearchRuns(), getMonitorStatus(),
      ]);
      setCommunities(communityData); setPosts(postData); setRuns(runData); setStatus(monitorStatus);
    } catch (err) { setMessage(err instanceof Error ? err.message : "Não foi possível carregar o monitor."); }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setMessage("");
    try {
      await createSubreddit({ name, include_keywords: include.split(",").map((item) => item.trim()).filter(Boolean), exclude_keywords: exclude.split(",").map((item) => item.trim()).filter(Boolean) });
      setName(""); await refresh();
    } catch (err) { setMessage(err instanceof Error ? err.message : "Não foi possível cadastrar."); }
    finally { setBusy(false); }
  }
  async function scan(id: number) {
    setBusy(true); setMessage("");
    try { await scanSubreddit(id); await refresh(); }
    catch (err) { setMessage(err instanceof Error ? err.message : "A busca falhou."); await refresh(); }
    finally { setBusy(false); }
  }
  return <section className="section-block monitor-panel" id="monitor">
    <div className="section-title"><div><p className="eyebrow">FASE 04 · DESCOBERTA</p><h2>Monitor de comunidades</h2></div><span className={`monitor-badge ${status?.can_scan ? "ready" : ""}`}>{status?.can_scan ? "API AUTORIZADA" : "BUSCA BLOQUEADA"}</span></div>
    <p className="monitor-note">Busca manual pela API oficial. Nenhuma mensagem ou publicação será enviada.</p>
    {status && !status.can_scan && <div className="monitor-gate">{status.message} Depois, configure o token e marque o acesso aprovado no arquivo <code>.env</code>.</div>}
    <form className="monitor-form" onSubmit={(event) => void submit(event)}>
      <input aria-label="Nome da comunidade" placeholder="Nome (ex.: artcommissions)" value={name} onChange={(event) => setName(event.target.value)} required maxLength={80} />
      <input aria-label="Palavras desejadas" placeholder="Incluir (separe por vírgulas)" value={include} onChange={(event) => setInclude(event.target.value)} />
      <input aria-label="Palavras a excluir" placeholder="Excluir (separe por vírgulas)" value={exclude} onChange={(event) => setExclude(event.target.value)} />
      <button disabled={busy || !name.trim()}>Adicionar comunidade</button>
    </form>
    {message && <p className="monitor-message" role="status">{message}</p>}
    <div className="monitor-list">{communities.length ? communities.map((item) => <article className="monitor-row" key={item.id}><div><strong>r/{item.name}</strong><small>Intervalo mínimo: 15 min · máximo {item.max_posts_per_check} posts</small></div><div className="monitor-actions"><button disabled={busy || !status?.can_scan} onClick={() => void scan(item.id)}>Buscar agora</button><button className="remove-community" disabled={busy} onClick={async () => { await deleteSubreddit(item.id); await refresh(); }}>Remover</button></div></article>) : <div className="monitor-empty">Cadastre uma comunidade para começar. A coleta permanece desligada até a configuração de acesso aprovado à API.</div>}</div>
    {posts.length > 0 && <div className="monitor-posts"><h3>Posts encontrados</h3>{posts.map((post) => <a key={post.reddit_id} href={post.permalink} target="_blank" rel="noreferrer"><strong>{post.title}</strong><small>r/{communities.find((item) => item.id === post.subreddit_id)?.name ?? "reddit"} · {new Date(post.created_utc).toLocaleString()}</small></a>)}</div>}
    {runs.length > 0 && <details className="monitor-history"><summary>Histórico de buscas ({runs.length})</summary>{runs.map((run) => <p key={run.id}>{new Date(run.started_at).toLocaleString()} · {run.status} · {run.message}</p>)}</details>}
  </section>;
}

function AISetupCard({ status }: { status: AIStatus | null }) {
  const ready = Boolean(status?.reachable && status.model_installed);
  const title = ready ? `Modelo visual pronto: ${status?.configured_model}` : !status?.reachable ? "Ollama local não está respondendo" : !status.model_configured ? "Escolha um modelo multimodal local" : `Modelo ${status.configured_model} não encontrado`;
  const [sample, setSample] = useState("");
  const [dimensionCount, setDimensionCount] = useState<number | null>(null);
  const [embeddingBusy, setEmbeddingBusy] = useState(false);
  const [embeddingError, setEmbeddingError] = useState("");
  async function testEmbedding(event: FormEvent) {
    event.preventDefault(); setEmbeddingBusy(true); setEmbeddingError(""); setDimensionCount(null);
    try { const result = await embedText(sample); setDimensionCount(result.dimensions); }
    catch (error) { setEmbeddingError(error instanceof Error ? error.message : "Falha ao gerar embedding."); }
    finally { setEmbeddingBusy(false); }
  }
  return <section className="ai-status-card"><div className="ai-status-symbol">AI</div><div className="ai-status-copy"><p className="eyebrow">FASE 03 · INTELIGÊNCIA LOCAL</p><strong>{title}</strong><p>{status?.message ?? "Inicie a API para verificar o runtime local."}</p>{status?.reachable && status.available_models.length > 0 && <small>Modelos encontrados: {status.available_models.map((item) => `${item.name}${item.parameter_size ? ` · ${item.parameter_size}` : ""}`).join(" | ")}</small>}{status?.embedding_model_installed && <form className="embedding-test" onSubmit={testEmbedding}><input aria-label="Texto para testar embeddings" placeholder="Texto curto para testar embeddings…" value={sample} onChange={(event) => setSample(event.target.value)} maxLength={8000} required /><button disabled={embeddingBusy || !sample.trim()}>{embeddingBusy ? "Calculando…" : "Testar embedding"}</button>{dimensionCount !== null && <span>{dimensionCount} dimensões</span>}{embeddingError && <small className="embedding-error">{embeddingError}</small>}</form>}</div><span className={`ai-state ${ready ? "ready" : "pending"}`}>{ready ? "DISPONÍVEL" : status?.reachable ? "MODELO PENDENTE" : "OLLAMA OFFLINE"}</span></section>;
}

function UploadPanel({ styles, onUpload }: { styles: ArtStyle[]; onUpload: (file: File, title: string, desc: string, ids: number[]) => Promise<void> }) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [ids, setIds] = useState<number[]>([]);
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); if (!file || !title.trim()) return;
    setBusy(true); await onUpload(file, title.trim(), description, ids);
    setBusy(false); setFile(null); setTitle(""); setDescription(""); setIds([]);
    const input = document.getElementById("art-file") as HTMLInputElement | null; if (input) input.value = "";
  }
  return <form className="upload-panel" onSubmit={submit}>
    <label className="file-drop" htmlFor="art-file"><span className="upload-icon">↑</span><strong>{file?.name ?? "Escolha uma imagem para adicionar"}</strong><small>PNG, JPG, WEBP ou GIF · até 15 MB</small><input id="art-file" type="file" accept="image/png,image/jpeg,image/webp,image/gif" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></label>
    <div className="upload-fields"><input aria-label="Nome da arte" placeholder="Nome da arte" maxLength={160} value={title} onChange={(event) => setTitle(event.target.value)} required /><textarea aria-label="Descrição" placeholder="Descrição opcional: técnica, personagem ou contexto…" maxLength={4000} value={description} onChange={(event) => setDescription(event.target.value)} /><StyleChecks styles={styles} selected={ids} onChange={setIds} /><button className="primary-button" disabled={!file || !title.trim() || busy}>{busy ? "Adicionando…" : "Adicionar ao portfólio"}<span>↗</span></button></div>
  </form>;
}

function StyleChecks({ styles, selected, onChange }: { styles: ArtStyle[]; selected: number[]; onChange: (ids: number[]) => void }) {
  if (!styles.length) return <p className="hint">Crie estilos e temas abaixo para classificar suas artes.</p>;
  return <div className="check-list">{styles.map((style) => <label key={style.id} className="check-chip"><input type="checkbox" checked={selected.includes(style.id)} onChange={(event) => onChange(event.target.checked ? [...selected, style.id] : selected.filter((id) => id !== style.id))} />{style.name}</label>)}</div>;
}

function ArtworkCard({ artwork, styles, canAnalyze, onAnalyze, onSave, onDelete }: { artwork: Artwork; styles: ArtStyle[]; canAnalyze: boolean; onAnalyze: () => Promise<ArtworkAnalysis | null>; onSave: (data: { title: string; description: string; style_ids: number[] }) => Promise<void>; onDelete: () => Promise<void> }) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(artwork.title);
  const [description, setDescription] = useState(artwork.description);
  const [ids, setIds] = useState(artwork.styles.map((style) => style.id));
  const [busy, setBusy] = useState(false);
  const [analysis, setAnalysis] = useState<ArtworkAnalysis | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  useEffect(() => { void getArtworkAnalyses(artwork.id).then((items) => setAnalysis(items[0] ?? null)).catch(() => undefined); }, [artwork.id]);
  async function runAnalysis() { setAnalyzing(true); const result = await onAnalyze(); if (result) setAnalysis(result); setAnalyzing(false); }
  return <article className="art-card"><div className="art-image"><img src={artwork.image_url} alt={artwork.title} loading="lazy" /><button className="delete-button" title="Remover arte" onClick={() => { if (window.confirm(`Remover “${artwork.title}” e apagar a imagem do computador?`)) void onDelete(); }}>×</button></div><div className="art-card-body">{editing ? <><input aria-label="Nome da arte" value={title} onChange={(event) => setTitle(event.target.value)} /><textarea aria-label="Descrição" value={description} onChange={(event) => setDescription(event.target.value)} /><StyleChecks styles={styles} selected={ids} onChange={setIds} /><div className="card-actions"><button onClick={() => setEditing(false)}>Cancelar</button><button className="save-button" disabled={busy} onClick={async () => { setBusy(true); await onSave({ title, description, style_ids: ids }); setBusy(false); setEditing(false); }}>Salvar</button></div></> : <><h3>{artwork.title}</h3><p>{artwork.description || "Sem descrição"}</p><div className="tag-row">{artwork.styles.map((style) => <span key={style.id}>{style.name}</span>)}</div><button className="text-button" onClick={() => setEditing(true)}>Editar detalhes ↗</button><button className="analyze-button" disabled={!canAnalyze || analyzing} onClick={() => void runAnalysis()}>{analyzing ? "Analisando localmente…" : canAnalyze ? "Analisar com IA local" : "Configure um modelo visual"}</button>{analysis && <AnalysisResult result={analysis} />}</>}</div></article>;
}

function AnalysisResult({ result }: { result: ArtworkAnalysis }) {
  const tags = [...result.result.styles, ...result.result.themes, ...result.result.subjects];
  return <section className="analysis-result"><span className="analysis-label">ANÁLISE · {result.model}</span><p>{result.result.visual_description}</p><div className="tag-row">{tags.map((tag, index) => <span key={`${tag}-${index}`}>{tag}</span>)}</div><small>Complexidade {result.result.complexity}/5 · Confiança {Math.round(result.result.confidence * 100)}%</small></section>;
}

function StyleManager({ styles, onCreate, onDelete }: { styles: ArtStyle[]; onCreate: (value: Pick<ArtStyle, "name" | "kind">) => Promise<void>; onDelete: (id: number) => Promise<void> }) {
  const [name, setName] = useState(""); const [kind, setKind] = useState<ArtStyle["kind"]>("style");
  return <><form className="inline-form" onSubmit={async (event) => { event.preventDefault(); if (name.trim()) { await onCreate({ name: name.trim(), kind }); setName(""); } }}><input placeholder="Ex.: Semi-realista, Vampiros…" aria-label="Nova classificação" value={name} onChange={(event) => setName(event.target.value)} maxLength={80} required /><select aria-label="Tipo" value={kind} onChange={(event) => setKind(event.target.value as ArtStyle["kind"])}><option value="style">Estilo</option><option value="category">Categoria</option><option value="theme">Tema</option></select><button className="icon-button" aria-label="Adicionar classificação">+</button></form><div className="managed-list">{styles.length ? styles.map((style) => <div className="managed-row" key={style.id}><span className="kind-label">{style.kind === "style" ? "ESTILO" : style.kind === "category" ? "CATEGORIA" : "TEMA"}</span><strong>{style.name}</strong><button aria-label={`Remover ${style.name}`} onClick={() => { if (window.confirm(`Remover a classificação “${style.name}”?`)) void onDelete(style.id); }}>×</button></div>) : <p className="hint">Cadastre estilos, categorias e temas para usá-los na galeria.</p>}</div></>;
}

type ServiceForm = Omit<CommissionService, "id" | "created_at">;
function ServiceManager({ services, onCreate, onUpdate, onDelete }: { services: CommissionService[]; onCreate: (value: ServiceForm) => Promise<void>; onUpdate: (id: number, value: ServiceForm) => Promise<void>; onDelete: (id: number) => Promise<void> }) {
  const blank: ServiceForm = { name: "", description: "", price_min: "", price_max: "", currency: "USD", active: true };
  const [form, setForm] = useState<ServiceForm>(blank); const [editingId, setEditingId] = useState<number | null>(null);
  function field<K extends keyof ServiceForm>(key: K, value: ServiceForm[K]) { setForm((current) => ({ ...current, [key]: value })); }
  return <><form className="service-form" onSubmit={async (event) => { event.preventDefault(); if (editingId === null) await onCreate(form); else await onUpdate(editingId, form); setForm(blank); setEditingId(null); }}><input placeholder="Ex.: Retrato de personagem" aria-label="Nome do serviço" value={form.name} onChange={(event) => field("name", event.target.value)} maxLength={120} required /><input placeholder="Descrição opcional" aria-label="Descrição do serviço" value={form.description} onChange={(event) => field("description", event.target.value)} maxLength={4000} /><div className="price-row"><label><small>A PARTIR DE</small><input type="number" min="0" step="0.01" placeholder="0" aria-label="Preço mínimo" value={form.price_min} onChange={(event) => field("price_min", event.target.value)} required /></label><label><small>ATÉ</small><input type="number" min="0" step="0.01" placeholder="0" aria-label="Preço máximo" value={form.price_max} onChange={(event) => field("price_max", event.target.value)} required /></label><select aria-label="Moeda" value={form.currency} onChange={(event) => field("currency", event.target.value)}><option>USD</option><option>BRL</option><option>EUR</option></select></div><label className="active-toggle"><input type="checkbox" checked={form.active} onChange={(event) => field("active", event.target.checked)} /> Aceitando pedidos deste serviço</label><button className="primary-button" type="submit">{editingId === null ? "Cadastrar serviço" : "Salvar alterações"}<span>↗</span></button></form><div className="managed-list service-list">{services.map((service) => <div className="service-row" key={service.id}><div><strong>{service.name}</strong><small>{service.currency} {service.price_min} – {service.price_max} · {service.active ? "Aceitando pedidos" : "Pausado"}</small></div><button aria-label={`Editar ${service.name}`} onClick={() => { setForm({ name: service.name, description: service.description, price_min: service.price_min, price_max: service.price_max, currency: service.currency, active: service.active }); setEditingId(service.id); }}>Editar</button><button aria-label={`Remover ${service.name}`} onClick={() => { if (window.confirm(`Remover o serviço “${service.name}”?`)) void onDelete(service.id); }}>×</button></div>)}{services.length === 0 && <p className="hint">Seus serviços e preços aparecerão aqui.</p>}</div></>;
}
