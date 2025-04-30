import streamlit as st
from pptx import Presentation
import io
import pdfplumber
import google.generativeai as genai
import os
from PIL import Image
import requests




# Configuração inicial
st.set_page_config(
    layout="wide",
    page_title="Agente HSL",
    page_icon="assets/page-icon.png"
)
st.image('assets/macLogo.png', width=300)

st.header('Agente HSL')
st.header(' ')




gemini_api_key = os.getenv("GEM_API_KEY")
genai.configure(api_key=gemini_api_key)
modelo_vision = genai.GenerativeModel("gemini-2.0-flash", generation_config={"temperature": 0.1})
modelo_texto = genai.GenerativeModel("gemini-1.5-flash")




# Carrega diretrizes
with open('data.txt', 'r') as file:
    conteudo = file.read()

tab_chatbot,  tab_geracao,  tab_resumo = st.tabs([
    "💬 Chatbot HSL", 
    "✨ Geração de Conteúdo",
    "📝 Resumo de Textos"
])


with tab_chatbot:  
    st.header("Chat Virtual HSL")
    st.caption("Pergunte qualquer coisa sobre as diretrizes e informações do HSL")
    
    # Inicializa o histórico de chat na session_state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Exibe o histórico de mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input do usuário
    if prompt := st.chat_input("Como posso ajudar?"):
        # Adiciona a mensagem do usuário ao histórico
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Prepara o contexto com as diretrizes
        contexto = f"""
        Você é um assistente virtual especializado no Hospital Sírio Libanês.
        Baseie todas as suas respostas nestas diretrizes oficiais da Hospital Sírio Libanês:
        {conteudo}


        
        Regras importantes:
        - Seja preciso e técnico
        - Mantenha o tom profissional mas amigável
        - Se a pergunta for irrelevante, oriente educadamente
        - Forneça exemplos quando útil
        """
        
        # Gera a resposta do modelo
        with st.chat_message("assistant"):
            with st.spinner('Pensando...'):
                try:
                    # Usa o histórico completo para contexto
                    historico_formatado = "\n".join(
                        [f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages]
                    )
                    
                    resposta = modelo_texto.generate_content(
                        f"{contexto}\n\nHistórico da conversa:\n{historico_formatado}\n\nResposta:"
                    )
                    
                    # Exibe a resposta
                    st.markdown(resposta.text)
                    
                    # Adiciona ao histórico
                    st.session_state.messages.append({"role": "assistant", "content": resposta.text})
                    
                except Exception as e:
                    st.error(f"Erro ao gerar resposta: {str(e)}")

# --- Estilização Adicional ---
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    [data-testid="stChatMessageContent"] {
        font-size: 1rem;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        padding: 0.5rem 1rem;
    }
    .stChatInput {
        bottom: 20px;
        position: fixed;
        width: calc(100% - 5rem);
    }
</style>
""", unsafe_allow_html=True)




with tab_geracao:
    st.header("Criação de Conteúdo")
    st.header(' ')
    campanha_brief = st.text_area("Briefing criativo:", help="Descreva objetivos, tom de voz e especificações", height=150)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Diretrizes Visuais")

        if st.button("Gerar Especificações", key="gen_visual"):
            with st.spinner('Criando guia de estilo...'):
                prompt = f"""
                Você é um designer que trabalha para a Macfor Marketing digital e você deve gerar conteúdo criativo para o cliente Hospital Sírio Libanês.

                Crie um manual técnico para designers baseado em:
                Brief: {campanha_brief}
                Diretrizes: {conteudo}

                
                Inclua:
                1. 🎨 Paleta de cores (códigos HEX/RGB)
                2. 🖼️ Diretrizes de fotografia
                3. ✏️ Tipografia hierárquica
                4. 📐 Grid e proporções
                5. ⚠️ Restrições de uso
                6. Descrição exata e palpável da imagem a ser utilizada no criativo que atenda a todas as guias acima
                """
                resposta = modelo_texto.generate_content(prompt)
                st.markdown(resposta.text)

    with col2:
        st.subheader("Copywriting")

        if st.button("Gerar Textos", key="gen_copy"):
            with st.spinner('Desenvolvendo conteúdo textual...'):
                prompt = f"""
                Crie textos para campanha considerando:
                Brief: {campanha_brief}
                Diretrizes: {conteudo}


                
                Entregar:
                - 🎯 3 opções de headline
                - 📝 Corpo de texto (200 caracteres)
                - 📢 2 variações de CTA
                - 🔍 Meta description (SEO)
                """
                resposta = modelo_texto.generate_content(prompt)
                st.markdown(resposta.text)

# --- Estilização ---
st.markdown("""
<style>
    div[data-testid="stTabs"] {
        margin-top: -30px;
    }
    div[data-testid="stVerticalBlock"] > div:has(>.stTextArea) {
        border-left: 3px solid #4CAF50;
        padding-left: 1rem;
    }
    button[kind="secondary"] {
        background: #f0f2f6 !important;
    }
</style>
""", unsafe_allow_html=True)





with tab_resumo:
    st.header("Resumo de Textos")
    st.caption("Resuma textos longos mantendo o alinhamento com as diretrizes do HSL")
    
    # Layout em colunas
    col_original, col_resumo = st.columns(2)
    
    with col_original:
        st.subheader("Texto Original")
        texto_original = st.text_area(
            "Cole o texto que deseja resumir:",
            height=400,
            placeholder="Insira aqui o texto completo que precisa ser resumido..."
        )
        
        # Configurações do resumo
        with st.expander("⚙️ Configurações do Resumo"):
            nivel_resumo = st.select_slider(
                "Nível de Resumo:",
                options=["Extenso", "Moderado", "Conciso"],
                value="Moderado"
            )
            
            incluir_pontos = st.checkbox(
                "Incluir pontos-chave em tópicos",
                value=True
            )
            
            manter_terminologia = st.checkbox(
                "Manter terminologia técnica",
                value=True
            )
    
    with col_resumo:
        st.subheader("Resumo Gerado")
        
        if st.button("Gerar Resumo", key="gerar_resumo"):
            if not texto_original.strip():
                st.warning("Por favor, insira um texto para resumir")
            else:
                with st.spinner("Processando resumo..."):
                    try:
                        # Configura o prompt de acordo com as opções selecionadas
                        config_resumo = {
                            "Extenso": "um resumo detalhado mantendo cerca de 50% do conteúdo original",
                            "Moderado": "um resumo conciso mantendo cerca de 30% do conteúdo original",
                            "Conciso": "um resumo muito breve com apenas os pontos essenciais (cerca de 10-15%)"
                        }[nivel_resumo]
                        
                        prompt = f"""
                        Crie um resumo profissional deste texto para O Hospital Sírio Libanês,
                        seguindo rigorosamente estas diretrizes da marca:
                        {conteudo}
                        
                        Requisitos:
                        - {config_resumo}
                        - {"Inclua os principais pontos em tópicos" if incluir_pontos else "Formato de texto contínuo"}
                        - {"Mantenha a terminologia técnica específica" if manter_terminologia else "Simplifique a linguagem"}
                        - Priorize informações relevantes para o agronegócio
                        - Mantenha o tom profissional do HSL
                        - Adapte para o público-alvo da cooperativa
                        
                        Texto para resumir:
                        {texto_original}
                        
                        Estrutura do resumo:
                        1. Título do resumo
                        2. {"Principais pontos em tópicos (se aplicável)" if incluir_pontos else "Resumo textual"}
                        3. Conclusão/Recomendações
                        """
                        
                        resposta = modelo_texto.generate_content(prompt)
                        
                        # Exibe o resultado
                        st.markdown(resposta.text)
                        
                        # Botão para copiar
                        st.download_button(
                            "📋 Copiar Resumo",
                            data=resposta.text,
                            file_name="resumo_hsl.txt",
                            mime="text/plain"
                        )
                        
                    except Exception as e:
                        st.error(f"Erro ao gerar resumo: {str(e)}")
