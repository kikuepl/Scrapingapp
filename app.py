from bs4 import BeautifulSoup
import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import altair as alt
import streamlit as st

def get_df_ec():
  url_ec = 'https://scraping.official.ec/'
  response = requests.get(url_ec)
  soup = BeautifulSoup(response.text, 'html.parser')
  item_list = soup.find('ul', {'id': 'itemList'})
  items = item_list.find_all('li')

  data_ec = []
  for item in items:
      datum_ec = {}
      datum_ec['title'] = item.find('p', {'class': 'items-grid_itemTitleText_5c97110f'}).text
      price = item.find('p', {'class': 'items-grid_price_5c97110f'}).text
      datum_ec['price'] = int(price.replace('¥', '').replace(',', ''))
      Link = item.find('a')['href']
      is_stock = item.find('p', {'class': 'items-grid_soldOut_5c97110f'}) == None
      datum_ec['is_stock'] = '在庫あり' if is_stock else '在庫なし'
      data_ec.append(datum_ec)
  df_ec = pd.DataFrame(data_ec)
  return df_ec

def get_worksheet():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    credentials = Credentials.from_service_account_file(
        './secret.json',
        scopes = scopes  
    )
    gc = gspread.authorize(credentials)

    SP_SHEET_KEY = '1YTwCaW1-Nrapm_y-fAXYYG8w5Q_5Zaz7dv4ghDGeOFE'
    sh = gc.open_by_key(SP_SHEET_KEY)

    SP_SHEET = 'db'
    worksheet = sh.worksheet(SP_SHEET)

    return worksheet

def get_chart():
    worksheet = get_worksheet()
    data = worksheet.get_all_values()
    df_udemy = pd.DataFrame(data[1:], columns = data[0])

    df_udemy = df_udemy.astype({
        'n_subscriber': int,
        'n_review': int
    })

    ymin1 = df_udemy['n_subscriber'].min()-10
    ymax1 = df_udemy['n_subscriber'].max()+10

    ymin2 = df_udemy['n_review'].min()-10
    ymax2 = df_udemy['n_review'].max()+10

    base = alt.Chart(df_udemy).encode(
        alt.X('date:T')  # X軸を時間としてエンコード
    )

    area = base.mark_area(opacity=0.3, color='#57A44C').encode(
        alt.Y('n_subscriber', title='受講生数', scale=alt.Scale(domain=[ymin1, ymax1]))
    )

    line = base.mark_line(stroke='#5276A7', interpolate='monotone').encode(
        alt.Y('n_review', title='レビュー数', scale=alt.Scale(domain=[ymin2, ymax2]))
    )

    chart = alt.layer(area, line).resolve_scale(
        y='independent'  # Y軸を独立して設定
    )

    return chart

df_ec = get_df_ec()
chart = get_chart()

st.title("webスクレイピング活用アプリ")

st.write('## Udemyの情報')

st.altair_chart(chart, use_container_width=True)

st.write('## EC在庫情報', df_ec)