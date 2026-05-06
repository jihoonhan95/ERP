import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
from modules.sales_manager import SalesManager

st.set_page_config(
    page_title="매출 관리 프로그램",
    page_icon="📊",
    layout="wide",
)

if "manager" not in st.session_state:
    st.session_state.manager = SalesManager()

manager: SalesManager = st.session_state.manager


def get_display_records():
    return st.session_state.get("view_records") or manager.get_all()


@st.dialog("매출 추가")
def add_dialog():
    d = st.text_input("날짜 (YYYY-MM-DD)", value=str(date.today()))
    cat = st.text_input("카테고리")
    item = st.text_input("품목명")
    qty = st.number_input("수량", min_value=1, value=1)
    price = st.number_input("단가 (원)", min_value=1, value=1000, step=100)

    if st.button("저장", type="primary", use_container_width=True):
        try:
            datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            st.error("날짜 형식이 잘못되었습니다. (YYYY-MM-DD)")
            return
        if not item.strip():
            st.error("품목명을 입력하세요.")
            return
        manager.add_sale(d, item.strip(), int(qty), int(price), cat.strip())
        st.session_state.pop("view_records", None)
        st.rerun()


@st.dialog("매출 수정")
def edit_dialog(record: dict):
    d = st.text_input("날짜 (YYYY-MM-DD)", value=record["date"])
    cat = st.text_input("카테고리", value=record.get("category", ""))
    item = st.text_input("품목명", value=record["item"])
    qty = st.number_input("수량", min_value=1, value=record["quantity"])
    price = st.number_input("단가 (원)", min_value=1, value=record["price"], step=100)

    if st.button("저장", type="primary", use_container_width=True):
        try:
            datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            st.error("날짜 형식이 잘못되었습니다. (YYYY-MM-DD)")
            return
        if not item.strip():
            st.error("품목명을 입력하세요.")
            return
        manager.update_sale(
            record["id"],
            date=d, item=item.strip(),
            quantity=int(qty), price=int(price),
            category=cat.strip(),
        )
        st.session_state.pop("view_records", None)
        st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 조회 조건")
    start = st.date_input("시작일", value=date(date.today().year, 1, 1))
    end = st.date_input("종료일", value=date.today())

    cat_options = ["(전체)"] + manager.get_categories()
    cat_sel = st.selectbox("카테고리", cat_options)

    col_s, col_a = st.columns(2)
    with col_s:
        if st.button("조회", use_container_width=True):
            recs = manager.filter_by_period(str(start), str(end))
            if cat_sel != "(전체)":
                recs = [r for r in recs if r.get("category") == cat_sel]
            st.session_state.view_records = recs
            st.rerun()
    with col_a:
        if st.button("전체보기", use_container_width=True):
            st.session_state.pop("view_records", None)
            st.rerun()

    st.divider()

    if st.button("➕ 매출 추가", type="primary", use_container_width=True):
        add_dialog()


# ── Main ──────────────────────────────────────────────────────────────────────
st.title("📊 매출 관리 프로그램")

records = get_display_records()

m1, m2, m3, m4 = st.columns(4)
s = manager.summary(records)
m1.metric("건수", f"{s['count']:,}건")
m2.metric("총 수량", f"{s['total_quantity']:,}")
m3.metric("총 매출", f"{s['total_revenue']:,}원")
m4.metric("평균", f"{s['average']:,}원")

st.divider()

tab_list, tab_chart = st.tabs(["📋 매출 목록", "📈 차트 분석"])

# ── 매출 목록 탭 ──────────────────────────────────────────────────────────────
with tab_list:
    if records:
        df = pd.DataFrame([{
            "날짜": r["date"],
            "카테고리": r.get("category", ""),
            "품목": r["item"],
            "수량": r["quantity"],
            "단가": r["price"],
            "합계": r["total"],
        } for r in records])

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "수량": st.column_config.NumberColumn("수량", format="%d"),
                "단가": st.column_config.NumberColumn("단가", format="%,d원"),
                "합계": st.column_config.NumberColumn("합계", format="%,d원"),
            },
        )

        st.markdown("##### 수정 / 삭제")
        options_map = {
            f"{r['date']}  |  {r.get('category') or '-'}  |  {r['item']}  |  {r['total']:,}원": r
            for r in records
        }
        selected_label = st.selectbox(
            "항목 선택",
            ["(선택 안 함)"] + list(options_map.keys()),
            label_visibility="collapsed",
        )

        if selected_label != "(선택 안 함)":
            selected_record = options_map[selected_label]
            col_e, col_d, _ = st.columns([1, 1, 6])
            with col_e:
                if st.button("✏️ 수정", use_container_width=True):
                    edit_dialog(selected_record)
            with col_d:
                if st.button("🗑️ 삭제", use_container_width=True):
                    manager.delete_sale(selected_record["id"])
                    st.session_state.pop("view_records", None)
                    st.rerun()
    else:
        st.info("데이터가 없습니다. 사이드바의 '➕ 매출 추가' 버튼으로 데이터를 입력하세요.")


# ── 차트 분석 탭 ──────────────────────────────────────────────────────────────
with tab_chart:
    if not records:
        st.info("데이터가 없습니다. 매출 데이터를 먼저 추가하세요.")
    else:
        df_all = pd.DataFrame(records)
        df_all["date"] = pd.to_datetime(df_all["date"])

        # 집계 단위 선택
        unit = st.radio("집계 단위", ["월별", "연도별", "일별"], horizontal=True)

        if unit == "월별":
            df_all["기간"] = df_all["date"].dt.to_period("M").astype(str)
        elif unit == "연도별":
            df_all["기간"] = df_all["date"].dt.year.astype(str) + "년"
        else:
            df_all["기간"] = df_all["date"].dt.strftime("%Y-%m-%d")

        period_df = (
            df_all.groupby("기간", sort=True)
            .agg(매출=("total", "sum"), 수량=("quantity", "sum"), 건수=("id", "count"))
            .reset_index()
        )

        # ── 매출 추이 라인 차트 ────────────────────────────────────────────────
        st.markdown("#### 매출 추이")
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=period_df["기간"],
            y=period_df["매출"],
            mode="lines+markers+text",
            text=[f"{v:,}원" for v in period_df["매출"]],
            textposition="top center",
            textfont=dict(size=12),
            line=dict(color="#1f77b4", width=2),
            marker=dict(size=8, color="#1f77b4"),
            name="매출",
        ))
        fig_line.update_layout(
            plot_bgcolor="white",
            yaxis=dict(
                tickformat=",",
                ticksuffix="원",
                gridcolor="#eeeeee",
                zeroline=False,
            ),
            xaxis=dict(showgrid=False),
            margin=dict(t=20, b=20),
            height=380,
        )
        st.plotly_chart(fig_line, use_container_width=True)

        # ── 카테고리별 / 품목별 바 차트 ──────────────────────────────────────
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### 카테고리별 매출")
            cat_df = (
                df_all[df_all["category"] != ""]
                .groupby("category")["total"].sum()
                .reset_index()
                .rename(columns={"category": "카테고리", "total": "매출"})
                .sort_values("매출", ascending=False)
            )
            if cat_df.empty:
                st.info("카테고리 데이터가 없습니다.")
            else:
                fig_cat = px.bar(
                    cat_df, x="카테고리", y="매출",
                    text=cat_df["매출"].apply(lambda v: f"{v:,}원"),
                    color="카테고리",
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                )
                fig_cat.update_traces(textposition="outside")
                fig_cat.update_layout(
                    plot_bgcolor="white",
                    yaxis=dict(tickformat=",", ticksuffix="원", gridcolor="#eeeeee"),
                    xaxis=dict(showgrid=False),
                    showlegend=False,
                    margin=dict(t=20, b=20),
                    height=320,
                )
                st.plotly_chart(fig_cat, use_container_width=True)

        with col_right:
            st.markdown("#### 품목별 매출 TOP 10")
            item_df = (
                df_all.groupby("item")["total"].sum()
                .reset_index()
                .rename(columns={"item": "품목", "total": "매출"})
                .sort_values("매출", ascending=False)
                .head(10)
            )
            fig_item = px.bar(
                item_df, x="매출", y="품목",
                orientation="h",
                text=item_df["매출"].apply(lambda v: f"{v:,}원"),
                color="매출",
                color_continuous_scale="Blues",
            )
            fig_item.update_traces(textposition="outside")
            fig_item.update_layout(
                plot_bgcolor="white",
                xaxis=dict(tickformat=",", ticksuffix="원", gridcolor="#eeeeee"),
                yaxis=dict(showgrid=False, autorange="reversed"),
                coloraxis_showscale=False,
                margin=dict(t=20, b=20),
                height=320,
            )
            st.plotly_chart(fig_item, use_container_width=True)
