import streamlit as st
from pptx import Presentation
import io
import pdfplumber
import google.generativeai as genai
import os
from PIL import Image
import requests
import datetime




# Configuração inicial
st.set_page_config(
    layout="wide",
    page_title="Agente Hospital Sírio Libanês",
    page_icon="assets/page-icon.png"
)
st.image('assets/macLogo.png', width=300)

st.header('Agente Hospital Sírio Libanês')
st.header(' ')




gemini_api_key = os.getenv("GEM_API_KEY")
genai.configure(api_key=gemini_api_key)
modelo_vision = genai.GenerativeModel("gemini-2.0-flash", generation_config={"temperature": 0.1})
modelo_texto = genai.GenerativeModel("gemini-1.5-flash")




# Carrega diretrizes
with open('data.txt', 'r') as file:
    conteudo = file.read()

tab_chatbot, tab_aprovacao, tab_geracao, tab_briefing, tab_resumo = st.tabs([
    "💬 Chatbot Hospital Sírio Libanês", 
    "✅ Aprovação de Conteúdo", 
    "✨ Geração de Conteúdo",
    "📋 Geração de Briefing Hospital Sírio Libanês",
    "📝 Resumo de Textos"
])


with tab_chatbot:  
    st.header("Chat Virtual Hospital Sírio Libanês")
    st.caption("Pergunte qualquer coisa sobre as diretrizes e informações da Hospital Sírio Libanês")
    
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
        Você é um assistente virtual especializado na Hospital Sírio Libanês
        Baseie todas as suas respostas nestas diretrizes oficiais da Hospital Sírio Libanês
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


with tab_aprovacao:
    st.header("Validação de Materiais")
    st.header(' ')
    subtab1, subtab2 = st.tabs(["🖼️ Análise de Imagens", "✍️ Revisão de Textos"])
    
    with subtab1:
        uploaded_image = st.file_uploader("Carregue imagem para análise (.jpg, .png)", type=["jpg", "jpeg", "png"], key="img_uploader")
        if uploaded_image:
            st.image(uploaded_image, use_column_width=True, caption="Pré-visualização")
            if st.button("Validar Imagem", key="analyze_img"):
                with st.spinner('Comparando com diretrizes da marca...'):
                    try:
                        image = Image.open(uploaded_image)
                        img_bytes = io.BytesIO()
                        image.save(img_bytes, format=image.format)
                        
                        resposta = modelo_vision.generate_content([
                            f"""Analise esta imagem considerando:
                            {conteudo}
                            Forneça um parecer técnico detalhado com:
                            - ✅ Acertos
                            - ❌ Desvios das diretrizes
                            - 🛠 Recomendações precisas
                            - Diga se a imagem é aprovada ou não""",
                            {"mime_type": "image/jpeg", "data": img_bytes.getvalue()}
                        ])
                        st.subheader("Resultado da Análise")
                        st.markdown(resposta.text)
                    except Exception as e:
                        st.error(f"Falha na análise: {str(e)}")

    with subtab2:
        texto_input = st.text_area("Insira o texto para validação:", height=200, key="text_input")
        if st.button("Validar Texto", key="validate_text"):
            with st.spinner('Verificando conformidade...'):
                resposta = modelo_texto.generate_content(
                    f"""Revise este texto conforme:
                    Diretrizes: {conteudo}
                    Texto: {texto_input}
                    
                    Formato requerido:
                    ### Texto Ajustado
                    [versão reformulada]
                    
                    ### Alterações Realizadas
                    - [lista itemizada de modificações]
                    ### Justificativas
                    [explicação técnica das mudanças]"""
                )
                st.subheader("Versão Validada")
                st.markdown(resposta.text)

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




with tab_briefing:
    st.header("Gerador de Briefing Hospital Sírio Libanês")
    st.caption("Crie briefings completos para diferentes áreas de atuação da Hospital Sírio Libanês")
    
    # Tipos de briefing disponíveis organizados por categoria
    tipos_briefing = {
        "Social": [
            "Post único",
            "Planejamento Mensal"
        ],
        "CRM": [
            "Planejamento de CRM",
            "Fluxo de Nutrição",
            "Email Marketing"
        ],
        "Mídias": [
            "Campanha de Mídia"
        ],
        "Tech": [
            "Manutenção de Site",
            "Construção de Site",
            "Landing Page"
        ],
        "Analytics": [
            "Dashboards"
        ],
        "Design": [
            "Social",
            "CRM",
            "Mídia",
            "KV/Identidade Visual"
        ],
        "Redação": [
            "Email Marketing",
            "Site",
            "Campanha de Mídias"
        ],
        "Planejamento": [
            "Relatórios",
            "Estratégico",
            "Concorrência"
        ]
    }

    # Layout em colunas
    col_config, col_preview = st.columns([1, 2])
    
    with col_config:
        # Seleção hierárquica do tipo de briefing
        categoria = st.selectbox("Categoria:", list(tipos_briefing.keys()))
        tipo_briefing = st.selectbox("Tipo de Briefing:", tipos_briefing[categoria])
        
        # Campos comuns a todos os briefings
        st.subheader("Informações Básicas")
        nome_projeto = st.text_input("Nome do Projeto:")
        responsavel = st.text_input("Responsável pelo Briefing:")
        data_entrega = st.date_input("Data de Entrega Prevista:")
        objetivo_geral = st.text_area("Objetivo Geral:")
        
        # Seção dinâmica baseada no tipo de briefing
        st.subheader("Informações Específicas")
        
        # ========== SOCIAL ==========
        if tipo_briefing == "Post único":
            fotos = st.text_area("Fotos necessárias:")
            texto = st.text_area("Texto do post:")
            expectativa = st.text_area("Expectativa de resultado:")
            tom_voz = st.selectbox("Tom de voz:", ["Institucional", "Inspiracional", "Educativo", "Promocional"])
            direcionamento_arte = st.text_area("Direcionamento para a arte (KV):")
            palavras_chave = st.text_area("Palavras/conceitos-chave:")
            do_donts = st.text_area("Do's and Don'ts:")
            referencias = st.text_area("Referências:")
            materiais_extras = st.text_area("Materiais extras:")
            info_sensiveis = st.text_area("Informações sensíveis:")
            if st.checkbox("É sobre produtos?"):
                produtos_destaque = st.text_area("Produtos para destacar:")
        
        elif tipo_briefing == "Planejamento Mensal":
            eventos_mes = st.text_area("Eventos do mês:")
            datas_comemorativas = st.text_area("Datas/comemorações:")
            expectativa_mensal = st.text_area("Expectativa de resultados:")
            planejamento_conteudos = st.text_area("Conteúdos planejados:")
            produtos_temas = st.text_area("Produtos/temas técnicos:")
            planejamento_anual = st.file_uploader("Planejamento anual aprovado:")
            manuais = st.text_area("Manuais de conteúdo disponíveis:")
        
        # ========== CRM ==========
        elif tipo_briefing == "Planejamento de CRM":
            escopo = st.text_area("Escopo contratado:")
            ferramenta_crm = st.text_input("Ferramenta de CRM utilizada:")
            maturidade = st.selectbox("Maturidade de CRM:", ["Iniciante", "Intermediário", "Avançado"])
            objetivo_crm = st.text_area("Objetivo com CRM:")
            canais = st.multiselect("Canais disponíveis:", ["Email", "SMS", "WhatsApp", "Mídia Paga"])
            perfil_empresa = st.radio("Perfil da empresa:", ["B2B", "B2C"])
            metas = st.text_area("Metas a serem alcançadas:")
            tamanho_base = st.text_input("Tamanho da base:")
            segmentacao = st.text_area("Segmentação/público-alvo:")
            tom_voz = st.text_area("Tom de voz:")
            fluxos = st.text_area("Fluxos/e-mails para trabalhar:")
            if st.checkbox("Geração de leads?"):
                sla = st.text_area("SLA entre marketing e vendas:")
        
        elif tipo_briefing == "Fluxo de Nutrição":
            gatilho = st.text_area("Gatilho de entrada:")
            asset_relacionado = st.text_area("Asset/evento relacionado:")
            etapa_funil = st.selectbox("Etapa do funil:", ["Topo", "Meio", "Fundo"])
            canais_fluxo = st.multiselect("Canais para o fluxo:", ["Email", "SMS", "WhatsApp", "Mídia Paga"])
            data_ativacao = st.date_input("Data de ativação esperada:")
            objetivo_fluxo = st.text_area("Objetivo do fluxo:")
            resultado_esperado = st.text_area("Resultado final esperado:")
        
        elif tipo_briefing == "Email Marketing":
            publico_email = st.text_area("Público e segmentação:")
            data_disparo = st.date_input("Data de disparo:")
            horario_preferencial = st.time_input("Horário preferencial:")
            objetivo_email = st.text_area("Objetivo:")
            resultado_esperado = st.text_area("Resultado final esperado:")
            psd_figma = st.file_uploader("Arquivo PSD/Figma do email:")
            google_doc = st.text_input("Link do Google Doc com conteúdo:")
            links_videos = st.text_area("Links de vídeos:")
            ctas = st.text_area("CTAs:")
        
        # ========== MÍDIAS ==========
        elif tipo_briefing == "Campanha de Mídia":
            periodo_acao = st.text_input("Período da ação:")
            orcamento = st.number_input("Orçamento (R$):", min_value=0)
            mecanismo_promocional = st.text_area("Mecanismo promocional:")
            praca_especifica = st.text_area("Praça específica:")
            responsavel_criativo = st.radio("Quem fará os criativos:", ["Macfor", "Cliente"])
            materiais = st.text_area("Materiais (copies e peças criativas):")
            objetivo_acao = st.text_area("Objetivo da ação:")
            meta = st.text_area("Meta:")
            plataformas = st.multiselect("Plataformas:", ["Facebook", "Instagram", "Google Ads", "LinkedIn"])
            segmentacao = st.text_area("Segmentação:")
            link_destino = st.text_input("Link de destino:")
        
        # ========== TECH ==========
        elif tipo_briefing == "Manutenção de Site":
            st.markdown("**Descreva a demanda usando 5W2H:**")
            what = st.text_area("O que precisa ser feito?")
            why = st.text_area("Por que é necessário?")
            where = st.text_area("Onde deve ser implementado?")
            when = st.text_area("Quando precisa estar pronto?")
            who = st.text_area("Quem será impactado?")
            how = st.text_area("Como deve funcionar?")
            how_much = st.text_area("Qual o esforço estimado?")
            descricao_alteracao = st.text_area("Descrição detalhada da alteração:")
            prints = st.file_uploader("Anexar prints (se aplicável):", accept_multiple_files=True)
            link_referencia = st.text_input("Link de referência:")
            if st.checkbox("É cliente novo?"):
                acessos = st.text_area("Acessos (servidor, CMS, etc.):")
        
        elif tipo_briefing == "Construção de Site":
            acessos = st.text_area("Acessos (servidor, nuvens, repositórios, CMS):")
            dominio = st.text_input("Domínio:")
            prototipo = st.file_uploader("Protótipo em Figma:")
            conteudos = st.text_area("Conteúdos (textos, banners, vídeos):")
            plataforma = st.selectbox("Plataforma:", ["WordPress", "React", "Vue.js", "Outra"])
            hierarquia = st.text_area("Hierarquia de páginas:")
            seo = st.checkbox("Incluir otimização SEO?")
            if seo:
                palavras_chave = st.text_area("Palavras-chave principais:")
        
        elif tipo_briefing == "Landing Page":
            objetivo_lp = st.text_area("Objetivo da LP:")
            plataforma = st.text_input("Plataforma de desenvolvimento:")
            integracao_site = st.radio("Precisa integrar com site existente?", ["Sim", "Não"])
            dados_coletar = st.text_area("Dados a serem coletados no formulário:")
            destino_dados = st.text_area("Onde os dados serão gravados:")
            kv_referencia = st.file_uploader("KV de referência:")
            conteudos_pagina = st.text_area("Conteúdos da página:")
            menu = st.text_area("Menu/barra de navegação:")
            header_footer = st.text_area("Header e Footer:")
            comunicar = st.text_area("O que deve ser comunicado:")
            nao_comunicar = st.text_area("O que não deve ser comunicado:")
            observacoes = st.text_area("Observações:")
        
        # ========== ANALYTICS ==========
        elif tipo_briefing == "Dashboards":
            st.markdown("**Acessos:**")
            google_access = st.checkbox("Solicitar acesso Google Analytics")
            meta_access = st.checkbox("Solicitar acesso Meta Ads")
            outros_acessos = st.text_area("Outros acessos necessários:")
            
            st.markdown("**Requisitos do Dashboard:**")
            okrs = st.text_area("OKRs e metas:")
            dados_necessarios = st.text_area("Dados que precisam ser exibidos:")
            tipos_graficos = st.multiselect("Tipos de gráficos preferidos:", 
                                         ["Barras", "Linhas", "Pizza", "Mapas", "Tabelas"])
            atualizacao = st.selectbox("Frequência de atualização:", 
                                    ["Tempo real", "Diária", "Semanal", "Mensal"])
        
        # ========== DESIGN ==========
        elif tipo_briefing == "Social":
            formato = st.selectbox("Formato:", ["Estático", "Motion"])
            kv = st.file_uploader("KV a ser seguido:")
            linha_criativa = st.text_area("Linha criativa:")
            usar_fotos = st.radio("Usar fotos?", ["Sim", "Não"])
            referencias = st.text_area("Referências:")
            identidade_visual = st.text_area("Elementos de identidade visual:")
            texto_arte = st.text_area("Texto da arte:")
        
        elif tipo_briefing == "CRM":
            st.info("Layouts simples são mais eficientes para CRM!")
            referencias = st.text_area("Referências visuais:")
            tipografia = st.text_input("Tipografia preferencial:")
            ferramenta_envio = st.text_input("Ferramenta de CRM que enviará a arte:")
            formato_arte = st.selectbox("Formato da arte:", ["Imagem", "HTML"])
        
        elif tipo_briefing == "Mídia":
            formato = st.selectbox("Formato:", ["Horizontal", "Vertical", "Quadrado"])
            tipo_peca = st.selectbox("Tipo de peça:", ["Arte estática", "Carrossel", "Motion"])
            direcionamento = st.text_area("Direcionamento de conteúdo:")
            num_pecas = st.number_input("Número de peças:", min_value=1)
            publico = st.text_area("Público-alvo:")
            objetivo = st.text_area("Objetivo:")
            referencias_concorrentes = st.text_area("Referências de concorrentes:")
        
        elif tipo_briefing == "KV/Identidade Visual":
            info_negocio = st.text_area("Informações do negócio:")
            referencias = st.text_area("Referências:")
            restricoes = st.text_area("O que não fazer (cores, elementos proibidos):")
            manual_anterior = st.file_uploader("Manual de marca anterior:")
            imagem_transmitir = st.text_area("Qual imagem queremos transmitir?")
            tema_campanha = st.text_area("Tema da campanha:")
            publico = st.text_area("Público-alvo:")
            tom_voz = st.text_area("Tom de voz:")
            banco_imagens = st.radio("Tipo de imagens:", ["Banco de imagens", "Pessoas reais"])
            limitacoes = st.text_area("Limitações de uso:")
        
        # ========== REDAÇÃO ==========
        elif tipo_briefing == "Email Marketing":
            objetivo_email = st.text_area("Objetivo:")
            produtos = st.text_area("Produtos a serem divulgados:")
            estrutura = st.text_area("Estrutura desejada:")
            cta = st.text_area("CTA desejado:")
            link_cta = st.text_input("Link para o CTA:")
            parte_campanha = st.radio("Faz parte de campanha maior?", ["Sim", "Não"])
        
        elif tipo_briefing == "Site":
            objetivo_site = st.text_area("Objetivo:")
            informacoes = st.text_area("Quais informações precisa ter:")
            links = st.text_area("Links necessários:")
            wireframe = st.file_uploader("Wireframe do site:")
            tamanho_texto = st.selectbox("Tamanho do texto:", ["Curto", "Médio", "Longo"])
            if st.checkbox("É site novo?"):
                insumos = st.text_area("Insumos sobre a empresa/projeto:")
        
        elif tipo_briefing == "Campanha de Mídias":
            objetivo_campanha = st.text_area("Objetivo:")
            plataformas = st.multiselect("Plataformas:", ["Facebook", "Instagram", "LinkedIn", "Google"])
            palavras_chave = st.text_area("Palavras-chave:")
            tom_voz = st.text_area("Tom de voz:")
            publico = st.text_area("Público-alvo:")
            cronograma = st.text_area("Cronograma:")
        
        # ========== PLANEJAMENTO ==========
        elif tipo_briefing == "Relatórios":
            objetivo_relatorio = st.text_area("Objetivo:")
            periodo_analise = st.text_area("Período de análise:")
            granularidade = st.selectbox("Granularidade:", ["Diária", "Semanal", "Mensal", "Trimestral"])
            metricas = st.text_area("Métricas a serem incluídas:")
            comparativos = st.text_area("Comparativos desejados:")
        
        elif tipo_briefing == "Estratégico":
            introducao = st.text_area("Introdução sobre a empresa:")
            orcamento = st.number_input("Orçamento (R$):", min_value=0)
            publico = st.text_area("Público-alvo:")
            objetivo_mkt = st.text_area("Objetivo de marketing:")
            etapas_funil = st.multiselect("Etapas do funil:", ["Topo", "Meio", "Fundo"])
            canais = st.multiselect("Canais disponíveis:", 
                                  ["Social", "Email", "Site", "Mídia Paga", "SEO"])
            produtos = st.text_area("Produtos/portfólio:")
            metas = st.text_area("Metas e métricas:")
            concorrentes = st.text_area("Concorrentes:")
            acessos = st.text_area("Acessos (GA, Meta Ads, etc.):")
            expectativas = st.text_area("Expectativas de resultados:")
            materiais = st.text_area("Materiais de apoio:")
        
        elif tipo_briefing == "Concorrência":
            orcamento = st.number_input("Orçamento (R$):", min_value=0)
            publico = st.text_area("Público-alvo:")
            objetivo = st.text_area("Objetivo:")
            etapas_funil = st.multiselect("Etapas do funil:", ["Topo", "Meio", "Fundo"])
            produtos = st.text_area("Produtos/portfólio:")
            metas = st.text_area("Metas e métricas:")
            concorrentes = st.text_area("Concorrentes:")
            acessos = st.text_area("Acessos (GA, Meta Ads, etc.):")
            expectativas = st.text_area("Expectativas de resultados:")
        
        # Botão para gerar o briefing
        if st.button("🔄 Gerar Briefing Completo", type="primary"):
            with st.spinner('Construindo briefing profissional...'):
                try:
                    # Construir o prompt com todas as informações coletadas
                    prompt_parts = [
                        f"# BRIEFING {tipo_briefing.upper()} - Hospital Sírio Libanês",
                        f"**Projeto:** {nome_projeto}",
                        f"**Responsável:** {responsavel}",
                        f"**Data de Entrega:** {data_entrega}",
                        "",
                        "## 1. INFORMAÇÕES BÁSICAS",
                        f"**Objetivo Geral:** {objetivo_geral}",
                        "",
                        "## 2. INFORMAÇÕES ESPECÍFICAS"
                    ]

                    # Adicionar campos específicos dinamicamente
                    if tipo_briefing == "Post único":
                        prompt_parts.extend([
                            f"### Post único",
                            f"**Fotos necessárias:** {fotos}",
                            f"**Texto do post:** {texto}",
                            f"**Expectativa de resultado:** {expectativa}",
                            f"**Tom de voz:** {tom_voz}",
                            f"**Direcionamento para arte:** {direcionamento_arte}",
                            f"**Palavras-chave:** {palavras_chave}",
                            f"**Do's and Don'ts:** {do_donts}",
                            f"**Referências:** {referencias}",
                            f"**Materiais extras:** {materiais_extras}",
                            f"**Informações sensíveis:** {info_sensiveis}",
                            f"**Produtos para destacar:** {produtos_destaque if 'produtos_destaque' in locals() else 'N/A'}"
                        ])
                    
                    elif tipo_briefing == "Planejamento de CRM":
                        prompt_parts.extend([
                            f"### Planejamento de CRM",
                            f"**Escopo contratado:** {escopo}",
                            f"**Ferramenta de CRM:** {ferramenta_crm}",
                            f"**Maturidade de CRM:** {maturidade}",
                            f"**Objetivo com CRM:** {objetivo_crm}",
                            f"**Canais disponíveis:** {', '.join(canais)}",
                            f"**Perfil da empresa:** {perfil_empresa}",
                            f"**Metas:** {metas}",
                            f"**Tamanho da base:** {tamanho_base}",
                            f"**Segmentação:** {segmentacao}",
                            f"**Tom de voz:** {tom_voz}",
                            f"**Fluxos/e-mails:** {fluxos}",
                            f"**SLA marketing/vendas:** {sla if 'sla' in locals() else 'N/A'}"
                        ])
                    
                    elif tipo_briefing == "Fluxo de Nutrição":
                        prompt_parts.extend([
                            f"### Fluxo de Nutrição",
                            f"**Gatilho de entrada:** {gatilho}",
                            f"**Asset/evento relacionado:** {asset_relacionado}",
                            f"**Etapa do funil:** {etapa_funil}",
                            f"**Canais:** {', '.join(canais_fluxo)}",
                            f"**Data de ativação:** {data_ativacao}",
                            f"**Objetivo:** {objetivo_fluxo}",
                            f"**Resultado esperado:** {resultado_esperado}"
                        ])

                    elif tipo_briefing == "Email Marketing":
                        prompt_parts.extend([
                            f"### Email Marketing",
                            f"**Público:** {publico_email}",
                            f"**Data/horário:** {data_disparo} {horario_preferencial}",
                            f"**Objetivo:** {objetivo_email}",
                            f"**Resultado esperado:** {resultado_esperado}",
                            f"**Arquivos:** {'PSD/Figma anexado' if psd_figma else 'Nenhum'}",
                            f"**Google Doc:** {google_doc}",
                            f"**Vídeos:** {links_videos}",
                            f"**CTAs:** {ctas}"
                        ])

                    elif tipo_briefing == "Campanha de Mídia":
                        prompt_parts.extend([
                            f"### Campanha de Mídia",
                            f"**Período:** {periodo_acao}",
                            f"**Orçamento:** R${orcamento}",
                            f"**Mecanismo promocional:** {mecanismo_promocional}",
                            f"**Praça específica:** {praca_especifica}",
                            f"**Responsável criativo:** {responsavel_criativo}",
                            f"**Materiais:** {materiais}",
                            f"**Objetivo:** {objetivo_acao}",
                            f"**Meta:** {meta}",
                            f"**Plataformas:** {', '.join(plataformas)}",
                            f"**Segmentação:** {segmentacao}",
                            f"**Link de destino:** {link_destino}"
                        ])

                    elif tipo_briefing == "Manutenção de Site":
                        prompt_parts.extend([
                            f"### Manutenção de Site (5W2H)",
                            f"**O que:** {what}",
                            f"**Por que:** {why}",
                            f"**Onde:** {where}",
                            f"**Quando:** {when}",
                            f"**Quem:** {who}",
                            f"**Como:** {how}",
                            f"**Quanto custa:** {how_much}",
                            f"**Descrição detalhada:** {descricao_alteracao}",
                            f"**Links/prints:** {link_referencia}",
                            f"**Acessos:** {acessos if 'acessos' in locals() else 'N/A'}"
                        ])

                    elif tipo_briefing == "Construção de Site":
                        prompt_parts.extend([
                            f"### Construção de Site",
                            f"**Acessos:** {acessos}",
                            f"**Domínio:** {dominio}",
                            f"**Protótipo:** {'Anexado' if prototipo else 'Não fornecido'}",
                            f"**Conteúdos:** {conteudos}",
                            f"**Plataforma:** {plataforma}",
                            f"**Hierarquia:** {hierarquia}",
                            f"**SEO:** {'Sim' + (f' - Palavras-chave: {palavras_chave}' if 'palavras_chave' in locals() else '') if seo else 'Não'}"
                        ])

                    elif tipo_briefing == "Landing Page":
                        prompt_parts.extend([
                            f"### Landing Page",
                            f"**Objetivo:** {objetivo_lp}",
                            f"**Plataforma:** {plataforma}",
                            f"**Integração com site:** {integracao_site}",
                            f"**Dados coletados:** {dados_coletar}",
                            f"**Destino dos dados:** {destino_dados}",
                            f"**KV referência:** {'Anexado' if kv_referencia else 'Não fornecido'}",
                            f"**Conteúdos:** {conteudos_pagina}",
                            f"**Menu:** {menu}",
                            f"**Header/Footer:** {header_footer}",
                            f"**Comunicação:** {comunicar}",
                            f"**Restrições:** {nao_comunicar}",
                            f"**Observações:** {observacoes}"
                        ])

                    elif tipo_briefing == "Dashboards":
                        prompt_parts.extend([
                            f"### Dashboards",
                            f"**Acessos solicitados:** {'Google Analytics' if google_access else ''} {'Meta Ads' if meta_access else ''} {outros_acessos}",
                            f"**OKRs/Metas:** {okrs}",
                            f"**Dados necessários:** {dados_necessarios}",
                            f"**Tipos de gráficos:** {', '.join(tipos_graficos)}",
                            f"**Atualização:** {atualizacao}"
                        ])

                    elif tipo_briefing == "Social (Design)":
                        prompt_parts.extend([
                            f"### Design para Social",
                            f"**Formato:** {formato}",
                            f"**KV referência:** {'Anexado' if kv else 'Não fornecido'}",
                            f"**Linha criativa:** {linha_criativa}",
                            f"**Fotos:** {usar_fotos}",
                            f"**Referências:** {referencias}",
                            f"**Identidade visual:** {identidade_visual}",
                            f"**Texto da arte:** {texto_arte}"
                        ])

                    elif tipo_briefing == "CRM (Design)":
                        prompt_parts.extend([
                            f"### Design para CRM",
                            f"**Referências visuais:** {referencias}",
                            f"**Tipografia:** {tipografia}",
                            f"**Ferramenta de envio:** {ferramenta_envio}",
                            f"**Formato da arte:** {formato_arte}"
                        ])

                    elif tipo_briefing == "Mídia (Design)":
                        prompt_parts.extend([
                            f"### Design para Mídia",
                            f"**Formato:** {formato}",
                            f"**Tipo de peça:** {tipo_peca}",
                            f"**Direcionamento:** {direcionamento}",
                            f"**Número de peças:** {num_pecas}",
                            f"**Público-alvo:** {publico}",
                            f"**Objetivo:** {objetivo}",
                            f"**Referências concorrentes:** {referencias_concorrentes}"
                        ])

                    elif tipo_briefing == "KV/Identidade Visual":
                        prompt_parts.extend([
                            f"### KV/Identidade Visual",
                            f"**Informações do negócio:** {info_negocio}",
                            f"**Referências:** {referencias}",
                            f"**Restrições:** {restricoes}",
                            f"**Manual anterior:** {'Anexado' if manual_anterior else 'Não fornecido'}",
                            f"**Imagem a transmitir:** {imagem_transmitir}",
                            f"**Tema da campanha:** {tema_campanha}",
                            f"**Público-alvo:** {publico}",
                            f"**Tom de voz:** {tom_voz}",
                            f"**Banco de imagens:** {banco_imagens}",
                            f"**Limitações:** {limitacoes}"
                        ])

                    elif tipo_briefing == "Email Marketing (Redação)":
                        prompt_parts.extend([
                            f"### Redação para Email Marketing",
                            f"**Objetivo:** {objetivo_email}",
                            f"**Produtos:** {produtos}",
                            f"**Estrutura:** {estrutura}",
                            f"**CTA:** {cta}",
                            f"**Link CTA:** {link_cta}",
                            f"**Parte de campanha:** {parte_campanha}"
                        ])

                    elif tipo_briefing == "Site (Redação)":
                        prompt_parts.extend([
                            f"### Redação para Site",
                            f"**Objetivo:** {objetivo_site}",
                            f"**Informações necessárias:** {informacoes}",
                            f"**Links:** {links}",
                            f"**Wireframe:** {'Anexado' if wireframe else 'Não fornecido'}",
                            f"**Tamanho do texto:** {tamanho_texto}",
                            f"**Insumos empresa:** {insumos if 'insumos' in locals() else 'N/A'}"
                        ])

                    elif tipo_briefing == "Campanha de Mídias (Redação)":
                        prompt_parts.extend([
                            f"### Redação para Campanha de Mídias",
                            f"**Objetivo:** {objetivo_campanha}",
                            f"**Plataformas:** {', '.join(plataformas)}",
                            f"**Palavras-chave:** {palavras_chave}",
                            f"**Tom de voz:** {tom_voz}",
                            f"**Público-alvo:** {publico}",
                            f"**Cronograma:** {cronograma}"
                        ])

                    elif tipo_briefing == "Relatórios":
                        prompt_parts.extend([
                            f"### Relatórios",
                            f"**Objetivo:** {objetivo_relatorio}",
                            f"**Período de análise:** {periodo_analise}",
                            f"**Granularidade:** {granularidade}",
                            f"**Métricas:** {metricas}",
                            f"**Comparativos:** {comparativos}"
                        ])

                    elif tipo_briefing == "Estratégico":
                        prompt_parts.extend([
                            f"### Planejamento Estratégico",
                            f"**Introdução:** {introducao}",
                            f"**Orçamento:** R${orcamento}",
                            f"**Público-alvo:** {publico}",
                            f"**Objetivo de marketing:** {objetivo_mkt}",
                            f"**Etapas do funil:** {', '.join(etapas_funil)}",
                            f"**Canais:** {', '.join(canais)}",
                            f"**Produtos/portfólio:** {produtos}",
                            f"**Metas:** {metas}",
                            f"**Concorrentes:** {concorrentes}",
                            f"**Acessos:** {acessos}",
                            f"**Expectativas:** {expectativas}",
                            f"**Materiais de apoio:** {materiais}"
                        ])

                    elif tipo_briefing == "Concorrência":
                        prompt_parts.extend([
                            f"### Briefing para Concorrência",
                            f"**Orçamento:** R${orcamento}",
                            f"**Público-alvo:** {publico}",
                            f"**Objetivo:** {objetivo}",
                            f"**Etapas do funil:** {', '.join(etapas_funil)}",
                            f"**Produtos/portfólio:** {produtos}",
                            f"**Metas:** {metas}",
                            f"**Concorrentes:** {concorrentes}",
                            f"**Acessos:** {acessos}",
                            f"**Expectativas:** {expectativas}"
                        ])
                    
                    prompt_parts.extend([
                        "",
                        "## 3. DIRETRIZES DA MARCA",
                        conteudo,
                        "",
                        
                    ])
                    
                    prompt = "\n".join(prompt_parts)
                    resposta = modelo_texto.generate_content(prompt)
                    
                    with col_preview:
                        st.subheader(f"Briefing {tipo_briefing} - {nome_projeto}")
                        st.markdown(resposta.text)
                        
                        st.download_button(
                            label="📥 Download do Briefing",
                            data=resposta.text,
                            file_name=f"briefing_{tipo_briefing.lower().replace(' ', '_')}_{nome_projeto.lower().replace(' ', '_')}.txt",
                            mime="text/plain"
                        )
                
                except Exception as e:
                    st.error(f"Erro ao gerar briefing: {str(e)}")

    with col_preview:
        st.subheader("Pré-visualização do Briefing")
        if 'resposta' in locals():
            st.markdown(resposta.text)
        else:
            st.info("Preencha os campos e clique em 'Gerar Briefing' para visualizar aqui")

# Estilização adicional
st.markdown("""
<style>
    div[data-testid="stTabs"] {
        margin-top: -30px;
    }
    .stDownloadButton button {
        background-color: #2e7d32 !important;
        color: white !important;
    }
    .stButton button {
        width: 100%;
    }
    [data-testid="stFileUploader"] {
        padding: 15px;
        border: 1px dashed #ccc;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

with tab_resumo:
    st.header("Resumo de Textos")
    st.caption("Resuma textos longos mantendo o alinhamento com as diretrizes da Hospital Sírio Libanês")
    
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
                        Crie um resumo profissional deste texto para a Hospital Sírio Libanês Cooperativa Agroindustrial,
                        seguindo rigorosamente estas diretrizes da marca:
                        {conteudo}
                        
                        Requisitos:
                        - {config_resumo}
                        - {"Inclua os principais pontos em tópicos" if incluir_pontos else "Formato de texto contínuo"}
                        - {"Mantenha a terminologia técnica específica" if manter_terminologia else "Simplifique a linguagem"}
                        - Priorize informações relevantes para o agronegócio
                        - Mantenha o tom profissional da Hospital Sírio Libanês
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
                            file_name="resumo_Hospital Sírio Libanês.txt",
                            mime="text/plain"
                        )
                        
                    except Exception as e:
                        st.error(f"Erro ao gerar resumo: {str(e)}")
