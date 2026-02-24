"""
Power BI Embed-Token Generator (Workspace Identity / Managed Identity).

Acquires an access token for the Power BI REST API using:
  1. ManagedIdentityCredential  — inside Fabric (workspace identity) or
     any Azure host with a managed identity.
  2. AzureCliCredential         — local development (requires `az login`).

No client secrets or environment variables are needed.

Pre-requisites (Fabric Workspace Identity)
------------------------------------------
1. In the Fabric portal, open your workspace → Settings → Workspace identity
   and enable it (creates a system-assigned managed identity).
2. In the Power BI workspace that contains your reports, grant the
   workspace identity at least *Viewer* access.
3. In the Power BI Admin Portal, enable
   "Service principals can use Power BI APIs" for the security group
   that contains the workspace identity.
4. No secrets or env-vars are required — the identity is attached
   automatically at runtime.

Local development
-----------------
Run ``az login`` once.  The app will use your Azure CLI session to
obtain tokens.
"""

import logging
from typing import Optional

import streamlit as st

# ── Silence noisy azure-identity / msal logs ──────────────────
logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("azure.core").setLevel(logging.WARNING)
logging.getLogger("msal").setLevel(logging.WARNING)

_POWERBI_SCOPE = "https://analysis.windows.net/powerbi/api/.default"


def _get_credential():
    """
    Build a credential that tries — in order:
      1. Azure CLI          (local dev, after ``az login``)
      2. Managed Identity   (Fabric workspace identity / Azure VM / App Service)

    AzureCliCredential is tried first so that on local machines with an
    Azure Arc agent (whose token files may not be readable) the chain
    succeeds immediately via the CLI without hitting a permission error.
    """
    from azure.identity import (
        ChainedTokenCredential,
        ManagedIdentityCredential,
        AzureCliCredential,
    )

    return ChainedTokenCredential(
        AzureCliCredential(),          # local dev after `az login`
        ManagedIdentityCredential(),   # Fabric workspace identity / Azure MI
    )


# ── Token cache (avoid re-auth on every Streamlit rerun) ──────
@st.cache_data(ttl=3000, show_spinner=False)
def get_access_token(report_id: str, group_id: str) -> Optional[dict]:
    """
    Return an AAD access token that can be used directly with the
    Power BI JS SDK (``TokenType.Aad``).  No ``GenerateToken`` REST
    call is needed — works with both user identities (Azure CLI) and
    managed identities (Fabric workspace identity).

    Returns
    -------
    dict  {"token": str, "embed_url": str, "report_id": str}
    """
    try:
        credential = _get_credential()
        token = credential.get_token(_POWERBI_SCOPE)
    except Exception:
        return None

    return {
        "token": token.token,
        "embed_url": (
            f"https://app.powerbi.com/reportEmbed"
            f"?reportId={report_id}&groupId={group_id}"
        ),
        "report_id": report_id,
    }
