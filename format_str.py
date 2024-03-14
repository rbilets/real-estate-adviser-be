sales = """Today
Nov 30, 2020
Date
Price Changed
GVR #R2515162
*
Price
Nov 5, 2020
Date
Listed (Active)
GVR #R2515162
*
Price
Dec 2005, Sold for $588,000
Dec 5, 2005
Date
Sold (Public Records)
Public Records
$588,000 (8.8%/yr)
Price
Aug, 2004
Aug 24, 2004
Date
Listed
GVR #V501476
**
Price
Jun 2000, Sold for $371,000
Jun 19, 2000
Date
Sold (Public Records)
Public Records
$371,000 (11.4%/yr)
Price
Nov 1985, Sold for $77,000
Nov 28, 1985
Date
Sold (Public Records)
Public Records
$77,000
Price"""


sale_history = []

if sales:
    for el in sales.split("Price")[:-1]:
        print(el)
        sale_info = el.split("\n")
        date = sale_info[sale_info.index("Date") - 1]
        price = sale_info[-2]
        
        sale_data = {
            "date": date,
            "price": price.split(" (")[0] if "$" in price else None
        }
        print(sale_data)
        sale_history.append(sale_data)
        print("-"*15)



print(sale_history)