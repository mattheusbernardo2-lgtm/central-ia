import streamlit as st
import requests
from bs4 import BeautifulSoup
import io

st.set_page_config(page_title="Central de Resolução", page_icon="⚡", layout="wide")
st.title("⚡ Central de Resolução Autônoma")
st.caption("Conexão Gemini + Claude com suporte a arquivos, links de projetos e pesquisa web em tempo real.")

# Barra lateral para chaves e configurações
with st.sidebar:
    st.header("🔑 Credenciais")
    st.markdown("Insira suas chaves de API:")
    gemini_key = st.text_input("Chave Gemini (Google AI Studio):", type="password")
    claude_key = st.text_input("Chave Claude (Anthropic Console):", type="password")
    
    st.markdown("---")
    st.header("⚙️ Recursos Adicionais")
    ativar_busca_web = st.checkbox("🌐 Ativar Pesquisa no Google (Gemini)", value=True, help="Permite que o Gemini pesquise dados atuais, projetos e referências na internet.")
    modo = st.radio("Modo de Operação:", ["Dupla Validação (Gemini + Claude)", "Apenas Gemini (Rápido)"])

# Layout em colunas para os dados de entrada
col_problema, col_anexos = st.columns([1.2, 0.8])

with col_problema:
    problema = st.text_area(
        "1. Descreva o problema, desafio ou meta financeira:",
        height=220,
        placeholder="Exemplo: Preciso de uma estratégia para reequilibrar meu fluxo de caixa deste mês, contingenciar despesas e alavancar a receita das minhas marcas..."
    )

with col_anexos:
    st.markdown("**2. Contexto Externo (Dossiês, Projetos e Links)**")
    arquivos_anexados = st.file_uploader(
        "Anexe arquivos de contexto (Dossiê, Notas, CSV, TXT, MD, PDF):",
        type=["txt", "md", "csv", "pdf"],
        accept_multiple_files=True
    )
    urls_digitadas = st.text_area(
        "Links de referência ou projetos da internet (um por linha):",
        height=85,
        placeholder="https://exemplo.com/projeto\nhttps://meusite.com/dados"
    )

botao_executar = st.button("🚀 Iniciar Resolução Autônoma", type="primary", use_container_width=True)

# Função auxiliar para extrair texto de links
def extrair_texto_de_url(url):
    try:
        url_limpa = url.strip()
        if not url_limpa.startswith(('http://', 'https://')):
            url_limpa = 'https://' + url_limpa
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(url_limpa, headers=headers, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            linhas = [linha.strip() for linha in soup.get_text().splitlines() if linha.strip()]
            conteudo = ' '.join(linhas)
            return conteudo[:4000] # Limite de segurança de caracteres
        return f"[Falha ao acessar status {resp.status_code}]"
    except Exception as e:
        return f"[Erro ao ler link: {e}]"

# Função auxiliar para ler arquivos enviados
def extrair_texto_arquivos(lista_arquivos):
    texto_total = ""
    for arq in lista_arquivos:
        nome = arq.name
        extensao = nome.split('.')[-1].lower()
        texto_total += f"\n\n--- INÍCIO DO ARQUIVO: {nome} ---\n"
        try:
            if extensao in ['txt', 'md', 'csv']:
                texto_total += arq.read().decode('utf-8', errors='ignore')
            elif extensao == 'pdf':
                from pypdf import PdfReader
                leitor_pdf = PdfReader(io.BytesIO(arq.read()))
                for num_pag, pagina in enumerate(leitor_pdf.pages):
                    texto_total += f"\n[Página {num_pag + 1}]\n" + (pagina.extract_text() or "")
        except Exception as e:
            texto_total += f"[Erro ao ler o arquivo {nome}: {e}]"
        texto_total += f"\n--- FIM DO ARQUIVO: {nome} ---\n"
    return texto_total

if botao_executar:
    if not problema.strip() and not arquivos_anexados and not urls_digitadas.strip():
        st.warning("Por favor, forneça pelo menos a descrição do problema, um arquivo ou um link de referência.")
        st.stop()
        
    if not gemini_key:
        st.error("A chave do Gemini é necessária para iniciar a resolução.")
        st.stop()
        
    status = st.status("Processando dados e ativando ecossistema de IA...", expanded=True)
    
    # Compilar Contexto Geral
    contexto_adicional = ""
    
    if arquivos_anexados:
        status.write("📄 Lendo arquivos anexados...")
        contexto_adicional += extrair_texto_arquivos(arquivos_anexados)
        
    if urls_digitadas.strip():
        status.write("🌐 Acessando e extraindo dados dos links fornecidos...")
        contexto_adicional += "\n\n--- CONTEÚDO EXTRAÍDO DE LINKS DA INTERNET ---\n"
        urls = [u.strip() for u in urls_digitadas.splitlines() if u.strip()]
        for u in urls:
            status.write(f"Conectando a: {u}")
            texto_url = extrair_texto_de_url(u)
            contexto_adicional += f"\n[URL: {u}]\n{texto_url}\n"
        contexto_adicional += "--- FIM DOS LINKS ---\n"

    # 1. Proposta inicial com Gemini
    status.write("🤖 1. Gemini estruturando proposta com pesquisa técnica...")
    try:
        from google import genai
        from google.genai import types
        client_gemini = genai.Client(api_key=gemini_key)
        
        prompt_gemini_1 = f"""Você é o Engenheiro Propositor e Arquiteto Estratégico.
Analise a demanda e o contexto técnico/financeiro fornecido (incluindo arquivos, links e benchmarks).

DEMANDA PRINCIPAL:
{problema}

DADOS ADICIONAIS, DOSSIÊS E REFERÊNCIAS:
{contexto_adicional if contexto_adicional else 'Nenhum arquivo/link adicional anexado.'}

Diretrizes:
- Entregue um plano de ação em etapas claras e práticas (ações imediatas de 48h e plano de 15 a 30 dias).
- Inclua projeções numéricas, tabelas de contingência ou fórmulas de cálculo se envolver custos/finanças.
- Seja realista, eliminando ideias genéricas."""

        # Configura ferramenta de busca se selecionada
        config_chamada = None
        if ativar_busca_web:
            config_chamada = types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )

        resposta_gemini = client_gemini.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt_gemini_1,
            config=config_chamada
        ).text
    except Exception as e:
        status.update(label="Erro na conexão com Gemini", state="error")
        st.error(f"Erro no Gemini: {e}")
        st.stop()
        
    with st.expander("📄 Ver Proposta Inicial e Análise de Mercado (Gemini)", expanded=False):
        st.markdown(resposta_gemini)
        
    # 2. Auditoria Crítica com Claude
    if modo == "Dupla Validação (Gemini + Claude)":
        if not claude_key:
            status.write("⚠️ Chave do Claude não informada. Concluindo apenas com a proposta do Gemini...")
            solucao_final = resposta_gemini
            status.update(label="Finalizado apenas com Gemini (Sem chave Claude)", state="complete")
        else:
            status.write("🧐 2. Claude auditando rigorosamente a proposta, buscando furos e riscos...")
            try:
                from anthropic import Anthropic
                client_claude = Anthropic(api_key=claude_key)
                
                prompt_claude = f"""Você é o Auditor Crítico Financeiro e Operacional.
Audite com rigor a proposta apresentada para a demanda original e o contexto fornecido.

DEMANDA ORIGINAL:
{problema}

CONTEXTO/DOSSIÊ ANEXADO:
{contexto_adicional if contexto_adicional else 'Sem anexos adicionais.'}

PROPOSTA APRESENTADA PELO GEMINI:
{resposta_gemini}

Instruções:
- Identifique furos lógicos, premissas financeiras otimistas demais, custos ocultos ou gargalos de execução.
- Dê a diretriz exata de correção para cada risco encontrado.
- Se o plano estiver perfeito e sem ressalvas, responda apenas: STATUS_OK"""
                
                resposta_claude = client_claude.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2500,
                    messages=[{"role": "user", "content": prompt_claude}]
                ).content[0].text
                
                with st.expander("🔍 Ver Auditoria Crítica (Claude)", expanded=False):
                    st.markdown(resposta_claude)
                    
                # 3. Refatoração Final
                if "STATUS_OK" in resposta_claude:
                    status.update(label="Solução aprovada sem ressalvas pelo Auditor!", state="complete")
                    solucao_final = resposta_gemini
                else:
                    status.write("🛠️ 3. Gemini ajustando a solução final com base nos apontamentos do Claude...")
                    prompt_refinamento = f"""Demanda original: {problema}
Sua proposta inicial: {resposta_gemini}
Auditoria rigorosa do Claude: {resposta_claude}

Reescreva a solução final corrigindo rigorosamente todos os pontos levantados pelo Auditor Claude. Entregue um roteiro consolidado e executável."""
                    solucao_final = client_gemini.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=prompt_refinamento
                    ).text
                    status.update(label="Resolução completa finalizada com sucesso!", state="complete")
            except Exception as e:
                status.write(f"⚠️ Claude indisponível ({e}). Mantendo proposta do Gemini...")
                solucao_final = resposta_gemini
                status.update(label="Finalizado com proposta do Gemini (Claude offline)", state="complete")
    else:
        solucao_final = resposta_gemini
        status.update(label="Resolução rápida com Gemini concluída!", state="complete")
        
    st.markdown("---")
    st.subheader("🎯 Resolução Consolidada e Blindada")
    st.markdown(solucao_final)
