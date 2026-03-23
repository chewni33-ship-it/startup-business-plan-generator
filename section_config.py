"""섹션 설정 및 Claude API 프롬프트 템플릿"""

# ==============================================================================
# Body 인덱스 → 섹션 매핑
# ==============================================================================
# 템플릿 document.xml body 자식 요소 인덱스 기준
SECTION_MAP = {
    # 일반현황
    "general_info_table": 11,       # TABLE 3rows x 4cols: 기업명, 개업일, 등록번호, 소재지
    "item_info_table": 13,          # TABLE 16rows x 20cols: 아이템명, 산출물, 분야, 예산, 팀

    # 개요(요약)
    "overview_table": 17,           # TABLE 8rows x 5cols: 명칭, 개요, 문제인식, 가능성, 전략, 팀, 이미지

    # 문제 인식
    "problem_guide": 20,            # PARA [BLUE]: 가이드 텍스트 (삭제 대상)
    "problem_bullet_1": 22,         # PARA: ㅇ
    "problem_bullet_2": 26,         # PARA: ㅇ
    "problem_bullet_3": 30,         # PARA: ㅇ

    # 실현 가능성
    "solution_guide": 56,           # PARA [BLUE]: 가이드 텍스트 (삭제 대상)
    "solution_bullet_1": 58,        # PARA: ㅇ
    "schedule_agreement_table": 67, # TABLE 6rows x 4cols: 협약기간 내 일정
    "budget_guide_table": 71,       # TABLE 1row: 예산 안내 (가이드 텍스트)
    "budget_table": 74,             # TABLE 8rows x 6cols: 사업비 집행계획

    # 성장전략
    "growth_guide": 77,             # PARA [BLUE]: 가이드 텍스트 (삭제 대상)
    "growth_bullet_1": 79,          # PARA: ㅇ
    "growth_bullet_2": 85,          # PARA: ㅇ
    "schedule_full_table": 104,     # TABLE 6rows x 4cols: 전체 사업추진 일정

    # 팀 구성
    "team_guide": 109,              # PARA [BLUE]: 가이드 텍스트 (삭제 대상)
    "team_bullet_1": 111,           # PARA: ㅇ
    "team_table": 123,              # TABLE 4rows x 5cols: 팀 구성(안)
    "partner_table": 127,           # TABLE 4rows x 5cols: 협력기관
}

# 삭제 또는 비울 파란색 가이드 텍스트 인덱스
BLUE_GUIDE_INDICES = [8, 20, 56, 77, 109]

# 삭제 대상 파란색 가이드 테이블 (목차 안내, 예산 안내)
BLUE_GUIDE_TABLE_INDICES = [0, 71]

# 빈 문단 범위 (페이지 채우기용 - 삭제하여 페이지 수 조절)
EMPTY_PARA_RANGES = [
    (23, 25),   # 문제인식 bullet 1 뒤
    (27, 29),   # 문제인식 bullet 2 뒤
    (31, 54),   # 문제인식 bullet 3 뒤 + 페이지 필러
    (59, 63),   # 실현가능성 bullet 1 뒤
    (80, 84),   # 성장전략 bullet 1 뒤
    (86, 101),  # 성장전략 bullet 2 뒤 + 페이지 필러
    (112, 120), # 팀구성 bullet 1 뒤
]


# ==============================================================================
# Claude API 프롬프트 템플릿
# ==============================================================================

SYSTEM_PROMPT = """당신은 한국 정부 지원 초기창업패키지 사업계획서 전문 작성가입니다.
정부 심사위원을 설득할 수 있는 전문적이고 구체적인 사업계획서를 작성합니다.
반드시 요청된 JSON 형식으로만 응답하세요. 설명이나 마크다운 없이 순수 JSON만 출력합니다."""

SECTION_PROMPTS = {
    "overview_summary": """다음 정보를 바탕으로 초기창업패키지 사업계획서의 '개요(요약)' 섹션을 작성해주세요.

기업명: {company_name}
창업아이템명: {item_name}
범주: {category}
핵심기술: {core_technology}
타겟시장: {target_market}
타겟고객: {target_customers}
해결하고자 하는 문제: {problem_description}
경쟁우위: {competitive_advantage}
추가 키워드: {keywords}

JSON 형식으로 응답:
{{
  "item_overview": "아이템 개요 (사용 용도, 사양, 가격, 핵심 기능·성능, 고객 제공 혜택 포함, 3-5문장)",
  "problem_recognition": "문제 인식 요약 (국내외 시장 현황 및 문제점, 개발 필요성, 2-3문장)",
  "solution": "실현 가능성 요약 (개발 계획, 차별성 및 경쟁력 확보 전략, 2-3문장)",
  "growth_strategy": "성장전략 요약 (경쟁사 분석, 시장 진입 전략, 비즈니스 모델, 투자유치 전략, 2-3문장)",
  "team": "팀 구성 요약 (대표자, 팀원, 업무파트너 역량 활용 계획, 1-2문장)"
}}""",

    "problem_recognition": """다음 정보를 바탕으로 초기창업패키지 사업계획서의 '1. 문제 인식(Problem)_창업 아이템의 필요성' 섹션을 작성해주세요.

창업아이템명: {item_name}
핵심기술: {core_technology}
타겟시장: {target_market}
타겟고객: {target_customers}
해결하고자 하는 문제: {problem_description}
추가 키워드: {keywords}

요구사항:
1. 3개의 핵심 포인트로 구성 (ㅇ 마커 사용)
2. 첫 번째 포인트: 국내외 시장 현황과 문제점 (구체적 데이터/통계 포함)
3. 두 번째 포인트: 기존 솔루션의 한계점과 문제 해결의 필요성
4. 세 번째 포인트: 창업 아이템 소개와 개발 필요성
5. 각 포인트는 3-5문장으로 서술
6. 전문적이고 설득력 있는 어조

JSON 형식으로 응답:
{{
  "point_1": "첫 번째 핵심 포인트 전체 텍스트 (시장 현황 및 문제점)",
  "point_2": "두 번째 핵심 포인트 전체 텍스트 (기존 솔루션 한계)",
  "point_3": "세 번째 핵심 포인트 전체 텍스트 (아이템 소개 및 필요성)"
}}""",

    "solution_plan": """다음 정보를 바탕으로 초기창업패키지 사업계획서의 '2. 실현 가능성(Solution)_창업 아이템의 개발 계획' 섹션을 작성해주세요.

창업아이템명: {item_name}
핵심기술: {core_technology}
타겟시장: {target_market}
해결하고자 하는 문제: {problem_description}
경쟁우위: {competitive_advantage}
산출물: {output_type}
총사업비: {total_budget}만원
추가 키워드: {keywords}

요구사항:
1. 아이디어를 제품·서비스로 개발/구체화하는 계획
2. 핵심 기능·성능의 차별성 및 경쟁력 확보 전략 포함
3. 3-5문장으로 구성

JSON 형식으로 응답:
{{
  "point_1": "개발 계획 및 차별성 설명 (3-5문장)"
}}""",

    "schedule_agreement": """다음 정보를 바탕으로 초기창업패키지 사업계획서의 '사업추진 일정(협약기간 내)' 테이블 데이터를 생성해주세요.

창업아이템명: {item_name}
핵심기술: {core_technology}
산출물: {output_type}
추가 키워드: {keywords}

요구사항:
- 4~5개 일정 항목 생성
- 협약기간은 약 10개월 (예: 26.04 ~ 27.01)
- 각 항목에 구분번호, 추진내용, 추진기간, 세부내용 포함

JSON 형식으로 응답:
{{
  "rows": [
    {{"no": "1", "content": "추진내용", "period": "26.04 ~ 26.06", "detail": "세부내용"}},
    {{"no": "2", "content": "추진내용", "period": "26.05 ~ 26.08", "detail": "세부내용"}},
    {{"no": "3", "content": "추진내용", "period": "26.07 ~ 26.10", "detail": "세부내용"}},
    {{"no": "4", "content": "추진내용", "period": "26.09 ~ 27.01", "detail": "세부내용"}}
  ]
}}""",

    "budget_plan": """다음 정보를 바탕으로 초기창업패키지 사업계획서의 '사업비 집행계획' 테이블 데이터를 생성해주세요.

창업아이템명: {item_name}
핵심기술: {core_technology}
총사업비: {total_budget}만원
정부지원금: {government_fund}만원
자기부담금(현금): {self_fund_cash}만원
자기부담금(현물): {self_fund_inkind}만원
추가 키워드: {keywords}

요구사항:
- 3~5개 비목별 항목 생성 (재료비, 외주용역비, 인건비, 지식재산권 등)
- 각 항목에 세부 집행 계획 포함 (▪ 마커 사용)
- 금액은 원 단위 (예: 3,448,000)
- 합계가 총사업비와 일치해야 함

JSON 형식으로 응답:
{{
  "rows": [
    {{"category": "재료비", "plan": "▪ 구체적 구입 항목(수량×단가)", "gov_fund": "3,448,000", "self_cash": "", "self_inkind": "", "total": "3,448,000"}},
    {{"category": "", "plan": "▪ 추가 항목", "gov_fund": "7,652,000", "self_cash": "", "self_inkind": "", "total": "7,652,000"}},
    {{"category": "외주용역비", "plan": "▪ 외주 항목", "gov_fund": "3,000,000", "self_cash": "7,000,000", "self_inkind": "", "total": "10,000,000"}}
  ],
  "total_gov": "총 정부지원금",
  "total_cash": "총 현금",
  "total_inkind": "총 현물",
  "grand_total": "총 합계"
}}""",

    "growth_strategy": """다음 정보를 바탕으로 초기창업패키지 사업계획서의 '3. 성장전략(Scale-up)_사업화 추진 전략' 섹션을 작성해주세요.

창업아이템명: {item_name}
핵심기술: {core_technology}
타겟시장: {target_market}
타겟고객: {target_customers}
경쟁우위: {competitive_advantage}
추가 키워드: {keywords}

요구사항:
1. 2개의 핵심 포인트로 구성
2. 첫 번째 포인트: 경쟁사 분석 + 목표 시장 진입 전략 + 비즈니스 모델(수익화 모델) (5-8문장)
3. 두 번째 포인트: 투자유치(자금확보) 전략 + ESG 지속가능성 + 사업 확장 계획 (5-8문장)
4. 전문적이고 설득력 있는 어조

JSON 형식으로 응답:
{{
  "point_1": "첫 번째 핵심 포인트 (시장 진입 + 비즈니스 모델)",
  "point_2": "두 번째 핵심 포인트 (투자유치 + ESG + 확장)"
}}""",

    "schedule_full": """다음 정보를 바탕으로 초기창업패키지 사업계획서의 '사업추진 일정(전체 사업단계)' 테이블을 생성해주세요.

창업아이템명: {item_name}
핵심기술: {core_technology}
타겟시장: {target_market}
추가 키워드: {keywords}

요구사항:
- 4~5개 단계 생성 (시제품 설계 → 제작 → 출시 → 홍보 → 확장)
- 전체 로드맵 관점 (2~3년)
- 각 항목에 구분번호, 추진내용, 추진기간, 세부내용

JSON 형식으로 응답:
{{
  "rows": [
    {{"no": "1", "content": "추진내용", "period": "26년 상반기", "detail": "세부내용"}},
    {{"no": "2", "content": "추진내용", "period": "26.06 ~ 27.01", "detail": "세부내용"}},
    {{"no": "3", "content": "추진내용", "period": "27년 상반기", "detail": "세부내용"}},
    {{"no": "4", "content": "추진내용", "period": "27년 하반기", "detail": "세부내용"}}
  ]
}}""",

    "team_intro": """다음 정보를 바탕으로 초기창업패키지 사업계획서의 '4. 팀 구성(Team)_대표자 및 팀원 구성계획' 섹션을 작성해주세요.

창업아이템명: {item_name}
핵심기술: {core_technology}
업종: {business_type}
팀원 정보: {team_info}
추가 키워드: {keywords}

요구사항:
1. 대표자의 보유 역량 중심으로 서술
2. 창업 아이템 개발/구체화 능력, 관련 경험, 기술력, 인적 네트워크 등 포함
3. 팀원 구성 계획과 역량 활용 방안 포함
4. 3-5문장으로 구성

JSON 형식으로 응답:
{{
  "point_1": "대표자 및 팀 역량 소개 텍스트 (3-5문장)"
}}""",

    "team_composition": """다음 정보를 바탕으로 초기창업패키지 사업계획서의 '팀 구성(안)' 테이블을 생성해주세요.

창업아이템명: {item_name}
핵심기술: {core_technology}
팀원 정보: {team_info}

요구사항:
- 팀원 정보가 제공되면 그대로 사용
- 없으면 2~3명의 예시 팀원 생성
- 각 항목: 구분번호, 직위, 담당업무, 보유역량(경력 및 학력), 구성상태
- 개인정보 마스킹 규칙 준수 (성명, 학교명 등 ○ 처리)

JSON 형식으로 응답:
{{
  "rows": [
    {{"no": "1", "position": "직위", "role": "담당업무", "capability": "보유역량", "status": "완료"}},
    {{"no": "2", "position": "직위", "role": "담당업무", "capability": "보유역량", "status": "예정('26.06)"}}
  ]
}}""",

    "partnerships": """다음 정보를 바탕으로 초기창업패키지 사업계획서의 '협력 기관 현황 및 협업 방안' 테이블을 생성해주세요.

창업아이템명: {item_name}
핵심기술: {core_technology}
업종: {business_type}
추가 키워드: {keywords}

요구사항:
- 2~3개 협력 기관 생성
- 실제 기업명 대신 ○○전자, ○○기업 등 마스킹
- 각 항목: 구분번호, 파트너명, 보유역량, 협업방안, 협력시기

JSON 형식으로 응답:
{{
  "rows": [
    {{"no": "1", "name": "○○전자", "capability": "보유역량", "plan": "협업방안", "timing": "26.06"}},
    {{"no": "2", "name": "○○기업", "capability": "보유역량", "plan": "협업방안", "timing": "26.09"}}
  ]
}}""",
}
