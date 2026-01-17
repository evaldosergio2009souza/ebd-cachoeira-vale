import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# =====================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================
st.set_page_config(page_title="EBD Digital - Regional", layout="wide")

# Conexão com Banco de Dados
def criar_conexao():
    conn = sqlite3.connect("chamada_escola_dominical.db", check_same_thread=False)
    return conn

conn = criar_conexao()
cursor = conn.cursor()

# Inicialização das Tabelas
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
# NOVO CABEÇALHO (IMAGEM PEQUENA E CENTRALIZADA)
# =====================================
# Criamos 3 colunas para centralizar a imagem e deixá-la pequena
col_esq, col_centro, col_dir = st.columns([1, 1, 1])

with col_centro: # A imagem entra na coluna do meio
    try:
        # width=200 deixa a imagem bem pequena, cerca de 1/3 da largura central
        st.image("igreja.png", width=200) 
    except:
        st.write("⛪ [Logo da Igreja]")

# Faixa Azul com informações dos Pastores
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
# MENU LATERAL E FUNÇÕES
# =====================================
st.sidebar.title("Navegação")
opcao = st.sidebar.radio("Selecione uma função:", 
                         ["Fazer Chamada", "Cadastrar Alunos", "Gerenciar Classes", "Relatórios e Prêmios"])

if opcao == "Gerenciar Classes":
    st.header("🏫 Gestão de Classes")
    nova_classe = st.text_input("Nome da nova classe")
    if st.button("Salvar Classe"):
        if nova_classe:
            try:
                cursor.execute("INSERT INTO classes (nome) VALUES (?)", (nova_classe.strip(),))
                conn.commit()
                st.success("Classe cadastrada!")
            except:
                st.error("Erro: Classe já existe.")

elif opcao == "Cadastrar Alunos":
    st.header("👥 Cadastro de Alunos")
    cursor.execute("SELECT nome FROM classes ORDER BY nome")
    lista_classes = [c[0] for c in cursor.fetchall()]
    
    if not lista_classes:
        st.warning("Cadastre uma classe primeiro!")
    else:
        aba_ind, aba_bloco = st.tabs(["Individual", "Em Bloco"])
        with aba_ind:
            nome_aluno = st.text_input("Nome do Aluno")
            classe_aluno = st.selectbox("Classe", lista_classes, key="ind")
            if st.button("Salvar Aluno"):
                cursor.execute("INSERT INTO alunos (nome, classe) VALUES (?, ?)", (nome_aluno.strip(), classe_aluno))
                conn.commit()
                st.success("Aluno cadastrado!")
        with aba_bloco:
            classe_bloco = st.selectbox("Classe", lista_classes, key="blc")
            texto_nomes = st.text_area("Cole os nomes abaixo (um por linha)")
            if st.button("Importar Lista"):
                nomes = texto_nomes.split('\n')
                for n in nomes:
                    if n.strip():
                        cursor.execute("INSERT INTO alunos (nome, classe) VALUES (?, ?)", (n.strip(), classe_bloco))
                conn.commit()
                st.success("Lista importada!")

elif opcao == "Fazer Chamada":
    st.header("📝 Chamada do Dia")
    cursor.execute("SELECT nome FROM classes ORDER BY nome")
    lista_classes = [c[0] for c in cursor.fetchall()]
    classe_chamada = st.selectbox("Escolha a Classe", lista_classes)
    data_chamada = st.date_input("Data da Aula", datetime.now())
    data_str = data_chamada.strftime("%d/%m/%Y")

    if classe_chamada:
        cursor.execute("SELECT id, nome FROM alunos WHERE classe = ? ORDER BY nome", (classe_chamada,))
        alunos = cursor.fetchall()
        for id_aluno, nome in alunos:
            c1, c2 = st.columns([3, 1])
            c1.write(nome)
            if c2.button("Presença ✅", key=f"btn_{id_aluno}"):
                cursor.execute("INSERT INTO presencas (aluno_id, data_chamada, presente) VALUES (?, ?, ?)", 
                               (id_aluno, data_str, 1))
                conn.commit()
                st.toast(f"Ok: {nome}")

elif opcao == "Relatórios e Prêmios":
    st.header("🏆 Ranking e Resultados")
    data_rank = st.date_input("Data para Ranking", datetime.now())
    if st.button("Ver Ganhador do Dia"):
        cursor.execute("SELECT nome FROM classes")
        classes = [c[0] for c in cursor.fetchall()]
        res = []
        for cl in classes:
            cursor.execute("SELECT id FROM alunos WHERE classe = ?", (cl,))
            total = len(cursor.fetchall())
            if total > 0:
                cursor.execute("SELECT SUM(presente) FROM presencas JOIN alunos ON presencas.aluno_id = alunos.id WHERE alunos.classe = ? AND data_chamada = ?", (cl, data_rank.strftime("%d/%m/%Y")))
                pres = cursor.fetchone()[0] or 0
                res.append({"Classe": cl, "%": round((pres/total)*100, 1)})
        if res:
            df = pd.DataFrame(res).sort_values(by="%", ascending=False)
            st.table(df)
            st.balloons()
            st.success(f"Ganhadora: {df.iloc[0]['Classe']}")

st.sidebar.markdown("---")
st.sidebar.info(f"**Dev:** Evaldo Sérgio\n\n**Regional:** Cachoeira do Vale")