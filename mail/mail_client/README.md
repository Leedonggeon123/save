# PySide6 Mail Client

The mail screen is a desktop rendering of the mail mockup: inbox, sent mail, drafts, mail list, mail detail, compose, delete confirmation, mail settings, and blacklist management.

This client uses a framed JSON-over-TCP protocol. The bundled TCP server shares the SQLite database with the mail features and implements the message types in `common/tcp_protocol.py`.

## Run

### Windows PowerShell

```powershell
cd C:\Users\iot\Documents\ChatGPT\wsl_project
.\mail_client\.venv\Scripts\Activate.ps1
python -m mail_client.database.init_db
python -m mail_client.server.mail_tcp_server
```

In another PowerShell window:

```powershell
cd C:\Users\iot\Documents\ChatGPT\wsl_project
.\mail_client\.venv\Scripts\Activate.ps1
python -m mail_client.client.mail_management_window
```

### WSL/Linux

```bash
cd ..
python3 -m mail_client.database.init_db
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m mail_client.server.mail_tcp_server
```

In another terminal, launch the GUI:

```bash
cd ..
python3 -m mail_client.client.mail_management_window
```

Set the TCP endpoint before launching:

```bash
export CLOUD_SERVER_HOST=127.0.0.1
export CLOUD_SERVER_PORT=9000
```

## Protocol messages

- `LOGIN_REQUEST`
- `LIST_MAILS`
- `READ_MAIL`
- `DELETE_MAIL`
- `DELETE_MAILS`
- Draft rows can be double-clicked to reopen the compose dialog; saving updates the existing draft and sending removes it after successful delivery.
- `SEND_MAIL`
- `SAVE_DRAFT`
- `GET_SETTINGS`
- `UPDATE_SETTINGS`
- `LIST_BLACKLIST`
- `ADD_BLACKLIST`
- `REMOVE_BLACKLIST`

After login, the client polls the inbox every 5 seconds. When a new message ID is detected it shows a `NEW_MAIL_NOTIFICATION` dialog and refreshes the current inbox/all-mail view.

The payload is JSON. File payloads can use the same frame format later by setting `payload_size` and appending binary bytes.

Expected response data shapes:

```json
{"type":"RESPONSE","success":true,"data":{"mails":[]}}
{"type":"RESPONSE","success":true,"data":{"settings":{"autoFit":true,"defaultSenderEmail":"me@example.com","prefixMsg":"","suffixMsg":"","downloadPath":""}}}
{"type":"RESPONSE","success":true,"data":{"blocked":[{"blocked_id":2,"name":"User","email":"user@example.com"}]}}
```
