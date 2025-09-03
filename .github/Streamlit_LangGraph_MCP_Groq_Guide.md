# Sử dụng Streamlit (FE) + LangGraph + **Groq API** + MCP (không cần Cursor Pro)

**Ngắn gọn:** Hoàn toàn khả thi. Dùng **Streamlit** (frontend) + **LangGraph** (điều phối flow) + **Groq API** (LLM) và gọi các **MCP server** (Pandoc/PDF/OCR/Excel/Filesystem) từ Python để xử lý spec và xuất test case vào Excel template — **không cần Cursor Pro**.

---

## 1) Kiến trúc (tiết kiệm chi phí)
- **Frontend:** Streamlit – form nhập cấu hình, upload spec, nút *Run flow*, thanh tiến độ, nút tải Excel.  
- **Orchestrator:** LangGraph – graph A→G (*parse_spec → checklist → testcases → export_excel*).  
- **LLM:** **Groq API** (chọn model phù hợp chi phí/độ chính xác, ví dụ *Llama 3.x 8B Instruct* cho draft, có thể nâng lên 70B khi cần).  
- **Tooling qua MCP (client Python):**
  - **Filesystem MCP**: đọc/ghi tệp cấu hình và artefacts.
  - **Pandoc MCP**: `.docx → .md/.txt`.
  - **PDF Reader MCP**: trích xuất text từ PDF.
  - **OCR MCP**: ảnh/screenshot → text.
  - **Excel MCP**: ghi **đúng range** vào sheet “test case”, copy sheet mẫu.

> App Streamlit kết nối tới MCP servers bằng Python SDK (stdio/SSE/HTTP). LLM gọi qua **Groq API** bằng SDK `groq`.

---

## 2) Quy trình A→G (triển khai với Streamlit + LangGraph + MCP + Groq)

### A. Khởi tạo project
- Nhập: tên dự án, phiên bản, tester, mapping cột Excel, đường dẫn template.  
- Lưu `project.json` (Filesystem MCP hoặc Python I/O).

### B. Chuẩn hoá spec
- `.docx → md`: Pandoc MCP.  
- `.pdf → text`: PDF Reader MCP.  
- `image → text`: OCR MCP.  
- (Nếu spec là `.xlsx` dạng bảng) dùng Excel MCP “read” vùng cần.  
- Gộp/ghi `spec.cleaned.md`.

### C. Sinh **checklist** (LLM qua Groq)
- Prompt yêu cầu JSON chuẩn `{id, title, module, priority}` từ `spec.cleaned.md`.  
- Lưu `checklist.draft.json`.

### D. Review checklist
- Hiển thị bảng trong Streamlit; người dùng sửa; lưu `checklist.approved.json`.

### E. Sinh **test case** (LLM qua Groq)
- Prompt ép **schema đúng tên cột sheet “test case”** (`TC_ID, Title, Precondition, Steps[], Expected, Priority, Module, ...`).  
- Lưu `testcases.draft.json` → người dùng sửa → `testcases.approved.json`.

### F. Review test case
- Sửa nhanh (reorder steps, priority, wording), chốt bản cuối.

### G. Export Excel (MCP)
- (Tuỳ chọn) `excel_copy_sheet` từ sheet mẫu sang sheet theo module.  
- `excel_write_to_sheet` ghi **values** vào vùng `A4:...` theo mapping cột; **không** đụng công thức/định dạng.

---

## 3) Mẫu code rút gọn

### 3.1 Gọi **Groq API** (Python)
```python
# pip install groq
import os
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

SYSTEM = "You are a senior QA who writes precise, structured test artifacts."

def llm_json(model: str, instructions: str, text: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"{instructions}\n\n=== INPUT ===\n{text}"}
    ]
    resp = client.chat.completions.create(
        model=model,  # ví dụ: "llama-3.1-8b-instant" hoặc "llama-3.1-70b-versatile"
        messages=messages,
        temperature=0.2,
        response_format={"type": "json_object"}  # ép JSON hợp lệ
    )
    return resp.choices[0].message.content  # JSON string
```

**Ví dụ hướng dẫn checklist (C):**
```python
CHECKLIST_INSTR = """
Hãy trích xuất CHECKLIST kiểm thử (happy/negative/boundary) từ INPUT.
Trả về JSON có dạng: {"items":[{"id": "...","title":"...","module":"...","priority":"High|Medium|Low"}]}
"""

checklist_json = llm_json("llama-3.1-8b-instant", CHECKLIST_INSTR, spec_text)
```

**Ví dụ hướng dẫn test case (E):**
```python
TC_INSTR = """
Sinh TEST CASE theo schema sheet 'test case':
- Keys: TC_ID, Title, Precondition, Steps (array of string), Expected, Priority, Module
- Mỗi mục checklist tạo >=1 TC; Steps đánh số 1.,2.,3. trong từng phần tử.
Trả về JSON: {"testcases":[{...}]}
"""
tcs_json = llm_json("llama-3.1-8b-instant", TC_INSTR, approved_checklist_text)
```

### 3.2 Kết nối **MCP server** từ Python
```python
# pip install "mcp[cli]"
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def connect_mcp(server_cmd: str, args: list[str]):
    params = StdioServerParameters(command=server_cmd, args=args, env=None)
    reader, writer = await stdio_client(params)
    session = await ClientSession(reader, writer).__aenter__()
    await session.initialize()
    return session
```

**Pandoc/PDF/OCR (B):**
```python
async def docx_to_md(pandoc_sess, infile, outfile):
    await pandoc_sess.call_tool("convert", {"file": infile, "to": "markdown", "out": outfile})

async def pdf_to_text(pdf_sess, pdf_path) -> str:
    res = await pdf_sess.call_tool("extract_text", {"file": pdf_path})
    return res.content[0].text

async def ocr_image(ocr_sess, img_path) -> str:
    res = await ocr_sess.call_tool("ocr_image", {"file": img_path, "lang": "eng+vie"})
    return res.content[0].text
```

**Excel MCP (G):**
```python
async def write_testcases(excel_sess, xlsx, sheet, start_row, rows_2d):
    end_row = start_row + len(rows_2d) - 1
    cols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:len(rows_2d[0])]
    rng = f"A{start_row}:{cols[-1]}{end_row}"
    await excel_sess.call_tool("excel_write_to_sheet", {
        "fileAbsolutePath": xlsx,
        "sheetName": sheet,
        "range": rng,
        "values": rows_2d
    })
```

### 3.3 LangGraph (sườn stateful)
```python
# pip install langgraph pydantic
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from typing import List, Dict

class State(BaseModel):
    meta: Dict = {}
    spec_text: str = ""
    checklist: List[Dict] = []
    testcases: List[Dict] = []

def parse_spec(state: State) -> State:  # B
    # ghép nội dung từ DOCX/PDF/IMG (đã OCR) vào state.spec_text
    return state

def make_checklist(state: State) -> State:  # C
    # gọi Groq API -> checklist JSON -> state.checklist
    return state

def make_testcases(state: State) -> State:  # E
    # gọi Groq API -> testcases JSON -> state.testcases
    return state

def export_excel(state: State) -> State:  # G
    # gọi Excel MCP -> ghi theo mapping cột/range
    return state

graph = StateGraph(State)
graph.add_node("parse_spec", parse_spec)
graph.add_node("make_checklist", make_checklist)
graph.add_node("make_testcases", make_testcases)
graph.add_node("export_excel", export_excel)
graph.set_entry_point("parse_spec")
graph.add_edge("parse_spec", "make_checklist")
graph.add_edge("make_checklist", "make_testcases")
graph.add_edge("make_testcases", "export_excel")
graph.add_edge("export_excel", END)
app = graph.compile()
```

### 3.4 Streamlit (UI)
```python
# pip install streamlit
import streamlit as st

st.title("Testcase Generator (Streamlit + LangGraph + Groq + MCP)")
proj = st.text_input("Project name")
template = st.text_input("Excel template path")
uploaded = st.file_uploader("Upload specs (.docx/.pdf/.png)", accept_multiple_files=True)

if st.button("Run flow"):
    with st.spinner("Running..."):
        # 1) chuẩn hoá spec (Pandoc/PDF/OCR MCP) -> spec_text
        # 2) Groq API -> checklist/testcases (JSON ép schema cột)
        # 3) Excel MCP -> ghi vào template (A4:... theo mapping)
        st.success("Done. Vui lòng kiểm tra file output trong thư mục outputs/.")
```

---

## 4) Tối ưu chi phí & hiệu năng với **Groq API**
- **Chọn model hợp lý:** dùng *Llama 3.x 8B* cho draft checklist/testcases; chỉ nâng cấp model lớn cho phần quan trọng.  
- **Giảm ngữ cảnh:** chunk/tóm tắt spec theo mục; truyền vào từng phần liên quan.  
- **Ép JSON ngắn/gọn:** tránh văn bản thừa; dùng `response_format={"type": "json_object"}`.  
- **Batching:** sinh TC theo module; ghi Excel theo lô (1k dòng/lần).  
- **Cache:** lưu `spec.cleaned.md`, checklist intermediate; tránh gọi lại khi không cần.

---

## 5) Lưu ý kỹ thuật
- **Biến môi trường:** `GROQ_API_KEY`; không commit lên repo.  
- **Schema/Mapping:** chốt tên **cột Excel** và **dòng bắt đầu** (vd. A4) để tránh lệch range/merge.  
- **Giữ template:** chỉ `write_to_sheet` (values); không tạo workbook mới → không phá công thức/format.  
- **OCR/PDF khó:** thêm bước *làm sạch* text (loại header/footer/số trang).  
- **Kiểm thử:** thêm bước “TC Lint” – bắt buộc có `Steps`, `Expected`, `Module`, `Priority`; cấm mô tả mơ hồ.

---

## 6) Checklist “Bắt đầu nhanh”
1) `pip install streamlit langgraph groq "mcp[cli]"`  
2) Khởi động MCP servers: Pandoc/PDF/OCR/Excel/Filesystem.  
3) Viết LangGraph nodes A→G; test riêng từng node.  
4) Gọi **Groq API** để sinh checklist/testcases (ép JSON).  
5) Dùng **Excel MCP** để ghi vào template theo mapping cột/range.

---

**Kết luận:** Giải pháp **Streamlit + LangGraph + Groq API + MCP** đáp ứng trọn quy trình A→G, tiết kiệm chi phí, dễ mở rộng. Bạn chỉ cần cung cấp **tên cột & dòng bắt đầu** của sheet “test case” để tôi soạn sẵn **schema + mapper** dùng ngay.
