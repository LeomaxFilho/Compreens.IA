from flask import Flask, request, redirect, url_for, session
from google.oauth2 import credentials
from google_auth_oauthlib.flow import Flow
from google.cloud import secret_manager
from models.email_model import EmailModel
from models.ai_model import AiModel
from views.response_view import ResponseView

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'  # Substitua por uma chave secreta forte

# Configurações do OAuth 2.0
CLIENT_ID = 'SEU_CLIENT_ID'  # Substitua pelo seu Client ID
CLIENT_SECRET = 'SEU_CLIENT_SECRET'  # Substitua pelo seu Client Secret
REDIRECT_URI = 'http://localhost:5000/callback/gmail'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# (Opcional) Se você estiver usando o Google Cloud Secret Manager para armazenar segredos
def access_secret_version(secret_id, version_id="latest"):
    client = secret_manager.SecretManagerServiceClient()
    name = f"projects/SEU_PROJETO_ID/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("utf-8")

@app.route('/login/gmail')
def login_gmail():
    flow = Flow.from_client_config(
        {'web': {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET,
                 'redirect_uris': [REDIRECT_URI], 'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                 'token_uri': 'https://oauth2.googleapis.com/token'}},
        scopes=SCOPES)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/callback/gmail')
def callback_gmail():
    state = session['state']
    flow = Flow.from_client_config(
        {'web': {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET,
                 'redirect_uris': [REDIRECT_URI], 'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                 'token_uri': 'https://oauth2.googleapis.com/token'}},
        scopes=SCOPES, state=state)
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials

    email_model = EmailModel(creds)
    ai_model = AiModel()
    response_view = ResponseView()

    email_content = email_model.get_latest_email_content()

    if email_content:
        interpretation = ai_model.analyze_email_for_neurodivergent(email_content)
        return response_view.render_email_analysis(email_content, interpretation)
    elif email_content is None:
        return response_view.render_error("Não foi possível obter o conteúdo do email.", 500)
    else:
        return response_view.render_message("Nenhum email encontrado na sua caixa de entrada.", 200)

if __name__ == '__main__':
    app.run(debug=True)