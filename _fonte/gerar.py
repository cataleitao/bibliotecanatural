# Gera o site estático da Biblioteca Natural a partir de _fonte/conteudo.json.
# Uso: python3 _fonte/gerar.py <pasta com as imagens originais (uploads do WordPress)>
import html, json, re, shutil, sys
from pathlib import Path
from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).parent))
from ao import ao_misto

RAIZ = Path(__file__).resolve().parent.parent
ORIGENS = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "_originais"
C = json.loads((RAIZ / "_fonte" / "conteudo.json").read_text())
DOMINIO = "https://bibliotecanatural.catarinaleitao.net"
SITE_PRINCIPAL = "https://catarinaleitao.net/"
INSTAGRAM = "https://www.instagram.com/biblioteca.natural/"

# ---------------------------------------------------------------- imagens

FEITAS = {}

def nome_img(f):
    return re.sub(r"[^a-z0-9]+", "-", Path(f).stem.lower()).strip("-")

def imagem(f):
    """Processa um original: g (1600px), m (800px), q (quadrado 600), r (3:2 600x400). Devolve dados."""
    if f in FEITAS:
        return FEITAS[f]
    n = nome_img(f)
    im = ImageOps.exif_transpose(Image.open(ORIGENS / f)).convert("RGB")
    d = RAIZ / "img"; d.mkdir(exist_ok=True)
    tam = {}
    for suf, lado, q in (("g", 1600, 82), ("m", 800, 80)):
        c = im.copy(); c.thumbnail((lado, lado), Image.LANCZOS)
        c.save(d / f"{n}-{suf}.jpg", "JPEG", quality=q, optimize=True, progressive=True)
        tam[suf] = c.size
    ImageOps.fit(im, (600, 600), Image.LANCZOS).save(d / f"{n}-q.jpg", "JPEG", quality=78, optimize=True, progressive=True)
    ImageOps.fit(im, (600, 400), Image.LANCZOS).save(d / f"{n}-r.jpg", "JPEG", quality=78, optimize=True, progressive=True)
    FEITAS[f] = dict(n=n, w=tam["g"][0], h=tam["g"][1], mw=tam["m"][0], mh=tam["m"][1])
    return FEITAS[f]

# ---------------------------------------------------------------- texto

def tx(s):
    """Texto vindo do conteúdo: já é HTML simples; aplica o Acordo Ortográfico às partes em português."""
    s = s.replace("<br />", "<br>")
    s = re.sub(r'<a href="(https?://[^"]+)">', r'<a href="\1" target="_blank" rel="noopener">', s)
    return ao_misto(s)

def sem_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("  ", " ").strip()

def paragrafo(s):
    t = sem_tags(s)
    en = len(re.findall(r"\b(the|and|of|is|was|at|in|by|with|from|for|on|which|it|are|has|been|to)\b", t, re.I))
    pt = len(re.findall(r"\b(de|da|do|das|dos|que|não|uma|um|em|no|na|com|para|pela|pelo|é|foi|são|ao|e)\b", t, re.I))
    lingua = ' lang="en"' if en > pt or re.fullmatch(r"(Natural Library\..*|Work in progress\.?)", t) else ""
    return f"<p{lingua}>{tx(s)}</p>"

# ---------------------------------------------------------------- moldura

def raiz_de(rel):
    return "../" * rel.count("/")

def pagina(rel, titulo, corpo, actual="", descricao="", imagem_og=None, classe=""):
    r = raiz_de(rel)
    t_completo = f"{titulo} · Biblioteca Natural" if titulo else "Natural Library | Biblioteca Natural · Catarina Leitão"
    canon = DOMINIO + "/" + rel.replace("index.html", "")
    og = f'\n<meta property="og:image" content="{DOMINIO}/img/{imagem_og}-g.jpg">' if imagem_og else ""
    ac = ' aria-current="page"'
    nav = lambda k, href, txt: f'<a href="{r}{href}"{ac if actual == k else ""}>{txt}</a>'
    return f'''<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(t_completo)}</title>
<meta name="description" content="{html.escape(descricao or 'Natural Library | Biblioteca Natural, um projeto de Catarina Leitão: uma série infinita de livros, todos exemplares únicos.')}">
<link rel="canonical" href="{canon}">
<meta property="og:title" content="{html.escape(t_completo)}">
<meta property="og:type" content="website">{og}
<link rel="icon" href="{r}icone.png">
<link rel="stylesheet" href="{r}css/site.css">
</head>
<body class="{classe}">
<div class="moldura">
<header class="topo">
  <a class="marca" href="{r}index.html">Natural Library | Biblioteca Natural</a>
  <nav aria-label="Principal">
    {nav("catalogo", "catalogo/index.html", "catalog/catálogo")}
    {nav("itinerancia", "itinerancia/index.html", "traveling/itinerância")}
  </nav>
</header>
<main>
{corpo}
</main>
</div>
<footer class="rodape">
  <p><a href="{INSTAGRAM}" target="_blank" rel="noopener">Instagram</a> · <a href="{SITE_PRINCIPAL}">catarinaleitao.net</a></p>
  <p>© Catarina Leitão</p>
</footer>
<dialog class="lupa" aria-label="Imagem ampliada">
  <figure tabindex="-1" autofocus><img alt=""><figcaption></figcaption></figure>
  <button class="fechar" type="button" aria-label="Fechar">×</button>
  <button class="anterior" type="button" aria-label="Imagem anterior">‹</button>
  <button class="seguinte" type="button" aria-label="Imagem seguinte">›</button>
</dialog>
<script src="{r}js/lupa.js" defer></script>
</body>
</html>
'''

def escrever(rel, conteudo):
    p = RAIZ / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(conteudo)

def redireccionar(antigo, novo_rel):
    alvo = "/" + novo_rel.replace("index.html", "")
    escrever(f"{antigo}/index.html", f'''<!doctype html>
<html lang="pt"><head><meta charset="utf-8"><title>Biblioteca Natural</title>
<link rel="canonical" href="{DOMINIO}{alvo}"><meta http-equiv="refresh" content="0; url={alvo}">
</head><body><p><a href="{alvo}">{DOMINIO}{alvo}</a></p></body></html>
''')

# ---------------------------------------------------------------- blocos

def miniatura(f, r, legenda="", descricao="", forma="q", grupo=""):
    d = imagem(f)
    leg_html = tx(legenda) if legenda else ""
    alt = html.escape(sem_tags(ao_misto(legenda))) if legenda else ""
    dados = f' data-grupo="{grupo}" data-larga="{r}img/{d["n"]}-g.jpg" data-legenda="{html.escape(leg_html)}" data-descricao="{html.escape(tx(descricao) if descricao else "")}"'
    w, h = (600, 600) if forma == "q" else (600, 400)
    cap = f"<figcaption>{leg_html}</figcaption>" if legenda else ""
    return (f'<figure class="mini"><a href="{r}img/{d["n"]}-g.jpg"{dados}>'
            f'<img src="{r}img/{d["n"]}-{forma}.jpg" width="{w}" height="{h}" alt="{alt}" loading="lazy"></a>{cap}</figure>')

def figura(f, r, legenda="", grupo="", carregar="lazy"):
    d = imagem(f)
    leg_html = tx(legenda) if legenda else ""
    alt = html.escape(sem_tags(ao_misto(legenda))) if legenda else ""
    cap = f"<figcaption>{leg_html}</figcaption>" if legenda else ""
    return (f'<figure class="grande"><a href="{r}img/{d["n"]}-g.jpg" data-grupo="{grupo}" data-larga="{r}img/{d["n"]}-g.jpg" data-legenda="{html.escape(leg_html)}" data-descricao="">'
            f'<img src="{r}img/{d["n"]}-m.jpg" srcset="{r}img/{d["n"]}-m.jpg {d["mw"]}w, {r}img/{d["n"]}-g.jpg {d["w"]}w" '
            f'sizes="(min-width: 64rem) 50rem, 100vw" width="{d["w"]}" height="{d["h"]}" alt="{alt}" loading="{carregar}"></a>{cap}</figure>')

def corpo_post(itens, r):
    """Converte a lista de parágrafos e marcadores [[img:…]] / [[legenda:…]] em HTML.
    Imagens seguidas formam uma galeria."""
    saida = []; galeria = []
    i = 0
    def fecha():
        nonlocal galeria
        if len(galeria) == 1:
            saida.append(figura(galeria[0][0], r, galeria[0][1], grupo="post"))
        elif galeria:
            saida.append('<div class="galeria">' + "".join(miniatura(f, r, l, forma="q", grupo="post") for f, l in galeria) + "</div>")
        galeria = []
    while i < len(itens):
        x = itens[i]
        m = re.match(r"\[\[img:(.+?)\]\]$", x)
        if m:
            leg = ""
            if i + 1 < len(itens) and itens[i + 1].startswith("[[legenda:"):
                leg = itens[i + 1][len("[[legenda:"):-2]; i += 1
            galeria.append((m.group(1), leg))
        else:
            fecha()
            if not x.startswith("[["):
                saida.append(paragrafo(x))
        i += 1
    fecha()
    return "\n".join(saida)

# ---------------------------------------------------------------- páginas

def gerar():
    for p in ["index.html", "404.html", "catalogo", "itinerancia", "portfolio", "img", "2014", "2016", "2017", "2020", "2021"]:
        q = RAIZ / p
        if q.is_dir(): shutil.rmtree(q)
        elif q.exists(): q.unlink()

    # início
    ini = C["inicio"]; rel = "index.html"; r = ""
    figs = "\n".join(figura(x["ficheiro"], r, x["legenda"], grupo="inicio", carregar="eager" if k == 0 else "lazy") for k, x in enumerate(ini["imagens"]))
    en = "".join(f'<p lang="en">{tx(x)}</p>' for x in ini["texto_en"])
    pt = "".join(f"<p>{tx(x)}</p>" for x in ini["texto_pt"])
    corpo = f'''<div class="inicio">
<div class="imagens">{figs}</div>
<div class="texto"><h1 class="visualmente-oculto">Natural Library | Biblioteca Natural</h1>
<div class="en">{en}</div><div class="pt">{pt}</div></div>
</div>'''
    escrever(rel, pagina(rel, "", corpo, imagem_og=imagem(ini["imagens"][0]["ficheiro"])["n"]))

    # catálogo
    cartoes = []
    for col in C["colecoes"]:
        d = imagem(col["capa"])
        cartoes.append(f'''<a class="cartao" href="{col["slug"]}/index.html">
  <img src="../img/{d["n"]}-m.jpg" width="{d["mw"]}" height="{d["mh"]}" alt="" loading="lazy">
  <span class="titulo">{tx(col["titulo"])}</span></a>''')
    rel = "catalogo/index.html"
    escrever(rel, pagina(rel, "catálogo", f'<h1 class="visualmente-oculto">catalog/catálogo</h1>\n<div class="catalogo">{"".join(cartoes)}</div>', actual="catalogo"))
    for col in C["colecoes"]:
        rel = f"catalogo/{col['slug']}/index.html"; r = raiz_de(rel)
        texto = "".join(paragrafo(x) for x in col["texto"])
        grelha = "".join(miniatura(im["ficheiro"], r, im["legenda"], im["descricao"], grupo="colecao") for im in col["imagens"])
        corpo = f'''<div class="colecao">
<div class="lateral"><h1>{tx(col["titulo"])}</h1>{texto}</div>
<div class="grelha">{grelha}</div>
</div>'''
        escrever(rel, pagina(rel, sem_tags(ao_misto(col["titulo"])), corpo, actual="catalogo", imagem_og=imagem(col["capa"])["n"]))
        if col.get("antigo"): redireccionar(col["antigo"], rel)
    redireccionar("portfolio", "catalogo/index.html")

    # itinerância
    linhas = []
    for it in C["itinerancia"]:
        capa = it["capa"]
        d = imagem(capa)
        resumo = "".join(paragrafo(x) for x in it["resumo"])
        linhas.append(f'''<article class="entrada">
  <a class="foto" href="{it["slug"]}/index.html" tabindex="-1" aria-hidden="true"><img src="../img/{d["n"]}-r.jpg" width="600" height="400" alt="" loading="lazy"></a>
  <div><h2><a href="{it["slug"]}/index.html">{tx(it["titulo"])}</a></h2>{resumo}</div>
</article>''')
    rel = "itinerancia/index.html"
    escrever(rel, pagina(rel, "itinerância", f'<h1 class="visualmente-oculto">traveling/itinerância</h1>\n<div class="lista">{"".join(linhas)}</div>', actual="itinerancia"))
    for it in C["itinerancia"]:
        rel = f"itinerancia/{it['slug']}/index.html"; r = raiz_de(rel)
        corpo = f'''<article class="post">
<h1>{tx(it["titulo"])}</h1>
{corpo_post(it["corpo"], r)}
<p class="voltar"><a href="../index.html">← traveling/itinerância</a></p>
</article>'''
        escrever(rel, pagina(rel, sem_tags(ao_misto(it["titulo"])), corpo, actual="itinerancia", imagem_og=imagem(it["capa"])["n"]))
        if it.get("antigo"): redireccionar(it["antigo"], rel)

    # 404
    escrever("404.html", pagina("404.html", "Página não encontrada", '<div class="post"><h1>Página não encontrada</h1><p><a href="/">Natural Library | Biblioteca Natural</a></p></div>').replace('href="img/', 'href="/img/').replace('href="css/', 'href="/css/').replace('src="js/', 'src="/js/').replace('href="index.html"', 'href="/"').replace('href="catalogo/', 'href="/catalogo/').replace('href="itinerancia/', 'href="/itinerancia/'))

    # apagar tamanhos de imagem que nenhuma página usa
    usadas = set()
    for h in RAIZ.rglob("*.html"):
        usadas |= set(re.findall(r"img/([\w-]+\.jpg)", h.read_text()))
    for f in (RAIZ / "img").iterdir():
        if f.name not in usadas: f.unlink()
    n = len(FEITAS)
    print(f"feito: {len(C['colecoes'])} colecções, {len(C['itinerancia'])} entradas de itinerância, {n} imagens")

if __name__ == "__main__":
    gerar()
