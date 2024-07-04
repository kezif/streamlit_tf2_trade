# streamlit_app.py

import streamlit as st
import pymongo
from datetime import datetime


# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return pymongo.MongoClient(st.secrets["mongo"]["CONNECTION_STRING"])

client = init_connection()

# Pull data from the collection.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def get_data(page=0, page_size=10):
    db = client.tf2_trade
    querry = {
    'spelled_items': {
        '$exists': True, 
        '$ne': []
    }, 
    'bp_info.scam_info.ban_vac': {
        '$ne': True
    }, 
    '$or': [
        {
            'bp_info.ref_value': {
                '$lt': 2000
            }
        }, {
            'bp_info.ref_value': {
                '$eq': None
            }
        }
    ]
}
    projection = {
  'user_steamID64': 1,
  'link_steamrep': {
    '$concat': [
      "https://steamrep.com/search?q=",
      "$user_steamID64"
    ]
  },
 'link_steam': {
    '$concat': [
      "https://steamcommunity.com/profiles/",
      "$user_steamID64"
    ]
  },
  'spelled_items': 1,
  'halloween_items': 1,
  'slots_used': "$total_items",
  'ref_value': "$bp_info.ref_value",
  'have_ban': {
    '$or': [
      {
        '$getField':
          "bp_info.scam_info.ban_steam_community"
      },
      {
        '$getField':
          "bp_info.scam_info.ban_steam_community"
      },
      { '$getField': "bp_info.scam_info.ban_vac" }
    ]
  },
  'bp_info': 1,
  'last_parsed': 1,
  'comment': 1
}
    sort = { 'total_items': 1 }
    items = db['parsed profiles'].find(querry, projection=projection, sort=sort).skip(page_size*page).limit(page_size)
    items = list(items)  # make hashable for st.cache_data
    return items

users = get_data()

# Print results.
st.header('Parsed items!')
for user in users:
    with st.container(border=True):
        cols = st.columns(2, gap="small")
        with cols[0]:
            st.write(user.get('name') or 'No Name 😞')
            st.link_button('steamrep', user['link_steamrep'])
            st.link_button('steam', user['link_steam'])
        with cols[1]:
            st.write(f'Slots used: {user["slots_used"]}/{user["bp_info"]["inventory_slots"]}')
            st.write(f'Ref Value: {user["ref_value"]}')
        if user["have_ban"]:
            st.warning('Have ban')

        if user.get('spelled_items') or None:
            st.write('Spelled items:')

            for sp_item in user['spelled_items']:
                with st.container(border=True):
                    cols = st.columns(3, gap="small")

                    if sp_item.get("icon_url") or None:
                        image_src = f'https://community.akamai.steamstatic.com/economy/image/{sp_item["icon_url"]}?allow_animated=1'
                        with cols[0]:
                            st.image(image_src, width=128)

                    item_name = f'{sp_item.get("quality") or ""} {sp_item["market_hash_name"]} {"" if sp_item["tradable"] else "**Non tradable!!**"}'
                    with cols[2]:
                        st.write(item_name)
                    
                    spells = f'{len(sp_item["spells"])} spells: ' + ','.join(v for v in sp_item['spells'])
                    with cols[1]:
                        st.write(spells)
                
                
        if user.get('halloween_items') or None:       
            st.write('Halloween items:')
            for hl_item in user['spelled_items']:
                st.write(hl_item)

        # st.write(f'Last parsed me: {datetime.strptime(user["last_parsed"], "%Y-%m-%d %H:%M:%S")}')
        # st.write(f'Last parsed bp: {datetime.strptime(user["bp_info"]["last_parsed_bp"], "%Y-%m-%d %H:%M:%S")}')
        st.write(f'Last parsed me: {user["last_parsed"]}')
        st.write(f'Last parsed by bp: {user["bp_info"]["last_parsed_bp"]}')
        st.write(f'Comment: {user.get("comment") or ""}')

        