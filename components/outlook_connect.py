import streamlit as st

import config
from services import graph_auth


def render_outlook_connect_section():
    if not config.GRAPH_CLIENT_ID or not config.GRAPH_TENANT_ID:
        with st.container(border=True):
            st.subheader("Connect Outlook")
            st.caption(
                "Not set up yet — add GRAPH_CLIENT_ID and GRAPH_TENANT_ID to your .env file "
                "once the Azure App Registration is ready, then restart the app."
            )
        return

    connected_account = graph_auth.get_connected_account()

    with st.container(border=True):
        st.subheader("Connect Outlook")

        if connected_account:
            st.success(f"Connected as {connected_account}")
            if st.button("Disconnect"):
                graph_auth.disconnect()
                st.session_state.pop("outlook_device_flow", None)
                st.rerun()
            return

        st.caption("Sign in once so the app can send emails on your behalf.")

        if st.button("Start sign-in"):
            try:
                flow = graph_auth.start_device_flow()
                st.session_state["outlook_device_flow"] = flow
            except Exception as e:
                st.error(f"Couldn't start sign-in: {e}")

        flow = st.session_state.get("outlook_device_flow")
        if flow:
            st.info(flow["message"])
            if st.button("I've signed in — Check now"):
                result = graph_auth.poll_device_flow(flow)
                if result["status"] == "success":
                    st.session_state.pop("outlook_device_flow", None)
                    st.success(f"Connected as {result['username']}")
                    st.rerun()
                elif result["status"] == "pending":
                    st.warning("Still waiting — sign in at the link above, then click Check again.")
                else:
                    st.error(f"Sign-in failed: {result['detail']}")
                    st.session_state.pop("outlook_device_flow", None)
