"""초기창업패키지 사업계획서 생성기 - Streamlit 웹 앱"""

import os
import logging
import tempfile
from datetime import datetime

import streamlit as st

from models import UserInput, TeamMember
from content_generator import generate_all_sections
from docx_writer import generate_docx

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 페이지 설정
st.set_page_config(
    page_title="초기창업패키지 사업계획서 생성기",
    page_icon="📋",
    layout="wide",
)

# 템플릿 파일 경로
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(
    SCRIPT_DIR,
    "(별첨1) 2026년도 초기창업패키지(일반형) 사업계획서 양식.docx"
)


def main():
    st.title("초기창업패키지 사업계획서 생성기")
    st.caption("키워드를 입력하면 AI가 사업계획서를 자동으로 작성합니다")

    # --- 사이드바: API 키 ---
    with st.sidebar:
        st.header("설정")
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            help="Claude API 호출에 필요합니다",
            value=os.environ.get("ANTHROPIC_API_KEY", ""),
        )

        st.divider()
        st.subheader("웹 리서치 (Firecrawl)")
        use_research = st.checkbox(
            "웹 리서치 활성화",
            help="Firecrawl로 시장 데이터, 경쟁사, 트렌드를 자동 수집하여 사업계획서에 반영합니다",
        )
        firecrawl_key = ""
        if use_research:
            firecrawl_key = st.text_input(
                "Firecrawl API Key",
                type="password",
                help="firecrawl.dev에서 발급받은 API Key",
                value=os.environ.get("FIRECRAWL_API_KEY", ""),
            )

        st.divider()
        st.markdown("**사용 방법**")
        st.markdown(
            "1. API Key를 입력하세요\n"
            "2. (선택) 웹 리서치를 활성화하세요\n"
            "3. 필수 항목을 작성하세요\n"
            "4. '사업계획서 생성' 클릭\n"
            "5. 완성된 DOCX를 다운로드하세요"
        )

    # --- 메인 입력 폼 ---
    with st.form("input_form"):
        st.subheader("필수 입력 항목")

        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("기업명 *", placeholder="예: (주)테크스타트")
            item_name = st.text_input("창업아이템명 *", placeholder="예: AI 기반 물류 최적화 플랫폼")
        with col2:
            business_type = st.selectbox("업종 *", ["지식서비스", "제조"])
            tech_field = st.selectbox("기술분야 *", [
                "정보·통신", "기계·소재", "전기·전자",
                "화공·섬유", "바이오·의료·생명", "에너지·자원", "공예·디자인"
            ])

        core_technology = st.text_area(
            "핵심기술 *",
            placeholder="예: 강화학습 기반 경로 최적화 알고리즘, 실시간 물류 데이터 분석 엔진",
            height=80,
        )
        target_market = st.text_area(
            "타겟시장 *",
            placeholder="예: 국내 중소 물류기업 시장 (시장규모 약 15조원)",
            height=80,
        )
        problem_description = st.text_area(
            "해결하고자 하는 문제 *",
            placeholder="예: 중소 물류기업의 비효율적인 배송 경로로 인한 물류비 증가 및 배송 지연 문제",
            height=80,
        )

        st.subheader("선택 입력 항목")

        col3, col4 = st.columns(2)
        with col3:
            target_customers = st.text_input("타겟고객", placeholder="예: 일 배송량 100건 이상 중소 물류기업")
            competitive_advantage = st.text_input("경쟁우위/차별성", placeholder="예: 특허 출원 AI 알고리즘")
            category = st.text_input("아이템 범주", placeholder="예: AI 프로그램, 모바일 앱")
            output_type = st.text_input("산출물 형태", placeholder="예: 웹 플랫폼(1개), 모바일 앱(1개)")
        with col4:
            location = st.text_input("사업장 소재지", placeholder="예: 서울특별시 강남구")
            entity_type = st.selectbox("사업자 구분", ["법인", "개인"])
            representative_type = st.selectbox("대표자 유형", ["단독", "공동", "각자대표"])
            establishment_date = st.text_input("개업연월일", placeholder="예: 25.01.15")

        col5, col6 = st.columns(2)
        with col5:
            business_registration_no = st.text_input("사업자등록번호", placeholder="예: 123-45-67890")
        with col6:
            keywords_str = st.text_input("추가 키워드 (쉼표 구분)", placeholder="예: ESG, 그린물류, 탄소중립")

        st.subheader("사업비 구성 (만원)")
        bcol1, bcol2, bcol3, bcol4 = st.columns(4)
        with bcol1:
            total_budget = st.number_input("총사업비", value=10000, min_value=0, step=100)
        with bcol2:
            government_fund = st.number_input("정부지원금", value=7000, min_value=0, step=100)
        with bcol3:
            self_fund_cash = st.number_input("자기부담(현금)", value=1000, min_value=0, step=100)
        with bcol4:
            self_fund_inkind = st.number_input("자기부담(현물)", value=2000, min_value=0, step=100)

        st.subheader("팀원 구성 (대표자 제외)")
        num_members = st.number_input("팀원 수", value=2, min_value=0, max_value=10, step=1)

        team_members = []
        for i in range(int(num_members)):
            st.markdown(f"**팀원 {i+1}**")
            tcol1, tcol2, tcol3, tcol4 = st.columns(4)
            with tcol1:
                pos = st.text_input(f"직위 #{i+1}", key=f"pos_{i}", placeholder="예: 이사")
            with tcol2:
                role = st.text_input(f"담당업무 #{i+1}", key=f"role_{i}", placeholder="예: 개발 총괄")
            with tcol3:
                cap = st.text_input(f"역량 #{i+1}", key=f"cap_{i}", placeholder="예: 관련 경력 5년")
            with tcol4:
                status = st.selectbox(f"상태 #{i+1}", ["완료", "예정"], key=f"status_{i}")
            team_members.append(TeamMember(
                position=pos, role=role, capability=cap, status=status
            ))

        submitted = st.form_submit_button(
            "사업계획서 생성",
            type="primary",
            use_container_width=True,
        )

    # --- 생성 처리 ---
    if submitted:
        # 유효성 검사
        if not api_key:
            st.error("사이드바에서 Anthropic API Key를 입력해주세요.")
            return
        if not company_name or not item_name or not core_technology or not target_market or not problem_description:
            st.error("필수 항목(*)을 모두 입력해주세요.")
            return
        if not os.path.exists(TEMPLATE_PATH):
            st.error(f"템플릿 파일을 찾을 수 없습니다: {TEMPLATE_PATH}")
            return

        # UserInput 구성
        user_input = UserInput(
            company_name=company_name,
            item_name=item_name,
            business_type=business_type,
            tech_field=tech_field,
            core_technology=core_technology,
            target_market=target_market,
            target_customers=target_customers,
            problem_description=problem_description,
            competitive_advantage=competitive_advantage,
            location=location,
            total_budget=total_budget,
            government_fund=government_fund,
            self_fund_cash=self_fund_cash,
            self_fund_inkind=self_fund_inkind,
            team_members=team_members,
            keywords=[k.strip() for k in keywords_str.split(",") if k.strip()] if keywords_str else [],
            business_registration_no=business_registration_no,
            establishment_date=establishment_date,
            entity_type=entity_type,
            representative_type=representative_type,
            category=category,
            output_type=output_type,
        )

        # 진행 표시
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(progress, message):
            progress_bar.progress(progress)
            status_text.text(message)

        try:
            # 0단계: 웹 리서치 (선택)
            research_context = ""
            if use_research and firecrawl_key:
                from web_researcher import run_full_research, format_research_for_prompt

                research_progress = st.progress(0)
                research_status = st.empty()

                def update_research_progress(progress, message):
                    research_progress.progress(progress)
                    research_status.text(message)

                research_data = run_full_research(
                    firecrawl_api_key=firecrawl_key,
                    item_name=item_name,
                    core_technology=core_technology,
                    target_market=target_market,
                    business_type=business_type,
                    keywords=[k.strip() for k in keywords_str.split(",") if k.strip()] if keywords_str else [],
                    progress_callback=update_research_progress,
                )
                research_context = format_research_for_prompt(research_data)

                total_results = sum(len(v) for v in research_data.values())
                research_status.text(f"웹 리서치 완료! ({total_results}건 수집)")

                with st.expander("수집된 리서치 데이터 미리보기"):
                    for category, items in research_data.items():
                        label = {"market": "시장 데이터", "competitors": "경쟁사 분석", "trends": "산업 트렌드"}
                        st.markdown(f"**{label.get(category, category)}** ({len(items)}건)")
                        for item in items[:3]:
                            st.markdown(f"- {item['title']}")

            # 1단계: 콘텐츠 생성
            status_text.text("AI가 사업계획서 콘텐츠를 생성하고 있습니다...")
            all_content = generate_all_sections(user_input, api_key, update_progress, research_context)

            # 2단계: DOCX 생성
            status_text.text("DOCX 문서를 생성하고 있습니다...")
            progress_bar.progress(0.95)

            output_filename = f"사업계획서_{company_name}_{datetime.now():%Y%m%d_%H%M%S}.docx"
            output_path = os.path.join(tempfile.gettempdir(), output_filename)

            generate_docx(TEMPLATE_PATH, output_path, user_input, all_content)

            progress_bar.progress(1.0)
            status_text.text("사업계획서 생성 완료!")

            # 3단계: 다운로드 버튼
            st.success("사업계획서가 성공적으로 생성되었습니다!")

            with open(output_path, "rb") as f:
                st.download_button(
                    label="사업계획서 다운로드 (.docx)",
                    data=f.read(),
                    file_name=output_filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                    use_container_width=True,
                )

            # 생성 결과 요약
            with st.expander("생성 결과 상세"):
                for section_id, content in all_content.items():
                    if "error" in content.generated_text:
                        st.error(f"{section_id}: {content.generated_text['error']}")
                    else:
                        st.success(f"{section_id}: 생성 완료")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")
            logger.exception("사업계획서 생성 중 오류")


if __name__ == "__main__":
    main()
