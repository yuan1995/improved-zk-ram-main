#!/usr/bin/env python3
"""Generate a small PPTX explaining ROM + Set Membership -> RAM.

This intentionally avoids third-party dependencies so it works in a minimal
Python environment. It writes a valid Office Open XML .pptx package directly.
"""

from __future__ import annotations

import html
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ROM_Set_Membership_to_RAM.pptx"

SLIDE_W = 13_333_333
SLIDE_H = 7_500_000


def esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def emu(inches: float) -> int:
    return int(inches * 914400)


def rgb(hex_color: str) -> str:
    return hex_color.replace("#", "").upper()


def solid_fill(color: str) -> str:
    return f'<a:solidFill><a:srgbClr val="{rgb(color)}"/></a:solidFill>'


def line(color: str = "#1f2937", width: int = 12700) -> str:
    return f'<a:ln w="{width}">{solid_fill(color)}</a:ln>'


def no_line() -> str:
    return '<a:ln><a:noFill/></a:ln>'


def text_runs(
    lines: list[str],
    font_size: int = 24,
    color: str = "#111827",
    bold: bool = False,
    font: str = "Microsoft YaHei",
) -> str:
    paragraphs = []
    for line_text in lines:
        if line_text == "":
            paragraphs.append("<a:p><a:endParaRPr/></a:p>")
            continue
        bold_xml = ' b="1"' if bold else ""
        paragraphs.append(
            "<a:p>"
            f'<a:r><a:rPr lang="zh-CN" sz="{font_size * 100}"{bold_xml}>'
            f'{solid_fill(color)}'
            f'<a:latin typeface="{esc(font)}"/><a:ea typeface="{esc(font)}"/>'
            "</a:rPr>"
            f"<a:t>{esc(line_text)}</a:t></a:r>"
            "</a:p>"
        )
    return "".join(paragraphs)


class Slide:
    def __init__(self, title: str | None = None, subtitle: str | None = None):
        self.shapes: list[str] = []
        self.next_id = 2
        if title:
            self.textbox(0.55, 0.28, 12.2, 0.58, [title], 30, "#0f172a", True)
        if subtitle:
            self.textbox(0.62, 0.86, 11.9, 0.38, [subtitle], 14, "#475569")

    def _id(self) -> int:
        sid = self.next_id
        self.next_id += 1
        return sid

    def textbox(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        lines: list[str],
        font_size: int = 22,
        color: str = "#111827",
        bold: bool = False,
        fill: str | None = None,
        outline: str | None = None,
        radius: bool = False,
        margin_l: int = 91440,
        margin_r: int = 91440,
        font: str = "Microsoft YaHei",
    ) -> None:
        sid = self._id()
        fill_xml = solid_fill(fill) if fill else "<a:noFill/>"
        line_xml = line(outline, 9525) if outline else no_line()
        prst = "roundRect" if radius else "rect"
        self.shapes.append(
            f"""
<p:sp>
  <p:nvSpPr><p:cNvPr id="{sid}" name="TextBox {sid}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
    <a:prstGeom prst="{prst}"><a:avLst/></a:prstGeom>
    {fill_xml}
    {line_xml}
  </p:spPr>
  <p:txBody>
    <a:bodyPr wrap="square" lIns="{margin_l}" rIns="{margin_r}" tIns="45720" bIns="45720"/>
    <a:lstStyle/>
    {text_runs(lines, font_size, color, bold, font)}
  </p:txBody>
</p:sp>
"""
        )

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        text: str,
        fill: str = "#ffffff",
        outline: str = "#334155",
        font_size: int = 20,
        color: str = "#111827",
        bold: bool = False,
        radius: bool = True,
    ) -> None:
        self.textbox(
            x,
            y,
            w,
            h,
            [text],
            font_size,
            color,
            bold,
            fill=fill,
            outline=outline,
            radius=radius,
            margin_l=45720,
            margin_r=45720,
        )

    def table(
        self,
        x: float,
        y: float,
        rows: list[list[str]],
        col_widths: list[float],
        row_h: float = 0.34,
        font_size: int = 13,
        header_fill: str = "#dbeafe",
        cell_fill: str = "#ffffff",
        outline: str = "#64748b",
    ) -> None:
        for r, row in enumerate(rows):
            cx = x
            for c, txt in enumerate(row):
                fill = header_fill if r == 0 else cell_fill
                bold = r == 0
                self.textbox(
                    cx,
                    y + r * row_h,
                    col_widths[c],
                    row_h,
                    [txt],
                    font_size,
                    "#0f172a",
                    bold,
                    fill=fill,
                    outline=outline,
                    margin_l=36576,
                    margin_r=36576,
                )
                cx += col_widths[c]

    def arrow(self, x1: float, y1: float, x2: float, y2: float, color: str = "#2563eb") -> None:
        sid = self._id()
        self.shapes.append(
            f"""
<p:cxnSp>
  <p:nvCxnSpPr><p:cNvPr id="{sid}" name="Arrow {sid}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>
  <p:spPr>
    <a:xfrm><a:off x="{emu(min(x1, x2))}" y="{emu(min(y1, y2))}"/><a:ext cx="{abs(emu(x2 - x1))}" cy="{abs(emu(y2 - y1))}"/></a:xfrm>
    <a:prstGeom prst="straightConnector1"><a:avLst/></a:prstGeom>
    <a:ln w="28575">{solid_fill(color)}<a:tailEnd type="triangle"/></a:ln>
  </p:spPr>
</p:cxnSp>
"""
        )

    def xml(self) -> str:
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg><p:bgPr>{solid_fill("#f8fafc")}<a:effectLst/></p:bgPr></p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {''.join(self.shapes)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>
"""


def slide_title() -> Slide:
    s = Slide()
    s.textbox(0.75, 1.05, 11.8, 0.85, ["从 ROM 到 RAM"], 42, "#0f172a", True)
    s.textbox(
        0.8,
        2.0,
        11.6,
        0.75,
        ["把 PPT 里的 ROM 例子加上 Set Membership Queries，完成 read/write RAM"],
        23,
        "#334155",
    )
    s.rect(0.85, 3.15, 2.3, 0.7, "ROM", "#e0f2fe", "#0284c7", 22, "#075985", True)
    s.arrow(3.25, 3.5, 4.25, 3.5)
    s.rect(4.45, 3.15, 3.5, 0.7, "Set Membership", "#dcfce7", "#16a34a", 20, "#166534", True)
    s.arrow(8.15, 3.5, 9.15, 3.5)
    s.rect(9.35, 3.15, 2.5, 0.7, "RAM", "#fef3c7", "#d97706", 22, "#92400e", True)
    s.textbox(
        0.88,
        4.7,
        11.7,
        0.8,
        ["Two shuffles:  一个检查 RAM 的 reads ~ writes，另一个检查集合查询的 reads ~ writes"],
        21,
        "#1f2937",
        fill="#ffffff",
        outline="#cbd5e1",
        radius=True,
    )
    return s


def slide_pipeline() -> Slide:
    s = Slide("整体路线", "ROM 解决“读到的是初始化过的值”，Set Membership 解决“读到的是过去写入”。")
    boxes = [
        ("Permutation Proof", "证明两个日志只是重排：reads ~ writes", "#e0e7ff", "#4f46e5"),
        ("Read-Only Memory", "每次 lookup 读旧版本、写新版本", "#e0f2fe", "#0284c7"),
        ("Set Membership", "把集合元素当作 ROM key，value 为空", "#dcfce7", "#16a34a"),
        ("Read/Write RAM", "version 换成 timestamp，并检查 clock - t > 0", "#fef3c7", "#d97706"),
    ]
    x = 0.7
    for idx, (title, desc, fill, outline) in enumerate(boxes):
        s.rect(x, 2.0, 2.75, 0.65, title, fill, outline, 17, "#0f172a", True)
        s.textbox(x, 2.78, 2.75, 1.05, [desc], 14, "#334155", fill="#ffffff", outline="#e2e8f0", radius=True)
        if idx < len(boxes) - 1:
            s.arrow(x + 2.85, 2.33, x + 3.35, 2.33, "#64748b")
        x += 3.1
    s.textbox(
        0.8,
        5.15,
        11.7,
        0.95,
        [
            "核心观察：证明者 P 可以输入 old value 和 time；电路不直接维护大数组，",
            "而是用两个日志和一次集合查询，把每次访问的合法性批量锁住。"
        ],
        20,
        "#0f172a",
        fill="#ffffff",
        outline="#cbd5e1",
        radius=True,
    )
    return s


def slide_rom_example() -> Slide:
    s = Slide("PPT 中的 ROM 例子", "三格只读表，执行 LOAD(1), LOAD(0), LOAD(1)。")
    s.table(
        0.8,
        1.55,
        [["Key", "Value"], ["0", "x[0]"], ["1", "x[1]"], ["2", "x[2]"]],
        [1.1, 2.0],
        0.48,
        16,
    )
    s.textbox(
        4.2,
        1.45,
        3.7,
        2.25,
        [
            "每个 LOAD(i)：",
            "1. P 输入 value = y 和 version = v",
            "2. reads 加入 (i, y, v)",
            "3. writes 加入 (i, y, v+1)"
        ],
        17,
        "#0f172a",
        fill="#ffffff",
        outline="#cbd5e1",
        radius=True,
    )
    s.table(
        8.4,
        1.25,
        [
            ["Step", "writes 新增", "reads 新增"],
            ["setup", "(0,x[0],0)", ""],
            ["setup", "(1,x[1],0)", ""],
            ["setup", "(2,x[2],0)", ""],
            ["LOAD(1)", "(1,y0,v0+1)", "(1,y0,v0)"],
            ["LOAD(0)", "(0,y1,v1+1)", "(0,y1,v1)"],
            ["LOAD(1)", "(1,y2,v2+1)", "(1,y2,v2)"],
        ],
        [1.1, 1.85, 1.85],
        0.38,
        11,
    )
    s.textbox(
        0.85,
        5.55,
        11.6,
        0.65,
        ["Teardown 再把每个 key 的最后版本读掉，最后检查 reads ~ writes。"],
        21,
        "#0f172a",
        fill="#eff6ff",
        outline="#93c5fd",
        radius=True,
    )
    return s


def slide_rom_invariant() -> Slide:
    s = Slide("ROM 为什么成立", "版本链把每个 key 的所有读取连接回 setup。")
    s.rect(0.9, 2.05, 1.25, 0.6, "v0", "#e0f2fe", "#0284c7", 20, "#075985", True)
    s.arrow(2.25, 2.35, 3.25, 2.35, "#0284c7")
    s.rect(3.45, 2.05, 1.25, 0.6, "v1", "#e0f2fe", "#0284c7", 20, "#075985", True)
    s.arrow(4.8, 2.35, 5.8, 2.35, "#0284c7")
    s.rect(6.0, 2.05, 1.25, 0.6, "v2", "#e0f2fe", "#0284c7", 20, "#075985", True)
    s.arrow(7.35, 2.35, 8.35, 2.35, "#0284c7")
    s.rect(8.55, 2.05, 2.05, 0.6, "teardown", "#f8fafc", "#64748b", 17, "#334155", True)
    s.textbox(
        0.95,
        3.35,
        11.2,
        1.55,
        [
            "只要 reads ~ writes，P 不能凭空读一个 setup 不存在的 key。",
            "ROM 允许“读未来”：因为同一个 key 的 value 永远不变，未来版本仍然携带同一个 x[i]。",
            "但 RAM 不能这样做，因为 RAM 的 value 会被 STORE 改写。"
        ],
        22,
        "#0f172a",
        fill="#ffffff",
        outline="#cbd5e1",
        radius=True,
    )
    return s


def slide_set_membership() -> Slide:
    s = Slide("Set Membership Queries", "把集合当作 value 为空的 ROM；查询序列对应 LOAD(1), LOAD(0), LOAD(1)。")
    s.textbox(
        0.8,
        1.45,
        5.0,
        1.2,
        ["集合：S = {1, 2, 3}", "member(d) 等价于 lookup(d)", "记录 tuple: (key, version)"],
        24,
        "#0f172a",
        fill="#dcfce7",
        outline="#16a34a",
        radius=True,
    )
    s.table(
        6.5,
        1.25,
        [
            ["Query", "set_reads 新增", "set_writes 新增"],
            ["setup", "", "(1,0), (2,0), (3,0)"],
            ["member(1)", "(1,0)", "(1,1)"],
            ["member(2)", "(2,0)", "(2,1)"],
            ["member(2)", "(2,1)", "(2,2)"],
            ["teardown", "(1,1),(2,2),(3,0)", ""],
        ],
        [1.3, 1.9, 2.25],
        0.45,
        11,
    )
    s.textbox(
        0.8,
        2.95,
        5.0,
        1.5,
        [
            "本例查询来自 LOAD(1), LOAD(0), LOAD(1)：",
            "每次访问做一次 member(clock − t)，",
            "diff = 1, 2, 2，",
            "依次 member(1), member(2), member(2)。",
        ],
        15,
        "#0f172a",
        fill="#ffffff",
        outline="#bbf7d0",
        radius=True,
    )
    s.textbox(
        0.85,
        5.35,
        11.55,
        0.85,
        ["最后检查 set_reads ~ set_writes。若 d 不在 setup 的集合里，就无法补出一条完整版本链。"],
        21,
        "#0f172a",
        fill="#ffffff",
        outline="#bbf7d0",
        radius=True,
    )
    return s


def slide_why_set_for_ram() -> Slide:
    s = Slide("Set Membership 怎么补上 RAM", "把 ROM 的 version 换成 RAM 的 timestamp。")
    s.textbox(
        0.9,
        1.35,
        11.45,
        1.0,
        ["RAM 的危险点：P 可能声称读到了未来才写出的值。"],
        28,
        "#991b1b",
        True,
        fill="#fee2e2",
        outline="#ef4444",
        radius=True,
    )
    s.table(
        0.9,
        2.8,
        [
            ["ROM", "RAM"],
            ["tuple = (key, value, version)", "tuple = (address, value, time_written)"],
            ["只需 reads ~ writes", "还要证明 time_written < clock"],
            ["允许读未来", "禁止读未来"],
        ],
        [5.5, 5.5],
        0.55,
        16,
    )
    s.textbox(
        0.95,
        5.3,
        11.35,
        0.85,
        ["用集合 S = {1, ..., T} 检查：clock - t ∈ S。于是 clock - t > 0，也就是 t < clock。"],
        22,
        "#0f172a",
        fill="#fef3c7",
        outline="#f59e0b",
        radius=True,
    )
    return s


def slide_ram_setup() -> Slide:
    s = Slide("完整 RAM 例子", "初始内存和三次访问。")
    s.table(
        0.8,
        1.4,
        [["Address", "Initial value"], ["0", "10"], ["1", "20"], ["2", "30"]],
        [1.8, 2.1],
        0.5,
        16,
    )
    s.table(
        5.15,
        1.4,
        [["Clock", "Operation"], ["1", "LOAD(1)"], ["2", "STORE(0,99)"], ["3", "LOAD(0)"]],
        [1.5, 2.75],
        0.5,
        16,
        header_fill="#fef3c7",
    )
    s.textbox(
        0.85,
        4.45,
        11.6,
        1.2,
        [
            "RAM setup 写入：",
            "writes = [(0,10,0), (1,20,0), (2,30,0)]",
            "Set setup 写入：S = {1,2,3}，用于检查 clock - t。"
        ],
        22,
        "#0f172a",
        fill="#ffffff",
        outline="#cbd5e1",
        radius=True,
    )
    return s


def slide_ram_accesses() -> Slide:
    s = Slide("三次 Access 的日志", "每次访问都做 RAM 日志更新 + 一次集合成员查询。")
    s.table(
        0.4,
        1.25,
        [
            ["clock", "op", "P 输入 (old,t)", "RAM reads", "RAM writes", "clock-t", "Set query"],
            ["1", "LOAD(1)", "(20,0)", "(1,20,0)", "(1,20,1)", "1", "member(1)"],
            ["2", "STORE(0,99)", "(10,0)", "(0,10,0)", "(0,99,2)", "2", "member(2)"],
            ["3", "LOAD(0)", "(99,2)", "(0,99,2)", "(0,99,3)", "1", "member(1)"],
        ],
        [0.8, 1.45, 1.75, 1.55, 1.55, 0.85, 1.35],
        0.62,
        11,
        header_fill="#fef3c7",
    )
    s.textbox(
        0.75,
        4.5,
        5.8,
        1.15,
        ["LOAD: new = old", "STORE: new = w", "统一写法：new = old + op * (w - old)"],
        20,
        "#0f172a",
        fill="#ffffff",
        outline="#fbbf24",
        radius=True,
    )
    s.textbox(
        6.85,
        4.5,
        5.65,
        1.15,
        ["每次 member(clock-t) 只证明差值在 {1,2,3}。", "这就排除了 t >= clock 的未来读取。"],
        20,
        "#0f172a",
        fill="#ffffff",
        outline="#86efac",
        radius=True,
    )
    return s


def slide_teardown() -> Slide:
    s = Slide("Teardown 后的两次 Shuffle", "一个 shuffle 给 RAM，一个 shuffle 给 Set。")
    s.table(
        0.45,
        1.25,
        [
            ["RAM writes", "RAM reads"],
            ["(0,10,0)", "(1,20,0)"],
            ["(1,20,0)", "(0,10,0)"],
            ["(2,30,0)", "(0,99,2)"],
            ["(1,20,1)", "(0,99,3)"],
            ["(0,99,2)", "(1,20,1)"],
            ["(0,99,3)", "(2,30,0)"],
        ],
        [2.5, 2.5],
        0.39,
        12,
        header_fill="#fef3c7",
    )
    s.table(
        5.95,
        1.25,
        [
            ["Set writes", "来源", "Set reads", "来源"],
            ["(1,0)", "setup", "(1,0)", "member(1)"],
            ["(1,1)", "member(1)", "(1,1)", "member(1)"],
            ["(1,2)", "member(1)", "(1,2)", "teardown"],
            ["(2,0)", "setup", "(2,0)", "member(2)"],
            ["(2,1)", "member(2)", "(2,1)", "teardown"],
            ["(3,0)", "setup", "(3,0)", "teardown"],
        ],
        [1.45, 1.2, 1.45, 1.55],
        0.39,
        10,
        header_fill="#dcfce7",
    )
    s.textbox(
        0.8,
        5.25,
        11.65,
        0.75,
        ["检查 RAM reads ~ writes，同时检查 Set reads ~ writes；Set 表按 tuple 排序展示多重集合相等。"],
        22,
        "#0f172a",
        fill="#ffffff",
        outline="#cbd5e1",
        radius=True,
    )
    return s


def slide_soundness() -> Slide:
    s = Slide("为什么不用显式检查 latest write", "局部时间检查 + 全局 permutation 已经隐含了最新性。")
    s.textbox(
        0.85,
        1.4,
        3.75,
        3.2,
        [
            "1. RAM reads ~ writes",
            "",
            "每个读到的",
            "(addr, value, t)",
            "必须真的曾经写入。"
        ],
        21,
        "#0f172a",
        fill="#fef3c7",
        outline="#d97706",
        radius=True,
    )
    s.textbox(
        4.85,
        1.4,
        3.75,
        3.2,
        [
            "2. member(clock - t)",
            "",
            "读到的写入时间",
            "必须严格早于",
            "当前 clock。"
        ],
        21,
        "#0f172a",
        fill="#dcfce7",
        outline="#16a34a",
        radius=True,
    )
    s.textbox(
        8.85,
        1.4,
        3.75,
        3.2,
        [
            "3. 每次访问都写回",
            "",
            "LOAD 写回 old，",
            "STORE 写入 w，",
            "未读旧版本会在 shuffle 中暴露。"
        ],
        21,
        "#0f172a",
        fill="#e0f2fe",
        outline="#0284c7",
        radius=True,
    )
    s.textbox(
        0.95,
        5.25,
        11.35,
        0.8,
        ["因此每个地址始终只剩一个未读的最新写入；下一次访问若不读它，最终 reads ~ writes 无法同时成立。"],
        21,
        "#0f172a",
        fill="#ffffff",
        outline="#cbd5e1",
        radius=True,
    )
    return s


def slide_summary() -> Slide:
    s = Slide("总结", "从 PPT 的 ROM 例子到完整 RAM 的最短路径。")
    s.textbox(
        0.85,
        1.35,
        11.65,
        0.75,
        ["ROM: 维护 (key, value, version)，最后证明 reads ~ writes。"],
        23,
        "#075985",
        True,
        fill="#e0f2fe",
        outline="#38bdf8",
        radius=True,
    )
    s.textbox(
        0.85,
        2.45,
        11.65,
        0.75,
        ["Set Membership: 维护 (key, version)，member(d) 就是 lookup(d)。"],
        23,
        "#166534",
        True,
        fill="#dcfce7",
        outline="#4ade80",
        radius=True,
    )
    s.textbox(
        0.85,
        3.55,
        11.65,
        0.75,
        ["RAM: 维护 (address, value, timestamp)，并证明 clock - timestamp ∈ {1,...,T}。"],
        23,
        "#92400e",
        True,
        fill="#fef3c7",
        outline="#f59e0b",
        radius=True,
    )
    s.textbox(
        0.85,
        5.15,
        11.65,
        0.7,
        ["最终：two shuffles + 一个 load/store multiplexer = 常数开销 ZK RAM。"],
        25,
        "#0f172a",
        True,
        fill="#ffffff",
        outline="#cbd5e1",
        radius=True,
    )
    return s


def make_slides() -> list[Slide]:
    return [
        slide_title(),
        slide_pipeline(),
        slide_rom_example(),
        slide_rom_invariant(),
        slide_set_membership(),
        slide_why_set_for_ram(),
        slide_ram_setup(),
        slide_ram_accesses(),
        slide_teardown(),
        slide_soundness(),
        slide_summary(),
    ]


def content_types(nslides: int) -> str:
    slides = "\n".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, nslides + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  {slides}
</Types>
"""


def root_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""


def core_xml() -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:dcterms="http://purl.org/dc/terms/"
  xmlns:dcmitype="http://purl.org/dc/dcmitype/"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>ROM Set Membership to RAM</dc:title>
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>
"""


def app_xml(nslides: int) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
  xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex</Application>
  <PresentationFormat>Widescreen</PresentationFormat>
  <Slides>{nslides}</Slides>
  <Company>OpenAI</Company>
</Properties>
"""


def presentation_xml(nslides: int) -> str:
    slide_ids = "\n".join(
        f'<p:sldId id="{255 + i}" r:id="rId{i}"/>' for i in range(1, nslides + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId{nslides + 1}"/></p:sldMasterIdLst>
  <p:sldIdLst>{slide_ids}</p:sldIdLst>
  <p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="custom"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle/>
</p:presentation>
"""


def presentation_rels(nslides: int) -> str:
    rels = []
    for i in range(1, nslides + 1):
        rels.append(
            f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        )
    rels.append(
        f'<Relationship Id="rId{nslides + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    )
    rels.append(
        f'<Relationship Id="rId{nslides + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>'
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  {' '.join(rels)}
</Relationships>
"""


def slide_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>
"""


def master_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
  </p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>
"""


def master_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>
"""


def layout_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
  </p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>
"""


def layout_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>
"""


def theme_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="CodexClean">
  <a:themeElements>
    <a:clrScheme name="CodexClean">
      <a:dk1><a:srgbClr val="111827"/></a:dk1>
      <a:lt1><a:srgbClr val="F8FAFC"/></a:lt1>
      <a:dk2><a:srgbClr val="334155"/></a:dk2>
      <a:lt2><a:srgbClr val="FFFFFF"/></a:lt2>
      <a:accent1><a:srgbClr val="2563EB"/></a:accent1>
      <a:accent2><a:srgbClr val="16A34A"/></a:accent2>
      <a:accent3><a:srgbClr val="D97706"/></a:accent3>
      <a:accent4><a:srgbClr val="0284C7"/></a:accent4>
      <a:accent5><a:srgbClr val="9333EA"/></a:accent5>
      <a:accent6><a:srgbClr val="DC2626"/></a:accent6>
      <a:hlink><a:srgbClr val="2563EB"/></a:hlink>
      <a:folHlink><a:srgbClr val="7C3AED"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="CodexFonts">
      <a:majorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/><a:cs typeface="Arial"/></a:majorFont>
      <a:minorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/><a:cs typeface="Arial"/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="CodexFmt">
      <a:fillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"><a:tint val="50000"/><a:satMod val="300000"/></a:schemeClr></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"><a:tint val="20000"/><a:satMod val="255000"/></a:schemeClr></a:solidFill>
      </a:fillStyleLst>
      <a:lnStyleLst>
        <a:ln w="6350" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
        <a:ln w="12700" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
        <a:ln w="19050" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
      </a:lnStyleLst>
      <a:effectStyleLst>
        <a:effectStyle><a:effectLst/></a:effectStyle>
        <a:effectStyle><a:effectLst/></a:effectStyle>
        <a:effectStyle><a:effectLst/></a:effectStyle>
      </a:effectStyleLst>
      <a:bgFillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"><a:tint val="95000"/><a:satMod val="170000"/></a:schemeClr></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"><a:shade val="60000"/><a:satMod val="120000"/></a:schemeClr></a:solidFill>
      </a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
</a:theme>
"""


def build_pptx() -> None:
    slides = make_slides()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types(len(slides)))
        z.writestr("_rels/.rels", root_rels())
        z.writestr("docProps/core.xml", core_xml())
        z.writestr("docProps/app.xml", app_xml(len(slides)))
        z.writestr("ppt/presentation.xml", presentation_xml(len(slides)))
        z.writestr("ppt/_rels/presentation.xml.rels", presentation_rels(len(slides)))
        z.writestr("ppt/slideMasters/slideMaster1.xml", master_xml())
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", master_rels())
        z.writestr("ppt/slideLayouts/slideLayout1.xml", layout_xml())
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", layout_rels())
        z.writestr("ppt/theme/theme1.xml", theme_xml())
        for idx, slide in enumerate(slides, start=1):
            z.writestr(f"ppt/slides/slide{idx}.xml", slide.xml())
            z.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", slide_rels())


if __name__ == "__main__":
    build_pptx()
    print(OUT)
