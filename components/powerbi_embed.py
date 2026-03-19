"""
Power BI Embedded Report Component.

Uses the Fabric Workspace Identity (managed identity) to generate
embed tokens server-side so end-users never see a Power BI sign-in
prompt.  Falls back to a plain iframe when running outside Fabric
or when azure-identity is not installed.
"""

import html as _html

import streamlit as st

from components.powerbi_auth import get_access_token


# ── Power BI JS SDK embed via st.components.v1.html ───────────
_EMBED_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <script src="https://cdn.jsdelivr.net/npm/powerbi-client@2.23.1/dist/powerbi.min.js"></script>
  <style>
    html, body {{ margin:0; padding:0; overflow:hidden; height:100%; }}
    #reportContainer {{ width:100%; height:100%; }}
  </style>
</head>
<body>
  <div id="reportContainer"></div>
  <script>
    var models = window["powerbi-client"].models;
    var config = {{
      type: "report",
      id: "{report_id}",
      embedUrl: "{embed_url}",
      accessToken: "{access_token}",
      tokenType: models.TokenType.Aad,
      settings: {{
        panes: {{
          filters: {{ expanded: false, visible: true }},
          pageNavigation: {{ visible: true }}
        }},
        background: models.BackgroundType.Transparent
      }}
    }};
    var container = document.getElementById("reportContainer");
    powerbi.embed(container, config);
  </script>
</body>
</html>
"""

# ── Power BI JS SDK embed in EDIT mode (for adhoc exploration) ───
_EMBED_HTML_EDIT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <script src="https://cdn.jsdelivr.net/npm/powerbi-client@2.23.1/dist/powerbi.min.js"></script>
  <style>
    html, body {{ margin:0; padding:0; overflow:hidden; height:100%; }}
    #reportContainer {{ width:100%; height:100%; }}
  </style>
</head>
<body>
  <div id="reportContainer"></div>
  <script>
    var models = window["powerbi-client"].models;
    var config = {{
      type: "report",
      id: "{report_id}",
      embedUrl: "{embed_url}",
      accessToken: "{access_token}",
      tokenType: models.TokenType.Aad,
      viewMode: models.ViewMode.Edit,
      permissions: models.Permissions.All,
      settings: {{
        panes: {{
          filters: {{ expanded: false, visible: true }},
          pageNavigation: {{ visible: true }},
          fields: {{ expanded: true, visible: true }},
          visualizations: {{ expanded: true, visible: true }}
        }},
        background: models.BackgroundType.Transparent,
        layoutType: models.LayoutType.Custom,
        customLayout: {{
          displayOption: models.DisplayOption.FitToPage
        }}
      }}
    }};
    var container = document.getElementById("reportContainer");
    var report = powerbi.embed(container, config);
    
    // Enable report editing
    report.on("loaded", function() {{
      console.log("Report loaded in edit mode");
    }});
    
    report.on("error", function(event) {{
      console.error("Report error:", event.detail);
    }});
  </script>
</body>
</html>
"""


def render_powerbi_report(
    embed_url: str,
    title: str = "Power BI Report",
    description: str = "",
    height: int = 500,
    report_id: str = "",
    group_id: str = "",
    edit_mode: bool = False,
) -> None:
    """
    Render an embedded Power BI report panel.

    Parameters
    ----------
    embed_url : str
        Fallback Power BI embed URL (used only when env-vars are not set).
    title : str
        Display title above the report.
    description : str
        Short description of report contents.
    height : int
        Iframe height in pixels.
    report_id : str
        Power BI report GUID (from config).
    group_id : str
        Power BI workspace / group GUID (from config).
    edit_mode : bool
        If True, embed report in edit mode with all authoring panes visible.
        Use for adhoc exploration and building custom visuals.
    """
    st.markdown(f"### 📊 {title}")
    if description:
        st.caption(description)

    is_placeholder = "<YOUR_" in embed_url and not report_id

    if is_placeholder:
        # ── Placeholder mode ──────────────────────────────
        st.info(
            "🔗 **Power BI report placeholder**\n\n"
            "To connect a live report:\n"
            "1. Open `config.py`\n"
            "2. Fill in `report_id` and `group_id` for this persona\n"
            "3. Enable Workspace Identity in Fabric workspace settings\n"
            "4. Reload the app\n\n"
            f"**Expected report:** {title}\n\n"
            f"**Contents:** {description}",
            icon="📊",
        )
        with st.expander("🛠️  Setup guide — Workspace Identity embedding"):
            st.markdown(
                """
1. In the **Fabric portal**, open your workspace → **Settings** →
   **Workspace identity** and enable it.
2. In the **Power BI workspace** that hosts your reports, add the
   workspace identity as *Member* (or *Viewer*).
3. In the **Power BI Admin Portal**, enable
   *"Service principals can use Power BI APIs"* for a security group
   containing the workspace identity.
4. In `config.py`, fill in `report_id` and `group_id` for each report.
5. Restart the app — reports will load with no sign-in required.

> **Local development:** If you are running locally you can also
> authenticate via Azure CLI (`az login`) — `DefaultAzureCredential`
> picks it up automatically.
                """
            )
        return

    # ── Try AAD-token path (no sign-in) ───────────────────
    token_info = None
    if report_id and group_id:
        token_info = get_access_token(report_id, group_id)

    if token_info:
        # Render with the Power BI JS SDK — AAD token, no sign-in
        # Use edit mode template if edit_mode is True
        template = _EMBED_HTML_EDIT_TEMPLATE if edit_mode else _EMBED_HTML_TEMPLATE
        page_html = template.format(
            report_id=_html.escape(token_info["report_id"]),
            embed_url=_html.escape(token_info["embed_url"]),
            access_token=_html.escape(token_info["token"]),
        )
        st.components.v1.html(page_html, height=height + 10)
    else:
        # Fallback: plain iframe (user may need to sign in)
        iframe_html = (
            f'<iframe title="{_html.escape(title)}" width="100%" height="{height}" '
            f'src="{_html.escape(embed_url)}" frameborder="0" '
            f'allowFullScreen="true"></iframe>'
        )
        st.components.v1.html(iframe_html, height=height + 10)
        if report_id and group_id:
            st.caption(
                "⚠️ Embed token could not be generated — showing interactive "
                "sign-in fallback. Ensure Workspace Identity is enabled or "
                "that you are signed in via Azure CLI (`az login`)."
            )
