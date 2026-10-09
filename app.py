import streamlit as st

import pandas as pd

import numpy as np

import sqlite3

import os

import uuid

import re

import random

import hashlib

import difflib

import unicodedata
import io

# Reconhecimento de voz opcional (áudio gravado pelo navegador)
try:
    import speech_recognition as sr
    RECONHECIMENTO_VOZ_DISPONIVEL = True
except Exception:
    sr = None
    RECONHECIMENTO_VOZ_DISPONIVEL = False


def transcrever_audio(audio_file):
    """Transcreve áudio WAV/WEBM recebido pelo Streamlit usando serviço online."""
    if not RECONHECIMENTO_VOZ_DISPONIVEL:
        return None, "Instale SpeechRecognition para ativar o reconhecimento de voz."
    try:
        reconhecedor = sr.Recognizer()
        # st.audio_input normalmente fornece WAV, aceito pelo AudioFile.
        audio_bytes = audio_file.getvalue()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as fonte:
            audio = reconhecedor.record(fonte)
        texto = reconhecedor.recognize_google(audio, language="pt-BR")
        return texto, None
    except sr.UnknownValueError:
        return None, "Não consegui entender o áudio. Tente falar mais perto do microfone."
    except sr.RequestError as exc:
        return None, f"O serviço de reconhecimento de voz não respondeu: {exc}"
    except Exception as exc:
        return None, f"Não consegui processar o áudio: {exc}"

from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.metrics.pairwise import cosine_similarity

# Núcleo neural opcional do ALVESMLD
try:
    from alvesmld_neural import treinar_modelo, responder_inteligente, status_modelo
    NUCLEO_NEURAL_DISPONIVEL = True
    ERRO_NUCLEO_NEURAL = None
except Exception as erro_neural:
    NUCLEO_NEURAL_DISPONIVEL = False
    ERRO_NUCLEO_NEURAL = str(erro_neural)



try:

    from moviepy.editor import TextClip, CompositeVideoClip, ColorClip

    MOVIEPY_DISPONIVEL = True

except ImportError:

    MOVIEPY_DISPONIVEL = False



DB_PATH = "alvesmld_cerebro.db"

PASTA_PLANILHAS = "planilhas"          # coloca aqui os .xlsx / .csv / .txt do cérebro

EMAILS_MESTRES = ["alves08911@gmail.com", "joaozinhozito231@gmail.com"]

TOKENS_INICIAIS = 10

CUSTO_VIDEO = 5

LIMIAR_SIMILARIDADE = 5.0              # % mínima do TF-IDF para aceitar uma resposta



st.set_page_config(

    page_title="ALVESMLD - AI Assistant, Cérebro Insano & Estúdio de Vídeo IA",

    page_icon="⚡",

    layout="wide"

)



# --- INICIALIZAÇÃO SEGURA DO SESSION_STATE ---

if 'email_utilizador' not in st.session_state:

    st.session_state['email_utilizador'] = None



if 'chat_historico' not in st.session_state:

    st.session_state['chat_historico'] = [

        {"role": "assistant", "content": "⚡ Olá, mano! Faz login com o teu e-mail na barra lateral para começar a estourar nos códigos.\n\n💡 Dica: pergunta **\"o que significa oxe\"** ou manda **\"traduz: vc viu o bagulho? tmj\"** que eu decifro gírias e abreviações."}

    ]



st.markdown("""

    <style>

    .stChatInput { bottom: 10px; }

    @media (max-width: 768px) {

        .main .block-container { padding: 1rem; }

        h1 { font-size: 1.4rem !important; }

    }

    </style>

""", unsafe_allow_html=True)



st.title("⚡ ALVESMLD — Cérebro Neural")
st.caption("Versão evoluída · treino monitorado · memória SQLite · modelo persistido")





# ======================================================================

# UTILITÁRIOS DE TEXTO

# ======================================================================

def limpar_texto(txt):

    """minúsculas, sem acentos, sem pontuação, espaços únicos."""

    t = unicodedata.normalize('NFKD', str(txt).lower().strip())

    t = ''.join(c for c in t if not unicodedata.combining(c))

    t = re.sub(r'[^\w\s]', ' ', t)

    return re.sub(r'\s+', ' ', t).strip()





def colapsar_repeticoes(token):

    """kkkkk/hahaha -> kkk ; oiiiii -> oi ; simmmm -> sim"""

    if re.fullmatch(r'k{2,}', token) or re.fullmatch(r'(?:ha|he|hi|rs){2,}h?', token):

        return 'kkk'

    return re.sub(r'(.)\1{2,}', r'\1', token)





# ======================================================================

# BANCO DE DADOS (CÉREBRO)

# ======================================================================

def inicializar_bd_e_popular_supremo():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()



    cursor.execute('''

        CREATE TABLE IF NOT EXISTS memoria (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            busca_txt TEXT,

            resposta_txt TEXT

        )

    ''')

    cursor.execute('''

        CREATE TABLE IF NOT EXISTS utilizadores (

            email TEXT PRIMARY KEY,

            tokens INTEGER,

            plano TEXT

        )

    ''')

    cursor.execute('''

        CREATE TABLE IF NOT EXISTS codigos_vip (

            codigo TEXT PRIMARY KEY,

            tokens_atribuidos INTEGER,

            usado INTEGER DEFAULT 0

        )

    ''')

    cursor.execute('''

        CREATE TABLE IF NOT EXISTS abreviacoes (

            abrev TEXT PRIMARY KEY,

            expansao TEXT,

            categoria TEXT,

            exemplo TEXT

        )

    ''')

    cursor.execute('''

        CREATE TABLE IF NOT EXISTS girias (

            termo TEXT PRIMARY KEY,

            termo_exibicao TEXT,

            significado TEXT,

            categoria TEXT,

            regiao TEXT,

            canonico TEXT,

            exemplo TEXT

        )

    ''')

    cursor.execute('''

        CREATE TABLE IF NOT EXISTS planilhas_importadas (

            arquivo TEXT PRIMARY KEY,

            hash TEXT,

            importado_em TEXT,

            linhas INTEGER

        )

    ''')



    # Dicionário Massivo com Múltiplas Respostas (5+ variações)

    dados_com_variacoes = [

        ("suave", "Suave? Suave é sabonete Dove, pdp? Vamos, me fale sua dúvida, caralho! 🚀"),

        ("suave", "Suave o caralho! Sabonete Dove é suave, aqui a quebrada é fogo e gás. Manda a braba! 💻"),

        ("suave", "Suave é perfume e sabonete Dove, meu nobre. Qual é o pique de hoje? ⚡"),

        ("suave", "Tudo suave porra nenhuma, o sistema tá a todo vapor! Qual é a fita? 🔥"),

        ("suave", "Suave só na pia com sabonete Dove. Fala logo o que tu quer codar, caralho! 🚀"),

        ("susu", "Susu é o caralho, mano! Suave é sabonete Dove. Manda a braba do que tá pegando aí! 🚀"),

        ("susu", "Susu o caralho! Aqui a gente não dorme no ponto, bota esse código para rodar! 💻"),

        ("susu", "Susu é o cacete, meu parceiro! O ritmo tá insano. Qual é o próximo commit? ⚡"),

        ("susu", "Susu é sabonete Dove, porra! Vai abrir o editor ou vai ficar de caô? 🔥"),

        ("susu", "Susu é a mãe, caralho! Aqui o cérebro SQLite tá tinindo. O que vamos desenrolar? 🚀"),



        ("ata", "Ata é o caralho, porra! Aqui a gente trabalha com certeza absoluta e código de elite. Qual é o próximo passo? 💻🔥"),

        ("ata", "Ata o cacete! Entendeu a fita direito ou quer que eu desenhe na base da marra? ⚡"),

        ("ata", "Ata nada, caralho! Quero ver botar a mão na massa e fazer essa porra compilar! 🚀"),

        ("ata", "Ata é o caralho! Absorveu a visão? Então vai lá e destrói nos códigos. 💎"),

        ("ata", "Ata porra nenhuma, agora o bicho vai pegar! Manda o próximo desafio técnico. 🔥"),

        ("tendeu", "Tendeu porra nenhuma, mas se tendeu agora vai abrir o editor e codar com sangue nos olhos! KKKK 🚀"),

        ("tendeu", "Tendeu o caralho, quero ver aplicar essa lógica sem dar bug na primeira linha! 💻"),

        ("tendeu", "Tendeu perfeitamente, nobre colega? Então execute com exímio rigor técnico! 🧐"),

        ("tendeu", "Tendeu a visão de cria? Agora o lucro é consequência, vai pra cima! ⚡"),

        ("tendeu", "Tendeu sim, porra! A mente tá blindada e o código vai rodar liso. Qual é a próxima? 🔥"),



        ("ixi", "Ixi o caralho, porra! Aqui não tem erro sem solução, bota pra rodar essa porra que a gente resolve! 💻🔥"),

        ("ixi", "Ixi nada, mano! Problema técnico nasceu para ser massacrado por nós. Manda o log do erro! ⚡"),

        ("ixi", "Ixi o caralho, respira fundo, pega o café e vamos debugar essa bosta agora mesmo. 🚀"),

        ("ixi", "Ixi nada, fita resolvida na base da marra e da lógica pura! O que deu errado? 💻"),

        ("ixi", "Ixi é o cu da mãe, caralho! Aqui a engenharia é de ponta, manda o pepino! 🔥"),

        ("pdp", "Pode crer, mano! Visão total e alinhada. Qual é o próximo comando? 🚀"),

        ("pdp", "Pdp total, parceiro! Estamos juntos nessa caminhada rumo ao topo. 💻"),

        ("pdp", "É a visão exata e insofismável! Vamos aplicar isso agora no projeto. ⚡"),

        ("pdp", "Pode crer, caralho! O papo tá reto e o código vai ficar tinindo. 🔥"),

        ("pdp", "Pdp, fechou com força! Ninguém segura o nosso bonde no desenvolvimento. 🚀"),

        ("que", "O que que tem, caralho? Manda a visão completa da tua dúvida para a gente desenrolar essa porra! 💻"),

        ("que", "O que foi, desgraçado? Fala logo o que tá engasgado na tua mente criativa! 🚀"),

        ("que", "Outrossim, nobre colega, especifique melhor a tua indagação para obtermos exímio sucesso. 🧐"),

        ("que", "O que é que há, mano? Tá voando baixo ou travou no meio do caminho? ⚡"),

        ("que", "O que que tá pegando, caralho? Solta o verbo e bota o cérebro para processar! 🔥"),



        ("eximio", "Exímio é o teu intelecto, nobre colega! Vamos arquitetar um código primoroso e insofismável. 🧐🚀"),

        ("eximio", "Trabalho exímio requer dedicação plena e algoritmos impecáveis, porra! 💻"),

        ("hodierno", "Em pleno cenário hodierno, este sistema opera com precisão máxima e eficiência implacável, porra! 💻"),

        ("hodierno", "No panorama tecnológico hodierno, a nossa infraestrutura SQLite reina absoluta. 🚀"),

        ("outrossim", "Outrossim, cumpre salientar que a nossa base de dados jamais falha. Qual é o comando?"),

        ("outrossim", "Outrossim, vale ressaltar que o sucesso é o único desfecho aceitável, caralho! ⚡"),

        ("dessarte", "Dessarte, conclui-se que o nosso ecossistema está deveras avassalador. Manda o papo reto! ⚡"),

        ("primoroso", "Trabalho primoroso e de altíssima estirpe, caralho! A engenharia está impecável."),

        ("insofismavel", "Verdade insofismável e absoluta: o topo é logo ali, meu nobre! 💻🔥"),



        ("qual a braba", "A braba é colocar esse sistema para rodar liso, faturando alto e gerando código de elite! Qual é o pique de hoje? 🚀"),

        ("qual o pique", "O pique tá insano, mano! Muito código, automações e projetos de ponta. Manda a visão."),

        ("papo reto", "Papo reto e sem caô: o sistema tá pronto para qualquer parada que tu inventar. Manda o comando! 💻"),

        ("visao", "Visão dada, parceiro! Vamos ajustar essa porra agora mesmo. 💻"),

        ("fechou", "Fechado com força, caralho! Negócio selado, bora pra cima fazer acontecer. 🚀"),



        ("eae", "Fala, desgraçado! Beleza pura. O que tá rolando na tua mente criativa? 💻"),

        ("ola", "E aí, mano! Pronto para estourar a boca do balão nos códigos. O que temos para hoje? 🚀"),

        ("kkk", "KKKKK po, pior que é verdade, mano! O bagulho é doido."),

        ("kkkk", "KKKKKKK caralho, essa foi foda! Mas bora voltar pro código antes que o chefe surte. 🔥"),

        ("me da um conselho", "Papo reto, mano: não adianta querer abraçar o mundo e codar tudo de uma vez. Faz o básico bem feito, testa linha por linha, e só avança quando o bagulho estiver rodando liso! 🚀"),

        ("to desanimado", "Desanimar o caralho, porra! Tu é o criador do bagulho, levanta essa cabeça. Dá uma pausa, bebe uma água, e volta com sangue nos olhos. O topo é logo ali, mano! 💻🔥"),

        ("quantos anos voce tem", "Porra, sou uma inteligência artificial criada por ti, caralho! Não envelheço, só fico mais braba a cada commit. 🚀"),

        ("quem e voce", "Sou o **ALVESMLD**, o teu assistente de IA avançado integrado com o cérebro SQLite e estúdio de vídeo. Criado pelo brabo, o **João Alves**! 🚀")

    ]



    cursor.execute("SELECT COUNT(*) FROM memoria")

    if cursor.fetchone()[0] < 30:

        for busca, resposta in dados_com_variacoes:

            cursor.execute("INSERT INTO memoria (busca_txt, resposta_txt) VALUES (?, ?)", (busca.lower(), resposta))

        conn.commit()



    conn.close()



inicializar_bd_e_popular_supremo()





# ======================================================================

# IMPORTADOR DE PLANILHAS E FICHEIROS .TXT PARA O CÉREBRO

# ======================================================================

def _ler_planilha(caminho):

    if caminho.lower().endswith('.csv'):

        for enc in ('utf-8-sig', 'latin-1'):

            try:

                return {'csv': pd.read_csv(caminho, dtype=str, sep=None, engine='python', encoding=enc)}

            except Exception:

                continue

        raise ValueError("não consegui ler o CSV")

    return pd.read_excel(caminho, sheet_name=None, dtype=str)





def _inserir_respostas(cursor, chave, respostas, memoria_existente):

    novas = []

    for resp in respostas:

        resp = str(resp).strip()

        if resp and (chave, resp) not in memoria_existente:

            memoria_existente.add((chave, resp))

            novas.append((chave, resp))

    if novas:

        cursor.executemany("INSERT INTO memoria (busca_txt, resposta_txt) VALUES (?, ?)", novas)

    return len(novas)





def _importar_df(cursor, df, memoria_existente):

    df = df.copy().fillna('')

    df.columns = [limpar_texto(c).replace(' ', '_') for c in df.columns]

    cols = set(df.columns)

    cont = {'abreviacoes': 0, 'girias': 0, 'respostas': 0}

    cols_resp = [c for c in df.columns if c.startswith('resposta')]



    def val(r, c):

        return str(r[c]).strip() if c in cols else ''



    if {'abreviacao', 'expansao'} <= cols:

        for _, r in df.iterrows():

            ab, ex = limpar_texto(r['abreviacao']), str(r['expansao']).strip()

            if ab and ex:

                cursor.execute(

                    "INSERT OR REPLACE INTO abreviacoes (abrev, expansao, categoria, exemplo) VALUES (?, ?, ?, ?)",

                    (ab, ex, val(r, 'categoria'), val(r, 'exemplo')))

                cont['abreviacoes'] += 1



    elif {'termo', 'significado'} <= cols:

        for _, r in df.iterrows():

            termo_disp = str(r['termo']).strip()

            chave, sig = limpar_texto(termo_disp), str(r['significado']).strip()

            if not chave or not sig:

                continue

            cursor.execute(

                "INSERT OR REPLACE INTO girias (termo, termo_exibicao, significado, categoria, regiao, canonico, exemplo) "

                "VALUES (?, ?, ?, ?, ?, ?, ?)",

                (chave, termo_disp, sig, val(r, 'categoria'), val(r, 'regiao'),

                 limpar_texto(val(r, 'canonico')), val(r, 'exemplo')))

            cont['girias'] += 1

            cont['respostas'] += _inserir_respostas(cursor, chave, [r[c] for c in cols_resp], memoria_existente)



    elif ('busca' in cols or 'busca_txt' in cols) and cols_resp:

        col_busca = 'busca' if 'busca' in cols else 'busca_txt'

        for _, r in df.iterrows():

            chave = limpar_texto(r[col_busca])

            if chave:

                cont['respostas'] += _inserir_respostas(cursor, chave, [r[c] for c in cols_resp], memoria_existente)

    return cont





def _importar_txt(cursor, caminho, memoria_existente):

    """Lê ficheiros .txt e aprende o conteúdo. Suporta linhas no formato 'pergunta: resposta' ou blocos."""

    conteudo = ""

    for enc in ('utf-8-sig', 'latin-1'):

        try:

            with open(caminho, 'r', encoding=enc) as f:

                conteudo = f.read()

            break

        except Exception:

            continue

    if not conteudo:

        return {'abreviacoes': 0, 'girias': 0, 'respostas': 0}



    novas_respostas = 0

    linhas = conteudo.splitlines()

    for linha in linhas:

        linha = linha.strip()

        if not linha or linha.startswith('#'):

            continue

        # Se contiver ':', separa chave e resposta (ex: "como fazer X: faz assim...")

        if ':' in linha:

            partes = linha.split(':', 1)

            chave = limpar_texto(partes[0])

            resposta = partes[1].strip()

            if chave and resposta:

                novas_respostas += _inserir_respostas(cursor, chave, [resposta], memoria_existente)

        else:

            # Se for texto livre, usa frases inteiras como chave e resposta para expandir o cérebro

            chave = limpar_texto(linha)

            if len(chave) > 3:

                novas_respostas += _inserir_respostas(cursor, chave, [linha], memoria_existente)



    return {'abreviacoes': 0, 'girias': 0, 'respostas': novas_respostas}





def importar_planilhas(forcar=False):

    """Importa tudo que estiver na pasta de planilhas (.xlsx, .csv, .txt). Só reimporta se alterado."""

    os.makedirs(PASTA_PLANILHAS, exist_ok=True)

    relatorio = []

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    ja = dict(cursor.execute("SELECT arquivo, hash FROM planilhas_importadas").fetchall())

    memoria_existente = None



    for nome in sorted(os.listdir(PASTA_PLANILHAS)):

        if nome.startswith('\~$') or not nome.lower().endswith(('.xlsx', '.csv', '.txt')):

            continue

        caminho = os.path.join(PASTA_PLANILHAS, nome)

        with open(caminho, 'rb') as f:

            h = hashlib.sha256(f.read()).hexdigest()

        if not forcar and ja.get(nome) == h:

            continue

        if memoria_existente is None:

            memoria_existente = set(cursor.execute("SELECT busca_txt, resposta_txt FROM memoria").fetchall())

        try:

            total = {'abreviacoes': 0, 'girias': 0, 'respostas': 0}

            if nome.lower().endswith('.txt'):

                parcial = _importar_txt(cursor, caminho, memoria_existente)

                for k in total:

                    total[k] += parcial[k]

            else:

                for _, df in _ler_planilha(caminho).items():

                    parcial = _importar_df(cursor, df, memoria_existente)

                    for k in total:

                        total[k] += parcial[k]



            cursor.execute(

                "INSERT OR REPLACE INTO planilhas_importadas (arquivo, hash, importado_em, linhas) "

                "VALUES (?, ?, datetime('now'), ?)", (nome, h, sum(total.values())))

            conn.commit()

            relatorio.append(f"✅ {nome}: {total['respostas']} respostas/dados novos aprendidos")

        except Exception as e:

            conn.rollback()

            relatorio.append(f"❌ {nome}: {e}")

    conn.close()

    return relatorio





def contar_cerebro():

    conn = sqlite3.connect(DB_PATH)

    cur = conn.cursor()

    res = {

        'abreviações': cur.execute("SELECT COUNT(*) FROM abreviacoes").fetchone()[0],

        'gírias': cur.execute("SELECT COUNT(*) FROM girias").fetchone()[0],

        'respostas': cur.execute("SELECT COUNT(*) FROM memoria").fetchone()[0],

    }

    conn.close()

    return res





# ======================================================================

# DICIONÁRIOS EM MEMÓRIA + NORMALIZAÇÃO

# ======================================================================

def carregar_dicionarios():

    conn = sqlite3.connect(DB_PATH)

    abrevs = conn.execute("SELECT abrev, expansao, categoria, exemplo FROM abreviacoes").fetchall()

    girias = conn.execute("SELECT termo, termo_exibicao, significado, categoria, regiao, canonico, exemplo FROM girias").fetchall()

    conn.close()



    dic = {'abrev': {}, 'abrev_info': {}, 'giria_info': {}, 'giria_tok': {}, 'giria_frases': []}

    for ab, ex, cat, exm in abrevs:

        dic['abrev'][ab] = limpar_texto(ex)

        dic['abrev_info'][ab] = (ab, ex, cat or '', exm or '')

    for termo, disp, sig, cat, reg, can, exm in girias:

        dic['giria_info'][termo] = (disp or termo, sig or '', cat or '', reg or '', exm or '')

        if can:

            if ' ' in termo:

                dic['giria_frases'].append((termo, can))

            else:

                dic['giria_tok'][termo] = can

    dic['giria_frases'].sort(key=lambda x: -len(x[0]))

    return dic





def obter_dic():

    if 'dic' not in st.session_state:

        st.session_state['dic'] = carregar_dicionarios()

    return st.session_state['dic']





def normalizar(texto, nivel=2):

    """nivel 1: expande abreviações / nivel 2: também troca gírias pelo termo padrão."""

    dic = obter_dic()

    t = limpar_texto(texto)

    if nivel >= 2:

        for termo, canon in dic['giria_frases']:

            if termo in t:

                t = re.sub(rf'\b{re.escape(termo)}\b', canon, t)

    saida = []

    for tok in t.split():

        tok = colapsar_repeticoes(tok)

        if tok in dic['abrev']:

            tok = dic['abrev'][tok]

        elif nivel >= 2 and tok in dic['giria_tok']:

            tok = dic['giria_tok'][tok]

        saida.append(tok)

    return ' '.join(saida)





def normalizar_giras_e_abreviacoes(texto):

    return normalizar(texto, nivel=1)





# ======================================================================

# MEMÓRIA DE RESPOSTAS E ÍNDICE VETORIAL

# ======================================================================

def carregar_amostra_memoria(limite=50000):

    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(f"SELECT busca_txt, resposta_txt FROM memoria LIMIT {limite}", conn)

    conn.close()

    return df



if 'memoria_global' not in st.session_state:

    st.session_state['memoria_global'] = carregar_amostra_memoria()





def montar_mapa_respostas():

    conn = sqlite3.connect(DB_PATH)

    rows = conn.execute("SELECT busca_txt, resposta_txt FROM memoria").fetchall()

    conn.close()

    mapa = {}

    for b, r in rows:

        k = limpar_texto(b or '')

        if k and r:

            mapa.setdefault(k, []).append(r)

    return mapa





def atualizar_indice_vetorial():

    df_m = carregar_amostra_memoria(100000)

    if not df_m.empty:

        df_m['busca_txt'] = df_m['busca_txt'].fillna("").astype(str).map(limpar_texto)

        df_m['resposta_txt'] = df_m['resposta_txt'].fillna("Informação aprendida.").astype(str)

        df_m = df_m[df_m['busca_txt'].str.strip() != ""]

        if len(df_m) > 0:

            vec = TfidfVectorizer(max_features=50000, ngram_range=(1, 2), sublinear_tf=True)

            X_mat = vec.fit_transform(df_m['busca_txt'])

            st.session_state['vec'] = vec

            st.session_state['X_mat'] = X_mat

            st.session_state['df_index'] = df_m

            st.session_state['ativo'] = True





def recarregar_cerebro():

    st.session_state['dic'] = carregar_dicionarios()

    st.session_state['mapa_resp'] = montar_mapa_respostas()

    st.session_state['chaves_fuzzy'] = [k for k in st.session_state['mapa_resp'] if 4 <= len(k) <= 30]

    atualizar_indice_vetorial()





if 'cerebro_pronto' not in st.session_state:

    st.session_state['relatorio_import'] = importar_planilhas()

    recarregar_cerebro()

    st.session_state['cerebro_pronto'] = True





# ======================================================================

# BUSCA DE RESPOSTAS

# ======================================================================

def achar_no_mapa(c, mapa):

    if not c:

        return None

    if c in mapa:

        return random.choice(mapa[c])

    tokens = c.split()

    ntok = len(tokens)

    for n in range(min(ntok, 6), 0, -1):

        if n == 1 and ntok > 4:

            continue

        for i in range(ntok - n + 1):

            chave = ' '.join(tokens[i:i + n])

            if chave in mapa:

                return random.choice(mapa[chave])

    return None





def procurar_resposta_aleatoria(pergunta_usuario):

    mapa = st.session_state.get('mapa_resp', {})

    candidatos = []

    for c in (limpar_texto(pergunta_usuario), normalizar(pergunta_usuario, 1), normalizar(pergunta_usuario, 2)):

        if c and c not in candidatos:

            candidatos.append(c)

    for c in candidatos:

        r = achar_no_mapa(c, mapa)

        if r:

            return r

    c0 = candidatos[0] if candidatos else ''

    if c0 and len(c0.split()) <= 3 and len(c0) >= 4:

        parecidas = difflib.get_close_matches(c0, st.session_state.get('chaves_fuzzy', []), n=1, cutoff=0.82)

        if parecidas:

            return random.choice(mapa[parecidas[0]])

    return None





def aprender_novos_dados(pergunta_usuario, resposta_gerada):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    try:

        cursor.execute("INSERT INTO memoria (busca_txt, resposta_txt) VALUES (?, ?)", (pergunta_usuario.lower().strip(), resposta_gerada))

        conn.commit()

        k = limpar_texto(pergunta_usuario)

        if k:

            st.session_state.setdefault('mapa_resp', {}).setdefault(k, []).append(resposta_gerada)

    except Exception:

        pass

    conn.close()





def buscar_tfidf(texto):

    if not st.session_state.get('ativo'):

        return None, 0.0

    vec, X_mat, df_index = st.session_state['vec'], st.session_state['X_mat'], st.session_state['df_index']

    sims = cosine_similarity(vec.transform([texto]), X_mat).flatten()

    melhor_idx = int(np.argmax(sims))

    return df_index.iloc[melhor_idx]['resposta_txt'], float(sims[melhor_idx] * 100)





ABERTURAS = ["Papo reto, mano:", "Visão dada, parceiro:", "Tá ligado?", "Bora decifrar:"]

CAUDAS = ["Qual é a próxima fita? 🚀", "Manda a braba! 💻", "Bora pro código? ⚡"]



PADROES_SIGNIFICADO = [

    r'^(?:o que|oq|q q) (?:significa|quer dizer|quer falar|seria|e|eh)\s+(.+)$',

    r'^que que e\s+(.+)$',

    r'^(?:qual (?:o )?)?significado (?:de|da|do|dessa|desse)\s+(.+)$',

    r'^(?:me )?(?:explica|explique|define|defina)\s+(.+)$',

    r'^(.+?)\s+(?:significa o que|quer dizer o que|e o que)$',

]

PADRAO_TRADUCAO = r'^(?:traduz|traduza|traduzir|decifra|decifre|interpreta|interprete)\s+(?:isso\s+|esse texto\s+|essa frase\s+)?(.+)$'





def buscar_termo(t):

    dic = obter_dic()

    t = re.sub(r'^(?:a |o |as |os )?(?:giria|girias|palavra|sigla|abreviacao|expressao|termo)\s+', '', t).strip()

    candidatos = [t]

    if t.startswith(('a ', 'o ')):

        candidatos.append(t[2:])

    for c in candidatos:

        if c in dic['giria_info']:

            return 'giria', c

        if c in dic['abrev_info']:

            return 'abrev', c

    if len(t) >= 3:

        chaves = list(dic['giria_info'].keys()) + list(dic['abrev_info'].keys())

        m = difflib.get_close_matches(t, chaves, n=1, cutoff=0.85)

        if m:

            return ('giria', m[0]) if m[0] in dic['giria_info'] else ('abrev', m[0])

    return None





def formatar_termo(tipo, chave):

    dic = obter_dic()

    if tipo == 'giria':

        disp, sig, cat, reg, exm = dic['giria_info'][chave]

        txt = f"📖 **{disp}** — {sig}"

        detalhes = []

        if cat:

            detalhes.append(f"🏷️ Categoria: `{cat}`")

        if reg:

            detalhes.append(f"📍 Região: `{reg}`")

        if detalhes:

            txt += "\n\n" + " · ".join(detalhes)

        if exm:

            txt += f"\n\n💬 Exemplo: *{exm}*"

    else:

        ab, ex, cat, exm = dic['abrev_info'][chave]

        txt = f"📖 **{ab}** = {ex}"

        if cat:

            txt += f"\n\n🏷️ Categoria: `{cat}`"

        if exm:

            txt += f"\n\n💬 Exemplo: *{exm}*"

    return txt





def responder_significado(pergunta):

    c = limpar_texto(pergunta)

    for padrao in PADROES_SIGNIFICADO:

        m = re.match(padrao, c)

        if m:

            achou = buscar_termo(m.group(1).strip())

            if achou:

                return f"{random.choice(ABERTURAS)}\n\n{formatar_termo(*achou)}"

    return None





def analisar_texto(texto_limpo):

    dic = obter_dic()

    achados = []

    resto = texto_limpo

    for termo in sorted([k for k in dic['giria_info'] if ' ' in k], key=len, reverse=True):

        padrao = rf'\b{re.escape(termo)}\b'

        if re.search(padrao, resto):

            achados.append(('giria', termo))

            resto = re.sub(padrao, ' ', resto)

    expandido = []

    for tok in texto_limpo.split():

        t = colapsar_repeticoes(tok)

        if t in dic['abrev_info']:

            expandido.append(dic['abrev_info'][t][1])

            achados.append(('abrev', t))

        else:

            expandido.append(tok)

    for tok in resto.split():

        t = colapsar_repeticoes(tok)

        if t in dic['giria_info']:

            achados.append(('giria', t))

    vistos, unicos = set(), []

    for a in achados:

        if a not in vistos:

            vistos.add(a)

            unicos.append(a)

    return ' '.join(expandido), unicos





def responder_traducao(pergunta):

    m = re.match(PADRAO_TRADUCAO, limpar_texto(pergunta))

    if not m:

        return None

    expandido, achados = analisar_texto(m.group(1).strip())

    dic = obter_dic()

    txt = f"🔎 **Tradução (abreviações expandidas):**\n\n> {expandido}\n\n"

    if not achados:

        return txt + "Não achei gíria nem abreviação conhecida aí. Se for nova, joga num ficheiro TXT ou planilha que eu aprendo! 🧠"

    linhas = []

    for tipo, chave in achados:

        if tipo == 'giria':

            disp, sig, cat, reg, _ = dic['giria_info'][chave]

            extra = f" *({reg})*" if reg and reg != 'Nacional' else ""

            linhas.append(f"- **{disp}** — {sig}{extra}")

        else:

            ab, ex, _, _ = dic['abrev_info'][chave]

            linhas.append(f"- **{ab}** → {ex}")

    return txt + "📚 **Termos que entendi:**\n" + "\n".join(linhas)





def resposta_por_giria(pergunta):

    c = limpar_texto(pergunta)

    dic = obter_dic()

    if c in dic['giria_info']:

        disp, sig, *_ = dic['giria_info'][c]

        return f"'{disp}' significa: {sig.rstrip('. ')}. {random.choice(CAUDAS)}"

    if c in dic['abrev_info']:

        ab, ex, *_ = dic['abrev_info'][c]

        return f"'{ab}' = {ex}, mano! {random.choice(CAUDAS)}"

    return None





# --- BARRA LATERAL ---

st.sidebar.header("🔐 Autenticação por E-mail")



email_input = st.sidebar.text_input("Insere o teu e-mail:", value=st.session_state['email_utilizador'] or "")

if st.sidebar.button("Entrar / Registar"):

    if email_input and "@" in email_input:

        st.session_state['email_utilizador'] = email_input.strip()

        st.rerun()

    else:

        st.sidebar.error("⚠️ Insere um e-mail válido.")



def verificar_ou_criar_utilizador(email):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("SELECT tokens, plano FROM utilizadores WHERE email = ?", (email,))

    res = cursor.fetchone()



    is_mestre = email.lower().strip() in [m.lower() for m in EMAILS_MESTRES]



    if not res:

        tokens = 999999 if is_mestre else TOKENS_INICIAIS

        plano = "MASTER / ILIMITADO" if is_mestre else "GRATUITO"

        cursor.execute("INSERT INTO utilizadores (email, tokens, plano) VALUES (?, ?, ?)", (email, tokens, plano))

        conn.commit()

        res = (tokens, plano)

    else:

        if is_mestre and res[1] != "MASTER / ILIMITADO":

            cursor.execute("UPDATE utilizadores SET tokens = 999999, plano = 'MASTER / ILIMITADO' WHERE email = ?", (email,))

            conn.commit()

            res = (999999, "MASTER / ILIMITADO")



    conn.close()

    return res



def gastar_token(email, quantidade=1):

    if email.lower().strip() in [m.lower() for m in EMAILS_MESTRES]:

        return True



    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("SELECT tokens FROM utilizadores WHERE email = ?", (email,))

    res = cursor.fetchone()

    if res and res[0] >= quantidade:

        novos_tokens = res[0] - quantidade

        cursor.execute("UPDATE utilizadores SET tokens = ? WHERE email = ?", (novos_tokens, email))

        conn.commit()

        conn.close()

        return True

    conn.close()

    return False



if st.session_state['email_utilizador']:

    email_atual = st.session_state['email_utilizador']

    tokens_atuais, plano_atual = verificar_ou_criar_utilizador(email_atual)

    is_mestre_atual = email_atual.lower().strip() in [m.lower() for m in EMAILS_MESTRES]



    st.sidebar.markdown("---")

    st.sidebar.write(f"📧 **Conta:** `{email_atual}`")

    st.sidebar.write(f"🏷️ **Plano:** `{plano_atual}`")



    if not is_mestre_atual:

        st.sidebar.metric("🪙 Tokens Disponíveis", tokens_atuais)

        st.sidebar.caption(f"💡 Custo por vídeo: {CUSTO_VIDEO} | Consulta: 1 token")



    st.sidebar.markdown("---")

    st.sidebar.subheader("🚀 Recarregar via PIX")

    st.sidebar.markdown("""

    Para obter mais créditos:

    * **Chave Pix (Telefone):** `17991656885`

    * **Nome:** João Alves (ALVESMLD)

    """)



    codigo_input = st.sidebar.text_input("🔑 Código VIP:")

    if st.sidebar.button("Ativar Código VIP"):

        if codigo_input:

            conn = sqlite3.connect(DB_PATH)

            cursor = conn.cursor()

            cursor.execute("SELECT tokens_atribuidos, usado FROM codigos_vip WHERE codigo = ?", (codigo_input,))

            res_codigo = cursor.fetchone()

            if res_codigo:

                tokens_extra, usado = res_codigo

                if usado == 0:

                    cursor.execute("UPDATE utilizadores SET tokens = tokens + ?, plano = 'VIP / PRO' WHERE email = ?", (tokens_extra, email_atual))

                    cursor.execute("UPDATE codigos_vip SET usado = 1 WHERE codigo = ?", (codigo_input,))

                    conn.commit()

                    conn.close()

                    st.sidebar.success(f"🎉 Código ativado! +{tokens_extra} tokens.")

                    st.rerun()

                else:

                    st.sidebar.error("⚠️ Este código já foi usado.")

            else:

                st.sidebar.error("❌ Código inválido.")

            conn.close()



    if is_mestre_atual:

        st.sidebar.markdown("---")

        st.sidebar.subheader("🛠️ Painel Admin (Mestre)")

        qtd_gerar = st.sidebar.number_input("Tokens do Código:", min_value=10, max_value=5000, value=100)

        if st.sidebar.button("Gerar Código VIP"):

            novo_cod = "ALVES-" + str(uuid.uuid4())[:8].upper()

            conn = sqlite3.connect(DB_PATH)

            cursor = conn.cursor()

            cursor.execute("INSERT INTO codigos_vip (codigo, tokens_atribuidos, usado) VALUES (?, ?, 0)", (novo_cod, qtd_gerar))

            conn.commit()

            conn.close()

            st.sidebar.code(novo_cod)

            st.sidebar.success("Código gerado com sucesso!")



        # --- NÚCLEO NEURAL EVOLUÍDO ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("🧠 Núcleo Neural ALVESMLD")
        if not NUCLEO_NEURAL_DISPONIVEL:
            st.sidebar.warning("Núcleo neural indisponível. Confira alvesmld_neural.py e as dependências.")
            st.sidebar.caption(ERRO_NUCLEO_NEURAL or "Módulo não carregado")
        else:
            try:
                estado_neural = status_modelo()
                if estado_neural.get("treinado"):
                    st.sidebar.success("Modelo salvo e pronto para carregar")
                    c1, c2 = st.sidebar.columns(2)
                    c1.metric("Exemplos", estado_neural.get("amostras", 0))
                    c2.metric("Respostas", estado_neural.get("respostas_conhecidas", 0))
                    st.sidebar.caption(f"Épocas: {estado_neural.get('epocas', 0)} · arquivo: {estado_neural.get('arquivo', '')}")
                    if estado_neural.get("perda_final") is not None:
                        st.sidebar.caption(f"Perda final: {estado_neural['perda_final']}")
                else:
                    st.sidebar.info("Ainda não existe modelo treinado salvo.")
            except Exception as erro_status:
                st.sidebar.warning(f"Não consegui ler o estado do modelo: {erro_status}")

            epocas_neurais = st.sidebar.slider("Épocas de treinamento", min_value=5, max_value=80, value=20, step=5)
            treinar_agora = st.sidebar.button("🚀 Treinar / atualizar modelo", use_container_width=True)
            if treinar_agora:
                barra = st.sidebar.progress(0, text="Lendo e limitando os dados para treinamento...")
                status_treino = st.sidebar.empty()
                perda_box = st.sidebar.empty()
                def _atualizar_progresso(atual, total, perda):
                    if atual <= 0:
                        barra.progress(0, text="Dados preparados; montando vocabulário e rede neural...")
                        status_treino.caption("Preparação concluída. Iniciando as épocas de treinamento...")
                        perda_box.empty()
                        return
                    barra.progress(min(100, int(atual * 100 / max(total, 1))), text=f"Treinando: época {atual}/{total}")
                    status_treino.caption(f"Progresso: {atual}/{total} épocas")
                    perda_box.caption(f"Perda da época: {perda:.5f}")
                try:
                    with st.spinner("O ALVESMLD está ajustando a rede neural. Não feche esta página..."):
                        resultado_treino = treinar_modelo(DB_PATH, epocas=epocas_neurais, callback_progresso=_atualizar_progresso)
                    if resultado_treino.get("ok"):
                        barra.progress(100, text="Treinamento concluído e modelo salvo")
                        st.sidebar.success(resultado_treino.get("mensagem", "Treino concluído."))
                        st.sidebar.caption(f"Duração: {resultado_treino.get('duracao_segundos', '?')} s · dispositivo: {resultado_treino.get('dispositivo', 'CPU')}")
                        st.sidebar.info("O modelo salvo será reutilizado nas próximas respostas enquanto o arquivo persistir.")
                    else:
                        barra.empty()
                        st.sidebar.warning(resultado_treino.get("mensagem", "Não foi possível treinar."))
                except Exception as erro_treino:
                    barra.empty()
                    st.sidebar.error(f"Falha no treinamento: {erro_treino}")

            with st.sidebar.expander("✍️ Ensinar uma resposta correta"):
                with st.form("form_ensinar_alvesmld", clear_on_submit=True):
                    pergunta_ensinada = st.text_input("Pergunta / frase", placeholder="Ex.: o que é uma variável em Python?")
                    resposta_ensinada = st.text_area("Resposta correta", placeholder="Escreva uma resposta que o ALVESMLD deve aprender...")
                    salvar_exemplo = st.form_submit_button("Salvar exemplo na memória")
                if salvar_exemplo:
                    if not pergunta_ensinada.strip() or not resposta_ensinada.strip():
                        st.sidebar.warning("Preencha a pergunta e a resposta.")
                    else:
                        try:
                            with sqlite3.connect(DB_PATH) as conn_ensino:
                                conn_ensino.execute("INSERT INTO memoria (busca_txt, resposta_txt) VALUES (?, ?)", (pergunta_ensinada.strip().lower(), resposta_ensinada.strip()))
                            st.sidebar.success("Exemplo salvo. Para incorporar ao modelo neural, clique em Treinar / atualizar modelo.")
                        except Exception as erro_ensino:
                            st.sidebar.error(f"Não consegui salvar o exemplo: {erro_ensino}")

        # --- PLANILHAS E TXT DO CÉREBRO ---

        st.sidebar.markdown("---")

        st.sidebar.subheader("📚 Ficheiros do Cérebro")

        stats = contar_cerebro()

        st.sidebar.caption(f"🧠 {stats['abreviações']} abreviações · {stats['gírias']} gírias · {stats['respostas']} respostas")



        arquivos_up = st.sidebar.file_uploader("Enviar planilhas (.xlsx, .csv) ou TXT", type=["xlsx", "csv", "txt"], accept_multiple_files=True)

        if st.sidebar.button("Importar ficheiros enviados") and arquivos_up:

            os.makedirs(PASTA_PLANILHAS, exist_ok=True)

            for arq in arquivos_up:

                with open(os.path.join(PASTA_PLANILHAS, os.path.basename(arq.name)), "wb") as f:

                    f.write(arq.getbuffer())

            rel = importar_planilhas()

            recarregar_cerebro()

            st.session_state['relatorio_import'] = rel

            st.rerun()



        if st.sidebar.button("🔄 Reimportar toda a pasta"):

            st.session_state['relatorio_import'] = importar_planilhas(forcar=True)

            recarregar_cerebro()

            st.rerun()



        for linha in st.session_state.get('relatorio_import', []):

            st.sidebar.caption(linha)



def e_pedido_de_video(pergunta):

    p_lower = pergunta.lower()

    return any(k in p_lower for k in ["video", "vídeo", "gerar video", "criar video", "fazer video", "produzir video", "vdeo"])



def gerar_ficheiro_video(texto_tema):

    output_path = "video_gerado.mp4"

    if MOVIEPY_DISPONIVEL:

        try:

            bg = ColorClip(size=(720, 480), color=(20, 20, 40), duration=4)

            txt = TextClip(texto_tema[:35], fontsize=28, color='white', size=(680, 440)).set_duration(4)

            video = CompositeVideoClip([bg, txt.set_position('center')])

            video.write_videofile(output_path, fps=24, codec='libx264', audio=False, logger=None)

            return output_path

        except Exception:

            pass

    with open(output_path, "wb") as f:

        f.write(b"DUMMY_MP4_CONTENT")

    return output_path



st.markdown("---")

for h in st.session_state['chat_historico']:

    with st.chat_message(h["role"]):

        st.markdown(h["content"])



if not st.session_state['email_utilizador']:

    st.warning("⚠️ Por favor, insere o teu e-mail na barra lateral para desbloquear o assistente.")

else:

    email_atual = st.session_state['email_utilizador']

    tokens_atuais, plano_atual = verificar_ou_criar_utilizador(email_atual)

    is_mestre_atual = email_atual.lower().strip() in [m.lower() for m in EMAILS_MESTRES]



    st.markdown("### 🎙️ Falar com o ALVESMLD")
    audio_usuario = st.audio_input("Grave uma pergunta em português", key="alvesmld_audio_input") if hasattr(st, "audio_input") else None
    pergunta_voz = None
    if audio_usuario is not None and st.button("🗣️ Transcrever áudio", key="alvesmld_transcrever"):
        with st.spinner("Transcrevendo áudio..."):
            pergunta_voz, erro_voz = transcrever_audio(audio_usuario)
        if erro_voz:
            st.warning(erro_voz)
        elif pergunta_voz:
            st.session_state["alvesmld_pergunta_voz"] = pergunta_voz
            st.success(f"Entendi: {pergunta_voz}")
            st.info("Transcrição recebida; o ALVESMLD vai processar a pergunta.")

    pergunta_digitada = st.chat_input("Digite sua mensagem ou envie a frase transcrita...")
    pergunta = pergunta_digitada or st.session_state.pop("alvesmld_pergunta_voz", None)

    if pergunta:

        if e_pedido_de_video(pergunta):

            if tokens_atuais < CUSTO_VIDEO and not is_mestre_atual:

                st.error(f"❌ Precisas de {CUSTO_VIDEO} tokens para gerar um vídeo. Envia Pix para **17991656885** e usa o código VIP.")

            else:

                if not is_mestre_atual:

                    gastar_token(email_atual, CUSTO_VIDEO)



                with st.chat_message("user"):

                    st.markdown(pergunta)

                    st.session_state['chat_historico'].append({"role": "user", "content": pergunta})



                with st.chat_message("assistant"):

                    with st.spinner("🎬 A renderizar vídeo com base no cérebro SQLite..."):

                        caminho_video = gerar_ficheiro_video(pergunta)

                        st.markdown(f"🎥 **Vídeo gerado com sucesso para:** *{pergunta}* 🚀")

                        if os.path.exists(caminho_video):

                            try:

                                st.video(caminho_video)

                            except:

                                st.write("Ficheiro de vídeo gerado com sucesso.")

                        st.session_state['chat_historico'].append({"role": "assistant", "content": f"Vídeo gerado para: {pergunta}"})



        else:

            if tokens_atuais <= 0 and not is_mestre_atual:

                st.error("❌ Tokens esgotados! Faz um Pix para **17991656885** e insere o código VIP na barra lateral.")

            else:

                if not is_mestre_atual:

                    gastar_token(email_atual, 1)



                with st.chat_message("user"):

                    st.markdown(pergunta)

                    st.session_state['chat_historico'].append({"role": "user", "content": pergunta})



                with st.chat_message("assistant"):

                    with st.spinner("🔍 A analisar o histórico e o cérebro SQLite..."):



                        historico_usuario = [h["content"].lower().strip() for h in st.session_state['chat_historico'] if h["role"] == "user"]

                        vezes_repetida = historico_usuario.count(pergunta.lower().strip())



                        resp = None



                        if vezes_repetida >= 2:

                            palavras = pergunta.split()

                            if len(palavras) <= 3:

                                zueiras_repeticao_simples = [

                                    f"Caralho, já é a {vezes_repetida}ª vez que me perguntas '{pergunta}'! Tá com Alzheimer digital, desgraçado? KKKK 🚀",

                                    f"Porra, tá travado no loop com '{pergunta}'? Acorda para a vida, mano! 💻",

                                    f"De novo com '{pergunta}'? Vai tomar um café para resetar esse teu cérebro lento, caralho! KKKK ⚡",

                                    f"Repetir '{pergunta}' duas vezes é atestado de demência, mano! Foca no progresso! 🔥"

                                ]

                                resp = random.choice(zueiras_repeticao_simples)

                            else:

                                cobrancas_complexas = [

                                    f"Outrossim, nobre colega, tu já perguntaste isso várias vezes. O que tu não entendeste exatamente em '{pergunta}'? Quer que eu desenhe na base da marra e da lógica? 🧐🚀",

                                    f"Papo reto e insofismável: já é a {vezes_repetida}ª vez que mandas essa questão complexa. O que tu não entendeste na explicação anterior, caralho? Fala logo! 💻",

                                    f"KKKKK porra, se repetiste essa mesma dúvida complexa é porque a cognição falhou. O que tu não entendeste de verdade? Manda a real! 🔥"

                                ]

                                resp = random.choice(cobrancas_complexas)



                        if not resp:

                            resp = responder_significado(pergunta)

                        if not resp:

                            resp = responder_traducao(pergunta)

                        if not resp:

                            resp = procurar_resposta_aleatoria(pergunta)

                        if not resp:

                            resp = resposta_por_giria(pergunta)

                        if not resp:

                            for nivel in (1, 2):

                                candidata, score = buscar_tfidf(normalizar(pergunta, nivel))

                                if candidata and score >= LIMIAR_SIMILARIDADE:

                                    resp = candidata

                                    break



                        if not resp and NUCLEO_NEURAL_DISPONIVEL:
                            try:
                                resultado_neural = responder_inteligente(pergunta, DB_PATH)
                                resposta_neural = resultado_neural.get("resposta")
                                metodo_neural = resultado_neural.get("metodo", "")
                                if resposta_neural and metodo_neural != "sem correspondência confiável":
                                    resp = resposta_neural
                                    if resultado_neural.get("precisa_confirmacao"):
                                        resp += "\n\n_Obs.: minha confiança nesta resposta é baixa; confirma com outro exemplo para eu melhorar._"
                            except Exception:
                                # Mantém o chat funcionando caso a inferência falhe.
                                pass

                        if not resp:

                            frases_fallback = [

                                f"Outrossim, nobre colega, sobre '{pergunta}', essa questão hodierna é deveras instigante, mas a gente resolve na base da marra e da lógica. 🧐🚀",

                                f"Papo reto e insofismável: para desenrolar essa fita de '{pergunta}', precisamos de um raciocínio exímio e sem caô. O que tu quer codar agora, caralho? 💻",

                                f"KKKKK porra, essa tua indagação sobre '{pergunta}' é primorosa! Vamos registrá-la no cérebro e estruturar a solução com rigor técnico. 🔥",

                                f"Visão de cria: essa dúvida sobre '{pergunta}' exige foco total e engenharia pesada. Bora pra cima! ⚡",

                                f"Caralho, essa fita de '{pergunta}' me pegou desprevenido, mas o sistema desenrola tudo na base da marra! 🚀"

                            ]

                            resp = random.choice(frases_fallback)

                            # Não registrar respostas genéricas aleatórias como conhecimento verdadeiro.
                            # O usuário pode ensinar uma resposta validada pelo painel administrativo.



                        st.markdown(resp)

                        st.session_state['chat_historico'].append({"role": "assistant", "content": resp})
# Estúdio local de programação: integração com VS Code no Linux.
try:
    from estudio_programacao import render_studio
    render_studio()
except Exception as erro_estudio:
    st.warning(f"O Estúdio de Programação não pôde ser carregado: {erro_estudio}")
