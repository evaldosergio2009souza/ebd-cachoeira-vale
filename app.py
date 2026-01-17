import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# =====================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================
st.set_page_config(page_title="EBD Digital - Regional", layout="wide")

# --- SISTEMA DE ACESSO (PROTEÇÃO DE DADOS) ---
def verificar_senha():
    """Retorna True se o usuário inseriu a senha correta."""
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"]:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown("### 🔐 Acesso Restrito")
            senha = st.text_input("Digite a senha da Regional:", type="password")
            if st.button("Entrar"):
                # Você pode alterar a senha 'EBD2026' para a que desejar
                if senha == "EBD2026": 
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Senha incorreta! Entre em contato com Evaldo Sérgio.")
        return False
    return True

# Se não estiver autenticado, o script para aqui
if not verificar_senha():
    st.stop()

# =====================================
# BANCO DE DADOS E LÓGICA
# =====================================
def criar_conexao():
    conn = sqlite3.connect("chamada_escola_dominical.db", check_same_thread=False)
    return conn

conn = criar_conexao()
cursor = conn.cursor()

# Garantir que as tabelas existam
cursor.execute("CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE NOT NULL)")
cursor.execute("CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, classe TEXT NOT NULL)")
cursor.execute("""
CREATE TABLE IF NOT EXISTS presencas (
    id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER NOT NULL, 
    data_chamada TEXT NOT NULL, presente INTEGER NOT NULL,
    FOREIGN KEY (aluno_id) REFERENCES alunos(id))
""")
conn.commit()

# =====================================
# CABEÇALHO CENTRALIZADO
# =====================================
col_esq, col_centro, col_dir = st.columns([1, 1, 1])
with col_centro:
    try:
        st.image("igreja.png", width=200)
    except:
        st.write("⛪ **EBD Regional**")

st.markdown(f"""
    <div style="text-align: center; background-color: #2c3e50; padding: 15px; border-radius: 10px; color: white; margin-bottom: 20px;">
        <h1 style='margin: 0; font-size: 22px;'>Igreja Evangélica Assembleia de Deus</h1>
        <h3 style='margin: 0; font-size: 17px;'>Regional Cachoeira do Vale</h3>
        <p style='margin: 10px 0 0 0; font-size: 14px;'>
            <b>Pr. Regional:</b> Helciley Fialho | <b>Pr. Presidente:</b> Carmo Matias
        </p>
    </div>
    """, unsafe_allow_html=True)

# =====================================
# MENU E NAVEGAÇÃO
# =====================================
st.sidebar.title("Menu Principal")
opcao = st.sidebar.radio("Selecione:", ["Fazer Chamada", "Ranking e Prêmios", "Cadastrar Alunos", "Gerenciar Classes"])

if opcao == "Gerenciar Classes":
    st.header("🏫 Gestão de Classes")
    nova_classe = st.text_input("Nome da nova classe")
    if st.button("Salvar"):
        if nova_classe:
            try:
                cursor.execute("INSERT INTO classes (nome) VALUES (?)", (nova_classe.strip(),))
                conn.commit()
                st.success("Classe registrada!")
            except: st.error("Erro: Classe já existe.")

elif opcao == "Cadastrar Alunos":
    st.header("👥 Cadastro de Alunos")
    cursor.execute("SELECT nome FROM classes ORDER BY nome")
    classes = [c[0] for c in cursor.fetchall()]
    
    if not classes: st.warning("Cadastre uma classe primeiro!")
    else:
        aba1, aba2 = st.tabs(["Individual", "Lista em Bloco"])
        with aba1:
            n_aluno = st.text_input("Nome do Aluno")
            c_aluno = st.selectbox("Classe", classes, key="i")
            if st.button("Salvar Aluno"):
                cursor.execute("INSERT INTO alunos (nome, classe) VALUES (?, ?)", (n_aluno.strip(), c_aluno))
                conn.commit()
                st.success("Cadastrado!")
        with aba2:
            c_bloco = st.selectbox("Classe", classes, key="b")
            txt_nomes = st.text_area("Cole a lista (um por linha)")
            if st.button("Importar"):
                for n in txt_nomes.split('\n'):
                    if n.strip(): cursor.execute("INSERT INTO alunos (nome, classe) VALUES (?, ?)", (n.strip(), c_bloco))
                conn.commit()
                st.success("Lista Importada!")

elif opcao == "Fazer Chamada":
    st.header("📝 Chamada")
    cursor.execute("SELECT nome FROM classes ORDER BY nome")
    classes = [c[0] for c in cursor.fetchall()]
    cl_sel = st.selectbox("Classe", classes)
    dt_sel = st.date_input("Data", datetime.now())
    
    if cl_sel:
        cursor.execute("SELECT id, nome FROM alunos WHERE classe = ? ORDER BY nome", (cl_sel,))
        alunos = cursor.fetchall()
        for id_a, nome in alunos:
            c1, c2 = st.columns([3, 1])
            c1.write(nome)
            if c2.button("Presente", key=f"p_{id_a}"):
                cursor.execute("INSERT INTO presencas (aluno_id, data_chamada, presente) VALUES (?, ?, ?)", 
                               (id_a, dt_sel.strftime("%d/%m/%Y"), 1))
                conn.commit()
                st.toast(f"Presença: {nome}")

elif opcao == "Ranking e Prêmios":
    st.header("🏆 Ranking do Dia")
    dt_r = st.date_input("Selecione o Domingo", datetime.now())
    if st.button("Ver Ganhador"):
        cursor.execute("SELECT nome FROM classes")
        cls = [c[0] for c in cursor.fetchall()]
        res = []
        for c in cls:
            cursor.execute("SELECT id FROM alunos WHERE classe = ?", (c,))
            tot = len(cursor.fetchall())
            if tot > 0:
                cursor.execute("SELECT SUM(presente) FROM presencas JOIN alunos ON presencas.aluno_id = alunos.id WHERE alunos.classe = ? AND data_chamada = ?", (c, dt_r.strftime("%d/%m/%Y")))
                pre = cursor.fetchone()[0] or 0
                res.append({"Classe": c, "Freq %": round((pre/tot)*100, 1)})
        if res:
            df = pd.DataFrame(res).sort_values(by="Freq %", ascending=False)
            st.table(df)
            st.balloons()
            st.success(f"🥇 Vencedora: {df.iloc[0]['Classe']}")

st.sidebar.markdown("---")
st.sidebar.info(f"Dev: Evaldo Sérgio\nRegional Cachoeira do Vale")