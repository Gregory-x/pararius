import requests
import json
import time
import os
from bs4 import BeautifulSoup
import random

# To do: 
# -apply to listing: go to each listing['url'] one by one to which I wanna apply to: select "Contact the estate agent"
#  get href from "button button--secondary listing-reaction-button listing-reaction-button--contact-agent "
#  and with https://www.pararius.com + href we get contact form, there send payload with all required fields -> DONE    
# -detailed search
# -custom text based on template  +  description analysis and based on that

CHECK_INTERVAL = 3  # seconds (5 minutes)
SEEN_FILE = "seen_listings.json"
LOGIN_URL = "https://www.pararius.com/login-email"
URL = "https://www.pararius.com/apartments/eindhoven/500-800"#"https://www.pararius.com/apartments/amsterdam/200-2500"
USERNAME = "gyerek116@gmail.com"
PASSWORD = "FASZFASZ!@#123a"
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1415806194861211790/G8Czl0YrVwppnSsk7dcX_ovtSA18A-bWIEejMXDZJugCCeCqCeMgPB6bWZe0UvVY82xy"
CHECK_INTERVAL = 10  # seconds (5 minutes)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.pararius.com/english"
}

session = requests.Session()


# Load previously seen IDs
def load_seen_ids():
    global seen_ids
    print("Loading seen IDs...")
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r") as f:
                data = f.read().strip()
                if data:
                    seen_ids = set(json.loads(data))
                else:
                    seen_ids = set()
        except Exception as e:
            print("Error loading seen IDs:", e)
            seen_ids = set()
    else:
        seen_ids = set()


def login():
    # Step 1: Get login page
    print("LOGIN")
    r = session.get(LOGIN_URL, headers=HEADERS)
    r.raise_for_status()

    # Step 2: Parse hidden token
    soup = BeautifulSoup(r.text, "html.parser")
    token = soup.find("input", {"name": "_token"})["value"]

    # Step 3: Send login POST
    payload = {
        "_token": token,
        "email": USERNAME,
        "password": PASSWORD,
    }
    resp = session.post(LOGIN_URL, data=payload, headers=HEADERS, allow_redirects=False)

    if resp.status_code in (200, 302):
        print("✅ Logged in successfully")
    else:
        print("❌ Login failed:", resp.status_code, resp.text[:200])

def fetch_listings():
    listings = []
    page = 1
    while True:
        if page == 1:
            page_url = URL
        else:
            page_url = f"{URL}/page-{page}"
            resp = session.get(page_url, headers=HEADERS)
            if resp.url == URL:
                break
        resp = session.get(page_url, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("section.listing-search-item")
        if not items:
            break  # No more listings, exit loop
        for item in items:
            title = item.select_one(".listing-search-item__title").get_text(strip=True)
            link = item.select_one(".listing-search-item__title a")["href"]
            price = item.select_one(".listing-search-item__price").get_text(strip=True)
            location = item.select_one(".listing-search-item__sub-title").get_text(strip=True)
            area_elem = item.select_one(".illustrated-features__item.illustrated-features__item--surface-area")
            area = area_elem.get_text(strip=True) if area_elem else "N/A"
            image_elem = item.select_one(".picture__image")
            image_url = image_elem["src"] if image_elem and image_elem.has_attr("src") else "N/A"
            rooms_elem = item.select_one(".illustrated-features__item.illustrated-features__item--number-of-rooms")
            rooms = rooms_elem.get_text(strip=True) if rooms_elem else "N/A"
            listings.append({
                "title": title,
                "url": "https://www.pararius.com" + link,
                "price": price,
                "location": location,
                "area": area,
                "rooms": rooms,
                "image_url": image_url
            })
        print("Iteration: ", page)    
        page += 1
    return listings

def send_discord_message(listing):
    link = listing['url']
    image_url = listing['image_url']
    
    embed = {
        "title": listing["title"],
        "url": link,
        "description": f"{listing['location']}",
        "color": 5814783,  # nice blue
        "fields": [
            {"name": "Price", "value": listing["price"], "inline": True},
            {"name": "Size", "value": listing['area'], "inline": True},
            {"name": "Rooms", "value": listing["rooms"], "inline": True}

        ],
        "image": {"url": image_url}
    }

    data = {"embeds": [embed]}
    try:
        requests.post(DISCORD_WEBHOOK, json=data)
    except Exception as e:
        print("Error sending to Discord:", e)

def get_new_listings():
    global new_listings
    listings = fetch_listings()
    print(listings)
    print(len(listings))  # This prints the number of listings
    new_listings = [l for l in listings if l["url"] not in seen_ids]

        #print(new_listings)
       
    if not new_listings:
        print("No new listings")
    else:
        for listing in new_listings:
                send_discord_message(listing)
                print("New listing found, sent to Discord:", listing["title"], "with link: ", listing["url"])
                seen_ids.add(listing["url"])
                #if(apply_to_all):
                #    apply_to_listing(listing["id"])
      

        # Save seen IDs
        with open(SEEN_FILE, "w") as f:
            json.dump(list(seen_ids), f)

        print("Ending in:", CHECK_INTERVAL ,"...")
        time.sleep(CHECK_INTERVAL)
        return

def apply_to_listing():
    print("Applying to listings...")
    for l in new_listings:
        contact_url = l['url']
        resp = session.get(contact_url, headers=HEADERS)
        soup = BeautifulSoup(resp.text, "html.parser")

        #contact_button = soup.find("a", class_="listing-reaction-button--contact-agent")
        contact_button = soup.find("a", href=lambda x: x and x.startswith("/contact/"))

        if contact_button:
           # print(f"Applying to listing {l["url"]}")
            contact_href = contact_button['href']
            full_contact_url = "https://www.pararius.com" + contact_href
            contact_resp = session.get(full_contact_url, headers=HEADERS)
            contact_resp.raise_for_status()
            contact_soup = BeautifulSoup(contact_resp.text, "html.parser")
            token = contact_soup.find("input", {"name": "contact_agent_huurprofiel_form[_token]"})["value"] # contact_agent_huurprofiel_form[_token]
            print("Using url", full_contact_url)

            #submit_button = soup.find("button", {"type": "submit"})
            #guid_name = submit_button["name"]

            payload = {
                "contact_agent_huurprofiel_form[_token]": token,
                "contact_agent_huurprofiel_form[motivation]": "Hello, I am very interested in this property. Please contact me for further details.",
                "contact_agent_huurprofiel_form[salutation]": "0",
                "contact_agent_huurprofiel_form[first_name]": "Nard",
                "contact_agent_huurprofiel_form[last_name]": "Lamb",
                "contact_agent_huurprofiel_form[phone_number]":"+31 958 489 325",
                "contact_agent_huurprofiel_form[date_of_birth]": "2001-02-10",
                "contact_agent_huurprofiel_form[work_situation]":"",
                "contact_agent_huurprofiel_form[gross_annual_household_income]":"",
                "contact_agent_huurprofiel_form[guarantor]":"",
                "contact_agent_huurprofiel_form[preferred_living_situation]":"",
                "contact_agent_huurprofiel_form[number_of_tenants]":"",
                "contact_agent_huurprofiel_form[rent_start_date]":"",
                "contact_agent_huurprofiel_form[preferred_contract_period]":"",
                "contact_agent_huurprofiel_form[current_housing_situation]":""

            }
            resp = session.post(full_contact_url, data=payload, headers=HEADERS, allow_redirects=False)
            if resp.status_code == 302:
                print(f"✅ Applied to listing {l["url"]}")
            else:
                # If first attempt failed and no roommate email, try with one
                #if not roommate_email:
                    #print(f"⚠️ Initial apply failed for listing {listing_id}, trying with roommate email...")
                    #return apply_to_listing(listing_id, roommate_email="gergely.bruncsak@gmail.com") # modify for different co-tenant
               # else:
                    print(f"❌ Failure: already applied to listing {l["url"]} or other error")
                    with open("apply_fail.html", "w", encoding="utf-8") as f:
                        f.write(resp.text)
        r = random.randint(4, 8)
        time.sleep(r)        

    return

def main():
    
    global seen_ids
    
    load_seen_ids()

    clear_seen_ids = False
    if (clear_seen_ids):
        seen_ids.clear()

    login()

    get_new_listings()
    
    apply_to_listing()



if __name__ == "__main__":
    main()
