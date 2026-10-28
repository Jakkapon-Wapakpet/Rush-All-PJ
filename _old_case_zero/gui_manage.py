#!/usr/bin/env python3
"""
GUI Manage Module - CASE ZERO (Bonus)
แท็บ "แฟ้มคดี" (ค้นหา กรอง เรียง เพิ่ม แก้ไข ลบ เพิ่มหลักฐาน) และแท็บ "รายงาน" (สถิติ)
ทุกการเปลี่ยนข้อมูลเรียกฟังก์ชันกลางใน cases.py / evidence.py ตัวเดียวกับเวอร์ชัน Terminal
Case-file and report tabs of the GUI, sharing the same rules as the terminal version.
"""

import tkinter as tk
from tkinter import ttk

from language import get_text
import cases
import evidence
from gui_theme import (COLORS, FONT, FONT_SMALL, FONT_BOLD, FONT_NAME, STATUS_STYLE,
                       ScrollableFrame, ask_confirm, flat_button, section_label, text_entry,
                       text_of, tk_safe, toggle_group, type_font)


def keep_only(rows: list, subset: list) -> list:
    """คืนเฉพาะคดีใน rows ที่อยู่ใน subset ด้วย (รักษาลำดับของ rows)"""
    wanted = {id(case) for case in subset}
    return [case for case in rows if id(case) in wanted]


class ManageView(tk.Frame):
    """แท็บแฟ้มคดี: ตารางคดีทางซ้าย และฟอร์มเพิ่ม/แก้ไขคดีพร้อมหลักฐานทางขวา"""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.selected = None          # คดีที่เลือกในตาราง (None = โหมดเพิ่มคดีใหม่)
        self.form_message = ("", COLORS["text"])
        self.evidence_message = ("", COLORS["text"])

        # ตัวกรองและการเรียง (คงค่าไว้แม้วาดหน้าจอใหม่)
        self.search_var = tk.StringVar()
        self.status_filter = tk.StringVar(value="all")
        self.difficulty_filter = tk.StringVar(value="all")
        self.sort_var = tk.StringVar(value="id")
        for variable in (self.search_var, self.status_filter, self.difficulty_filter, self.sort_var):
            variable.trace_add("write", lambda *args: self.render_table())

        # ช่องกรอกในฟอร์ม
        self.id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.difficulty_var = tk.StringVar(value="medium")
        self.status_var = tk.StringVar(value="open")
        self.evidence_name_var = tk.StringVar()
        self.evidence_desc_var = tk.StringVar()

        self.table = None
        self.configure_table_style()

    @staticmethod
    def configure_table_style() -> None:
        """ตกแต่งตาราง (ttk.Treeview) ให้เข้ากับธีมมืด"""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Case.Treeview", background=COLORS["panel"], fieldbackground=COLORS["panel"],
                        foreground=COLORS["text"], rowheight=34, font=FONT, borderwidth=0)
        style.configure("Case.Treeview.Heading", background=COLORS["panel_light"], foreground=COLORS["accent"],
                        font=FONT_BOLD, relief="flat", padding=6)
        style.map("Case.Treeview", background=[("selected", COLORS["accent"])],
                  foreground=[("selected", COLORS["ink"])])
        style.map("Case.Treeview.Heading", background=[("active", COLORS["disabled"])])

    # ---------- วาดหน้าจอ ----------

    def render(self) -> None:
        """วาดทั้งแท็บใหม่ (ใช้ตอนเปิดแท็บ เปลี่ยนภาษา และหลังเปลี่ยนข้อมูล)"""
        for widget in self.winfo_children():
            widget.destroy()

        # ขวา: ฟอร์ม (เลื่อนได้)
        self.form_area = ScrollableFrame(self, COLORS["panel"])
        self.form_area.config(width=460)
        self.form_area.pack(side="right", fill="y")
        self.form_area.pack_propagate(False)

        # ซ้าย: ตัวกรอง + ตาราง
        left = tk.Frame(self, bg=COLORS["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 16))

        top = tk.Frame(left, bg=COLORS["bg"])
        top.pack(fill="x")
        section_label(top, get_text("แฟ้มคดีทั้งหมด", "ALL CASE FILES"), COLORS["bg"], 14).pack(side="left")
        self.count_label = tk.Label(top, font=FONT_SMALL, bg=COLORS["bg"], fg=COLORS["muted"])
        self.count_label.pack(side="right")

        search_row = tk.Frame(left, bg=COLORS["bg"])
        search_row.pack(fill="x", pady=(10, 6))
        tk.Label(search_row, text=get_text("ค้นหา", "Search"), font=FONT_SMALL, width=8, anchor="w",
                 bg=COLORS["bg"], fg=COLORS["muted"]).pack(side="left")
        text_entry(search_row, self.search_var).pack(side="left", fill="x", expand=True)

        filters = (
            (get_text("สถานะ", "Status"), self.status_filter, [
                ("all", get_text("ทั้งหมด", "All")),
                ("open", get_text("กำลังสืบสวน", "Open")),
                ("closed", get_text("ปิดแล้ว", "Closed")),
                ("cold", get_text("คดีค้าง", "Cold")),
            ]),
            (get_text("ระดับ", "Level"), self.difficulty_filter, [
                ("all", get_text("ทั้งหมด", "All")),
                ("easy", cases.difficulty_text("easy")),
                ("medium", cases.difficulty_text("medium")),
                ("hard", cases.difficulty_text("hard")),
            ]),
            (get_text("เรียงตาม", "Sort by"), self.sort_var, [
                ("id", get_text("รหัส", "ID")),
                ("name", get_text("ชื่อ", "Name")),
                ("difficulty", get_text("ง่าย → ยาก", "Easy → Hard")),
            ]),
        )
        for label, variable, options in filters:
            row = tk.Frame(left, bg=COLORS["bg"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, font=FONT_SMALL, width=8, anchor="w",
                     bg=COLORS["bg"], fg=COLORS["muted"]).pack(side="left")
            toggle_group(row, variable, options, COLORS["bg"]).pack(side="left")

        columns = ("id", "name", "status", "difficulty", "evidence")
        self.table = ttk.Treeview(left, columns=columns, show="headings", style="Case.Treeview",
                                  selectmode="browse")
        headings = (
            ("id", get_text("รหัส", "ID"), 110),
            ("name", get_text("ชื่อคดี", "Case Name"), 220),
            ("status", get_text("สถานะ", "Status"), 140),
            ("difficulty", get_text("ระดับ", "Level"), 100),
            ("evidence", get_text("หลักฐาน", "Evidence"), 120),
        )
        for column, text, width in headings:
            self.table.heading(column, text=text, anchor="w")
            self.table.column(column, width=width, anchor="w", stretch=column == "name")
        for status, (mark, color) in STATUS_STYLE.items():
            self.table.tag_configure(status, foreground=color)
        self.table.pack(fill="both", expand=True, pady=(10, 0))
        self.table.bind("<<TreeviewSelect>>", self.on_select_row)

        self.render_table()
        self.render_form()

    def render_table(self) -> None:
        """เติมตารางตามคำค้น ตัวกรอง และการเรียงที่เลือก"""
        if self.table is None or not self.table.winfo_exists():
            return

        # ใช้ฟังก์ชันประมวลผลข้อมูลชุดเดียวกับเมนูรายงานใน Terminal
        rows = cases.sort_cases(self.sort_var.get())
        query = self.search_var.get().strip()
        if query:
            rows = keep_only(rows, cases.match_cases(query))
        if self.status_filter.get() != "all":
            rows = keep_only(rows, cases.filter_cases("สถานะ", self.status_filter.get()))
        if self.difficulty_filter.get() != "all":
            rows = keep_only(rows, cases.filter_cases("ระดับ", self.difficulty_filter.get()))

        self.table.delete(*self.table.get_children())
        for case in rows:
            mark = STATUS_STYLE.get(case["สถานะ"], ("", ""))[0]
            short_status = {"open": get_text("กำลังสืบสวน", "Open"),
                            "closed": get_text("ปิดแล้ว", "Closed"),
                            "cold": get_text("คดีค้าง", "Cold")}.get(case["สถานะ"], case["สถานะ"])
            self.table.insert("", "end", iid=case["รหัส"], tags=(case["สถานะ"],), values=(
                tk_safe(case["รหัส"]), text_of(case, "ชื่อ"), f"{mark} {short_status}",
                cases.difficulty_text(case["ระดับ"]), len(evidence.find_evidence_by_case(case["รหัส"]))
            ))

        if self.selected is not None and self.table.exists(self.selected["รหัส"]):
            self.table.selection_set(self.selected["รหัส"])
        self.count_label.config(text=get_text(
            f"แสดง {len(rows)} จาก {len(cases.get_all_cases())} คดี",
            f"Showing {len(rows)} of {len(cases.get_all_cases())} cases"
        ))

    def field_label(self, parent: tk.Widget, text: str) -> None:
        """ป้ายชื่อช่องกรอกในฟอร์ม"""
        tk.Label(parent, text=text, font=FONT_SMALL, bg=COLORS["panel"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(10, 3))

    def render_form(self) -> None:
        """ฟอร์มด้านขวา: เพิ่มคดีใหม่ หรือแก้ไขคดีที่เลือก พร้อมรายการหลักฐาน"""
        self.form_area.clear()
        form = tk.Frame(self.form_area.inner, bg=COLORS["panel"], padx=22, pady=18)
        form.pack(fill="both", expand=True)
        case = self.selected
        editing = case is not None

        if editing:
            title = get_text("แก้ไขคดี", "EDIT CASE")
            self.id_var.set(case["รหัส"])
            self.name_var.set(text_of(case, "ชื่อ"))
            self.difficulty_var.set(case["ระดับ"])
            self.status_var.set(case["สถานะ"])
        else:
            title = get_text("เพิ่มคดีใหม่", "NEW CASE")

        header = tk.Frame(form, bg=COLORS["panel"])
        header.pack(fill="x")
        section_label(header, title, COLORS["panel"], 16).pack(side="left")
        if editing:
            flat_button(header, get_text("+ คดีใหม่", "+ New"), self.on_new_case,
                        COLORS["panel_light"], COLORS["disabled"]).pack(side="right")

        self.field_label(form, get_text("รหัสคดี", "Case ID"))
        text_entry(form, self.id_var, state="disabled" if editing else "normal").pack(fill="x")

        self.field_label(form, get_text("ชื่อคดี", "Case Name"))
        text_entry(form, self.name_var).pack(fill="x")

        self.field_label(form, get_text("รายละเอียด", "Description"))
        self.desc_text = tk.Text(form, height=4, width=10, wrap="word", font=FONT, relief="flat", bd=6,
                                 bg=COLORS["panel_light"], fg=COLORS["text"], insertbackground=COLORS["text"],
                                 highlightthickness=1, highlightbackground=COLORS["panel_light"],
                                 highlightcolor=COLORS["accent"])
        self.desc_text.pack(fill="x")
        if editing:
            self.desc_text.insert("1.0", text_of(case, "รายละเอียด"))

        self.field_label(form, get_text("ระดับความยาก", "Difficulty"))
        toggle_group(form, self.difficulty_var, [(level, cases.difficulty_text(level))
                                                 for level in ("easy", "medium", "hard")],
                     COLORS["panel"]).pack(anchor="w")

        if editing:
            self.field_label(form, get_text("สถานะ", "Status"))
            toggle_group(form, self.status_var, [
                ("open", get_text("กำลังสืบสวน", "Open")),
                ("closed", get_text("ปิดแล้ว", "Closed")),
                ("cold", get_text("คดีค้าง", "Cold")),
            ], COLORS["panel"]).pack(anchor="w")

        text, color = self.form_message
        tk.Label(form, text=text, font=FONT_BOLD, wraplength=400, justify="left",
                 bg=COLORS["panel"], fg=color).pack(anchor="w", pady=(12, 0))

        buttons = tk.Frame(form, bg=COLORS["panel"])
        buttons.pack(fill="x", pady=(10, 0))
        flat_button(buttons, get_text("บันทึก", "SAVE"), self.on_save, COLORS["accent"], "#b8893a",
                    fg=COLORS["ink"]).pack(side="left")
        if editing:
            flat_button(buttons, get_text("ลบคดี", "DELETE"), self.on_delete,
                        COLORS["danger"], COLORS["danger_dark"]).pack(side="right")
            self.render_evidence_section(form, case)

    def render_evidence_section(self, form: tk.Frame, case: dict) -> None:
        """รายการหลักฐานของคดีที่เลือก และฟอร์มเพิ่มหลักฐาน"""
        linked = evidence.find_evidence_by_case(case["รหัส"])
        tk.Frame(form, bg=COLORS["panel_light"], height=1).pack(fill="x", pady=(22, 14))
        row = tk.Frame(form, bg=COLORS["panel"])
        row.pack(fill="x")
        section_label(row, get_text("หลักฐานของคดีนี้", "EVIDENCE"), COLORS["panel"], 14).pack(side="left")
        tk.Label(row, text=str(len(linked)), font=FONT_SMALL, bg=COLORS["panel"],
                 fg=COLORS["muted"]).pack(side="left", padx=8)

        if not linked:
            tk.Label(form, text=get_text("ยังไม่มีหลักฐาน", "No evidence yet."), font=FONT_SMALL,
                     bg=COLORS["panel"], fg=COLORS["muted"]).pack(anchor="w", pady=(6, 0))
        for evd in linked:
            item = tk.Frame(form, bg=COLORS["paper"], padx=10, pady=6)
            item.pack(fill="x", pady=3)
            tk.Label(item, text=evd["รหัส"], font=type_font("A", 10), bg=COLORS["paper"],
                     fg=COLORS["danger"]).pack(side="left")
            tk.Label(item, text=text_of(evd, "ชื่อ"), font=FONT_SMALL + ("bold",), wraplength=300,
                     justify="left", bg=COLORS["paper"], fg=COLORS["ink"]).pack(side="left", padx=8)

        self.field_label(form, get_text("ชื่อหลักฐานใหม่", "New evidence name"))
        text_entry(form, self.evidence_name_var).pack(fill="x")
        self.field_label(form, get_text("รายละเอียดหลักฐาน", "Evidence description"))
        text_entry(form, self.evidence_desc_var).pack(fill="x")

        text, color = self.evidence_message
        tk.Label(form, text=text, font=FONT_BOLD, bg=COLORS["panel"], fg=color).pack(anchor="w", pady=(8, 0))
        flat_button(form, get_text("+ เพิ่มหลักฐาน", "+ ADD EVIDENCE"), self.on_add_evidence,
                    COLORS["panel_light"], COLORS["disabled"]).pack(anchor="w", pady=(6, 0))

    # ---------- เหตุการณ์ ----------

    def clear_messages(self) -> None:
        """ล้างข้อความแจ้งผลในฟอร์ม"""
        self.form_message = ("", COLORS["text"])
        self.evidence_message = ("", COLORS["text"])

    def on_select_row(self, event) -> None:
        """คลิกแถวในตาราง: เปิดคดีนั้นในฟอร์มแก้ไข"""
        selection = self.table.selection()
        if not selection:
            return
        case = cases.find_case_by_id(selection[0])
        if case is None or case is self.selected:
            return
        self.selected = case
        self.clear_messages()
        self.evidence_name_var.set("")
        self.evidence_desc_var.set("")
        self.render_form()

    def on_new_case(self) -> None:
        """ล้างฟอร์มเพื่อเพิ่มคดีใหม่"""
        self.selected = None
        self.clear_messages()
        for variable in (self.id_var, self.name_var):
            variable.set("")
        self.difficulty_var.set("medium")
        self.table.selection_remove(*self.table.selection())
        self.render_form()

    def on_save(self) -> None:
        """บันทึกฟอร์ม: เพิ่มคดีใหม่ หรือแก้ไขคดีที่เลือก (ตรวจกฎด้วยฟังก์ชันกลางใน cases.py)"""
        case_id = self.id_var.get().strip()
        name = self.name_var.get().strip()
        description = self.desc_text.get("1.0", "end").strip()
        difficulty = self.difficulty_var.get()

        if self.selected is None:
            error = cases.validate_case_id(case_id) or cases.validate_case_fields(name, description, difficulty)
            if error:
                self.form_message = (error, COLORS["danger"])
                self.render_form()
                return
            self.selected = cases.create_case(case_id, name, description, difficulty)
            self.form_message = (get_text("เพิ่มคดีใหม่สำเร็จ", "Case added successfully."), COLORS["success"])
        else:
            # กฎ: ห้ามแก้ไขคดีที่ไม่มีอยู่จริง (เช่น ถูกลบไปแล้ว)
            if cases.find_case_by_id(self.selected["รหัส"]) is None:
                self.selected = None
                self.form_message = (get_text("ไม่พบคดี", "Case not found."), COLORS["danger"])
                self.render()
                return
            error = cases.validate_case_fields(name, description, difficulty)
            if error:
                self.form_message = (error, COLORS["danger"])
                self.render_form()
                return
            cases.update_case(self.selected, name, description, difficulty)
            if self.status_var.get() != self.selected["สถานะ"]:
                cases.set_case_status(self.selected, self.status_var.get())
            self.form_message = (get_text("แก้ไขข้อมูลคดีสำเร็จ", "Case updated successfully."), COLORS["success"])

        self.render_table()
        self.render_form()

    def on_delete(self) -> None:
        """ลบคดีที่เลือก (ถามยืนยันก่อน และหลักฐานของคดีจะถูกลบไปด้วย)"""
        case = self.selected
        linked = len(evidence.find_evidence_by_case(case["รหัส"]))
        message = f"[{case['รหัส']}] {text_of(case, 'ชื่อ')}"
        if linked:
            message += get_text(f"\n\nหลักฐานที่เกี่ยวข้อง {linked} รายการจะถูกลบไปด้วย",
                                f"\n\n{linked} linked evidence item(s) will also be deleted.")
        if not ask_confirm(self.app.root, get_text("ลบคดี?", "DELETE CASE?"), message):
            return

        if cases.find_case_by_id(case["รหัส"]) is not None:
            cases.remove_case(case)
        self.selected = None
        self.clear_messages()
        self.form_message = (get_text("ลบคดีสำเร็จ", "Case deleted successfully."), COLORS["success"])
        for variable in (self.id_var, self.name_var):
            variable.set("")
        self.render_table()
        self.render_form()

    def on_add_evidence(self) -> None:
        """เพิ่มหลักฐานให้คดีที่เลือก"""
        name = self.evidence_name_var.get().strip()
        desc = self.evidence_desc_var.get().strip()
        self.form_message = ("", COLORS["text"])

        # กฎ: หลักฐานต้องผูกกับคดีที่มีอยู่จริง และข้อมูลห้ามว่าง
        if self.selected is None or cases.find_case_by_id(self.selected["รหัส"]) is None:
            self.evidence_message = (get_text("ไม่พบคดี", "Case not found."), COLORS["danger"])
        elif not name or not desc:
            self.evidence_message = (get_text("กรุณากรอกข้อมูลให้ครบ", "Please fill in all fields."),
                                     COLORS["danger"])
        else:
            evidence.create_evidence(self.selected, name, desc)
            self.evidence_name_var.set("")
            self.evidence_desc_var.set("")
            self.evidence_message = (get_text("เพิ่มหลักฐานสำเร็จ", "Evidence added successfully."),
                                     COLORS["success"])
            self.render_table()

        self.render_form()


class ReportView(tk.Frame):
    """แท็บรายงาน: การ์ดตัวเลข อัตราปิดคดี และกราฟแท่งตามสถานะ/ระดับ"""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app

    def render(self) -> None:
        """วาดรายงานใหม่จาก cases.case_statistics()"""
        for widget in self.winfo_children():
            widget.destroy()
        stats = cases.case_statistics()

        section_label(self, get_text("รายงานการสืบสวน", "INVESTIGATION REPORT"),
                      COLORS["bg"], 16).pack(anchor="w")

        # แถวการ์ดตัวเลข
        tiles = tk.Frame(self, bg=COLORS["bg"])
        tiles.pack(fill="x", pady=(12, 0))
        tile_data = (
            (get_text("คดีทั้งหมด", "Total cases"), stats["total"], COLORS["text"]),
            (get_text("กำลังสืบสวน", "Open"), stats["open"], COLORS["accent"]),
            (get_text("ปิดคดีแล้ว", "Closed"), stats["closed"], COLORS["success"]),
            (get_text("คดีค้าง", "Cold"), stats["cold"], COLORS["cold"]),
            (get_text("หลักฐานทั้งหมด", "Evidence"), stats["evidence"], COLORS["text"]),
        )
        for column, (label, value, color) in enumerate(tile_data):
            tiles.columnconfigure(column, weight=1, uniform="tile")
            tile = tk.Frame(tiles, bg=COLORS["panel"], padx=18, pady=14)
            tile.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0))
            tk.Label(tile, text=label, font=FONT_SMALL, bg=COLORS["panel"], fg=COLORS["muted"]).pack(anchor="w")
            tk.Label(tile, text=str(value), font=("TkDefaultFont", 30, "bold"),
                     bg=COLORS["panel"], fg=color).pack(anchor="w")

        # อัตราปิดคดี + แถบความคืบหน้า
        rate_box = tk.Frame(self, bg=COLORS["panel"], padx=22, pady=16)
        rate_box.pack(fill="x", pady=12)
        row = tk.Frame(rate_box, bg=COLORS["panel"])
        row.pack(fill="x")
        tk.Label(row, text=get_text("อัตราปิดคดี", "Case closure rate"), font=FONT_BOLD,
                 bg=COLORS["panel"], fg=COLORS["text"]).pack(side="left")
        tk.Label(row, text=f"{stats['rate']:.1f}%", font=FONT_NAME,
                 bg=COLORS["panel"], fg=COLORS["success"]).pack(side="right")
        bar = tk.Canvas(rate_box, height=16, bg=COLORS["panel_light"], bd=0, highlightthickness=0)
        bar.pack(fill="x", pady=(10, 0))
        bar.bind("<Configure>", lambda event: self.draw_progress(bar, stats["rate"]))

        # กราฟแท่ง 2 กราฟ
        charts = tk.Frame(self, bg=COLORS["bg"])
        charts.pack(fill="both", expand=True)
        charts.columnconfigure((0, 1), weight=1, uniform="chart")
        self.bar_chart(charts, 0, get_text("คดีตามสถานะ", "CASES BY STATUS"), [
            (get_text("กำลังสืบสวน", "Open"), stats["open"], COLORS["accent"]),
            (get_text("ปิดคดีแล้ว", "Closed"), stats["closed"], COLORS["success"]),
            (get_text("คดีค้าง", "Cold"), stats["cold"], COLORS["cold"]),
        ], stats["total"])
        self.bar_chart(charts, 1, get_text("คดีตามระดับความยาก", "CASES BY DIFFICULTY"), [
            (cases.difficulty_text("easy"), stats["easy"], "#7fb069"),
            (cases.difficulty_text("medium"), stats["medium"], COLORS["accent"]),
            (cases.difficulty_text("hard"), stats["hard"], COLORS["danger"]),
        ], stats["total"])

    @staticmethod
    def draw_progress(canvas: tk.Canvas, rate: float) -> None:
        """วาดแถบเปอร์เซ็นต์ตามความกว้างปัจจุบันของ canvas"""
        canvas.delete("all")
        width = canvas.winfo_width() * rate / 100
        if width > 0:
            canvas.create_rectangle(0, 0, width, 16, fill=COLORS["success"], width=0)

    def bar_chart(self, parent: tk.Frame, column: int, title: str, items: list, total: int) -> None:
        """กราฟแท่งแนวนอน: items = [(ชื่อ, จำนวน, สี), ...]"""
        box = tk.Frame(parent, bg=COLORS["panel"], padx=22, pady=16)
        box.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0))
        section_label(box, title, COLORS["panel"], 12).pack(anchor="w", pady=(0, 10))

        for label, value, color in items:
            row = tk.Frame(box, bg=COLORS["panel"])
            row.pack(fill="x", pady=5)
            tk.Label(row, text=label, font=FONT, width=12, anchor="w",
                     bg=COLORS["panel"], fg=COLORS["text"]).pack(side="left")
            tk.Label(row, text=str(value), font=FONT_BOLD, width=3, anchor="e",
                     bg=COLORS["panel"], fg=color).pack(side="right")
            canvas = tk.Canvas(row, height=22, bg=COLORS["panel_light"], bd=0, highlightthickness=0)
            canvas.pack(side="left", fill="x", expand=True, padx=10)
            share = value / total * 100 if total else 0
            canvas.bind("<Configure>", lambda event, c=canvas, s=share, col=color: self.draw_bar(c, s, col))

    @staticmethod
    def draw_bar(canvas: tk.Canvas, share: float, color: str) -> None:
        """วาดแท่งเดียวตามสัดส่วน (%)"""
        canvas.delete("all")
        width = canvas.winfo_width() * share / 100
        if width > 0:
            canvas.create_rectangle(0, 0, width, 22, fill=color, width=0)
