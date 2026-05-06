import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
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
