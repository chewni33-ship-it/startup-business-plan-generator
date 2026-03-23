"""데이터 모델 정의 - 사업계획서 생성기"""

from dataclasses import dataclass, field


@dataclass
class TeamMember:
    """팀원 정보"""
    position: str = ""        # 직위 (예: 대표, 이사, 대리)
    role: str = ""            # 담당 업무
    capability: str = ""      # 보유 역량
    status: str = "구성완료"  # 구성 상태 (구성완료/채용예정)


@dataclass
class UserInput:
    """사용자 입력 데이터"""
    # 필수 입력
    company_name: str = ""              # 기업명
    item_name: str = ""                 # 창업아이템명
    core_technology: str = ""           # 핵심기술
    target_market: str = ""             # 타겟시장
    problem_description: str = ""       # 해결하고자 하는 문제

    # 선택 입력
    business_type: str = "지식서비스"   # 업종 (제조/지식서비스/...)
    tech_field: str = "ICT·정보통신"    # 기술분야
    target_customers: str = ""          # 타겟고객
    competitive_advantage: str = ""     # 경쟁우위/차별성
    location: str = ""                  # 사업장 소재지
    total_budget: int = 10000           # 총사업비 (만원)
    government_fund: int = 7000         # 정부지원금 (만원)
    self_fund_cash: int = 1000          # 자기부담금-현금 (만원)
    self_fund_inkind: int = 2000        # 자기부담금-현물 (만원)
    team_members: list = field(default_factory=list)  # TeamMember 리스트
    keywords: list = field(default_factory=list)      # 추가 키워드
    business_registration_no: str = ""  # 사업자등록번호
    establishment_date: str = ""        # 개업연월일
    entity_type: str = "법인"           # 개인/법인
    representative_type: str = "단독"   # 단독/공동/각자 대표
    category: str = ""                  # 아이템 범주 (예: AI 프로그램, 모바일 앱)
    output_type: str = ""               # 산출물 형태 (예: 모바일 앱 1개, 웹사이트 1개)


@dataclass
class SectionContent:
    """섹션별 생성된 콘텐츠"""
    section_id: str              # 섹션 식별자
    generated_text: dict = field(default_factory=dict)  # 필드키 → 생성된 텍스트
