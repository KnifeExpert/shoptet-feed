import xml.etree.ElementTree as ET
import requests
import filecmp
import os

def format_decimal(value):
    return value.replace(',', '.').strip()

def transform_product(supplier_item):
    # EAN môže byť prázdny — NEvyhadzujeme produkt
    ean = supplier_item.findtext("ean", default="").strip()

    shopitem = ET.Element("SHOPITEM")
    item_id = supplier_item.findtext("item_id", default="N/A").strip()
    code_elem = ET.SubElement(shopitem, "CODE")
    code_elem.text = item_id

    productname = supplier_item.findtext("productname", default="N/A").strip()
    name_elem = ET.SubElement(shopitem, "NAME")
    name_elem.text = f"{productname}, {item_id}" if productname != "N/A" else item_id

    description = supplier_item.findtext("description", default="").strip()
    desc_elem = ET.SubElement(shopitem, "DESCRIPTION")
    desc_elem.text = description

    orig_url = supplier_item.findtext("url", default="N/A").strip()
    orig_url_elem = ET.SubElement(shopitem, "ORIG_URL")
    orig_url_elem.text = orig_url

    item_condition_elem = ET.SubElement(shopitem, "ITEM_CONDITION")
    grade_elem = ET.SubElement(item_condition_elem, "GRADE")
    grade_elem.text = "used"
    ic_desc_elem = ET.SubElement(item_condition_elem, "DESCRIPTION")
    ic_desc_elem.text = "No description provided."

    price_vat = supplier_item.findtext("price_vat", default="0").strip()
    price_vat_elem = ET.SubElement(shopitem, "PRICE_VAT")
    price_vat_elem.text = format_decimal(price_vat)

    delivery_date = supplier_item.findtext("delivery_date", default="").strip()
    availability_elem = ET.SubElement(shopitem, "AVAILABILITY")
    negative_elem = ET.SubElement(shopitem, "NEGATIVE_AMOUNT")
    if delivery_date == "0":
        availability_elem.text = "3-7 dní"
        negative_elem.text = "1"
    else:
        availability_elem.text = "7-11 dní"
        negative_elem.text = "0"

    categorytext = supplier_item.findtext("categorytext", default="N/A").strip()
    categories_elem = ET.SubElement(shopitem, "CATEGORIES")
    category_elem = ET.SubElement(categories_elem, "CATEGORY")
    category_elem.text = categorytext

    imgurl = supplier_item.findtext("imgurl", default="N/A").strip()
    images_elem = ET.SubElement(shopitem, "IMAGES")
    image_elem = ET.SubElement(images_elem, "IMAGE")
    image_elem.text = imgurl

    manufacturer = supplier_item.findtext("manufacturer", default="N/A").strip()
    manufacturer_elem = ET.SubElement(shopitem, "MANUFACTURER")
    manufacturer_elem.text = manufacturer

    # EAN môže byť prázdny
    ean_elem = ET.SubElement(shopitem, "EAN")
    ean_elem.text = ean

    defaults = {
        "ACTION_PRICE": "0",
        "ACTION_PRICE_FROM": "2023-01-01",
        "ACTION_PRICE_UNTIL": "2023-12-31",
        "ADULT": "false",
        "ALLOWS_IPLATBA": "false",
        "ALLOWS_PAYU": "false",
        "ALLOWS_PAY_ONLINE": "false",
        "APPLY_DISCOUNT_COUPON": "false",
        "APPLY_LOYALTY_DISCOUNT": "false",
        "APPLY_QUANTITY_DISCOUNT": "false",
        "APPLY_VOLUME_DISCOUNT": "false",
        "ARUKERESO_HIDDEN": "false",
        "ARUKERESO_MARKETPLACE_HIDDEN": "false",
        "ATYPICAL_BILLING": "false",
        "ATYPICAL_SHIPPING": "false",
        "CURRENCY": "EUR",
        "DECIMAL_COUNT": "2",
        "EXTERNAL_ID": "N/A",
        "FIRMY_CZ": "false",
        "FREE_BILLING": "false",
        "FREE_SHIPPING": "false",
        "GUID": "00000000-0000-0000-0000-000000000000",
        "HEUREKA_CART_HIDDEN": "false",
        "HEUREKA_HIDDEN": "false",
        "ITEM_TYPE": "product",
        "MIN_PRICE_RATIO": "0.0",
        "PRICE": "0.0",
        "PRICE_RATIO": "0.0",
        "TOLL_FREE": "false",
        "VAT": "20",
        "VISIBILITY": "visible",
        "VISIBLE": "true",
        "XML_FEED_NAME": "N/A",
        "ZBOZI_HIDDEN": "false"
    }

    for tag, value in defaults.items():
        elem = ET.SubElement(shopitem, tag)
        elem.text = value

    sizeid_elem = ET.SubElement(shopitem, "SIZEID")
    id_elem = ET.SubElement(sizeid_elem, "ID")
    id_elem.text = "0"
    label_elem = ET.SubElement(sizeid_elem, "LABEL")
    label_elem.text = "N/A"

    return shopitem

def transform_feed(supplier_feed_url, output_filename):
    try:
        response = requests.get(supplier_feed_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Chyba pri sťahovaní dodávateľského feedu: {e}")
        exit(1)

    xml_data = response.text

    try:
        supplier_root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"Chyba pri parsovaní dodávateľského feedu: {e}")
        exit(1)

    shop = ET.Element("SHOP")

    for tag in ["shopitem", "SHOPITEM"]:
        for item in supplier_root.findall(f".//{tag}"):
            transformed_item = transform_product(item)
            if transformed_item is not None:
                shop.append(transformed_item)

    return ET.ElementTree(shop)

if __name__ == "__main__":
    supplier_feed_url = "https://vreckovynoz.sk/heureka"
    output_file = "valid_shoptet_feed.xml"
    temp_file = "temp_output.xml"

    tree = transform_feed(supplier_feed_url, temp_file)
    tree.write(temp_file, encoding="UTF-8", xml_declaration=True)

    # Vždy prepíš feed (neporovnávaj)
    os.replace(temp_file, output_file)
    print(f"Feed prepísaný: {output_file}")
