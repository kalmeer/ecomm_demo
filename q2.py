"""
Fetches all active products from a Shopify store using GraphQL API and saves them to CSV.
"""

import requests
import csv

SHOP_URL = "sdpjy2-rp.myshopify.com"
API_VERSION = "2026-01"
ACCESS_TOKEN = "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"

PRODUCTS_QUERY = """
query getProducts($cursor: String) {
  products(first: 50, after: $cursor, query: "status:active") {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        id
        title
        tags
        variants(first: 1) {
          edges {
            node {
              price
              compareAtPrice
            }
          }
        }
        collections(first: 50) {
          edges {
            node {
              title
            }
          }
        }
      }
    }
  }
}
"""


def fetch_all_products():
    endpoint = f"https://{SHOP_URL}/admin/api/{API_VERSION}/graphql.json"
    headers = {"X-Shopify-Access-Token": ACCESS_TOKEN, "Content-Type": "application/json"}
    
    all_products = []
    cursor = None
    
    while True:
        response = requests.post(endpoint, json={"query": PRODUCTS_QUERY, "variables": {"cursor": cursor}}, headers=headers)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break
        
        data = response.json()
        if "errors" in data:
            print(f"GraphQL Error: {data['errors']}")
            break
        
        products_data = data.get("data", {}).get("products", {})
        edges = products_data.get("edges", [])
        
        for edge in edges:
            node = edge["node"]
            variants = node.get("variants", {}).get("edges", [])
            price = variants[0]["node"].get("price", "0") if variants else "0"
            compare_at_price = variants[0]["node"].get("compareAtPrice") if variants else None
            
            is_on_sale = False
            if compare_at_price:
                try:
                    is_on_sale = float(compare_at_price) > float(price)
                except (ValueError, TypeError):
                    pass
            
            collections = [c["node"]["title"] for c in node.get("collections", {}).get("edges", [])]
            full_id = node.get("id", "")
            
            all_products.append({
                "id": full_id.split("/")[-1] if "/" in full_id else full_id,
                "title": node.get("title", ""),
                "price": price,
                "tags": ", ".join(node.get("tags", [])),
                "collections": ", ".join(collections),
                "sale": is_on_sale
            })
        
        if not products_data.get("pageInfo", {}).get("hasNextPage", False):
            break
        cursor = products_data.get("pageInfo", {}).get("endCursor")
    
    return all_products


def save_to_csv(products, filename="products.csv"):
    if not products:
        return
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "price", "tags", "collections", "sale"])
        writer.writeheader()
        writer.writerows(products)
    
    print(f"Saved {len(products)} products to {filename}")


if __name__ == "__main__":
    products = fetch_all_products()
    save_to_csv(products)