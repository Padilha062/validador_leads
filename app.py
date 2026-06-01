"""
app.py
======
Interface web moderna construída com Streamlit para o Validador de Leads.

Permite que o usuário informe o nome de um lead e cole uma lista de até 30
números de telefone. O sistema consulta a Evolution API de forma assíncrona,
aplica o algoritmo de fuzzy-matching e exibe o número vencedor com destaque.

Execute com:
    streamlit run app.py
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import List, Dict, Any

import httpx
import pandas as pd
import streamlit as st

from src.phone import parse_phone_list
from src.whatsapp_client import fetch_profile
from src.matcher import calculate_match_score


# ── Configuração da página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Validador de Leads · WhatsApp",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ── CSS customizado para visual moderno ─────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Import Google Font ─────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── Global ─────────────────────────────────────────────────────────── */
    *, html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* ── Header gradient ────────────────────────────────────────────────── */
    .main-header {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(48, 43, 99, 0.35);
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 800;
        margin: 0 0 0.4rem 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: rgba(255, 255, 255, 0.7);
        font-size: 1rem;
        margin: 0;
        font-weight: 400;
    }

    /* ── Cards ──────────────────────────────────────────────────────────── */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 14px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    .metric-card h3 {
        color: rgba(255,255,255,0.8);
        font-size: 0.85rem;
        margin: 0 0 0.3rem 0;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    .metric-card .value {
        color: #fff;
        font-size: 1.8rem;
        font-weight: 800;
    }

    /* ── Winner card ────────────────────────────────────────────────────── */
    .winner-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(17, 153, 142, 0.3);
        animation: pulse-glow 2s ease-in-out infinite;
    }
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 8px 32px rgba(17, 153, 142, 0.3); }
        50% { box-shadow: 0 8px 48px rgba(56, 239, 125, 0.5); }
    }
    .winner-card h2 {
        color: #fff;
        font-size: 1.4rem;
        margin: 0 0 0.8rem 0;
        font-weight: 700;
    }
    .winner-card .phone {
        color: #fff;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: 1px;
        text-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    .winner-card .score-badge {
        display: inline-block;
        background: rgba(255,255,255,0.25);
        color: #fff;
        padding: 0.35rem 1rem;
        border-radius: 50px;
        font-size: 0.9rem;
        font-weight: 600;
        margin-top: 0.8rem;
        backdrop-filter: blur(4px);
    }
    .winner-card .profile-name {
        color: rgba(255,255,255,0.9);
        font-size: 1rem;
        margin-top: 0.5rem;
        font-weight: 500;
    }

    /* ── Table styling ──────────────────────────────────────────────────── */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* ── Button override ────────────────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2.5rem;
        font-size: 1.05rem;
        font-weight: 700;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        width: 100%;
        letter-spacing: 0.3px;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6);
    }
    .stButton > button:active {
        transform: translateY(0);
    }

    /* ── Input styling ──────────────────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 10px !important;
        border: 2px solid rgba(102, 126, 234, 0.2) !important;
        transition: border-color 0.3s ease !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15) !important;
    }

    /* ── Footer ─────────────────────────────────────────────────────────── */
    .footer {
        text-align: center;
        padding: 2rem 0 1rem;
        color: rgba(120, 120, 140, 0.7);
        font-size: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Header ──────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="main-header">
        <h1>🔍 Validador de Leads · WhatsApp</h1>
        <p>Identifique o número pessoal de um lead entre até 30 candidatos</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Formulário de entrada ───────────────────────────────────────────────────
lead_name = st.text_input(
    "📋 Nome Completo do Lead",
    placeholder="Ex.: Carlos Eduardo da Silva",
    help="Informe o nome completo do lead para comparação com os perfis.",
)

raw_phones = st.text_area(
    "📱 Lista de Números (até 30)",
    placeholder="Cole os números aqui, um por linha ou separados por vírgula.\n\nEx.:\n(11) 98888-1111\n11 97777-2222\n+55 11 96666-3333",
    height=220,
    help="Aceita formatos variados: com DDD, DDI, parênteses, traços, etc.",
)


# ── Função principal (síncrona com threads) ─────────────────────────────────
def _process_phones(
    lead_name: str,
    phones: List[str],
    progress_bar: Any,
    status_text: Any,
) -> List[Dict[str, Any]]:
    total = len(phones)
    results: List[Dict[str, Any]] = [None] * total  # type: ignore[list-item]
    lock = threading.Lock()
    completed = [0]

    def _fetch_single(phone: str) -> Dict[str, Any]:
        profile = fetch_profile(phone, shared_client)
        score = calculate_match_score(lead_name, profile)
        with lock:
            completed[0] += 1
        return {"phone": phone, "profile": profile, "score": score}

    max_workers = min(10, total)
    with httpx.Client() as shared_client:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_fetch_single, phone): i
                for i, phone in enumerate(phones)
            }
            for future in as_completed(futures):
                idx = futures[future]
                results[idx] = future.result()
                progress_bar.progress(completed[0] / total)
                status_text.text(f"🔄 Consultado {completed[0]}/{total} números...")

    return results


# ── Botão de ação ───────────────────────────────────────────────────────────
st.markdown("")  # Espaçamento
clicked = st.button("🚀 Identificar Número Pessoal", use_container_width=True)

if clicked:
    # ── Validações ──────────────────────────────────────────────────────
    if not lead_name.strip():
        st.error("⚠️ Por favor, informe o **nome completo do lead**.")
        st.stop()

    if not raw_phones.strip():
        st.error("⚠️ Por favor, cole a **lista de números** para validação.")
        st.stop()

    phones = parse_phone_list(raw_phones)

    if not phones:
        st.error(
            "⚠️ Nenhum número válido foi encontrado na lista. "
            "Verifique o formato dos números."
        )
        st.stop()

    if len(phones) > 30:
        st.warning(
            f"⚠️ Foram encontrados {len(phones)} números. "
            "Apenas os primeiros 30 serão processados."
        )
        phones = phones[:30]

    # ── Execução assíncrona ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⏳ Processando...")

    progress_bar = st.progress(0)
    status_text = st.empty()

    results = _process_phones(lead_name, phones, progress_bar, status_text)

    status_text.text("✅ Consulta finalizada!")

    # ── Ordena por score (maior primeiro) ───────────────────────────────
    results.sort(key=lambda r: r["score"], reverse=True)
    winner = results[0]

    # ── Card do vencedor ────────────────────────────────────────────────
    winner_name = winner["profile"].get("name", "") or "—"
    winner_pic = winner["profile"].get("profilePictureUrl", "")

    st.markdown(
        f"""
        <div class="winner-card">
            <h2>🏆 Número Pessoal Identificado</h2>
            <div class="phone">{winner["phone"]}</div>
            <div class="profile-name">Perfil: {winner_name}</div>
            <div class="score-badge">Score: {winner["score"]:.1f} / 10.0</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if winner_pic and winner_pic.startswith("http"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(winner_pic, caption=f"Foto de perfil — {winner_name}", width=200)

    # ── Métricas resumo ─────────────────────────────────────────────────
    total_with_name = sum(
        1 for r in results if r["profile"].get("name", "").strip()
    )
    total_with_photo = sum(
        1 for r in results
        if str(r["profile"].get("profilePictureUrl", "")).startswith("http")
    )
    avg_score = sum(r["score"] for r in results) / len(results) if results else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <h3>Números Testados</h3>
                <div class="value">{len(results)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <h3>Com Nome no Perfil</h3>
                <div class="value">{total_with_name}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <h3>Score Médio</h3>
                <div class="value">{avg_score:.1f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Tabela detalhada ────────────────────────────────────────────────
    st.markdown("")
    st.markdown("### 📊 Resultado Detalhado")

    table_data = []
    for r in results:
        pic_url = str(r["profile"].get("profilePictureUrl", "")).strip()
        has_pic = "✅" if pic_url.startswith("http") else "❌"
        error = r["profile"].get("_error", "")

        table_data.append(
            {
                "📱 Número": r["phone"],
                "👤 Nome no WhatsApp": r["profile"].get("name", "") or "—",
                "📸 Foto": has_pic,
                "💬 Bio/Status": r["profile"].get("status", "") or "—",
                "⭐ Score": f"{r['score']:.1f}",
                "⚠️ Erro": error if error else "—",
            }
        )

    df = pd.DataFrame(table_data)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "⭐ Score": st.column_config.TextColumn(width="small"),
            "📸 Foto": st.column_config.TextColumn(width="small"),
        },
    )

    # ── Galeria de fotos de perfil (se houver) ──────────────────────────
    photos = [
        r for r in results
        if str(r["profile"].get("profilePictureUrl", "")).startswith("http")
    ]

    if photos:
        st.markdown("")
        st.markdown("### 🖼️ Fotos de Perfil Encontradas")
        cols = st.columns(min(len(photos), 5))
        for i, r in enumerate(photos):
            with cols[i % min(len(photos), 5)]:
                st.image(
                    r["profile"]["profilePictureUrl"],
                    caption=f"{r['profile'].get('name', '?')}\n{r['phone']}",
                    use_container_width=True,
                )

    st.success("✅ Análise completa! O número com maior pontuação está destacado acima.")


# ── Footer ──────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="footer">
        Desenvolvido com ❤️ usando Streamlit + Evolution API<br>
        Validador de Leads v1.0
    </div>
    """,
    unsafe_allow_html=True,
)
