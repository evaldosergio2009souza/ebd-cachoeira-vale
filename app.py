import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# =====================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================
st.set_page_config(page_title="EBD Digital - Regional", layout="wide")

# --- SISTEMA DE ACESSO PROFISSIONAL (OPÇÃO 2 - SECRETS) ---
def verificar_senha():
    """Retorna True se o usuário inseriu a senha correta configurada nos Secrets."""
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"]:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown("### 🔐 Acesso Restrito")
            st.info("Sistema da Regional Cachoeira do Vale")
            senha_digitada = st.text_input("Digite a senha de acesso:", type="password")
            
            if st.button("Entrar"):
                try:
                    # Busca a senha definida no painel 'Secrets' do Streamlit
                    if senha_digitada == st.secrets["senha_geral"]:
                        st.session_state["autenticado"] = True
                        st.rerun()
                    else:
                        st.error("Senha incorreta! Procure o Coordenador Evaldo Sérgio.")
                except KeyError:
                    st.error("Erro Crítico: A senha não foi configurada no painel Secrets do Streamlit.")
                    st.warning("Vá em Settings > Secrets e adicione: senha_geral = 'suasenha'")
        return False
    return True

# Bloqueia o restante do código se não estiver autenticado
if not verificar_senha():
    st.stop()

# =====================================
# BANCO DE DADOS
# =====================================
def criar_conexao():
    # Conecta ao arquivo de banco de dados que você enviou ao GitHub
    conn = sqlite3.connect("chamada_escola_dominical.db", check_same_thread=False)
    return conn

conn = criar_conexao()
cursor = conn.cursor()

# Garantir estrutura básica das tabelas
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
# CABEÇALHO (IMAGEM CENTRALIZADA)
# =====================================
col_esq, col_centro, col_dir = st.columns([1, 1, 1])
with col_centro:
    try:
        # Tenta carregar sua imagem igreja.png (tamanho 1/3)
        st.image("igreja.png", width=200)
    except:
        st.write("⛪ **EBD DIGITAL**")

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
# NAVEGAÇÃO LATERAL
# =====================================
st.sidebar.title("Painel de Controle")
opcao = st.sidebar.radio("Navegação:", 
                         ["Fazer Chamada", "Ranking e Prêmios", "Cadastrar Alunos", "Gerenciar Classes"])

# --- FUNÇÃO: CHAMADA ---
if opcao == "Fazer Chamada":
    st.header("📝 Chamada do Dia")
    cursor.execute("SELECT nome FROM classes ORDER BY nome")
    classes = [c[0] for c in cursor.fetchall()]
    
    if not classes:
        st.info("Cadastre uma classe primeiro no menu lateral.")
    else:
        cl_sel = st.selectbox("Selecione a Classe", classes)
        dt_sel = st.date_input("Data da Aula", datetime.now())
        
        cursor.execute("SELECT id, nome FROM alunos WHERE classe = ? ORDER BY nome", (cl_sel,))
        alunos = cursor.fetchall()
        
        for id_a, nome in alunos:
            c1, c2 = st.columns([3, 1])
            c1.write(f"👤 {nome}")
            if c2.button("Presente ✅", key=f"p_{id_a}"):
                cursor.execute("INSERT INTO presencas (aluno_id, data_chamada, presente) VALUES (?, ?, ?)", 
                               (id_a, dt_sel.strftime("%d/%m/%Y"), 1))
                conn.commit()
                st.toast(f"Presença confirmada: {nome}")

# --- FUNÇÃO: RANKING ---
elif opcao == "Ranking e Prêmios":
    st.header("🏆 Ranking de Frequência")
    dt_r = st.date_input("Data do Domingo", datetime.now())
    
    if st.button("Calcular Vencedor"):
        cursor.execute("SELECT nome FROM classes")
        todas_classes = [c[0] for c in cursor.fetchall()]
        ranking = []
        
        for c in todas_classes:
            cursor.execute("SELECT id FROM alunos WHERE classe = ?", (c,))
            total_inscritos = len(cursor.fetchall())
            
            if total_inscritos > 0:
                cursor.execute("""
                    SELECT SUM(presente) FROM presencas 
                    JOIN alunos ON presencas.aluno_id = alunos.id 
                    WHERE alunos.classe = ? AND data_chamada = ?""", (c, dt_r.strftime("%d/%m/%Y")))
                total_presentes = cursor.fetchone()[0] or 0
                perc = (total_presentes / total_inscritos) * 100
                ranking.append({"Classe": c, "Presentes": total_presentes, "Total": total_inscritos, "%": round(perc, 1)})
        
        if ranking:
            df = pd.DataFrame(ranking).sort_values(by="%", ascending=False)
            st.table(df)
            st.balloons()
            st.success(f"⭐ A classe vencedora é: {df.iloc[0]['Classe']}")
        else:
            st.warning("Nenhuma chamada realizada nesta data.")

# --- FUNÇÃO: CADASTROS ---
elif opcao == "Cadastrar Alunos":
    st.header("👥 Cadastro de Alunos")
    cursor.execute("SELECT nome FROM classes ORDER BY nome")
    classes_disp = [c[0] for c in cursor.fetchall()]
    
    aba1, aba2 = st.tabs(["Individual", "Em Bloco (WhatsApp/Excel)"])
    
    with aba1:
        nome_novo = st.text_input("Nome Completo")
        classe_nova = st.selectbox("Classe", classes_disp, key="cad_ind")
        if st.button("Salvar Aluno"):
            if nome_novo:
                cursor.execute("INSERT INTO alunos (nome, classe) VALUES (?, ?)", (nome_novo.strip(), classe_nova))
                conn.commit()
                st.success("Aluno cadastrado!")
    
    with aba2:
        classe_lista = st.selectbox("Classe para a lista", classes_disp, key="cad_blc")
        area_texto = st.text_area("Cole os nomes (um por linha)")
        if st.button("Importar Lista Agora"):
            nomes = area_texto.split('\n')
            for n in nomes:
                if n.strip():
                    cursor.execute("INSERT INTO alunos (nome, classe) VALUES (?, ?)", (n.strip(), classe_lista))
            conn.commit()
            st.success("Lista processada com sucesso!")

elif opcao == "Gerenciar Classes":
    st.header("🏫 Gestão de Classes")
    n_cl = st.text_input("Nome da nova classe")
    if st.button("Adicionar Classe"):
        try:
            cursor.execute("INSERT INTO classes (nome) VALUES (?)", (n_cl.strip(),))
            conn.commit()
            st.success("Classe criada!")
        except:
            st.error("Esta classe já existe.")

# Rodapé
st.sidebar.markdown("---")
st.sidebar.info(f"**Desenvolvedor:**\nEvaldo Sérgio\n\n**Regional:**\nCachoeira do Vale")