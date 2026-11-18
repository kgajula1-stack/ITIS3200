"""Build the course project proposal, final report, and presentation files."""

from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from pptx import Presentation
from pptx.dml.color import RGBColor as SlideColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches as SlideInches, Pt as SlidePt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
NAVY = "17324D"
TEAL = "007C83"
LIGHT_BLUE = "EAF1F7"
GRAY = "526171"


PROPOSAL = [
    ("System", [
        "We will demonstrate a role-based access control (RBAC) retrofit for a "
        "multi-user task-tracking web application. Authenticated users create, "
        "read, update, and delete tasks; each task has an owner. In the broken "
        "state, logging in is incorrectly treated as permission to access every "
        "user's tasks. In the hardened state, regular users manage only their "
        "own tasks and administrators receive explicitly broader permissions."
    ]),
    ("Threat model", [
        "The attacker is a legitimate, authenticated standard user with a "
        "low-privilege account. The attacker can inspect ordinary HTTP requests, "
        "change task identifiers or other request parameters, bypass browser "
        "controls, and send direct requests. The attacker cannot access the "
        "server database or another user's credentials. The protected assets "
        "are task confidentiality and integrity, along with administrative "
        "operations."
    ]),
    ("Mechanism and rationale", [
        "The primary mechanism is server-side RBAC with user and admin roles, "
        "a role-to-permission policy, and ownership checks for regular users. "
        "A server-side reference-monitor pattern mediates protected task and "
        "administrative requests; unknown roles and permissions are denied. "
        "Authentication establishes who is making a request, while authorization "
        "decides whether that principal may perform this action on this task. "
        "The combination supports least privilege and protects confidentiality "
        "and integrity."
    ]),
    ("Broken state and demonstration", [
        "In the vulnerable, login-only baseline, User A changes a task ID in a "
        "direct request to target User B's task. The baseline allows the read or "
        "update because it checks login but not task ownership. We will replay "
        "the same request against the hardened app: the server returns "
        "403 Forbidden and stored task data remains unchanged. A same-owner "
        "request and an intended admin action will show that legitimate "
        "operations still work."
    ]),
]


REPORT_SECTIONS = [
    (
        "1. System and threat model",
        [
            "TaskFlow is a server-rendered Flask and SQLite task manager. "
            "Registered users authenticate with username and password, then "
            "create, view, update, and delete task records. Each task stores a "
            "creator/owner identifier (`created_by`), title, description, and "
            "workflow state. The protected assets are the confidentiality of "
            "task contents, the integrity of task records, user-role assignments, "
            "and administrator-only operations.",
            "The attacker is an authenticated standard user with a valid account. "
            "They can inspect ordinary HTTP traffic, alter a numeric task ID or "
            "form field, bypass the browser interface, and issue direct requests "
            "with an HTTP client. They cannot compromise the server, directly "
            "query its database, or use another user's credentials. The central "
            "threat is broken object-level authorization: authentication succeeds, "
            "but a request for another user's task is not checked against the "
            "requesting user's authority. This includes unauthorized reads and "
            "writes, direct route access, and attempts to reach an admin-only "
            "operation (OWASP, 2021).",
            "The security objective is not to hide task IDs. IDs are identifiers, "
            "not authorization secrets. The server must decide every request "
            "using the authenticated principal, requested action, role, and "
            "task ownership. This separates authentication (who is the user?) "
            "from authorization (may this user do this to this object?)."
        ],
    ),
    (
        "2. Mechanism design and policy",
        [
            "The primary mechanism is role-based access control. The `user` and "
            "`admin` roles map to explicit permissions in `todor/authz.py`. "
            "For standard users, resource permissions are additionally scoped "
            "to task ownership (`Todo.created_by == g.user.id`). Admin permissions "
            "allow cross-owner task management and access to the administrator "
            "task list. Role assignment is server-controlled; registration "
            "does not accept an admin role from client form data (Sandhu et al., "
            "1996).",
            "The supporting design is a server-side reference monitor: protected "
            "task requests are mediated at the route boundary and at the object "
            "authorization helper before task data is returned or mutated. The "
            "task list query also scopes records by owner. A deny-by-default "
            "permission map gives unknown roles no grants; routes require their "
            "declared permission. This supports least privilege: standard users "
            "receive only the task capabilities needed for their own work."
        ],
        [
            ["Principal", "Allowed actions in hardened mode"],
            ["Anonymous", "No task access; login required"],
            ["Standard user", "Create tasks; list/read/update/delete own tasks"],
            ["Admin", "Create and manage all tasks; view admin task list"],
            ["Unknown role", "No mapped permissions; deny"],
        ],
    ),
    (
        "3. Why the mechanisms address the threat",
        [
            "RBAC makes authorization policy explicit instead of treating a "
            "successful login as a universal grant. The permission map ties "
            "capabilities to roles, while the object-ownership check distinguishes "
            "two tasks reached through the same route. Role checks alone would "
            "not stop one standard user from targeting another standard user's "
            "record; ownership is the necessary object-level condition. Conversely, "
            "ownership alone would not represent admin-only capabilities.",
            "Complete mediation is necessary because the attacker controls the "
            "client. Hiding an edit button or filtering links cannot stop a direct "
            "GET or a forged POST. The app checks the task on both the read path "
            "and state-changing paths; update and delete do not rely on a prior "
            "page visit. The list query limits data returned to a standard user, "
            "but it is not a replacement for checks on individual task IDs.",
            "The resulting security properties are confidentiality (a standard "
            "user cannot read another user's task), integrity (they cannot alter "
            "or delete it), and least privilege (permissions are limited by role "
            "and ownership). Authentication remains a prerequisite, but it does "
            "not itself provide these properties. In the classroom demonstration, "
            "a known cross-owner task returns 403 so the authorization decision "
            "is observable; a nonexistent ID returns 404."
        ],
    ),
    (
        "4. Failure case and reproducible demonstration",
        [
            "The baseline intentionally keeps login but bypasses both the role "
            "policy and owner check. This models the proposal's broken state. "
            "After signing in as User A, requesting "
            "`GET /todo/update/<User-B-task-ID>` displays User B's title and "
            "description. A `POST` to the same route changes the task, and a "
            "`POST /todo/delete/<User-B-task-ID>` can remove it. The numeric ID "
            "is not a capability; the failure is the server's missing "
            "authorization decision.",
            "In hardened mode, replay the identical request while signed in as "
            "User A. `authorize_todo` verifies the action permission and owner "
            "before the route renders or commits a change. The response is 403 "
            "and the database record remains unchanged. The control case signs "
            "in as User A and performs the same operation on User A's task; it "
            "succeeds. The role case shows an admin can access the all-task view, "
            "while a standard user receives 403 from `/todo/admin/tasks`.",
            "The baseline is opt-in and bound to `127.0.0.1`; an additional "
            "request guard rejects non-loopback source addresses. The seeder "
            "creates synthetic local accounts and tasks from the sum of four "
            "member suffixes modulo 11. The README documents both server "
            "commands, seed and reset steps, test credentials, task IDs, and "
            "expected outcomes. The baseline must never be deployed or used "
            "with real data."
        ],
    ),
    (
        "5. Implementation evidence, limits, and conclusion",
        [
            "The implementation separates policy (`todor/authz.py`), routes "
            "(`todor/todo.py`), data model (`todor/models.py`), and app mode "
            "configuration. The hardened mode is the default. Tests exercise "
            "cross-owner read/update/delete denial and unchanged data, baseline "
            "cross-owner access, same-owner operations, admin access, anonymous "
            "redirects, unknown-role denial, registration role assignment, the "
            "loopback restriction, and seed validation. In this execution "
            "environment, all 11 unittest cases passed; both demo entry points "
            "also returned HTTP 200 on their landing pages. Students should "
            "rerun these checks after cloning the public repository. The "
            "hardened version is intended for "
            "https://github.com/kgajula1-stack/ITIS3200/tree/hardened/courseproject; "
            "the login-only comparison is maintained on the separate "
            "baseline branch.",
            "The demonstration is intentionally limited. It is not a production "
            "deployment and does not add CSRF protection, rate limiting, "
            "production secrets management, or a full migrations framework. "
            "The baseline's 403-versus-404 distinction is useful for teaching "
            "but can reveal whether a forbidden object exists; a real service "
            "may choose a uniform 404. The route-level policy is explicit, so "
            "each future protected route must invoke the permission or ownership "
            "helper. Tests cover current task and admin endpoints, not arbitrary "
            "future routes.",
            "The comparison demonstrates the core lesson: a login check proves "
            "identity, not authority. Mapping permissions to roles, checking "
            "ownership for each object action, and denying unmapped access "
            "changes an ID-tampering attack from a successful read or write "
            "into a rejected request without changing legitimate owner or admin "
            "behavior (Course Lab05 access-control material)."
        ],
    ),
]


REFERENCES = [
    "Course project handout and grading rubric, supplied by the course. "
    "Project brief: system/threat description, mechanism design, justification, "
    "failure case, AI Appendix, and deliverables.",
    "Course Lab05 access-control material, as identified in the approved topic "
    "proposal. The project applies access-control concepts as an RBAC retrofit.",
    "Sandhu, R. S., Coyne, E. J., Feinstein, H. L., and Youman, C. E. "
    "\"Role-Based Access Control Models.\" IEEE Computer, 29(2), 1996, pp. 38-47.",
    "OWASP Foundation. \"A01:2021 – Broken Access Control.\" "
    "https://owasp.org/Top10/A01_2021-Broken_Access_Control/",
    "OWASP Foundation. \"Authorization Cheat Sheet.\" "
    "https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html",
]


AI_APPENDIX = [
    "AI assistance was used to expand the project plan, implement and test the "
    "RBAC demonstration, draft README instructions, and prepare this report and "
    "presentation. The prompts included: (1) “improve the plan, reread the md "
    "file closely and figure out all the deliverables and steps that are needed "
    "to get full points”; (2) provision of the course project brief, grading "
    "rubric, and approved proposal, with the instruction that the approved "
    "proposal contents must be retained; and (3) “ok continue” to resume "
    "implementation of the plan. Follow-up work asked for testable code and "
    "reproducible project deliverables.",
    "AI-generated or AI-assisted parts include implementation scaffolding, "
    "authorization tests, the seeding utility, README, and drafts of the "
    "proposal/report/presentation. The code was exercised with 11 automated "
    "tests and both local server entry points were checked for an HTTP 200 "
    "landing-page response in the available environment. Those checks are "
    "tool-run evidence, not a claim that every group member independently "
    "reviewed the security logic.",
    "Before submission, the students must inspect the permission map and every "
    "protected route, verify the live baseline and hardened trace, review all "
    "claims and citations, and record any changes they make. Each student "
    "should replace this note with the accurate account of which security "
    "logic they personally modified or verified, as required by the course. "
    "No additional security library beyond the project's existing Flask and "
    "SQLAlchemy stack was introduced for the authorization mechanism."
]


SLIDES = [
    {
        "title": "Login is not authorization",
        "subtitle": "RBAC retrofit for a multi-user task app",
        "time": "0:40",
        "bullets": [
            "One system, two modes: login-only baseline vs. hardened RBAC",
            "Question: can an authenticated user change a task ID to access another user's data?",
            "Goal: show the attack, the policy, and the observable fix",
        ],
        "notes": "Open with the core distinction: authentication establishes identity; authorization decides what that identity may do. State that this is a controlled local demonstration, not a production system.",
    },
    {
        "title": "System and threat model",
        "time": "1:00",
        "bullets": [
            "Assets: task contents, task integrity, role-restricted admin actions",
            "Attacker: valid standard-user account",
            "Capabilities: inspect and alter IDs/forms; send direct HTTP requests",
            "Assumptions: no database/server compromise or stolen credentials",
        ],
        "notes": "Explain the attacker controls the browser and request, but not the server. An object ID is not a secret or proof of authority. Scope to authenticated IDOR and missing authorization.",
    },
    {
        "title": "RBAC policy",
        "time": "1:00",
        "bullets": [
            "Standard user: create tasks; read/update/delete own tasks",
            "Admin: manage all tasks and open the admin task list",
            "Every user-task action checks both permission and ownership",
            "Unknown roles/permissions: deny",
        ],
        "notes": "Clarify RBAC role grants alone are not enough for object-level access. Ownership is a resource-specific condition for standard users. Admin receives only the explicitly mapped broader permissions.",
    },
    {
        "title": "Where enforcement happens",
        "time": "1:10",
        "bullets": [
            "todor/authz.py: permission map + task ownership policy",
            "todor/todo.py: list/create/read/update/delete/admin routes",
            "Server checks each protected request; UI visibility is not security",
            "Role comes from server-side user data, never form input",
        ],
        "notes": "Point out the complete mediation path: list and create use permission checks; update chooses read vs update based on method, then authorizes task; delete authorizes before deletion; admin view requires admin permission. New protected routes must invoke policy helpers.",
    },
    {
        "title": "Failure case: IDOR succeeds",
        "time": "1:20",
        "bullets": [
            "Baseline still requires login, but bypasses role and owner checks",
            "Sign in as User A; request /todo/update/<User-B-task-ID>",
            "GET reveals User B's task; POST changes it",
            "The server mistakes authentication for authorization",
        ],
        "notes": "Live demo: use printed synthetic credentials. Show baseline port 5001, User A, User B task ID. GET first, then POST the edit; refresh as User B or inspect the record to prove stored data changed. Do not use real accounts/data.",
    },
    {
        "title": "Hardened case: same request denied",
        "time": "1:25",
        "bullets": [
            "Replay the identical cross-owner request on port 5000",
            "Hardened server returns 403 before rendering or mutation",
            "Verify User B's title remains unchanged",
            "Same-owner task operation still succeeds",
        ],
        "notes": "Use same task ID and same User A login against the hardened server. Show 403 and unchanged title. Then show User A can access and update their own task. Mention the classroom response is 403 for clarity; a production system may mask existence with 404.",
    },
    {
        "title": "Admin and regression evidence",
        "time": "1:00",
        "bullets": [
            "Admin can list and manage both users' tasks",
            "Standard user is denied /todo/admin/tasks",
            "11 automated tests cover baseline, RBAC, roles, ownership, seed guard",
            "Both local launchers returned HTTP 200",
        ],
        "notes": "Show admin view briefly. Report evidence accurately: tests were run in this development environment, and both servers' landing pages responded. The group should rerun tests from a clean checkout before presenting.",
    },
    {
        "title": "What this does not solve",
        "time": "0:50",
        "bullets": [
            "No CSRF defense, login rate limiting, or production secrets setup",
            "Explicit route policy must be applied to future protected routes",
            "403 vs. 404 may disclose whether a task ID exists",
            "Baseline is loopback-only and must never be deployed",
        ],
        "notes": "Show understanding, not overclaiming. Describe the controls as a focused course demonstration. Stress the baseline warning and residual risks.",
    },
    {
        "title": "Takeaway and Q&A",
        "time": "1:35",
        "bullets": [
            "Login proves who; role + ownership decide what",
            "Complete mediation protects direct requests, not only UI clicks",
            "Demonstration: baseline succeeds; RBAC rejects; owner/admin flows work",
            "Q&A: defend threat assumptions, policy, evidence, and limitations",
        ],
        "notes": "Close with the exact security lesson. Reserve the formal two-minute Q&A after the 10-minute presentation. Likely questions: why roles plus ownership, why 403, what if a route forgets the helper, how is admin assigned, and what remains out of scope.",
    },
]


def set_doc_defaults(document, compact=False):
    section = document.sections[0]
    section.top_margin = Inches(0.55 if compact else 0.65)
    section.bottom_margin = Inches(0.55 if compact else 0.65)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)
    normal = document.styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(9.2 if compact else 9.5)
    normal.font.color.rgb = RGBColor.from_string("263746")
    normal.paragraph_format.space_after = Pt(4)
    normal.paragraph_format.line_spacing = 1.03
    for style_name, size, color in (
        ("Title", 24, NAVY),
        ("Heading 1", 15, NAVY),
        ("Heading 2", 11.5, TEAL),
    ):
        style = document.styles[style_name]
        style.font.name = "Aptos Display"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)


def add_doc_title(document, title, subtitle):
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(title)
    run.bold = True
    run.font.size = Pt(22)
    run.font.color.rgb = RGBColor.from_string(NAVY)
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(subtitle)
    run.italic = True
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor.from_string(GRAY)


def make_proposal_docx(path):
    document = Document()
    set_doc_defaults(document, compact=True)
    add_doc_title(
        document,
        "RBAC Retrofit for a Multi-User Task App",
        "Course Project Proposal | Approved topic, refined for implementation",
    )
    for heading, paragraphs in PROPOSAL:
        document.add_heading(heading, level=2)
        for text in paragraphs:
            document.add_paragraph(text)
    document.save(path)


def add_doc_table(document, rows):
    table = document.add_table(rows=0, cols=len(rows[0]))
    table.style = "Light Shading Accent 1"
    for row_index, row_data in enumerate(rows):
        cells = table.add_row().cells
        for column, value in enumerate(row_data):
            cells[column].text = value
            for paragraph in cells[column].paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(8.5)
                    if row_index == 0:
                        run.bold = True
                        run.font.color.rgb = RGBColor.from_string(NAVY)


def make_report_docx(path):
    document = Document()
    set_doc_defaults(document)
    add_doc_title(
        document,
        "Role-Based Access Control Retrofit",
        "Security Mechanisms in Practice | Final Report",
    )
    p = document.add_paragraph(
        "Group 1 | Multi-user task management | Baseline and hardened demonstration"
    )
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].font.color.rgb = RGBColor.from_string(GRAY)
    for section_index, (heading, paragraphs, *table_data) in enumerate(REPORT_SECTIONS):
        if section_index:
            document.add_page_break()
        document.add_heading(heading, level=1)
        for paragraph_text in paragraphs:
            document.add_paragraph(paragraph_text)
        if table_data:
            add_doc_table(document, table_data[0])

    document.add_page_break()
    document.add_heading("References", level=1)
    for reference in REFERENCES:
        document.add_paragraph(reference, style="List Number")
    document.add_page_break()
    document.add_heading("AI Appendix: Usage and disclosure", level=1)
    for paragraph_text in AI_APPENDIX:
        document.add_paragraph(paragraph_text)
    document.save(path)


def report_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=20, leading=24, textColor=colors.HexColor("#" + NAVY),
            alignment=TA_CENTER, spaceAfter=6,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle", parent=base["Normal"], fontSize=9, leading=12,
            textColor=colors.HexColor("#" + GRAY), alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "heading": ParagraphStyle(
            "ReportHeading", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=13, leading=16, textColor=colors.HexColor("#" + NAVY),
            spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "ReportBody", parent=base["BodyText"], fontName="Helvetica",
            fontSize=8.8, leading=11.2, textColor=colors.HexColor("#263746"),
            spaceAfter=6,
        ),
        "table": ParagraphStyle(
            "ReportTable", parent=base["BodyText"], fontSize=8, leading=10,
            textColor=colors.HexColor("#263746"),
        ),
        "reference": ParagraphStyle(
            "Reference", parent=base["BodyText"], fontSize=9.2, leading=13,
            leftIndent=18, firstLineIndent=-18, spaceAfter=9,
        ),
    }


def add_pdf_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D7E1EA"))
    canvas.line(0.7 * inch, 0.48 * inch, 7.8 * inch, 0.48 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#" + GRAY))
    canvas.drawString(0.7 * inch, 0.31 * inch, "RBAC Retrofit | Course Project")
    canvas.drawRightString(7.8 * inch, 0.31 * inch, f"{doc.page}")
    canvas.restoreState()


def make_proposal_pdf(path):
    styles = report_styles()
    story = [
        Paragraph("RBAC Retrofit for a Multi-User Task App", styles["title"]),
        Paragraph(
            "Course Project Proposal | Approved topic, refined for implementation",
            styles["subtitle"],
        ),
    ]
    proposal_heading = ParagraphStyle(
        "ProposalHeading", parent=styles["heading"], fontSize=11, leading=14,
        spaceBefore=3, spaceAfter=4,
    )
    proposal_body = ParagraphStyle(
        "ProposalBody", parent=styles["body"], fontSize=9.1, leading=12,
        spaceAfter=7,
    )
    for heading, paragraphs in PROPOSAL:
        story.append(Paragraph(escape(heading), proposal_heading))
        story.extend(Paragraph(escape(text), proposal_body) for text in paragraphs)
    doc = SimpleDocTemplate(
        str(path), pagesize=letter, rightMargin=0.76 * inch,
        leftMargin=0.76 * inch, topMargin=0.62 * inch, bottomMargin=0.62 * inch,
        title="RBAC Retrofit - Project Proposal",
        author="Group 1",
    )
    doc.build(story, onFirstPage=add_pdf_footer, onLaterPages=add_pdf_footer)


def make_report_pdf(path):
    styles = report_styles()
    story = [
        Paragraph("Role-Based Access Control Retrofit", styles["title"]),
        Paragraph(
            "Security Mechanisms in Practice | Final Report<br/>"
            "Group 1 | Multi-user task management | Baseline and hardened demonstration",
            styles["subtitle"],
        ),
    ]
    for section_index, (heading, paragraphs, *table_data) in enumerate(REPORT_SECTIONS):
        if section_index:
            story.append(PageBreak())
        story.append(Paragraph(escape(heading), styles["heading"]))
        story.extend(
            Paragraph(escape(text), styles["body"]) for text in paragraphs
        )
        if table_data:
            rows = [
                [Paragraph(escape(cell), styles["table"]) for cell in row]
                for row in table_data[0]
            ]
            table = Table(rows, colWidths=[1.25 * inch, 5.65 * inch], repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#" + LIGHT_BLUE)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#" + NAVY)),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD7E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.extend([Spacer(1, 5), table])
    story.extend([PageBreak(), Paragraph("References", styles["heading"])])
    for reference in REFERENCES:
        story.append(Paragraph(reference, styles["reference"]))
    story.extend([
        PageBreak(),
        Paragraph("AI Appendix: Usage and disclosure", styles["heading"]),
    ])
    story.extend(Paragraph(escape(text), styles["body"]) for text in AI_APPENDIX)
    doc = SimpleDocTemplate(
        str(path), pagesize=letter, rightMargin=0.7 * inch,
        leftMargin=0.7 * inch, topMargin=0.62 * inch, bottomMargin=0.65 * inch,
        title="Role-Based Access Control Retrofit - Final Report",
        author="Group 1",
    )
    doc.build(story, onFirstPage=add_pdf_footer, onLaterPages=add_pdf_footer)


def add_slide_notes(slide, notes):
    slide.notes_slide.notes_text_frame.text = notes


def make_presentation(path):
    presentation = Presentation()
    presentation.slide_width = SlideInches(13.333)
    presentation.slide_height = SlideInches(7.5)
    blank = presentation.slide_layouts[6]
    for index, content in enumerate(SLIDES):
        slide = presentation.slides.add_slide(blank)
        background = slide.background.fill
        background.solid()
        background.fore_color.rgb = SlideColor(248, 250, 252)

        from pptx.enum.shapes import MSO_SHAPE

        accent = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, SlideInches(0.2), presentation.slide_height
        )
        accent.fill.solid()
        accent.fill.fore_color.rgb = SlideColor(0, 124, 131)
        accent.line.fill.background()

        title_box = slide.shapes.add_textbox(
            SlideInches(0.72), SlideInches(0.52),
            SlideInches(11.9), SlideInches(0.82),
        )
        title_frame = title_box.text_frame
        title_frame.text = content["title"]
        title_run = title_frame.paragraphs[0].runs[0]
        title_run.font.name = "Aptos Display"
        title_run.font.size = SlidePt(30)
        title_run.font.bold = True
        title_run.font.color.rgb = SlideColor(23, 50, 77)

        if content.get("subtitle"):
            subtitle = slide.shapes.add_textbox(
                SlideInches(0.76), SlideInches(1.55),
                SlideInches(11.6), SlideInches(0.55),
            )
            frame = subtitle.text_frame
            frame.text = content["subtitle"]
            run = frame.paragraphs[0].runs[0]
            run.font.size = SlidePt(19)
            run.font.color.rgb = SlideColor(0, 124, 131)
            top = 2.45
        else:
            top = 1.65

        bullets = slide.shapes.add_textbox(
            SlideInches(0.95), SlideInches(top),
            SlideInches(11.3), SlideInches(4.75),
        )
        frame = bullets.text_frame
        frame.clear()
        frame.word_wrap = True
        for bullet_index, text in enumerate(content["bullets"]):
            paragraph = frame.paragraphs[0] if bullet_index == 0 else frame.add_paragraph()
            paragraph.text = text
            paragraph.level = 0
            paragraph.font.size = SlidePt(22 if len(content["bullets"]) < 5 else 20)
            paragraph.font.color.rgb = SlideColor(38, 55, 70)
            paragraph.space_after = SlidePt(22)

        footer = slide.shapes.add_textbox(
            SlideInches(0.75), SlideInches(7.02),
            SlideInches(11.9), SlideInches(0.28),
        )
        footer_frame = footer.text_frame
        footer_frame.text = (
            f"RBAC Retrofit  |  {content['time']}  |  Slide {index + 1}/{len(SLIDES)}"
        )
        footer_p = footer_frame.paragraphs[0]
        footer_p.alignment = PP_ALIGN.RIGHT
        footer_p.font.size = SlidePt(10)
        footer_p.font.color.rgb = SlideColor(82, 97, 113)
        add_slide_notes(slide, content["notes"])
    presentation.save(path)


def main():
    DOCS.mkdir(exist_ok=True)
    make_proposal_docx(DOCS / "project_proposal.docx")
    make_proposal_pdf(DOCS / "project_proposal.pdf")
    make_report_docx(DOCS / "final_report.docx")
    make_report_pdf(DOCS / "final_report.pdf")
    make_presentation(DOCS / "presentation.pptx")
    print(
        "Created project_proposal.docx/pdf, final_report.docx/pdf, "
        "and presentation.pptx"
    )


if __name__ == "__main__":
    main()
