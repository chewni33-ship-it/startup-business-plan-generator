"""DOCX 템플릿 분석 및 섹션 매핑"""

import os
import zipfile
import tempfile
from copy import deepcopy
from lxml import etree

WNS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
RNS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
XML_NS = 'http://www.w3.org/XML/1998/namespace'
NS = {'w': WNS, 'r': RNS}


def extract_docx(docx_path):
    """DOCX를 임시 디렉토리에 압축 해제하고 document.xml 경로 반환"""
    tmp_dir = tempfile.mkdtemp(prefix="docx_")
    with zipfile.ZipFile(docx_path, 'r') as z:
        z.extractall(tmp_dir)
    return tmp_dir


def parse_document_xml(tmp_dir):
    """document.xml 파싱하여 (tree, body) 반환"""
    doc_path = os.path.join(tmp_dir, 'word', 'document.xml')
    tree = etree.parse(doc_path)
    root = tree.getroot()
    body = root.find(f'{{{WNS}}}body')
    return tree, body


def get_text(elem):
    """요소 내 모든 텍스트 추출"""
    texts = []
    for t in elem.iter(f'{{{WNS}}}t'):
        if t.text:
            texts.append(t.text)
    return ''.join(texts)


def has_blue_color(elem):
    """요소 내에 파란색(0000FF) 텍스트가 있는지 확인"""
    for color in elem.iter(f'{{{WNS}}}color'):
        val = color.get(f'{{{WNS}}}val', '')
        if val.upper() == '0000FF':
            return True
    return False


def find_blue_runs(elem):
    """요소 내 파란색 런(w:r) 목록 반환"""
    blue_runs = []
    for run in elem.iter(f'{{{WNS}}}r'):
        rpr = run.find(f'{{{WNS}}}rPr')
        if rpr is not None:
            color = rpr.find(f'{{{WNS}}}color')
            if color is not None and color.get(f'{{{WNS}}}val', '').upper() == '0000FF':
                blue_runs.append(run)
    return blue_runs


def get_body_children(body):
    """body의 직접 자식 요소 목록 반환 (인덱스 포함)"""
    children = []
    for i, child in enumerate(body):
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        children.append((i, tag, child))
    return children


def get_table_cell(table, row_idx, col_idx):
    """테이블에서 특정 행/열의 셀 요소 반환"""
    rows = table.findall(f'{{{WNS}}}tr')
    if row_idx >= len(rows):
        return None
    cells = rows[row_idx].findall(f'{{{WNS}}}tc')
    if col_idx >= len(cells):
        return None
    return cells[col_idx]


def get_table_rows(table):
    """테이블의 행 목록 반환"""
    return table.findall(f'{{{WNS}}}tr')


def clone_run_properties(run):
    """런의 서식(rPr)을 복사하되, 색상을 검정(000000)으로 변경"""
    rpr = run.find(f'{{{WNS}}}rPr')
    if rpr is None:
        return None
    new_rpr = deepcopy(rpr)
    color = new_rpr.find(f'{{{WNS}}}color')
    if color is not None:
        color.set(f'{{{WNS}}}val', '000000')
    return new_rpr


def get_paragraph_properties(para):
    """문단의 속성(pPr) 복사본 반환"""
    ppr = para.find(f'{{{WNS}}}pPr')
    if ppr is None:
        return None
    return deepcopy(ppr)
