"""DOCX XML 조작 및 저장 모듈

DOCX_XML_규칙_가이드.md의 절대 규칙을 준수:
- 네임스페이스 선언 보존
- rsid 속성 보존
- w:tblGrid, w:tcPr, w:sectPr 절대 삭제 금지
- 빈 셀에도 <w:p/> 유지
- \\n 대신 새 <w:p> 사용
"""

import os
import zipfile
import shutil
import logging
from copy import deepcopy
from lxml import etree

from template_parser import (
    WNS, XML_NS, NS,
    extract_docx, parse_document_xml,
    get_text, has_blue_color, find_blue_runs,
    clone_run_properties, get_paragraph_properties,
    get_table_cell, get_table_rows,
)
from section_config import (
    SECTION_MAP, BLUE_GUIDE_INDICES, BLUE_GUIDE_TABLE_INDICES, EMPTY_PARA_RANGES,
)
from models import UserInput, SectionContent

logger = logging.getLogger(__name__)


# ==============================================================================
# 기본 XML 조작 함수
# ==============================================================================

def create_run(text, rpr_template=None):
    """새 런(w:r) 요소 생성"""
    run = etree.SubElement(etree.Element("dummy"), f'{{{WNS}}}r')
    run.getparent().remove(run)

    if rpr_template is not None:
        run.append(deepcopy(rpr_template))

    t = etree.SubElement(run, f'{{{WNS}}}t')
    t.text = text
    if text and (' ' in text or text.startswith(' ') or text.endswith(' ')):
        t.set(f'{{{XML_NS}}}space', 'preserve')

    return run


def create_paragraph(text, ppr_template=None, rpr_template=None):
    """새 문단(w:p) 요소 생성"""
    para = etree.Element(f'{{{WNS}}}p')

    if ppr_template is not None:
        para.append(deepcopy(ppr_template))

    run = create_run(text, rpr_template)
    para.append(run)

    return para


def replace_paragraph_text(para, new_text, change_color=True):
    """문단 내 파란색 텍스트를 새 텍스트로 교체 (서식 유지, 색상만 변경)"""
    blue_runs = find_blue_runs(para)
    if not blue_runs:
        return

    # 첫 번째 파란색 런의 서식을 복사
    first_rpr = clone_run_properties(blue_runs[0])

    # 모든 파란색 런 제거
    for run in blue_runs:
        run.getparent().remove(run)

    # 새 런 추가
    new_run = create_run(new_text, first_rpr)
    para.append(new_run)


def replace_cell_blue_text(cell, new_text):
    """테이블 셀 내 파란색 텍스트만 교체 (w:tcPr 보존)"""
    for para in cell.findall(f'{{{WNS}}}p'):
        blue_runs = find_blue_runs(para)
        if blue_runs:
            rpr = clone_run_properties(blue_runs[0])
            for run in blue_runs:
                run.getparent().remove(run)
            new_run = create_run(new_text, rpr)
            para.append(new_run)
            return  # 첫 번째 파란색 문단만 교체


def clear_blue_guide_paragraph(para):
    """파란색 가이드 문단의 텍스트를 비움 (구조는 유지)"""
    blue_runs = find_blue_runs(para)
    for run in blue_runs:
        run.getparent().remove(run)


def insert_paragraphs_after(body, ref_index, texts, ppr_template=None, rpr_template=None):
    """body의 ref_index 뒤에 여러 문단 삽입"""
    for i, text in enumerate(texts):
        para = create_paragraph(text, ppr_template, rpr_template)
        body.insert(ref_index + 1 + i, para)


# ==============================================================================
# 섹션별 콘텐츠 적용 함수
# ==============================================================================

def apply_general_info(body, user_input):
    """일반현황 테이블에 사용자 입력 적용"""
    table = body[SECTION_MAP["general_info_table"]]
    rows = get_table_rows(table)

    # r0c1: 기업명
    if user_input.company_name:
        replace_cell_blue_text(rows[0].findall(f'{{{WNS}}}tc')[1], user_input.company_name)

    # r0c3: 개업연월일
    if user_input.establishment_date:
        replace_cell_blue_text(rows[0].findall(f'{{{WNS}}}tc')[3], user_input.establishment_date)

    # r1c1: 사업자 구분
    if user_input.entity_type:
        replace_cell_blue_text(rows[1].findall(f'{{{WNS}}}tc')[1],
                               f"{'개인사업자' if user_input.entity_type == '개인' else '법인사업자'}")

    # r1c3: 대표자 유형
    if user_input.representative_type:
        replace_cell_blue_text(rows[1].findall(f'{{{WNS}}}tc')[3], user_input.representative_type)

    # r2c1: 사업자등록번호
    if user_input.business_registration_no:
        replace_cell_blue_text(rows[2].findall(f'{{{WNS}}}tc')[1], user_input.business_registration_no)

    # r2c3: 소재지
    if user_input.location:
        replace_cell_blue_text(rows[2].findall(f'{{{WNS}}}tc')[3], user_input.location)


def apply_item_info(body, user_input, overview_content=None):
    """아이템 정보 테이블에 사용자 입력 적용"""
    table = body[SECTION_MAP["item_info_table"]]
    rows = get_table_rows(table)

    # r0c1: 창업아이템명
    if user_input.item_name:
        replace_cell_blue_text(rows[0].findall(f'{{{WNS}}}tc')[1], user_input.item_name)

    # r1c1: 산출물
    if user_input.output_type:
        replace_cell_blue_text(rows[1].findall(f'{{{WNS}}}tc')[1], user_input.output_type)

    # r8c1~c4: 사업비 (00백만원 → 실제 금액)
    cells_r8 = rows[8].findall(f'{{{WNS}}}tc')
    budget_values = [
        f"{user_input.government_fund // 100}백만원" if user_input.government_fund else "",
        f"{user_input.self_fund_cash // 100}백만원" if user_input.self_fund_cash else "",
        f"{user_input.self_fund_inkind // 100}백만원" if user_input.self_fund_inkind else "",
        f"{user_input.total_budget // 100}백만원" if user_input.total_budget else "",
    ]
    for ci, val in enumerate(budget_values):
        if val and ci + 1 < len(cells_r8):
            # 이 셀의 텍스트는 "00백만원" 형태 - 파란색이 아닐 수 있으므로 직접 텍스트 교체
            for para in cells_r8[ci + 1].findall(f'{{{WNS}}}p'):
                for run in para.findall(f'{{{WNS}}}r'):
                    t_elem = run.find(f'{{{WNS}}}t')
                    if t_elem is not None and t_elem.text and '백만원' in t_elem.text:
                        t_elem.text = val

    # r12~r15: 팀 구성 현황 (파란색 예시 데이터)
    if user_input.team_members:
        for ti, tm in enumerate(user_input.team_members):
            row_idx = 12 + ti
            if row_idx >= len(rows):
                break
            cells = rows[row_idx].findall(f'{{{WNS}}}tc')
            values = [str(ti + 1), tm.position, tm.role, tm.capability, tm.status]
            for ci, val in enumerate(values):
                if ci < len(cells):
                    replace_cell_blue_text(cells[ci], val)


def apply_overview_table(body, content):
    """개요(요약) 테이블에 생성된 콘텐츠 적용"""
    table = body[SECTION_MAP["overview_table"]]
    rows = get_table_rows(table)

    data = content.generated_text
    row_mapping = {
        1: "item_overview",         # r1: 아이템 개요
        2: "problem_recognition",   # r2: 문제 인식
        3: "solution",              # r3: 실현 가능성
        4: "growth_strategy",       # r4: 성장전략
        5: "team",                  # r5: 팀 구성
    }

    for row_idx, key in row_mapping.items():
        if key in data and row_idx < len(rows):
            cells = rows[row_idx].findall(f'{{{WNS}}}tc')
            if len(cells) > 1:
                replace_cell_blue_text(cells[1], data[key])


def apply_free_text_section(body, bullet_indices, content, point_keys):
    """자유 텍스트 섹션 (문제인식, 실현가능성, 성장전략, 팀구성)에 콘텐츠 적용"""
    data = content.generated_text

    for i, (idx, key) in enumerate(zip(bullet_indices, point_keys)):
        if key in data and idx < len(body):
            para = body[idx]
            text = get_text(para)

            # "ㅇ" 마커가 있는 문단에 텍스트 추가
            if 'ㅇ' in text:
                # 기존 런 찾기
                runs = para.findall(f'{{{WNS}}}r')
                if runs:
                    # 첫 번째 런의 서식 복사
                    rpr = clone_run_properties(runs[0])
                    if rpr is None:
                        # 서식이 없으면 기본 rpr 생성
                        rpr = etree.Element(f'{{{WNS}}}rPr')
                        color = etree.SubElement(rpr, f'{{{WNS}}}color')
                        color.set(f'{{{WNS}}}val', '000000')

                    # 기존 텍스트 런의 텍스트를 변경
                    t_elem = runs[0].find(f'{{{WNS}}}t')
                    if t_elem is not None:
                        t_elem.text = f"ㅇ {data[key]}"
                        t_elem.set(f'{{{XML_NS}}}space', 'preserve')
                else:
                    # 런이 없으면 새로 생성
                    rpr = etree.Element(f'{{{WNS}}}rPr')
                    color = etree.SubElement(rpr, f'{{{WNS}}}color')
                    color.set(f'{{{WNS}}}val', '000000')
                    new_run = create_run(f"ㅇ {data[key]}", rpr)
                    para.append(new_run)


def apply_data_table(body, table_index, content, column_keys):
    """데이터 테이블 (일정, 예산, 팀, 협력기관)에 콘텐츠 적용"""
    table = body[table_index]
    rows = get_table_rows(table)
    data = content.generated_text

    if "rows" not in data:
        return

    data_rows = data["rows"]

    # 데이터 행은 row 1부터 시작 (row 0은 헤더)
    # 예산 테이블은 row 3부터 (row 0~2는 헤더)
    header_rows = 3 if table_index == SECTION_MAP["budget_table"] else 1

    for di, row_data in enumerate(data_rows):
        row_idx = header_rows + di

        if row_idx < len(rows):
            # 기존 행에 데이터 채우기
            cells = rows[row_idx].findall(f'{{{WNS}}}tc')
            for ci, key in enumerate(column_keys):
                if ci < len(cells) and key in row_data:
                    val = row_data[key]
                    if val:
                        replace_cell_blue_text(cells[ci], val)
        else:
            # 행이 부족하면 마지막 데이터 행을 복제
            if len(rows) > header_rows:
                last_data_row = rows[-1]
                new_row = deepcopy(last_data_row)
                cells = new_row.findall(f'{{{WNS}}}tc')
                for ci, key in enumerate(column_keys):
                    if ci < len(cells) and key in row_data:
                        # 복제된 행의 셀 텍스트 교체
                        for p in cells[ci].findall(f'{{{WNS}}}p'):
                            for r in p.findall(f'{{{WNS}}}r'):
                                t = r.find(f'{{{WNS}}}t')
                                if t is not None:
                                    t.text = row_data[key]
                                    t.set(f'{{{XML_NS}}}space', 'preserve')
                                    # 색상을 검정으로
                                    rpr = r.find(f'{{{WNS}}}rPr')
                                    if rpr is not None:
                                        c = rpr.find(f'{{{WNS}}}color')
                                        if c is not None:
                                            c.set(f'{{{WNS}}}val', '000000')
                table.append(new_row)

    # 예산 테이블 합계 행 처리
    if table_index == SECTION_MAP["budget_table"] and "total_gov" in data:
        # 마지막 행이 합계
        total_row = get_table_rows(table)[-1]
        cells = total_row.findall(f'{{{WNS}}}tc')
        total_values = [data.get("total_gov", ""), data.get("total_cash", ""),
                        data.get("total_inkind", ""), data.get("grand_total", "")]
        # 합계 행 c2~c5에 값 채우기
        for ci, val in enumerate(total_values):
            if val and ci + 2 < len(cells):
                replace_cell_blue_text(cells[ci + 2], val)


def remove_empty_paragraphs(body):
    """불필요한 빈 문단들 제거 (페이지 수 조절)"""
    # 뒤에서부터 제거해야 인덱스가 밀리지 않음
    indices_to_remove = []
    for start, end in EMPTY_PARA_RANGES:
        for idx in range(start, end + 1):
            if idx < len(body):
                child = body[idx]
                tag = child.tag.split('}')[-1]
                if tag == 'p' and not get_text(child).strip():
                    indices_to_remove.append(idx)

    # 역순으로 제거
    for idx in sorted(indices_to_remove, reverse=True):
        if idx < len(body):
            body.remove(body[idx])


def clear_guide_texts(body):
    """파란색 가이드 텍스트 문단 비우기"""
    for idx in BLUE_GUIDE_INDICES:
        if idx < len(body):
            clear_blue_guide_paragraph(body[idx])

    # 가이드 테이블의 파란색 텍스트도 비우기
    for idx in BLUE_GUIDE_TABLE_INDICES:
        if idx < len(body):
            child = body[idx]
            tag = child.tag.split('}')[-1]
            if tag == 'tbl':
                for cell in child.iter(f'{{{WNS}}}tc'):
                    blue_runs = find_blue_runs(cell)
                    for run in blue_runs:
                        run.getparent().remove(run)


# ==============================================================================
# 메인 적용 함수
# ==============================================================================

def apply_all_content(body, user_input, all_content):
    """모든 생성된 콘텐츠를 템플릿에 적용"""

    # 1. 일반현황 (사용자 입력 직접 매핑)
    logger.info("일반현황 적용 중...")
    apply_general_info(body, user_input)

    # 2. 아이템 정보
    logger.info("아이템 정보 적용 중...")
    apply_item_info(body, user_input)

    # 3. 개요(요약) 테이블
    if "overview_summary" in all_content:
        logger.info("개요(요약) 적용 중...")
        apply_overview_table(body, all_content["overview_summary"])

    # 4. 문제 인식
    if "problem_recognition" in all_content:
        logger.info("문제 인식 적용 중...")
        apply_free_text_section(
            body,
            [SECTION_MAP["problem_bullet_1"], SECTION_MAP["problem_bullet_2"], SECTION_MAP["problem_bullet_3"]],
            all_content["problem_recognition"],
            ["point_1", "point_2", "point_3"]
        )

    # 5. 실현 가능성
    if "solution_plan" in all_content:
        logger.info("실현 가능성 적용 중...")
        apply_free_text_section(
            body,
            [SECTION_MAP["solution_bullet_1"]],
            all_content["solution_plan"],
            ["point_1"]
        )

    # 6. 사업추진 일정 (협약기간)
    if "schedule_agreement" in all_content:
        logger.info("사업추진 일정(협약) 적용 중...")
        apply_data_table(
            body, SECTION_MAP["schedule_agreement_table"],
            all_content["schedule_agreement"],
            ["no", "content", "period", "detail"]
        )

    # 7. 사업비 집행계획
    if "budget_plan" in all_content:
        logger.info("사업비 집행계획 적용 중...")
        apply_data_table(
            body, SECTION_MAP["budget_table"],
            all_content["budget_plan"],
            ["category", "plan", "gov_fund", "self_cash", "self_inkind", "total"]
        )

    # 8. 성장전략
    if "growth_strategy" in all_content:
        logger.info("성장전략 적용 중...")
        apply_free_text_section(
            body,
            [SECTION_MAP["growth_bullet_1"], SECTION_MAP["growth_bullet_2"]],
            all_content["growth_strategy"],
            ["point_1", "point_2"]
        )

    # 9. 사업추진 일정 (전체)
    if "schedule_full" in all_content:
        logger.info("사업추진 일정(전체) 적용 중...")
        apply_data_table(
            body, SECTION_MAP["schedule_full_table"],
            all_content["schedule_full"],
            ["no", "content", "period", "detail"]
        )

    # 10. 팀 구성 소개
    if "team_intro" in all_content:
        logger.info("팀 구성 소개 적용 중...")
        apply_free_text_section(
            body,
            [SECTION_MAP["team_bullet_1"]],
            all_content["team_intro"],
            ["point_1"]
        )

    # 11. 팀 구성(안) 테이블
    if "team_composition" in all_content:
        logger.info("팀 구성 테이블 적용 중...")
        apply_data_table(
            body, SECTION_MAP["team_table"],
            all_content["team_composition"],
            ["no", "position", "role", "capability", "status"]
        )

    # 12. 협력기관 테이블
    if "partnerships" in all_content:
        logger.info("협력기관 테이블 적용 중...")
        apply_data_table(
            body, SECTION_MAP["partner_table"],
            all_content["partnerships"],
            ["no", "name", "capability", "plan", "timing"]
        )

    # 13. 파란색 가이드 텍스트 비우기
    logger.info("가이드 텍스트 정리 중...")
    clear_guide_texts(body)

    # 14. 빈 문단 제거 (페이지 수 조절)
    logger.info("빈 문단 정리 중...")
    remove_empty_paragraphs(body)


# ==============================================================================
# DOCX 저장
# ==============================================================================

def save_docx(original_path, output_path, tree):
    """수정된 XML 트리를 새 DOCX 파일로 저장

    원본 ZIP에서 document.xml만 교체하여 이미지, 스타일, 폰트 등 모든 리소스를 보존
    """
    tmp_dir = extract_docx(original_path)

    try:
        # 수정된 document.xml 저장
        doc_path = os.path.join(tmp_dir, 'word', 'document.xml')
        tree.write(doc_path, xml_declaration=True, encoding='UTF-8', standalone=True)

        # 새 ZIP 파일 생성
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
            for root_dir, dirs, files in os.walk(tmp_dir):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    arcname = os.path.relpath(file_path, tmp_dir)
                    zout.write(file_path, arcname)

        logger.info(f"DOCX 저장 완료: {output_path}")

    finally:
        # 임시 디렉토리 정리
        shutil.rmtree(tmp_dir, ignore_errors=True)


def generate_docx(template_path, output_path, user_input, all_content):
    """전체 DOCX 생성 파이프라인"""
    # 1. 템플릿 파싱
    tmp_dir = extract_docx(template_path)
    try:
        tree, body = parse_document_xml(tmp_dir)

        # 2. 콘텐츠 적용
        apply_all_content(body, user_input, all_content)

        # 3. 수정된 document.xml을 임시 디렉토리에 저장
        doc_path = os.path.join(tmp_dir, 'word', 'document.xml')
        tree.write(doc_path, xml_declaration=True, encoding='UTF-8', standalone=True)

        # 4. 새 DOCX ZIP 생성
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
            for root_dir, dirs, files in os.walk(tmp_dir):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    arcname = os.path.relpath(file_path, tmp_dir)
                    zout.write(file_path, arcname)

        logger.info(f"사업계획서 생성 완료: {output_path}")
        return output_path

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
