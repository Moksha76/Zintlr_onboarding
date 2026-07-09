import os

import streamlit as st

import config
from services import email_service, pdf_service, stage_service, template_engine


@st.dialog("Email Preview", width="large")
def show_email_preview(template_key: str, joiner: dict):
    """Reusable send-preview modal. `joiner` is a plain dict with keys:
    id, name, email, designation, team_name, doj, uan.
    """
    context = dict(
        designation=joiner.get("designation", ""),
        team_name=joiner.get("team_name", ""),
        doj=joiner.get("doj", ""),
        uan=joiner.get("uan", ""),
    )

    if template_key == "bg_verification":
        st.markdown("**BG Verification deadline** (required)")
        col1, col2 = st.columns(2)
        with col1:
            bg_deadline_date = st.text_input("Deadline date (dd/mm/yyyy)", key="bg_deadline_date")
        with col2:
            bg_deadline_time = st.text_input("Deadline time", value="09:00 AM", key="bg_deadline_time")
        context["bg_deadline_date"] = bg_deadline_date
        context["bg_deadline_time"] = bg_deadline_time

    rendered = template_engine.render_template(
        template_key, to_addr=joiner["email"], name=joiner["name"], **context
    )

    st.text_input("To", value=rendered.to_addr, disabled=True)
    st.text_input("From", value=config.SENDER_EMAIL, disabled=True)
    st.text_input("CC (mandatory)", value=rendered.mandatory_cc, disabled=True)
    additional_cc = st.text_input("Additional CC (editable)", value=rendered.additional_cc)
    subject = st.text_input("Subject", value=rendered.subject)

    edit_body = st.toggle("Edit body for this send only")
    if edit_body:
        body_html = st.text_area("Body", value=rendered.body_html, height=300)
    else:
        body_html = rendered.body_html
        st.markdown("**Body preview:**")
        st.markdown(body_html, unsafe_allow_html=True)

    bg_missing_deadline = template_key == "bg_verification" and not context.get("bg_deadline_date")

    attachment_paths = []
    if rendered.attachment_keys:
        st.markdown("**Attachments**")
        if bg_missing_deadline:
            st.warning("Enter the BG deadline date above to generate the attachment.")
        else:
            attachment_paths = pdf_service.resolve_attachments(
                rendered.attachment_keys, name=joiner["name"], **context
            )
            for path in attachment_paths:
                st.write(f"\U0001F4CE {os.path.basename(path)}")
                preview_key = f"show_preview_{path}"
                if st.button(f"Preview {os.path.basename(path)}", key=f"btn_{path}"):
                    st.session_state[preview_key] = not st.session_state.get(preview_key, False)
                if st.session_state.get(preview_key):
                    url = pdf_service.to_static_url(path)
                    st.markdown(f"\U0001F517 [Open in new tab]({url})")
                    with open(path, "rb") as f:
                        st.download_button(
                            "Download to view",
                            data=f.read(),
                            file_name=os.path.basename(path),
                            mime="application/pdf",
                            key=f"download_{path}",
                        )

    st.markdown("**Add attachment** (optional — attached to this send only)")
    extra_file = st.file_uploader("Attach an additional file", key="extra_attachment")
    extra_attachment_path = None
    if extra_file is not None:
        os.makedirs(config.GENERATED_DIR, exist_ok=True)
        extra_attachment_path = os.path.join(config.GENERATED_DIR, f"extra_{extra_file.name}")
        with open(extra_attachment_path, "wb") as f:
            f.write(extra_file.getvalue())
        st.caption(f"Will also attach: {extra_file.name}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel"):
            st.rerun()
    with col2:
        if st.button("Send via Outlook", type="primary", disabled=bg_missing_deadline):
            full_cc = ", ".join(filter(None, [rendered.mandatory_cc, additional_cc]))
            final_attachments = attachment_paths + ([extra_attachment_path] if extra_attachment_path else [])
            with st.spinner("Sending via Outlook... (may take up to 30s if a retry is needed)"):
                success, error = email_service.send_email(
                    to=rendered.to_addr,
                    cc=full_cc,
                    subject=subject,
                    body_html=body_html,
                    attachment_paths=final_attachments,
                    joiner_id=joiner.get("id"),
                    template_key=template_key,
                )
            if success:
                extra_fields = {}
                if template_key == "bg_verification":
                    extra_fields = {
                        "bg_deadline_date": context.get("bg_deadline_date"),
                        "bg_deadline_time": context.get("bg_deadline_time"),
                    }
                stage_service.advance_stage_after_send(joiner.get("id"), template_key, extra_fields=extra_fields)
                st.success("Email sent. Close this window to see the updated stage.")
            else:
                st.error(f"Send failed: {error}")
