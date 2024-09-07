
# Automate Workflow: Periodic Sync of Sorbonne Université CalDAV with Personal Google Calendar via GitHub Actions

This guide outlines the steps to access your Google Calendar using OAuth 2.0 credentials through a Python script. You will set up credentials via the Google Cloud Console, run a Python script to generate tokens, and then configure them in GitHub Actions.

### 1. Create OAuth 2.0 Credentials in Google Cloud Console
- Go to the Google Cloud Console.                      
- Create a new project or use an existing one.    
- Enable the Google Calendar API: 
- In the left-hand menu, navigate to APIs & Services → Library. 
- Search for Google Calendar API and click Enable. 
- Create OAuth 2.0 Credentials: 
- Go to the Credentials tab in the Google Cloud Console. 
- Click Create Credentials → OAuth 2.0 Client ID. 
- Set the Application Type to Desktop App. 
- Download the generated client_secret.json file to your local machine.
### 2. Creating google service account:
follow the steps to get a private key type json 
  https://github.com/expo/fyi/blob/main/creating-google-service-account.md

### 2. Running the Python Script to Generate Token 
Make sure that the client_secret.json file is saved in the same directory as your Python script. Use the following Python code to authenticate and generate a refresh token: 


```
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Define the required Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Load credentials from the client_secret.json file
flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json', SCOPES)
creds = flow.run_local_server(port=0)

# Save the credentials (token.json) for future use
with open('token.json', 'w') as token:
    token.write(creds.to_json())

# Print the refresh token
print("Refresh Token:", creds.refresh_token)
```
1. Save the script as get_token.py.
2. Run the script in the same directory where client_secret.json is located:
```
python get_token.py
```
### 3. Converting token.json to Base64
You need to encode the token.json file to base64. You can do this in one of the following ways:


```
import base64

with open("token.json", "rb") as token_file:
    token_data = token_file.read()
    base64_encoded = base64.b64encode(token_data).decode('utf-8')
    print(base64_encoded)
Using Command Line Tools:
```
Windows: \
certutil -encode token.json token.base64 \
Linux/macOS: \
base64 token.json > token.base64 

Online: Use an online tool like Base64 Encode. 

### 4. Add Secrets to GitHub Actions
- Go to your GitHub repository. 
- Navigate to Settings → Secrets → Actios. 
- Click New repository secret and add the following secrets: 
- CYPRESS_CONFIG_JSON: Paste the base64 encoded content of token.json. 
- GOOGLE_CREDENTIALS: Paste the content json file generated in part 2 (Creating google service account)
