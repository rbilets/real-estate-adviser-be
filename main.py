from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

options = Options()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
options.add_argument(f'user-agent={user_agent}')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument("--disable-extensions")
options.add_experimental_option('useAutomationExtension', False)
options.add_experimental_option("excludeSwitches", ["enable-automation"])

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

search_street_address = "1018 W 58th Ave"
search_city = "Vancouver"
search_address = f"{search_street_address} {search_city}"


driver.get("https://www.redfin.ca/")
time.sleep(3)
input_field = driver.find_element(By.ID, "search-box-input")
input_field.send_keys(search_address)
search_box = driver.find_element(By.CLASS_NAME, "inline-block.SearchButton.clickable.float-right")
search_box.click()
time.sleep(3)

current_url = driver.current_url

try:
    try:
        all_prices_btn = driver.find_element(By.CLASS_NAME, "ExpandableLink.clickable")
        all_prices_btn.click()
    except:
        pass


    try: # sale_status
        sale_status = driver.find_element(By.XPATH, "/html/body/div[1]/div[10]/div[2]/div[1]/div/div/div/div[1]/div[1]/span").text
    except:
        sale_status = None
    try: # address
        address = driver.find_element(By.CLASS_NAME, "full-address").text
    except:
        address = None
    try: # key_details
        key_details = driver.find_element(By.CLASS_NAME, "KeyDetailsTable").text.lower()
    except:
        key_details = None
    try: # public_facts
        public_facts = driver.find_element(By.CLASS_NAME, "DPTableDisplay").text.lower().split("\n")
    except:
        public_facts = None
    try: # rates
        rates = driver.find_element(By.CLASS_NAME, "bp-walk-score.row.desktop").text.lower().split("\n")
    except:
        rates = None
    try: # sales
        sales = driver.find_element(By.CLASS_NAME, "timeline").text
    except:
        sales = None
    try: # schools
        schools = driver.find_element(By.CLASS_NAME, "schools-content").text.lower()
    except:
        schools = None


    if address: # address
        try:
            address = " ".join(address.split("\n"))
        except:
            address = None
    else:
        address = None
    
    if key_details: # key_details
        try:
            key_details = ",".join(key_details.split("\n"))
        except:
            key_details = None
        try:
            garage_spaces = list(filter(lambda r: "garage space" in r, key_details.split(",")))[0].split(" ")[0]
        except:
            garage_spaces = None
        try:
            parking_spaces = list(filter(lambda r: "parking space" in r, key_details.split(",")))[0].split(" ")[0]
        except:
            parking_spaces = None
    else:
        key_details, garage_spaces, parking_spaces = None, None, None
    
    if public_facts: # public_facts
        try:
            beds = public_facts[public_facts.index('beds') + 1]
        except:
            beds = None
        try:
            baths = public_facts[public_facts.index('baths') + 1]
        except:
            baths = None
        try:
            area = public_facts[public_facts.index('sq. ft.') + 1]
        except:
            area = None
        try:
            stories = public_facts[public_facts.index('stories') + 1]
        except:
            stories = None
        try:
            lot_area = public_facts[public_facts.index('lot size') + 1]
        except:
            lot_area = None
        try:
            style = public_facts[public_facts.index('style') + 1]
        except:
            style = None
        try:
            year_built = public_facts[public_facts.index('year built') + 1]
        except:
            year_built = None
        try:
            year_renovated = public_facts[public_facts.index('year renovated') + 1]
        except:
            year_renovated = None
        try:
            region = public_facts[public_facts.index('region') + 1]
        except:
            region = None
    else:
        beds, baths, area, stories, lot_area, style, year_built, year_renovated, region = None, None, None, None, None, None, None, None, None

    if rates: # rates
        try:
            walk_score = rates[rates.index("walk score®") - 2]
        except:
            walk_score = None
        try:
            transit_score = rates[rates.index("transit score®") - 2]
        except:
            transit_score = None
        try:
            bike_score = rates[rates.index("bike score®") - 2]
        except:
            bike_score = None
    else:
        walk_score, transit_score, bike_score = None, None, None

    sale_history = []
    if sales: # sales
        print(sales)
        try:
            if sales:
                for el in sales.split("Price")[:-1]:
                    try:
                        sale_info = el.split("\n")
                        date = sale_info[sale_info.index("Date") - 1]
                        price = sale_info[-2]
                        
                        sale_data = {
                            "date": date,
                            "price": price.split(" (")[0] if "$" in price else None
                        }
                        sale_history.append(sale_data)
                    except:
                        continue
        except:
            sale_history = []

    schools_less_1km = 0
    schools_1km_2km = 0
    schools_2km_5km = 0
    schools_5km_10km = 0
    schools_more_10km = 0
    if schools: #schools
        for dist in list(map(lambda d: float(d.rstrip("km")), schools.split("\n")[::3])):
            if dist < 1.0:
                schools_less_1km += 1
            elif 1.0 <= dist < 2.0:
                schools_1km_2km += 1
            elif 2.0 <= dist < 5.0:
                schools_2km_5km += 1
            elif 5.0 <= dist < 10.0:
                schools_5km_10km += 1
            elif dist >= 10.0:
                schools_more_10km += 1


    property_info = {
        "url": current_url,
        "address": address,
        "key_details": key_details,
        "sale_status": sale_status,
        "garage_spaces": garage_spaces,
        "parking_spaces": parking_spaces,
        "beds": None if beds == "—" else beds,
        "baths": None if baths == "—" else baths,
        "area": None if area == "—" else area,
        "stories": None if stories == "—" else stories,
        "lot_area": None if lot_area == "—" else lot_area,
        "style": None if style == "—" else style,
        "year_built": None if year_built == "—" else year_built,
        "year_renovated": None if year_renovated == "—" else year_renovated,
        "region": region,
        "sale_history": sale_history,
        "walk_score": walk_score,
        "transit_score": transit_score,
        "bike_score": bike_score,
        "schools_less_1km": str(schools_less_1km),
        "schools_1km_2km": str(schools_1km_2km),
        "schools_2km_5km": str(schools_2km_5km),
        "schools_5km_10km": str(schools_5km_10km),
        "schools_more_10km": str(schools_more_10km)
    }

    print(json.dumps(property_info))

except Exception as e:
    print("Error:", e)

# Close the browser
driver.quit()
