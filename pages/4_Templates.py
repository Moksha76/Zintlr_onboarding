import json
import os

import streamlit as st
from jinja2 import Template

import config
from components.email_preview import show_email_preview
from database.db import SessionLocal, init_db
from database.models import DocumentTemplate, EmailTemplate, Joiner
from services import pdf_service
from services.scheduler import start_scheduler

init_db()
start_scheduler()

st.title("Templates")

_SAMPLE_CONTEXT = dict(
    name="Test User",
    designation="Engineering",
    team_name="Engineering Team",
    doj="15/07/2026",
    uan="",
    bg_deadline_date="10/07/2026",
    bg_deadline_time="09:00 AM",
    links=config.LINKS,
    signature=config.SIGNATURE_BLOCK,
)

session = SessionLocal()
try:
    templates = (
        session.query(EmailTemplate)
        .filter(EmailTemplate.active.is_(True))
        .order_by(EmailTemplate.id)
        .all()
    )
    joiners = session.query(Joiner).order_by(Joiner.full_name).all()
    joiner_options = {f"{j.full_name} ({j.candidate_email})": j for j in joiners}

    st.subheader("Email Templates")

    for t in templates:
        with st.expander(f"{t.display_name}  ·  v{t.version}"):
            attachments = json.loads(t.attachments_json) if t.attachments_json else []
            cc_line = config.HR_ADMIN_EMAIL
            if t.cc_default:
                cc_line += f" + {t.cc_default}"

            st.caption(f"Subject: {t.subject}")
            st.caption(f"CC: {cc_line} (HR Admin is always mandatory)")
            st.caption(f"Attachments: {', '.join(attachments) if attachments else 'None'}")
            st.caption(f"Last updated: {t.updated_at}")

            static_keys = [k for k in attachments if k in config.STATIC_ATTACHMENTS]
            for skey in static_keys:
                static_path = config.STATIC_ATTACHMENTS[skey]
                st.markdown(f"**Attachment file:** `{os.path.basename(static_path)}`")
                new_file = st.file_uploader(
                    "Replace this PDF (same file gets sent to every candidate)",
                    type=["pdf"],
                    key=f"replace_{t.template_key}_{skey}",
                )
                if new_file is not None and st.button(
                    "Save replacement", key=f"save_replace_{t.template_key}_{skey}"
                ):
                    os.makedirs(os.path.dirname(static_path), exist_ok=True)
                    with open(static_path, "wb") as f:
                        f.write(new_file.getvalue())
                    st.success(f"Replaced {os.path.basename(static_path)}.")

            st.markdown("**Body preview:**")
            st.code(t.body_html, language="html")

            edit_key = f"editing_{t.template_key}"
            if st.button("Edit", key=f"edit_btn_{t.template_key}"):
                st.session_state[edit_key] = True

            if st.session_state.get(edit_key):
                new_subject = st.text_input("Subject", value=t.subject, key=f"subject_{t.template_key}")
                new_cc = st.text_input(
                    "Additional default CC (HR Admin is always included separately)",
                    value=t.cc_default or "",
                    key=f"cc_{t.template_key}",
                )
                new_body = st.text_area("Body (HTML)", value=t.body_html, height=250, key=f"body_{t.template_key}")
                st.caption(
                    "Available variables: {{ name }}, {{ designation }}, {{ team_name }}, {{ doj }}, "
                    "{{ uan }}, {{ links.* }}, {{ signature }}, {{ bg_deadline_date }}, {{ bg_deadline_time }}"
                )

                if st.button("Test render", key=f"test_render_{t.template_key}"):
                    try:
                        rendered_subject = Template(new_subject).render(**_SAMPLE_CONTEXT)
                        rendered_body = Template(new_body).render(**_SAMPLE_CONTEXT)
                        st.success("Rendered without errors.")
                        st.write(f"**Subject:** {rendered_subject}")
                        st.markdown(rendered_body, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Render error: {e}")

                if st.button("Save as new version", key=f"save_{t.template_key}"):
                    t.active = False
                    session.add(
                        EmailTemplate(
                            template_key=t.template_key,
                            display_name=t.display_name,
                            subject=new_subject,
                            body_html=new_body,
                            cc_default=new_cc,
                            attachments_json=t.attachments_json,
                            version=t.version + 1,
                            active=True,
                        )
                    )
                    session.commit()
                    st.session_state[edit_key] = False
                    st.success("Saved as new version.")
                    st.rerun()

            st.markdown("---")
            st.markdown("**Send using this template**")
            if joiner_options:
                selected_label = st.selectbox(
                    "Candidate", options=list(joiner_options.keys()), key=f"joiner_pick_{t.template_key}"
                )
                if st.button("Preview & Send", key=f"preview_send_{t.template_key}"):
                    j = joiner_options[selected_label]
                    joiner_dict = dict(
                        id=j.id,
                        name=j.full_name,
                        email=j.candidate_email,
                        designation=j.designation,
                        team_name=j.team_name,
                        doj=j.doj.strftime("%d/%m/%Y") if j.doj else "",
                        uan=j.uan or "",
                    )
                    show_email_preview(t.template_key, joiner_dict)
            else:
                st.info("Add a joiner first (Add Joiner page) to send a real preview.")

    st.subheader("Documents")
    documents = session.query(DocumentTemplate).filter(DocumentTemplate.active.is_(True)).all()
    for d in documents:
        with st.expander(f"{d.display_name}  ·  v{d.version}"):
            st.code(d.body_text)

            edit_key = f"editing_doc_{d.document_key}"
            if st.button("Edit", key=f"edit_doc_btn_{d.document_key}"):
                st.session_state[edit_key] = True

            if st.session_state.get(edit_key):
                new_body = st.text_area(
                    "Body text", value=d.body_text, height=300, key=f"doc_body_{d.document_key}"
                )
                st.caption(
                    "Available variables: {{ name }}, {{ designation }}, {{ team_name }}, {{ doj }}, "
                    "{{ uan }}, {{ links.* }}, {{ signature }}"
                )
                test_name = st.text_input(
                    "Test render with name", value="Test User", key=f"doc_test_name_{d.document_key}"
                )
                doc_test_context = dict(_SAMPLE_CONTEXT)
                doc_test_context["name"] = test_name

                if st.button("Test render", key=f"doc_test_render_{d.document_key}"):
                    try:
                        rendered_text = Template(new_body).render(**doc_test_context)
                        st.success("Rendered without errors.")
                        st.text(rendered_text)
                    except Exception as e:
                        st.error(f"Render error: {e}")

                if st.button("Preview as PDF", key=f"doc_pdf_{d.document_key}"):
                    try:
                        rendered_text = Template(new_body).render(**doc_test_context)
                        tmp_path = os.path.join(config.GENERATED_DIR, f"_preview_{d.document_key}.pdf")
                        os.makedirs(config.GENERATED_DIR, exist_ok=True)
                        pdf_service.render_text_to_pdf(rendered_text, tmp_path)
                        url = pdf_service.to_static_url(tmp_path)
                        st.markdown(f"\U0001F517 [Open in new tab]({url})")
                        with open(tmp_path, "rb") as f:
                            st.download_button(
                                "Download to view",
                                data=f.read(),
                                file_name=f"{d.document_key}_preview.pdf",
                                mime="application/pdf",
                                key=f"doc_download_{d.document_key}",
                            )
                    except Exception as e:
                        st.error(f"PDF generation failed: {e}")

                if st.button("Save as new version", key=f"doc_save_{d.document_key}"):
                    d.active = False
                    session.add(
                        DocumentTemplate(
                            document_key=d.document_key,
                            display_name=d.display_name,
                            body_text=new_body,
                            version=d.version + 1,
                            active=True,
                        )
                    )
                    session.commit()
                    st.session_state[edit_key] = False
                    st.success("Saved as new version.")
                    st.rerun()
finally:
    session.close()
