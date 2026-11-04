"""학습 플래너 화면."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from planner import make_plan, compare_plans


st.set_page_config(
    page_title="배움의 궤도 | 주간 학습 플래너",
    page_icon="📘",
    layout="wide",
)

st.markdown("""
<style>
.stApp {background: #f5f7fc;}
.block-container {max-width: 1200px; padding-top: 2rem;}
h1, h2, h3 {color: #172b4d;}
[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #e0e6f0;
}
</style>
""", unsafe_allow_html=True)

DAYS = ["월", "화", "수", "목", "금", "토", "일"]

today = datetime.now(ZoneInfo("Asia/Seoul")).date()
default_start = today + timedelta(days=(7 - today.weekday()) % 7)


def example_tasks(start):
    """처음 표시할 가상 학습 데이터."""
    return pd.DataFrame([
        {
            "학습 항목": "자료구조 중간 복습",
            "필요 시간": 8.0,
            "중요도": 5,
            "마감일": start + timedelta(days=4),
            "장기 목표 관련": True,
        },
        {
            "학습 항목": "영어 독해 연습",
            "필요 시간": 12.0,
            "중요도": 3,
            "마감일": start + timedelta(days=27),
            "장기 목표 관련": True,
        },
        {
            "학습 항목": "자바 과제",
            "필요 시간": 5.0,
            "중요도": 4,
            "마감일": start + timedelta(days=3),
            "장기 목표 관련": False,
        },
        {
            "학습 항목": "운영체제 예습",
            "필요 시간": 6.0,
            "중요도": 2,
            "마감일": start + timedelta(days=13),
            "장기 목표 관련": True,
        },
    ])


def read_tasks(frame):
    """입력 표를 계획 계산에 사용할 목록으로 변환."""
    if frame.empty or frame.isna().any().any():
        raise ValueError("빈 칸 없이 학습 항목을 한 개 이상 입력해 주세요.")

    return [
        {
            "name": str(r["학습 항목"]).strip(),
            "hours": float(r["필요 시간"]),
            "importance": int(r["중요도"]),
            "deadline": pd.Timestamp(r["마감일"]).date(),
            "related": bool(r["장기 목표 관련"]),
        }
        for _, r in frame.iterrows()
    ]
def capacity_inputs(prefix, defaults, start):
    columns = st.columns(7)
    return [col.number_input(f'{DAYS[(start.weekday()+i)%7]} {start + timedelta(days=i):%m/%d}',
                            min_value=0.0, max_value=24.0, value=float(defaults[i]), step=0.5,
                            key=f'{prefix}_{i}') for i, col in enumerate(columns)]


def show_plan(plan):
    total = sum(t['allocated'] for t in plan['summary'])
    deferred = sum(t['deferred'] for t in plan['summary'])
    a, b, c = st.columns(3)
    a.metric('주간 가능 시간', f'{sum(plan["capacities"]):g}시간')
    b.metric('배정된 학습', f'{total:g}시간')
    c.metric('미배정 · 다음 주 재검토', f'{deferred:g}시간')
    rows = []
    for i in range(7):
        day = plan['start'] + timedelta(days=i)
        entries = [s for s in plan['schedule'] if s['date'] == day]
        rows.append({'날짜': f'{day:%m/%d} ({DAYS[day.weekday()]})', '가능(시간)': plan['capacities'][i],
                     '배정(시간)': sum(s['hours'] for s in entries),
                     '학습 계획': ' / '.join(f'{s["name"]} {s["hours"]:g}시간' for s in entries) or '휴식 / 배정 없음'})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch')
    st.markdown('#### 학습량과 이월 현황')
    st.dataframe(pd.DataFrame([{'학습 항목': t['name'], '중요도': t['importance'],
        '유효 마감일': t['due'], '전체 필요(시간)': t['hours'], '이번 주 목표(시간)': t['need'],
        '배정(시간)': t['allocated'], '다음 주 재검토(시간)': t['deferred'],
        '장기 분산 잔량(시간)': t['future']} for t in plan['summary']]), hide_index=True, width='stretch')
    st.caption('다음 주 재검토 = 이번 주 목표 중 배정하지 못한 양. 장기 분산 잔량 = 처음부터 이후 주에 나누어 공부할 양. 다음 주 배정을 보장하지 않습니다.')
    overdue = [t['name'] for t in plan['summary'] if t['deferred'] and t['due'] <= plan['start'] + timedelta(days=6)]
    if overdue:
        st.warning('이번 주 마감 위험: ' + ', '.join(overdue) + ' — 마감 전 가능 시간을 늘리거나 학습 범위를 조정하세요. 마감 이후에는 배정하지 않습니다.')


st.caption('DSU AI CHALLENGE · 학습 계획 MVP')
st.title('📘 배움의 궤도')
st.write('장기 목표는 꾸준하게, 이번 주 계획은 유연하게.')
st.info('규칙 기반 재계획 모드 · AI API 미연동. 설명은 실제 배정 결과와 우선순위 규칙으로 생성합니다.')
page = st.radio('시연 화면 선택', ['1. 목표·일정 입력', '2. 초기 학습 계획', '3. 학습 일정 변경', '4. 수정 계획·변경 이유'], horizontal=True)

if page.startswith('1.'):
    st.header('01  학습 목표 및 일정 입력')
    st.caption('가상 예시입니다. 입력값을 바꾼 뒤 계획 생성 버튼을 누르세요. 새로 생성하면 이전 비교 기록을 대체합니다.')
    goal = st.text_input('장기 학습 목표', value='전공 기초를 다지고 영어 독해 습관 만들기', key='goal_input')
    left, right = st.columns(2)
    start = left.date_input('계획 시작일 (7일간)', value=default_start, key='start_input')
    target = right.date_input('목표 날짜', value=default_start + timedelta(days=27), key='target_input')
    st.subheader('학습 항목')
    st.caption('필요 시간은 해당 항목의 전체 남은 학습량입니다. 중요도는 1(낮음)~5(높음)입니다. 표 아래 빈 행으로 항목을 추가할 수 있습니다.')
    edited = st.data_editor(example_tasks(start), num_rows='dynamic', hide_index=True, width='stretch', key='task_editor',
        column_config={'필요 시간': st.column_config.NumberColumn(min_value=0.5, max_value=10000.0, step=0.5, required=True),
                       '중요도': st.column_config.NumberColumn(min_value=1, max_value=5, step=1, required=True),
                       '마감일': st.column_config.DateColumn(required=True),
                       '학습 항목': st.column_config.TextColumn(required=True),
                       '장기 목표 관련': st.column_config.CheckboxColumn(default=False)})
    st.subheader('하루 학습 가능 시간')
    capacities = capacity_inputs('initial', [2, 2, 2, 2, 2, 3, 1], start)
    if st.button('주간 학습 계획 생성', type='primary'):
        try:
            if not goal.strip():
                raise ValueError('장기 학습 목표를 입력해 주세요.')
            tasks = read_tasks(edited)
            plan = make_plan(tasks, capacities, start, target)
            st.session_state.baseline = plan
            st.session_state.revised = plan
            st.session_state.tasks = tasks
            st.session_state.saved_goal = goal
            st.session_state.events = []
            for i in range(7):
                st.session_state.pop(f'changed_{i}', None)
            st.success('계획이 생성되었습니다. 2번 화면에서 초기 계획을 확인하세요.')
        except (ValueError, TypeError, OverflowError) as e:
            st.error(str(e))
else:
    if 'baseline' not in st.session_state:
        st.warning('먼저 1번 화면에서 주간 학습 계획을 생성해 주세요.')
        st.stop()
    base = st.session_state.baseline
    st.caption(f'장기 목표: {st.session_state.saved_goal} · 목표 날짜: {base["target"]:%Y-%m-%d}')
    if page.startswith('2.'):
        st.header('02  초기 학습 계획')
        show_plan(base)
        st.caption('초기 계획은 비교 기준으로 보관됩니다. 3번 화면에서 조건을 변경해도 이 화면은 유지됩니다.')
    elif page.startswith('3.'):
        st.header('03  학습 일정 변경')
        st.write('가능 시간을 바꾸면 즉시 재계획됩니다. 예: 아르바이트로 월요일 2시간 → 0시간.')
        capacities = capacity_inputs('changed', st.session_state.revised['capacities'], base['start'])
        st.subheader('새 학습 일정 추가')
        with st.form('new_task', clear_on_submit=True):
            name = st.text_input('새 학습 항목')
            c1, c2, c3 = st.columns(3)
            hours = c1.number_input('필요 시간', min_value=0.5, max_value=10000.0, value=3.0, step=0.5)
            importance = c2.number_input('중요도', min_value=1, max_value=5, value=5)
            deadline = c3.date_input('마감일', value=base['start'] + timedelta(days=2))
            related = st.checkbox('장기 목표 관련')
            submitted = st.form_submit_button('새 일정 추가 및 자동 재계획', type='primary')
        if submitted:
            if name.strip():
                st.session_state.tasks.append(dict(name=name.strip(), hours=hours, importance=importance, deadline=deadline, related=related))
                st.session_state.events.append(f'{name.strip()} · {hours:g}시간 · 중요도 {importance} · 마감 {deadline}')
                st.success('새 일정을 추가하고 재계획했습니다.')
            else:
                st.error('새 학습 항목 이름을 입력해 주세요.')
        st.session_state.revised = make_plan(st.session_state.tasks, capacities, base['start'], base['target'])
        if st.session_state.events:
            st.write('추가한 일정')
            for event in st.session_state.events:
                st.write('• ' + event)
        st.caption('변경 내용은 자동 반영됩니다. 4번 화면에서 기존 계획과 비교하세요.')
        show_plan(st.session_state.revised)
    else:
        st.header('04  수정된 학습 계획 및 변경 이유')
        revised = st.session_state.revised
        if revised == base:
            st.info('아직 변경된 조건이 없습니다. 3번 화면에서 가능 시간 또는 새 일정을 변경하세요.')
        rows, reasons = compare_plans(base, revised)
        st.subheader('기존 계획과 수정 계획 비교')
        st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch')
        st.subheader('계획이 바뀐 이유 · 규칙 기반 분석')
        for reason in reasons:
            st.write('• ' + reason)
        st.write('• 장기 목표 관련 항목은 학습 마감과 목표 날짜 중 빠른 날짜를 기준으로 남은 주 수에 나눠 이번 주 목표량을 계산합니다. 목표 문장 자체를 AI가 해석하지 않으며, 관련 여부는 입력한 체크값을 사용합니다.')
        st.write('• 각 날짜의 남은 가능 시간 안에서만 30분 단위로 배정합니다. 마감 전 시간이 부족하면 다음 주 재검토 대상으로 표시합니다.')
        show_plan(revised)
st.caption('데이터는 현재 브라우저 세션에만 유지됩니다. 새로고침·세션 종료 시 초기화될 수 있습니다. 학습 완료량 추적 기능은 포함하지 않습니다.')
