import os, sys
directory = os.getcwd()
sys.path.insert(0, directory+"\lib")
try:
    import pyshopee2
except ImportError:
    input("Please install pyshopee2 library!")
    exit()
import random
import string
import json

PartnerID = [YOUR PARTNER ID]
APIKey = "[YOUR API KEY]"
redirect_url = "[YOUR REDIRECT URL]"

ShopeeShopIds = [[YOUR SHOP ID 1],[YOUR SHOP ID 2]]


def get_orders_ready_to_ship():
    ReadyOrders = []
    for shopid in ShopeeShopIds:
        rt,at = check_shopid_auth_valid(shopid)
        if at == "Invalid":
            continue
        client = pyshopee2.Client(shopid, PartnerID, APIKey, redirect_url, access_token=at)
                
        # get_order_by_status (UNPAID/READY_TO_SHIP/SHIPPED/COMPLETED/CANCELLED/ALL)
        resp = client.order.get_shipment_list(page_size=20)
        #print(resp)
        if "http error code" in str(resp):
            at = get_access_token(shopid,rt)
            return get_orders_ready_to_ship()
            
        if "order_list" in resp["response"]:
            for order in resp["response"]["order_list"]:
                ReadyOrders.append(order["order_sn"])
    return ReadyOrders

def get_order_items(orderid):
    items = {}
    buyername = ""
    for shopid in ShopeeShopIds:
        rt,at = check_shopid_auth_valid(shopid)
        if at == "Invalid":
            continue
        client = pyshopee2.Client(shopid, PartnerID, APIKey, redirect_url, access_token=at)

        ordersn_list = orderid
        extend = "recipient_address,item_list"
        resp = client.order.get_order_detail(order_sn_list = ordersn_list,response_optional_fields=extend)
        #print(resp)
        if "http error code" in str(resp):
            at = get_access_token(shopid,rt)
            return get_order_items(orderid)
        
        if "response" in resp:
            resp = resp["response"]
        if "order_list" in resp:
            if len(resp["order_list"]) > 0:
                buyername = resp["order_list"][0]["recipient_address"]["name"]
                for item in resp["order_list"][0]["item_list"]:
                    if "**" in item["item_sku"]:
                        item_id = item["item_sku"].replace("**","")
                        quantity = item["model_quantity_purchased"]
                        if item_id in items:
                            items[item_id] += quantity
                        else:
                            items[item_id] = quantity
    return buyername,items

def process_shipment(orderid):
    for shopid in ShopeeShopIds:
        rt,at = check_shopid_auth_valid(shopid)
        if at == "Invalid":
            continue
        client = pyshopee2.Client(shopid, PartnerID, APIKey, redirect_url, access_token=at)
        
        resp = client.logistics.get_shipping_parameter(order_sn=orderid)
        if "http error code" in str(resp):
            at = get_access_token(shopid,rt)
            return process_shipment(orderid)
        #print(resp)
        if resp["error"] == "":
            resp = resp["response"]
            if "info_needed" in resp:
                length = 25
                tracking_no = ''.join(random.choices(string.ascii_letters+string.digits,k=length))
                if "dropoff" in resp["info_needed"]:
                    shipout = client.logistics.ship_order(order_sn=orderid,dropoff={"tracking_number":tracking_no})
                if "non_integrated" in resp["info_needed"]:
                    shipout = client.logistics.ship_order(order_sn=orderid,non_integrated={"tracking_number":tracking_no})
                #print(shipout)
                if shipout["error"]=="":
                    return True


file_path = "pyshopee.json"
def save_to_cache(shopid,refresh_token,access_token):
    try:
        with open(file_path) as f:
            cached = json.load(f)
    except Exception as e:
        print(str(e))
        cached = {}
    if refresh_token is not None:
        cached[str(shopid)+"|refresh_token"] = refresh_token
    if access_token is not None:
        cached[str(shopid)+"|access_token"] = access_token
    with open(file_path, 'w') as f:
        json.dump(cached, f, sort_keys=True, indent=4)
def read_cache(shopid):
    try:
        with open(file_path) as f:
            cached = json.load(f)
    except Exception as e:
        print(str(e))
        cached = {}
    refresh_token = None
    access_token = None
    if str(shopid)+"|refresh_token" in cached:
        refresh_token = cached[str(shopid)+"|refresh_token"]
    if str(shopid)+"|access_token" in cached:
        access_token = cached[str(shopid)+"|access_token"]
    return refresh_token,access_token
def check_shopid_auth_valid(shopid):
    rt,at = read_cache(shopid)
    if at is None:
        if rt is not None:
            at = get_access_token(shopid, rt)
            if at is None:
                print("Refresh token",str(rt),"Access token",str(at),"Invalid Credentials")
                at = "Invalid"
        else:
            print("Refresh token",str(rt),"Access token",str(at),"Invalid Credentials")
            at = "Invalid"
    return rt,at
            
        
def get_refresh_code_with_upgrade():
    client = pyshopee2.Client(0, PartnerID, APIKey, redirect_url)
    upgrade_code = "496e6d786e536650484c734a6e7175586b756a667561537359766c466d724c6b"
    resp = client.public.get_refresh_token_by_upgrade_code(upgrade_code=upgrade_code,
                                                           shop_id_list=ShopeeShopIds)
    #print(resp)
    refresh_code = resp["response"]["refresh_token"]
    print(ShopeeShopIds,refresh_code)
    for shopid in ShopeeShopIds:
        save_to_cache(shopid,refresh_code,None)
        
def get_access_token(shopid,refresh_token):
    client = pyshopee2.Client(shopid, PartnerID, APIKey, redirect_url)
    resp = client.get_access_token(shopid, PartnerID, APIKey, refresh_token)
    try:
        access_token, timeout, refresh_token = resp
        print("At ->",shopid,refresh_token,access_token)
        save_to_cache(shopid,refresh_token,access_token)
        return access_token
    except:
        print(resp)
        return None
