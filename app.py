import streamlit as st

st.set_page_config(page_title="Central de Resolução", page_icon="⚡", layout="wide")
st.title("⚡ Central de Resolução Autônoma")
st.caption("Conexão direta entre Gemini e Claude para análise e solução crítica de problemas.")

# Barra lateral para chaves e configurações
with st.sidebar:
    st.header("🔑 Credenciais")
    st.markdown("Insira suas chaves de API. Elas não ficam salvas publicamente.")
    gemini_key = st.text_input("Chave Gemini (Google AI Studio):", type="password")
    claude_key = st.text_input("Chave Claude (Anthropic Console):", type="password")
    st.markdown("---")
    modo = st.radio("Modo de Operação:", ["Dupla Validação (Gemini + Claude)", "Apenas Gemini (Rápido)"])

# Campo principal para o seu problema
problema = st.text_area("Descreva o problema, projeto ou dúvida técnica:", height=180, placeholder="Exemplo: Preciso de uma estratégia para resolver o gargalo X mantendo o custo baixo...")

botao_executar = st.button("🚀 Iniciar Resolução Autônoma", type="primary")

if botao_executar:
    if not problema.strip():
        st.warning("Por favor, digite o seu problema antes de iniciar.")
        st.stop()
        
    if not gemini_key:
        st.error("A chave do Gemini é obrigatória para iniciar.")
        st.stop()
        
    status = st.status("Iniciando fluxo de trabalho...", expanded=True)
    
    # 1. Proposta inicial com Gemini
    status.write("🤖 1. Gemini analisando e elaborando proposta inicial...")
    try:
        from google import genai
        client_gemini = genai.Client(api_key=gemini_key)
        
        prompt_gemini_1 = f"Você é o Engenheiro Propositor. Apresente uma solução técnica, estruturada e direta para o seguinte caso:\n\n{problema}"
        resposta_gemini = client_gemini.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_gemini_1
        ).text
    except Exception as e:
        status.update(label="Erro na conexão com Gemini", state="error")
        st.error(f"Erro no Gemini: {e}")
        st.stop()
        
    with st.expander("📄 Ver Proposta Inicial (Gemini)", expanded=False):
        st.markdown(resposta_gemini)
        
    # 2. Auditoria com Claude (se selecionado e com chave presente)
    if modo == "Dupla Validação (Gemini + Claude)":
        if not claude_key:
            status.write("⚠️ Chave do Claude não informada. Concluindo apenas com a proposta do Gemini...")
            solucao_final = resposta_gemini
            status.update(label="Finalizado apenas com Gemini (Sem chave Claude)", state="complete")
        else:
            status.write("🧐 2. Claude auditando a proposta e buscando falhas/riscos...")
            try:
                from anthropic import Anthropic
                client_claude = Anthropic(api_key=claude_key)
                
                prompt_claude = f"""Você é o Auditor Crítico. Analise a solução abaixo para o problema original.
Problema: {problema}
Proposta apresentada: {resposta_gemini}

Aponte falhas lógicas, omissões, riscos práticos e dê a diretriz de correção. Se estiver impecável, responda apenas: STATUS_OK"""
                
                resposta_claude = client_claude.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt_claude}]
                ).content[0].text
                
                with st.expander("🔍 Ver Apontamentos Críticos (Claude)", expanded=False):
                    st.markdown(resposta_claude)
                    
                # 3. Refatoração no Gemini se o Claude apontar problemas
                if "STATUS_OK" in resposta_claude:
                    status.update(label="Solução aprovada de primeira pelo Auditor!", state="complete")
                    solucao_final = resposta_gemini
                else:
                    status.write("🛠️ 3. Gemini corrigindo as falhas apontadas pelo Claude...")
                    prompt_refinamento = f"""Problema original: {problema}
Sua proposta inicial: {resposta_gemini}
Críticas e correções do Auditor: {resposta_claude}

Reescreva a solução final corrigindo rigorosamente todos os pontos levantados pelo Auditor."""
                    solucao_final = client_gemini.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt_refinamento
                    ).text
                    status.update(label="Resolução finalizada com sucesso!", state="complete")
            except Exception as e:
                status.write(f"⚠️ Claude indisponível no momento ({e}). Mantendo proposta do Gemini...")
                solucao_final = resposta_gemini
                status.update(label="Finalizado com proposta do Gemini (Claude offline)", state="complete")
    else:
        solucao_final = resposta_gemini
        status.update(label="Resolução rápida com Gemini concluída!", state="complete")
        
    st.markdown("---")
    st.subheader("🎯 Resultado Consolidado")
    st.markdown(solucao_final)
