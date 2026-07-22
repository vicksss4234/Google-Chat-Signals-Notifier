import os
import pandas as pd
import requests
import re
import time
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

# ================= Settings =================
load_dotenv()
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
SHEET_NAME = os.getenv('SHEET_NAME', '[NEW] Pending Signals')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE', 'service_account.json')

TSR_IDS = {
   'victorparedes': '110213385377468768641',
}

TSR_A_FILTRAR = list(TSR_IDS.keys())

def enviar_reporte_chat(request=None):
    scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    service = build('sheets', 'v4', credentials=creds)

    # 2.Data extraction from the spreedshet below
    sheet_request = service.spreadsheets().get(
        spreadsheetId=SPREADSHEET_ID,
        ranges=[SHEET_NAME],
        fields="sheets(data(rowData(values(formattedValue,hyperlink,userEnteredValue(formulaValue)))))"
    )
    response = sheet_request.execute()

    try:
        rows_data = response['sheets'][0]['data'][0]['rowData']
    except KeyError:
        print("La pestaña está vacía o no existe.")
        return "No data"

    # 3. Parsing the data
    parsed_data = []
    for row in rows_data:
        row_values = []
        if 'values' in row:
            for cell in row['values']:
                val = cell.get('formattedValue', '')
                link = cell.get('hyperlink')
                if not link:
                    formula = cell.get('userEnteredValue', {}).get('formulaValue', '')
                    if formula:
                        match = re.search(r'=HYPERLINK\(\s*["\']([^"\']+)["\']', formula, re.IGNORECASE)
                        if match:
                            link = match.group(1)
                row_values.append({'value': val, 'link': link or 'No tiene link'})
        parsed_data.append(row_values)

    if not parsed_data or len(parsed_data) < 2:
        return "Sin datos suficientes."

    # 4. Building the dataframe
    headers = [col['value'].lower() for col in parsed_data[0]]
    df_rows = []
    for r in parsed_data[1:]:
        padded_row = r + [{'value': '', 'link': 'No tiene link'}] * (len(headers) - len(r))
        df_rows.append(padded_row[:len(headers)])

    df_valores = pd.DataFrame([[c['value'] for c in row] for row in df_rows], columns=headers)
    df_links = pd.DataFrame([[c['link'] for c in row] for row in df_rows], columns=headers)

    if 'form' in df_links.columns:
        df_valores['form_link'] = df_links['form']

    if 'tsr' not in df_valores.columns or 'form_link' not in df_valores.columns:
        return "Missing columns"

    df_filtrado = df_valores[df_valores['tsr'].isin(TSR_A_FILTRAR)]

    if df_filtrado.empty:
        return "Empty result"

    # 5. Grouping and card creation
    agrupado_por_tsr = df_filtrado.groupby('tsr')

    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    requests.post(WEBHOOK_URL, json={"text": f"*{'Team Lore Inflight Signals ' + fecha_hoy}*"})
    time.sleep(2)

    for tsr_val, grupo_casos in agrupado_por_tsr:
        tsr_id = TSR_IDS.get(tsr_val)
        mencion_tsr = f"<users/{tsr_id}>" if tsr_id else tsr_val
        cantidad_pendientes = len(grupo_casos)

        #saving every case as a widget inside the card
        widgets_casos = []

        for idx, row in grupo_casos.iterrows():
            case_val = row.get('case number', 'N/A')
            act_val = row.get('recommended action', 'N/A')
            link_form = row.get('form_link', '')
            decorated_text = {
                "text": f"<b>Caso: {case_val}</b><br>{act_val}",
                "wrapText": True
            }

            if link_form.startswith('http'):
                decorated_text["button"] = {
                    "text": "Link Form",
                    "onClick": {
                        "openLink": {
                            "url": link_form
                        }
                    }
                }

            widgets_casos.append({
                "decoratedText": decorated_text
            })

        # --- Chunking logic for the card ---
        MAX_WIDGETS_PER_CARD = 50 

        for i in range(0, len(widgets_casos), MAX_WIDGETS_PER_CARD):
            chunk_widgets = widgets_casos[i:i + MAX_WIDGETS_PER_CARD]
            
            texto_parte = f" (Parte {i//MAX_WIDGETS_PER_CARD + 1})" if len(widgets_casos) > MAX_WIDGETS_PER_CARD else ""

            # Builiding final payload for this TSR
            payload = {
                "text": f"{mencion_tsr} signals update: {cantidad_pendientes} pending" if i == 0 else f"Continuación de signals para {tsr_val.capitalize()}...",
                "cardsV2": [
                    {
                        "cardId": f"card-{tsr_val}-{i}",
                        "card": {
                            "header": {
                                "title": f"{tsr_val.capitalize()} — Inflight Signals{texto_parte}",
                                "subtitle": f"{len(chunk_widgets)} mostrados aquí" if len(widgets_casos) > MAX_WIDGETS_PER_CARD else f"{cantidad_pendientes} pending",
                                "imageUrl": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/error/default/24px.svg",
                                "imageType": "CIRCLE"
                            },
                            "sections": [
                                {
                                    # show more / show less option 
                                    "collapsible": True,
                                    "uncollapsibleWidgetsCount": 3,
                                    "widgets": chunk_widgets
                                }
                            ]
                        }
                    }
                ]
            }

            # sending the card for this specific TSR
            webhook_response = requests.post(WEBHOOK_URL, json=payload)
            
            if webhook_response.status_code != 200:
                print(f"Error enviando tarjeta para {tsr_val}: {webhook_response.text}")
            
            # Stop to avoid hitting the limits of the API
            time.sleep(2)

    return "Success"

if __name__ == "__main__":
    enviar_reporte_chat()