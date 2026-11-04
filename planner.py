"""화면에 의존하지 않는 30분 단위 주간 계획 계산."""
from datetime import date, timedelta
from math import ceil


def make_plan(tasks, capacities, start, target):
    """마감·중요도·목표 연관도로 정렬해 날짜별 가용 시간에 배정한다."""
    if len(capacities) != 7 or any(h < 0 or h > 24 or h * 2 != int(h * 2) for h in capacities):
        raise ValueError('요일별 가능 시간은 0~24시간, 0.5시간 단위로 입력해 주세요.')
    if target < start:
        raise ValueError('목표 날짜는 계획 시작일 이후여야 합니다.')
    ranked = []
    for i, task in enumerate(tasks):
        t = dict(task)
        if not str(t['name']).strip():
            raise ValueError('학습 항목 이름을 입력해 주세요.')
        if t['hours'] <= 0 or t['hours'] * 2 != int(t['hours'] * 2):
            raise ValueError('필요 시간은 0.5시간 이상의 0.5시간 단위여야 합니다.')
        if t['importance'] not in range(1, 6):
            raise ValueError('중요도는 1~5 사이여야 합니다.')
        due = min(t['deadline'], target) if t['related'] else t['deadline']
        days = (due - start).days
        # 장기 목표 관련 학습은 유효 마감일까지 남은 주 수로 나눈다.
        weeks = max(1, ceil((days + 1) / 7)) if t['related'] else 1
        need = min(t['hours'], ceil(t['hours'] * 2 / weeks) / 2)
        score = (100 if days < 7 else 30 if days < 14 else 0) + t['importance'] * 10 + (15 if t['related'] else 0)
        ranked.append(dict(t, id=i, due=due, need=need, score=score))
    slots = [int(h * 2) for h in capacities]
    schedule, summary = [], []
    for t in sorted(ranked, key=lambda t: (-t['score'], t['due'], t['id'])):
        remaining = int(t['need'] * 2)
        for day in range(7):
            current = start + timedelta(days=day)
            if current > t['due']:
                continue
            assigned = min(slots[day], remaining)
            if assigned:
                schedule.append({'date': current, 'id': t['id'], 'name': t['name'], 'hours': assigned / 2})
                slots[day] -= assigned
                remaining -= assigned
        allocated = t['need'] - remaining / 2
        summary.append(dict(t, allocated=allocated, deferred=remaining / 2,
                            future=max(0, t['hours'] - t['need'])))
    return {'schedule': schedule, 'summary': sorted(summary, key=lambda t: t['id']),
            'capacities': list(capacities), 'start': start, 'target': target}


def compare_plans(before, after):
    """실제 계산값으로 증감과 날짜 이동 이유를 설명한다."""
    old = {t['id']: t for t in before['summary']}
    delta = sum(after['capacities']) - sum(before['capacities'])
    reasons = [f'주간 가능 시간이 {sum(before["capacities"]):g}시간에서 {sum(after["capacities"]):g}시간으로 변경되었습니다 (차이 {delta:+g}시간).',
               '유효 마감이 이번 주인 항목에 100점, 다음 주인 항목에 30점, 중요도당 10점, 장기 목표 관련 항목에 15점을 부여해 다시 정렬했습니다. 동점이면 마감이 빠른 항목을 먼저 배정합니다.']
    rows = []
    for t in after['summary']:
        previous = old.get(t['id'])
        prev_hours = previous['allocated'] if previous else 0
        if not previous:
            why = f'새 일정 추가 · 우선순위 점수 {t["score"]}'
        elif t['allocated'] < prev_hours:
            why = '가용 시간과 더 높은 우선순위 항목을 반영해 배정 감소'
        elif t['allocated'] > prev_hours:
            why = '변경된 가용 시간에서 우선순위에 따라 추가 배정'
        else:
            old_dates = [(s['date'], s['hours']) for s in before['schedule'] if s['id'] == t['id']]
            new_dates = [(s['date'], s['hours']) for s in after['schedule'] if s['id'] == t['id']]
            why = '총시간 유지 · 가능 시간 변경으로 날짜 이동' if old_dates != new_dates else '기존 배정 유지'
        if t['due'] < after['start']:
            why += ' · 마감 경과로 배정 불가'
        rows.append({'학습 항목': t['name'], '기존(시간)': prev_hours, '수정(시간)': t['allocated'],
                     '증감(시간)': t['allocated'] - prev_hours, '변경 이유': why})
    return rows, reasons
