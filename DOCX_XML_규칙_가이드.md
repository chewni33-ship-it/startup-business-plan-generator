# DOCX(OOXML) XML 구조 규칙 가이드

> AI가 Word 사업계획서 양식을 프로그래밍 방식으로 편집할 때 반드시 알아야 하는 규칙 정리
>
> 공식 규격: [ECMA-376 Office Open XML](https://www.ecma-international.org/publications-and-standards/standards/ecma-376/) / [ISO/IEC 29500](https://www.loc.gov/preservation/digital/formats/fdd/fdd000395.shtml)
>
> Microsoft 참고: [Open XML SDK 문서](https://learn.microsoft.com/en-us/office/open-xml/open-xml-sdk)

---

## 1. DOCX 파일 구조

`.docx` 파일은 ZIP 아카이브이며, 내부에 XML 파일들이 구조화되어 있다.

```
파일.docx (ZIP)
├── [Content_Types].xml          # 모든 파일의 MIME 타입 등록
├── _rels/
│   └── .rels                    # 최상위 관계 정의
├── docProps/
│   ├── app.xml                  # 애플리케이션 속성 (페이지 수, 단어 수 등)
│   └── core.xml                 # 핵심 속성 (제목, 작성자, 날짜 등)
└── word/
    ├── _rels/
    │   └── document.xml.rels    # 문서 내 관계 (이미지, 스타일, 푸터 참조)
    ├── document.xml             # ★ 핵심: 본문 콘텐츠
    ├── styles.xml               # 스타일 정의 (문단/글자/표 스타일)
    ├── numbering.xml            # 번호매기기/불릿 정의
    ├── fontTable.xml            # 폰트 등록
    ├── settings.xml             # 문서 설정
    ├── footer1.xml              # 푸터
    ├── endnotes.xml             # 미주
    ├── footnotes.xml            # 각주
    ├── media/                   # 이미지 파일들
    │   └── image1.png
    └── theme/
        └── theme1.xml           # 테마 (색상, 폰트 스키마)
```

**핵심 규칙:**
- 새 파일(이미지 등)을 추가하면 `[Content_Types].xml`에 반드시 등록해야 함
- 이미지 참조 시 `document.xml.rels`에 Relationship ID가 필요

---

## 2. 네임스페이스 (Namespace)

document.xml의 루트 요소에 선언되며, 모든 요소에 접두사로 사용된다.

| 접두사 | URI | 용도 |
|--------|-----|------|
| `w:` | `http://schemas.openxmlformats.org/.../main` | **핵심** - 문단, 런, 표, 속성 등 |
| `r:` | `http://schemas.openxmlformats.org/.../relationships` | 관계 참조 (이미지 등) |
| `wp:` | `http://schemas.openxmlformats.org/.../wordprocessingDrawing` | 그림/도형 배치 |
| `wps:` | `http://schemas.microsoft.com/.../wordprocessingShape` | 도형 |
| `v:` | `urn:schemas-microsoft-com:vml` | 레거시 VML 도형 |
| `mc:` | `http://schemas.openxmlformats.org/markup-compatibility/2006` | 호환성 |

**규칙:** 네임스페이스 선언을 절대 삭제하면 안 됨. Word가 파일을 열 수 없게 됨.

---

## 3. 단위 체계

| 단위 | 설명 | 변환 |
|------|------|------|
| **DXA (twips)** | 대부분의 크기/간격 | 1인치 = 1440, 1cm ≈ 567 |
| **반포인트 (half-point)** | 글자 크기 (`w:sz`) | sz="20" → 10pt, sz="24" → 12pt |
| **EMU** | 그림/도형 크기 | 1인치 = 914,400 |
| **8분의 1 포인트** | 테두리 두께 (`w:sz` in borders) | sz="4" → 0.5pt |

---

## 4. 문단 구조 (Paragraph)

```xml
<w:p w:rsidR="00764084" w:rsidRDefault="007F280D" w:rsidP="00684787">
  <w:pPr>                          <!-- 문단 속성 -->
    <w:pStyle w:val="a5"/>          <!-- 스타일 참조 -->
    <w:spacing w:before="60" w:after="60" w:line="276" w:lineRule="auto"/>
    <w:ind w:left="200" w:hanging="100"/>   <!-- 들여쓰기 -->
    <w:jc w:val="center"/>          <!-- 정렬: left, center, right, both -->
    <w:rPr>                         <!-- 문단 기본 런 속성 -->
      <w:color w:val="000000"/>
    </w:rPr>
  </w:pPr>
  <w:r>                             <!-- 런 (텍스트 조각) -->
    <w:rPr>                         <!-- 런 속성 (글자 서식) -->
      <w:rFonts w:ascii="맑은 고딕" w:eastAsia="맑은 고딕" w:hAnsi="맑은 고딕"/>
      <w:b/>                        <!-- 볼드 -->
      <w:color w:val="0000FF"/>     <!-- 글자색 (RGB) -->
      <w:sz w:val="20"/>            <!-- 글자 크기 (반포인트) -->
    </w:rPr>
    <w:t xml:space="preserve">텍스트 내용</w:t>
  </w:r>
</w:p>
```

### 4.1 문단 속성 (w:pPr) 주요 요소

| 요소 | 용도 | 예시 |
|------|------|------|
| `w:pStyle` | 스타일 참조 | `w:val="Heading1"` |
| `w:spacing` | 줄간격/전후 간격 | `w:line="276" w:lineRule="auto"` |
| `w:ind` | 들여쓰기 | `w:left="200" w:hanging="100"` |
| `w:jc` | 정렬 | `"left"`, `"center"`, `"right"`, `"both"` |
| `w:numPr` | 번호매기기/불릿 | `w:numId`, `w:ilvl` |
| `w:sectPr` | 섹션 구분 (페이지 나눔) | 페이지 크기, 여백 등 |

**요소 순서 규칙:** `w:pPr` 안의 요소는 순서가 중요함
→ `w:pStyle` → `w:numPr` → `w:spacing` → `w:ind` → `w:jc` → `w:rPr` (마지막)

### 4.2 런 속성 (w:rPr) 주요 요소

| 요소 | 용도 | 값 |
|------|------|-----|
| `w:rFonts` | 폰트 | `w:ascii`, `w:eastAsia`, `w:hAnsi`, `w:cs` |
| `w:b` | 볼드 | 빈 태그 = true, `w:val="0"` = false |
| `w:i` | 이탤릭 | 빈 태그 = true |
| `w:u` | 밑줄 | `w:val="single"`, `"double"`, `"none"` |
| `w:color` | 글자색 | `w:val="0000FF"` (RGB 6자리) |
| `w:sz` | 크기 | 반포인트 (20 = 10pt) |
| `w:szCs` | 복합 스크립트 크기 | `w:sz`와 동일하게 설정 |
| `w:shd` | 형광펜/배경 | `w:fill="FFFF00"` |
| `w:spacing` | 자간 | twips 단위 |
| `w:highlight` | 하이라이트 | `w:val="yellow"` |

### 4.3 텍스트 요소 (w:t) 규칙

```xml
<!-- 공백이 있는 텍스트는 반드시 xml:space="preserve" 필요 -->
<w:t xml:space="preserve"> 앞뒤 공백 포함 </w:t>

<!-- 공백 없으면 생략 가능 -->
<w:t>공백없는텍스트</w:t>
```

**주의:** `\n` (줄바꿈)은 사용 불가. 새 줄은 새 `<w:p>` 요소로 만들어야 함.

---

## 5. 표 구조 (Table)

```xml
<w:tbl>
  <w:tblPr>                              <!-- 표 속성 -->
    <w:tblW w:w="9610" w:type="dxa"/>     <!-- 표 너비 -->
    <w:tblBorders>                        <!-- 테두리 -->
      <w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>
      <w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>
    </w:tblBorders>
    <w:tblLayout w:type="fixed"/>         <!-- fixed 또는 auto -->
  </w:tblPr>
  <w:tblGrid>                            <!-- ★ 열 격자 정의 -->
    <w:gridCol w:w="1968"/>
    <w:gridCol w:w="7646"/>
  </w:tblGrid>
  <w:tr>                                 <!-- 행 (Table Row) -->
    <w:trPr>
      <w:trHeight w:val="454"/>          <!-- 행 높이 -->
    </w:trPr>
    <w:tc>                               <!-- 셀 (Table Cell) -->
      <w:tcPr>
        <w:tcW w:w="1968" w:type="dxa"/> <!-- 셀 너비 -->
        <w:shd w:val="clear" w:color="auto" w:fill="CCCCCC"/> <!-- 배경색 -->
        <w:vAlign w:val="center"/>       <!-- 수직 정렬 -->
      </w:tcPr>
      <w:p>...</w:p>                     <!-- 셀 내용 (최소 1개 문단 필수) -->
    </w:tc>
  </w:tr>
</w:tbl>
```

### 5.1 셀 병합

**가로 병합 (gridSpan):**
```xml
<w:tc>
  <w:tcPr>
    <w:gridSpan w:val="3"/>   <!-- 3개 열 병합 -->
  </w:tcPr>
</w:tc>
```

**세로 병합 (vMerge):**
```xml
<!-- 병합 시작 셀 -->
<w:tc>
  <w:tcPr>
    <w:vMerge w:val="restart"/>  <!-- 시작 -->
  </w:tcPr>
  <w:p><w:r><w:t>내용</w:t></w:r></w:p>
</w:tc>

<!-- 병합 연속 셀 (다음 행에서) -->
<w:tc>
  <w:tcPr>
    <w:vMerge/>                  <!-- 값 없음 = 연속 -->
  </w:tcPr>
  <w:p/>                         <!-- 빈 문단 필수 -->
</w:tc>
```

### 5.2 표 편집 시 주의사항

1. **`w:tcPr`을 절대 삭제하지 말 것** - 셀 너비/병합 정보가 깨짐
2. **`w:tblGrid`의 열 수와 실제 셀 수가 일치해야 함** (gridSpan 고려)
3. **빈 셀에도 최소 `<w:p/>`가 필요** - 없으면 Word에서 오류
4. **테두리는 표 레벨 또는 셀 레벨 중 하나로 통일** - 혼합 시 예측 불가

---

## 6. 섹션 구분 (Section Break)

페이지 나눔은 `w:sectPr`로 정의된다.

```xml
<!-- 문단 안에 포함된 섹션 구분 -->
<w:p>
  <w:pPr>
    <w:sectPr>
      <w:pgSz w:w="11900" w:h="16820"/>              <!-- A4 크기 -->
      <w:pgMar w:top="1701" w:right="1134"
               w:bottom="1701" w:left="1134"
               w:header="720" w:footer="720"/>         <!-- 여백 -->
      <w:type w:val="continuous"/>                     <!-- 연속 / nextPage -->
      <w:cols w:space="720"/>                          <!-- 단 설정 -->
    </w:sectPr>
  </w:pPr>
</w:p>

<!-- 문서 마지막 sectPr은 body 직계 자식 -->
<w:body>
  ...
  <w:sectPr>...</w:sectPr>
</w:body>
```

**type 값:**
- `continuous`: 같은 페이지에서 섹션 구분
- `nextPage`: 다음 페이지에서 시작 (기본값)
- `oddPage` / `evenPage`: 홀수/짝수 페이지에서 시작

---

## 7. 스타일 시스템 (styles.xml)

```xml
<w:style w:type="paragraph" w:styleId="Heading1">
  <w:name w:val="heading 1"/>
  <w:basedOn w:val="Normal"/>        <!-- 상속 -->
  <w:next w:val="Normal"/>           <!-- 다음 문단 스타일 -->
  <w:pPr>...</w:pPr>                 <!-- 문단 기본 속성 -->
  <w:rPr>...</w:rPr>                 <!-- 런 기본 속성 -->
</w:style>
```

**스타일 타입:** `paragraph`, `character`, `table`, `numbering`

**이 문서에서 사용하는 주요 스타일 ID:**
| styleId | 이름 | 용도 |
|---------|------|------|
| `a` | Normal | 기본 문단 |
| `a3` | 제목 | 제목 스타일 |
| `a5` | 바탕글 | 본문 기본 |
| `TableParagraph` | Table Paragraph | 표 안 문단 |

---

## 8. 번호매기기 / 불릿 (numbering.xml)

**2단계 구조:**
1. `w:abstractNum` - 번호매기기 템플릿 정의 (9개 레벨)
2. `w:num` - 실제 참조 인스턴스

```xml
<!-- 문단에서 번호매기기 참조 -->
<w:p>
  <w:pPr>
    <w:numPr>
      <w:ilvl w:val="0"/>       <!-- 레벨 (0부터 시작) -->
      <w:numId w:val="10"/>     <!-- 번호매기기 인스턴스 ID -->
    </w:numPr>
  </w:pPr>
</w:p>
```

**번호 형식 (`w:numFmt`):** `bullet`, `decimal`, `lowerLetter`, `upperLetter`, `lowerRoman`

---

## 9. 이미지/그림

**관계 등록 (document.xml.rels):**
```xml
<Relationship Id="rId9" Type=".../image" Target="media/image1.png"/>
```

**문서에서 참조 (document.xml):**
```xml
<w:drawing>
  <wp:anchor>
    <a:graphic>
      <a:graphicData>
        <pic:pic>
          <pic:blipFill>
            <a:blip r:embed="rId9"/>  <!-- 관계 ID 참조 -->
          </pic:blipFill>
        </pic:pic>
      </a:graphicData>
    </a:graphic>
  </wp:anchor>
</w:drawing>
```

**Content_Types 등록:**
```xml
<Default Extension="png" ContentType="image/png"/>
```

---

## 10. 이 사업계획서 양식의 색상 코딩 규칙

| 색상 | RGB | 의미 | 프로그래밍 시 처리 |
|------|-----|------|-------------------|
| 파란색 | `0000FF` | 가이드/안내 텍스트 (삭제 대상) | AI 생성 콘텐츠로 교체 |
| 검정색 | `000000` | 정상 본문 텍스트 | 유지 |
| 회색 배경 | `CCCCCC` (fill) | 섹션 헤더 셀 배경 | 유지 (구조) |

**파란색 텍스트 탐지 패턴:**
```python
# w:r 요소에서 파란색 확인
rpr = run.find('{...}rPr')
color = rpr.find('{...}color')
if color.get('{...}val') == '0000FF':
    # → 가이드 텍스트 (교체 대상)
```

---

## 11. 프로그래밍 편집 시 절대 규칙

### 반드시 보존해야 할 것
1. **네임스페이스 선언** - 루트 요소의 xmlns 속성 전체
2. **rsid 속성** - `w:rsidR`, `w:rsidRDefault`, `w:rsidP` (변경 추적용)
3. **w:tblGrid** - 열 정의 (삭제하면 표 깨짐)
4. **w:tcPr** - 셀 속성 (삭제하면 병합/너비 깨짐)
5. **w:sectPr** - 페이지 구분 (삭제하면 페이지 레이아웃 깨짐)
6. **빈 셀의 `<w:p/>`** - 반드시 최소 1개 문단 필요

### 절대 하면 안 되는 것
1. `\n`으로 줄바꿈 → 새 `<w:p>` 요소 사용
2. 유니코드 불릿 문자 직접 삽입 → `w:numPr` 사용
3. `w:tblGrid` 열 수 변경 없이 셀 추가/삭제
4. `w:vMerge` 연속 셀에서 내용 삽입 (빈 문단만 가능)
5. 네임스페이스 접두사 없이 요소 생성

### 안전한 편집 패턴
```python
# 1. 기존 문단의 서식을 복사해서 새 문단 생성
# 2. w:t 텍스트만 교체 (w:rPr 서식 유지)
# 3. 표 셀 내용 교체 시 w:tcPr은 건드리지 않고 w:p만 교체
# 4. xml:space="preserve"를 공백 포함 텍스트에 반드시 설정
```

---

## 12. 참고 자료

- [ECMA-376 공식 규격](https://www.ecma-international.org/publications-and-standards/standards/ecma-376/)
- [ISO/IEC 29500 (Library of Congress)](https://www.loc.gov/preservation/digital/formats/fdd/fdd000395.shtml)
- [Microsoft Open XML SDK 문서](https://learn.microsoft.com/en-us/office/open-xml/open-xml-sdk)
- [Office Open XML 파일 형식 (Wikipedia)](https://en.wikipedia.org/wiki/Office_Open_XML_file_formats)
