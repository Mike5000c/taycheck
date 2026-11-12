import json
import os
import time
import certifi
import requests

# Configuration
STORE_URL = "https://storeuk.taylorswift.com"
WEBHOOK_URL = (
    "YOUR_DISCORD_OR_TELEGRAM_WEBHOOK_URL"  # Optional: leave blank if using terminal/logs
)
CACHE_FILE = "product_cache.json"


def load_cache():
  if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
      return json.load(f)
  return {}


def save_cache(cache):
  with open(CACHE_FILE, "w") as f:
    json.dump(cache, f, indent=2)


def send_alert(message):
  print(f"[ALERT] {message}")
  if WEBHOOK_URL and "http" in WEBHOOK_URL:
    try:
      requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)
    except Exception as e:
      print(f"Failed to send webhook notification: {e}")


def check_store():
  url = f"{STORE_URL}/products.json?limit=250"
  headers = {"User-Agent": "Mozilla/5.0"}

  try:
    response = requests.get(
        url, headers=headers, verify=certifi.where(), timeout=10
    )
    if response.status_code != 200:
      print(f"Error fetching store: HTTP {response.status_code}")
      return

    data = response.json()
    products = data.get("products", [])
  except Exception as e:
    print(f"Connection error: {e}")
    return

  cache = load_cache()
  new_cache = {}
  is_first_run = len(cache) == 0

  for product in products:
    p_id = str(product["id"])
    title = product["title"]
    handle = product["handle"]
    product_url = f"{STORE_URL}/products/{handle}"

    variants = product.get("variants", [])
    variant_states = {}

    for v in variants:
      v_id = str(v["id"])
      v_title = v["title"]
      available = v.get("available", False)
      price = v.get("price")
      variant_states[v_id] = {
          "title": v_title,
          "available": available,
          "price": price,
      }

      if not is_first_run and p_id in cache:
        old_v = cache[p_id]["variants"].get(v_id)
        if old_v and not old_v["available"] and available:
          send_alert(
              f"🟢 **RESTOCK ALERT!**\n**{title}**"
              f" ({v_title})\nPrice: ${price}\n{product_url}"
          )

    if not is_first_run and p_id not in cache:
      send_alert(f"🚨 **NEW PRODUCT DROP!**\n**{title}**\nLink: {product_url}")

    new_cache[p_id] = {"title": title, "variants": variant_states}

  if is_first_run and new_cache:
    print(f"Initial baseline saved. Tracking {len(new_cache)} products.")

  save_cache(new_cache)


if __name__ == "__main__":
  check_store()