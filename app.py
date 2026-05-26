import dash
from dash import dcc, html, Input, Output, State, ctx, clientside_callback
import dash_bootstrap_components as dbc
import kuzu
import pandas as pd
import google.generativeai as genai
import base64
import os
import json
import numpy as np

# ==========================================
# 1. SETUP GENAI, DB, & SCHEMA
# ==========================================
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

db = kuzu.Database(r"./generated_files/instance_db")
conn = kuzu.Connection(db)

DB_SCHEMA = """
--- NODE TABLES ---
Person (personId: STRING PRIMARY_KEY, firstName: STRING, lastName: STRING, dob: DATE, taxId: STRING, nationality: STRING, pepStatus: BOOLEAN, kycStatus: STRING, riskScore: DOUBLE)
Company (companyId: STRING PRIMARY_KEY, name: STRING, regNumber: STRING, incorporationDate: DATE, industryCode: STRING, kycStatus: STRING, riskScore: DOUBLE)
Account (accountId: STRING PRIMARY_KEY, accountType: STRING, balance: DOUBLE, currency: STRING, status: STRING, openedDate: DATE, branchCode: STRING)
Transaction (txId: STRING PRIMARY_KEY, amount: DOUBLE, baseCurrencyAmount: DOUBLE, timestamp: TIMESTAMP, txType: STRING, channel: STRING, status: STRING)
Address (addressId: STRING PRIMARY_KEY, street: STRING, city: STRING, state: STRING, zipCode: STRING, country: STRING)
Device (deviceId: STRING PRIMARY_KEY, deviceType: STRING, os: STRING, ipAddress: STRING, macAddress: STRING, isp: STRING, registeredCountry: STRING)
Document (docId: STRING PRIMARY_KEY, docType: STRING, issuedCountry: STRING, expiryDate: DATE, isForged: BOOLEAN)
WatchlistEntity (entityId PRIMARY_KEY: STRING, listName: STRING, listType: STRING, addedDate: DATE)

--- RELATIONSHIP TABLES ---
OWNS_ACCOUNT (FROM Person TO Account) | (FROM Company TO Account) -> properties: [role: STRING, since: DATE]
HAS_ADDRESS (FROM Person TO Address) | (FROM Company TO Address) -> properties: [addressType: STRING, isCurrent: BOOLEAN]
USES_DEVICE (FROM Person TO Device) | (FROM Company TO Device) -> properties: [firstSeen: TIMESTAMP, lastSeen: TIMESTAMP, trustScore: DOUBLE]
SENT_TX (FROM Account TO Transaction) -> properties: [postTxBalance: DOUBLE]
RECEIVED_TX (FROM Transaction TO Account) -> properties: [postTxBalance: DOUBLE]
INITIATED_VIA (FROM Transaction TO Device) -> properties: [locationData: STRING]
WORKS_FOR (FROM Person TO Company) -> properties: [jobTitle: STRING, employmentType: STRING, startDate: DATE, salaryRange: STRING]
OWNS_EQUITY (FROM Person TO Company) | (FROM Company TO Company) -> properties: [percentage: DOUBLE, votingRights: DOUBLE]
DIRECTS (FROM Person TO Company) -> properties: [role: STRING, appointedDate: DATE]
PROVIDED_DOC (FROM Person TO Document) | (FROM Company TO Document) -> properties: [submissionDate: TIMESTAMP, verificationMethod: STRING]
MATCHES_WATCHLIST (FROM Person TO WatchlistEntity) | (FROM Company TO WatchlistEntity) -> properties: [similarityScore: DOUBLE, matchDate: TIMESTAMP, status: STRING]
"""

# ==========================================
# 1.5 SETUP MODELS & FEW-SHOT RAG
# ==========================================
LLM_OPTIONS = [
    "models/gemini-2.5-flash",
    "models/gemini-2.5-flash-lite",
    "models/gemini-3.1-flash-lite",
    "models/gemini-3.5-flash",
    "models/gemma-4-26b-a4b-it",
    "models/gemma-4-31b-it"
]

EMBEDDING_OPTIONS = [
    "models/gemini-embedding-001",
    "models/gemini-embedding-2"
]

print("Loading and embedding few-shot examples for all embedding models...")
try:
    with open("./generated_files/cypher_example.json", "r") as f:
        raw_examples = json.load(f)
except FileNotFoundError:
    print("Warning: queries.json not found. Few-shot prompting will be disabled.")
    raw_examples = []

precomputed_embeddings = {model: [] for model in EMBEDDING_OPTIONS}

if raw_examples:
    for emb_model in EMBEDDING_OPTIONS:
        print(f"  -> Pre-computing for {emb_model}...")
        for ex in raw_examples:
            try:
                emb = genai.embed_content(model=emb_model, content=ex["question"], task_type="retrieval_document")[
                    'embedding']
                precomputed_embeddings[emb_model].append({
                    "question": ex["question"],
                    "cypher": ex["cypher"],
                    "embedding": emb
                })
            except Exception as e:
                print(f"Error embedding with {emb_model}: {e}")
                break


def cosine_similarity(vec_a, vec_b):
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0: return 0.0
    return dot_product / (norm_a * norm_b)


# ==========================================
# 2. DASH APP UI LAYOUT
# ==========================================
# Use dbc.themes for dynamic switching (Darkly/Flatly)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME])

# Theme Switcher Component
theme_switch = html.Div(
    [
        html.I(className="fas fa-sun me-2", style={"color": "#f39c12"}),
        dbc.Switch(id="theme-toggle", value=False, className="d-inline-block", style={"verticalAlign": "middle"}),
        html.I(className="fas fa-moon ms-1", style={"color": "#bdc3c7"}),
    ],
    className="d-flex align-items-center bg-dark bg-opacity-25 px-3 py-1 rounded-pill border border-secondary"
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.Span([html.I(className="fas fa-university me-2"), "Banking Intelligence Hub"],
                      className="navbar-brand text-white fw-bold fs-5"),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                dbc.Nav([theme_switch], className="ms-auto", navbar=True),
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ],
        fluid=True,
    ),
    color="#2c3e50",  # Corporate bank blue-grey
    dark=True,
    className="mb-3 py-1 shadow-sm",
)

# Wrapper div that will receive the theme class (bg-light or bg-dark)
app.layout = html.Div(id="main-container", className="bg-body text-body",
                      style={"height": "100vh", "display": "flex", "flexDirection": "column", "overflow": "hidden"},
                      children=[
                          dcc.Location(id='url', refresh=False),
                          navbar,

                          dbc.Container([
                              dbc.Row([

                                  # --- LEFT PANEL: DATA INGESTION ---
                                  dbc.Col([
                                      dbc.Card([
                                          dbc.CardHeader(html.H6(
                                              [html.I(className="fas fa-file-upload me-2"), "Data Ingestion Pipeline"],
                                              className="mb-0 fw-bold")),
                                          dbc.CardBody([
                                              html.Div([
                                                  html.P(
                                                      "Upload unstructured investigator notes. The AI will extract entities and sync them to the graph database.",
                                                      className="text-muted small"),

                                                  dcc.Upload(
                                                      id='upload-data',
                                                      children=html.Div([
                                                          html.I(
                                                              className="fas fa-cloud-upload-alt fa-2x mb-2 text-primary"),
                                                          html.Br(),
                                                          'Drag & Drop or ',
                                                          html.A('Select .txt File', className="fw-bold text-primary")
                                                      ]),
                                                      style={
                                                          'width': '100%', 'height': '100px', 'borderWidth': '2px',
                                                          'borderStyle': 'dashed',
                                                          'borderRadius': '10px', 'textAlign': 'center',
                                                          'marginBottom': '10px',
                                                          'display': 'flex', 'flexDirection': 'column',
                                                          'justifyContent': 'center', 'cursor': 'pointer'
                                                      },
                                                      className="border-secondary mb-3",
                                                      multiple=False
                                                  ),

                                                  html.Hr(className="border-secondary my-2"),
                                                  html.H6([html.I(className="fas fa-terminal me-2"), "Ingestion Logs"],
                                                          className="mb-2"),
                                              ], style={"flexShrink": 0}),

                                              html.Div(
                                                  dcc.Loading(
                                                      html.Pre(id="upload-log", style={
                                                          "whiteSpace": "pre-wrap", "margin": "0", "height": "100%",
                                                          "padding": "10px", "borderRadius": "8px", "fontSize": "12px", "overflowY": "auto"
                                                      }, className="border border-secondary shadow-sm bg-body text-body w-100"),
                                                      parent_style={"height": "100%"}
                                                  ),
                                                  style={"flex": 1, "minHeight": 0, "overflow": "hidden"}
                                              )
                                          ], style={"display": "flex", "flexDirection": "column", "flex": 1, "minHeight": 0, "padding": "1rem"})
                                      ], className="shadow-sm border-0", style={"height": "100%", "display": "flex", "flexDirection": "column"})
                                  ], width=3, style={"height": "100%"}),

                                  # --- RIGHT PANEL: CHAT INTERFACE ---
                                  dbc.Col([
                                      dbc.Card([
                                          # Header with built-in Model Selectors
                                          dbc.CardHeader(
                                              dbc.Row([
                                                  dbc.Col(html.H6([html.I(className="fas fa-robot me-2 text-primary"),
                                                                   "AI Investigator"], className="mb-0 fw-bold"),
                                                          width=3, className="align-self-center"),
                                                  dbc.Col([
                                                      dbc.Button(
                                                          [html.I(className="fas fa-eraser me-1"), "Clear"],
                                                          id="clear-chat-btn", color="danger", size="sm", outline=True,
                                                          className="w-100 shadow-sm", title="Clear Chat History"
                                                      )
                                                  ], width=1, className="align-self-center px-1"),
                                                  dbc.Col([
                                                      dbc.Select(
                                                          id="llm-selector",
                                                          options=[{"label": m.split('/')[-1], "value": m} for m in
                                                                   LLM_OPTIONS],
                                                          value=LLM_OPTIONS[0],
                                                          className="dropdown-theme shadow-sm",
                                                          style={"fontSize": "13px"}
                                                      )
                                                  ], width=4),
                                                  dbc.Col([
                                                      dbc.Select(
                                                          id="embedding-selector",
                                                          options=[{"label": m.split('/')[-1], "value": m} for m in
                                                                   EMBEDDING_OPTIONS],
                                                          value=EMBEDDING_OPTIONS[0],
                                                          className="dropdown-theme shadow-sm",
                                                          style={"fontSize": "13px"}
                                                      )
                                                  ], width=4),
                                              ]),
                                          ),

                                          # Chat Window
                                          dbc.CardBody([
                                              # The chat-display div handles the auto-scroll
                                              html.Div(id="chat-display", style={
                                                  "flex": 1, "minHeight": 0, "overflowY": "auto",
                                                  "padding": "20px", "borderRadius": "8px",
                                                  "marginBottom": "15px", "scrollBehavior": "smooth"
                                              }, className="bg-body border border-secondary"),

                                              # Input Area
                                              html.Div([
                                                  dcc.Loading(
                                                      dbc.InputGroup([
                                                          dbc.Input(
                                                              id="user-input",
                                                              placeholder="e.g., Show me the smurfing ring...",
                                                              type="text",
                                                              style={"borderRadius": "20px 0 0 20px"},
                                                              className="bg-body text-body border-secondary"
                                                          ),
                                                          dbc.Button(
                                                              [html.I(className="fas fa-paper-plane me-1"), "Run"],
                                                              id="submit-btn", color="primary", n_clicks=0,
                                                              style={"borderRadius": "0 20px 20px 0"}
                                                          ),
                                                      ], className="shadow-sm")
                                                  )
                                              ], style={"flexShrink": 0}),

                                              # Hidden storage for memory/context
                                              dcc.Store(id="chat-history", data=[], storage_type="session")
                                          ], style={"display": "flex", "flexDirection": "column", "flex": 1, "minHeight": 0, "padding": "1rem"})
                                      ], className="shadow-sm border-0", style={"height": "100%", "display": "flex", "flexDirection": "column"})
                                  ], width=9, style={"height": "100%"})

                              ], style={"height": "100%", "margin": 0})
                          ], fluid=True, style={"flex": 1, "minHeight": 0, "paddingBottom": "1rem", "maxWidth": "1800px"})
                      ])

# ==========================================
# 3. CALLBACKS (LOGIC)
# ==========================================

# --- AUTO SCROLL JAVASCRIPT ---
# This tiny JS script forces the chat window to scroll to the bottom whenever it updates.
clientside_callback(
    """
    function(children) {
        if (!children) return;
        setTimeout(function() {
            var chatDiv = document.getElementById("chat-display");
            if(chatDiv) {
                chatDiv.scrollTop = chatDiv.scrollHeight;
            }
        }, 100); 
        return window.dash_clientside.no_update;
    }
    """,
    Output("chat-display", "id"),  # Dummy output, just triggers the side effect
    Input("chat-display", "children")
)


# --- THEME TOGGLE LOGIC ---
clientside_callback(
    """
    function(is_dark) {
        document.documentElement.setAttribute('data-bs-theme', is_dark ? 'dark' : 'light');
        return "bg-body text-body";
    }
    """,
    Output("main-container", "className"),
    Input("theme-toggle", "value"),
)


# --- FEATURE 4: File Upload & Automated Database Insertion ---
@app.callback(
    Output("upload-log", "children"),
    Output("upload-data", "contents"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("llm-selector", "value"),
    prevent_initial_call=True
)
def process_upload(contents, filename, selected_llm):
    if contents is None: return dash.no_update, dash.no_update

    content_type, content_string = contents.split(',')
    decoded_text = base64.b64decode(content_string).decode('utf-8')

    model = genai.GenerativeModel(selected_llm)
    prompt = f"""
    You are a database engineer. Our Kuzu graph database schema contains:
    {DB_SCHEMA}

    Read the following investigator notes and extract the newly discovered entities and relationships.
    Return ONLY a list of valid Cypher MERGE queries to insert this knowledge into Kuzu.
    Separate multiple queries with a semicolon (;). Do NOT wrap in markdown formatting.

    Notes:
    {decoded_text}
    """

    response = model.generate_content(prompt)
    raw_queries = response.text.replace("```cypher", "").replace("```", "").strip().split(";")

    logs = [f"--- Processing {filename} using {selected_llm.split('/')[-1]} ---"]
    for q in raw_queries:
        q = q.strip()
        if not q: continue
        try:
            conn.execute(q)
            logs.append(f"SUCCESS:\n{q}")
        except Exception as e:
            logs.append(f"FAILED:\n{q}\nReason: {e}")

    return "\n\n".join(logs), None


# --- FEATURES 1, 2, 3, 5: Chat, History, Context, and Auto-Correction ---
@app.callback(
    Output("chat-display", "children"),
    Output("chat-history", "data"),
    Output("user-input", "value"),
    Input("submit-btn", "n_clicks"),
    Input("clear-chat-btn", "n_clicks"),
    Input("url", "pathname"),  # Triggers on page load to render history immediately
    State("user-input", "value"),
    State("chat-history", "data"),
    State("llm-selector", "value"),
    State("embedding-selector", "value"),
)
def process_chat(submit_clicks, clear_clicks, pathname, user_message, chat_history, selected_llm, selected_embedding):
    if chat_history is None: chat_history = []

    # Identify what triggered the callback (Page Load vs Button Click)
    triggered_id = ctx.triggered_id

    if triggered_id == "clear-chat-btn":
        chat_history = []
        user_message = ""

    # If a button was clicked and there is a message, process it!
    elif triggered_id == "submit-btn" and user_message:
        chat_history.append({"role": "user", "content": user_message})
        history_str = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in chat_history[:-1]])

        model = genai.GenerativeModel(selected_llm)

        # --- DYNAMIC FEW-SHOT RETRIEVAL ---
        few_shot_context = ""
        active_examples = precomputed_embeddings.get(selected_embedding, [])

        if active_examples:
            user_embedding = \
            genai.embed_content(model=selected_embedding, content=user_message, task_type="retrieval_query")[
                'embedding']

            scored_examples = []
            for ex in active_examples:
                score = cosine_similarity(user_embedding, ex["embedding"])
                scored_examples.append((score, ex))

            scored_examples.sort(key=lambda x: x[0], reverse=True)
            top_5 = scored_examples[:5]

            print(f"\n--- RAG RETRIEVAL FOR: '{user_message}' ---")
            for i, (score, ex) in enumerate(top_5):
                print(f"Match {i + 1} Score: {score:.4f} | {ex['question']}")

            few_shot_context = "Here are similar verified queries to learn the syntax from:\n\n"
            for i, (score, ex) in enumerate(top_5):
                few_shot_context += f"Example {i + 1}:\nQuestion: {ex['question']}\nCypher: {ex['cypher']}\n\n"

        cypher_query = ""
        db_result_str = ""
        error_msg = ""

        # --- AUTO-CORRECTION LOOP ---
        for attempt in range(2):
            cypher_prompt = f"""
                    You are a Cypher expert assisting an investigator querying a Kuzu database.
                    Database Tables: {DB_SCHEMA}

                    Conversation History for context:
                    {history_str}

                    {few_shot_context}

                    CRITICAL INSTRUCTIONS: 
                    1. If the user's request matches one of the Examples provided above, you MUST use the exact Cypher logic and thresholds from that example. 
                    2. DO NOT treat relationships as properties. A Person node does NOT have an 'accountId' or 'companyId' property. You MUST traverse the graph to get those (e.g., `MATCH (p:Person)-[:OWNS_ACCOUNT]->(a:Account) RETURN a.accountId`).
                    3. Use OPTIONAL MATCH when the user asks for multiple independent pieces of data about an entity (e.g., their accounts AND their companies) so the query does not fail if one is missing.

                    User's current request: {user_message}

                    {"Previous attempt failed with error: " + error_msg + ". Please fix the syntax or property names." if error_msg else ""}

                    Write a valid Kuzu Cypher query to retrieve the answer. 
                    Return ONLY the raw Cypher code. No markdown, no explanations.
                    """

            cypher_res = model.generate_content(cypher_prompt)
            cypher_query = cypher_res.text.replace("```cypher", "").replace("```", "").strip()

            try:
                result_df = conn.execute(cypher_query).get_as_df()
                if result_df.empty:
                    db_result_str = "Query succeeded but returned 0 results."
                else:
                    db_result_str = result_df.to_string(index=False)
                error_msg = ""
                break
            except Exception as e:
                error_msg = str(e)

                # --- FINAL ANSWER GENERATION ---
        final_prompt = f"""
        You are a professional banking fraud investigator AI.
        The user asked: "{user_message}"

        To answer this, I ran the following query in our graph database:
        {cypher_query}

        The database returned: 
        {db_result_str if not error_msg else "Database execution completely failed after retries: " + error_msg}

        Explain what this data means clearly to the user. Do not expose the raw Cypher syntax to them unless they explicitly ask for it.
        """

        final_response = model.generate_content(final_prompt)
        bot_reply = final_response.text

        chat_history.append({
            "role": "model",
            "content": bot_reply,
            "query": cypher_query,
            "db_result": db_result_str,
            "error": error_msg,
            "rag_context": few_shot_context
        })

    # --- RENDER CHAT UI (For both fresh loads and new messages) ---
    chat_ui = []

    if not chat_history:
        # Show a friendly welcome message if history is empty
        chat_ui.append(html.Div(
            [html.I(className="fas fa-robot me-2 text-primary"), html.Span(
                "Hello Investigator. My connection to the Kuzu graph database is active. What would you like to query?",
                className="fw-bold")],
            className="text-secondary",
            style={"textAlign": "center", "marginTop": "40%"}
        ))

    for msg in chat_history:
        if msg["role"] == "user":
            chat_ui.append(html.Div(
                [html.I(className="fas fa-user-circle me-2"), html.Span(msg["content"])],
                className="bg-primary text-white",
                style={
                    "padding": "12px 18px",
                    "borderRadius": "18px 18px 0px 18px", "marginBottom": "12px",
                    "marginLeft": "auto", "maxWidth": "75%", "width": "fit-content",
                    "boxShadow": "0 2px 5px rgba(0,0,0,0.1)"
                }
            ))
        else:
            thought_content = []

            if msg.get("rag_context"):
                thought_content.append(
                    html.Strong([html.I(className="fas fa-search me-1"), "Retrieved RAG Context (from queries.json):"],
                                className="text-warning text-opacity-75", style={"fontSize": "12px"}))
                thought_content.append(html.Pre(msg["rag_context"],
                                                className="border border-warning border-opacity-50 text-body",
                                                style={"backgroundColor": "rgba(var(--bs-warning-rgb), 0.1)",
                                                       "padding": "10px", "borderRadius": "5px", "fontSize": "11px",
                                                       "whiteSpace": "pre-wrap", "maxHeight": "150px",
                                                       "overflowY": "auto"}))

            if msg.get("query"):
                thought_content.append(html.Strong([html.I(className="fas fa-code me-1"), "Generated Cypher:"],
                                                   className="text-success", style={"fontSize": "12px"}))
                thought_content.append(html.Pre(msg["query"],
                                                className="bg-dark text-light",
                                                style={"padding": "10px", "borderRadius": "5px",
                                                       "fontSize": "12px", "whiteSpace": "pre-wrap"}))

            if msg.get("error"):
                thought_content.append(html.Strong(
                    [html.I(className="fas fa-exclamation-triangle me-1"), "Error Encountered (Auto-corrected):"],
                    className="text-danger", style={"fontSize": "12px"}))
                thought_content.append(html.Pre(msg["error"],
                                                className="text-danger border border-danger border-opacity-25",
                                                style={"fontSize": "11px", "whiteSpace": "pre-wrap",
                                                       "backgroundColor": "rgba(var(--bs-danger-rgb), 0.1)", "padding": "10px",
                                                       "borderRadius": "5px"}))

            elif msg.get("db_result"):
                thought_content.append(html.Strong([html.I(className="fas fa-table me-1"), "Raw Database Result:"],
                                                   style={"fontSize": "12px"}))
                res_str = msg["db_result"]
                if len(res_str) > 800: res_str = res_str[:800] + "\n... [Truncated for UI limit]"
                thought_content.append(html.Pre(res_str, className="text-body border border-secondary",
                                                style={"backgroundColor": "rgba(var(--bs-secondary-rgb), 0.1)",
                                                                "padding": "10px",
                                                                "borderRadius": "5px", "fontSize": "11px",
                                                                "maxHeight": "200px", "overflowY": "auto",
                                                                "whiteSpace": "pre-wrap"}))

            thought_process_details = html.Details([
                html.Summary(
                    html.Span([html.I(className="fas fa-brain me-2"), "View AI Thought Process (Cypher & DB Logs)"]),
                    className="text-secondary",
                    style={"cursor": "pointer", "fontSize": "12px", "marginBottom": "10px",
                           "fontWeight": "bold", "listStyle": "none"}
                ),
                html.Div(thought_content,
                         className="border-start border-success border-3",
                         style={"marginTop": "10px", "paddingLeft": "15px"})
            ])

            chat_ui.append(html.Div([
                thought_process_details,
                dcc.Markdown(msg["content"], style={"marginTop": "10px", "marginBottom": "0px"})
            ], className="bg-body border border-secondary",
               style={
                "padding": "15px 20px",
                "borderRadius": "18px 18px 18px 0px", "marginBottom": "15px", "marginRight": "auto",
                "maxWidth": "85%", "boxShadow": "0 2px 5px rgba(0,0,0,0.05)"
            }))

    return chat_ui, chat_history, ""


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, port=8050)