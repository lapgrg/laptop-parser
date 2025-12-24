
#!/usr/bin/env python3
"""
Парсер ноутбуков с грузинских сайтов
Находит ноутбуки дороже 7000 GEL
"""

import json
import csv
import re
import os
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Минимальная цена для фильтрации
MIN_PRICE = 7000

# Создаём папку для результатов
os.makedirs('output', exist_ok=True)

def extract_price(text):
    """Извлекает число из текста цены"""
    if not text:
        return 0
    numbers = re.findall(r'[\d\s]+', text.replace(',', '').replace(' ', ''))
    if numbers:
        try:
            return int(''.join(numbers[0].split()))
        except:
            return 0
    return 0

def scrape_site(page, site_config):
    """Парсит один сайт"""
    products = []
    
    try:
        print(f"🔍 Парсинг {site_config['name']}...")
        page.goto(site_config['url'], timeout=60000, wait_until='networkidle')
        page.wait_for_timeout(3000)
        
        # Прокручиваем страницу для загрузки всех товаров
        for _ in range(5):
            page.evaluate('window.scrollBy(0, 1000)')
            page.wait_for_timeout(500)
        
        html = page.content()
        soup = BeautifulSoup(html, 'lxml')
        
        items = soup.select(site_config['item_selector'])
        print(f"   Найдено товаров: {len(items)}")
        
        for item in items:
            try:
                # Название
                name_elem = item.select_one(site_config['name_selector'])
                name = name_elem.get_text(strip=True) if name_elem else "Без названия"
                
                # Цена
                price_elem = item.select_one(site_config['price_selector'])
                price_text = price_elem.get_text(strip=True) if price_elem else "0"
                price = extract_price(price_text)
                
                # Ссылка
                link_elem = item.select_one(site_config['link_selector'])
                link = ""
                if link_elem:
                    link = link_elem.get('href', '')
                    if link and not link.startswith('http'):
                        link = site_config['base_url'] + link
                
                # Фильтруем по цене
                if price >= MIN_PRICE:
                    products.append({
                        'name': name,
                        'price': price,
                        'price_formatted': f"{price:,} GEL".replace(',', ' '),
                        'link': link,
                        'site': site_config['name']
                    })
                    
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"❌ Ошибка при парсинге {site_config['name']}: {e}")
    
    print(f"   ✅ Ноутбуков >= {MIN_PRICE} GEL: {len(products)}")
    return products

def main():
    # Конфигурация сайтов
    sites = [
        {
            'name': 'Ultra.ge',
            'url': 'https://ultra.ge/category/notebook?sort=price_desc',
            'base_url': 'https://ultra.ge',
            'item_selector': '.product-item, .product-card, [class*="product"]',
            'name_selector': '.product-name, .product-title, h3, h4, [class*="name"], [class*="title"]',
            'price_selector': '.product-price, .price, [class*="price"]',
            'link_selector': 'a'
        },
        {
            'name': 'Allmarket.ge',
            'url': 'https://allmarket.ge/ka/products?category_id=46&sort=-price',
            'base_url': 'https://allmarket.ge',
            'item_selector': '.product-card, .product-item, [class*="product"]',
            'name_selector': '.product-name, .name, h3, [class*="name"], [class*="title"]',
            'price_selector': '.price, [class*="price"]',
            'link_selector': 'a'
        },
        {
            'name': 'EE.ge',
            'url': 'https://ee.ge/ka/products/computers-and-notebooks/notebooks?sort=-price',
            'base_url': 'https://ee.ge',
            'item_selector': '.product-card, .product-item, [class*="product"]',
            'name_selector': '.product-name, .name, h3, [class*="name"]',
            'price_selector': '.price, [class*="price"]',
            'link_selector': 'a'
        },
        {
            'name': 'PCShop.ge',
            'url': 'https://pcshop.ge/product-category/notebook/?orderby=price-desc',
            'base_url': 'https://pcshop.ge',
            'item_selector': '.product, .product-item, [class*="product"]',
            'name_selector': '.woocommerce-loop-product__title, h2, .product-title',
            'price_selector': '.price, .woocommerce-Price-amount',
            'link_selector': 'a'
        },
        {
            'name': 'Gaming-Laptops.ge',
            'url': 'https://gaming-laptops.ge/product-category/laptops/?orderby=price-desc',
            'base_url': 'https://gaming-laptops.ge',
            'item_selector': '.product, [class*="product"]',
            'name_selector': '.woocommerce-loop-product__title, h2',
            'price_selector': '.price, .woocommerce-Price-amount',
            'link_selector': 'a'
        },
        {
            'name': 'Alta.ge',
            'url': 'https://alta.ge/notebooks.html?dir=desc&order=price',
            'base_url': 'https://alta.ge',
            'item_selector': '.product-item, .item, [class*="product"]',
            'name_selector': '.product-item-link, .product-name, a[class*="product"]',
            'price_selector': '.price, [class*="price"]',
            'link_selector': 'a'
        },
        {
            'name': 'Zoommer.ge',
            'url': 'https://zoommer.ge/ka/computers-and-notebooks/notebooks?sort=price_desc',
            'base_url': 'https://zoommer.ge',
            'item_selector': '.product-card, [class*="ProductCard"], [class*="product"]',
            'name_selector': '.product-name, [class*="name"], [class*="title"], h3',
            'price_selector': '.price, [class*="price"]',
            'link_selector': 'a'
        }
    ]
    
    all_products = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        for site in sites:
            products = scrape_site(page, site)
            all_products.extend(products)
        
        browser.close()
    
    # Сортируем по цене (от высокой к низкой)
    all_products.sort(key=lambda x: x['price'], reverse=True)
    
    # Сохраняем результаты
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # JSON
    with open('output/laptops.json', 'w', encoding='utf-8') as f:
        json.dump({
            'updated': timestamp,
            'count': len(all_products),
            'min_price': MIN_PRICE,
            'products': all_products
        }, f, ensure_ascii=False, indent=2)
    
    # CSV
    with open('output/laptops.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['Название', 'Цена', 'Сайт', 'Ссылка'])
        for p in all_products:
            writer.writerow([p['name'], p['price_formatted'], p['site'], p['link']])
    
    # HTML
    html_content = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ноутбуки >= {MIN_PRICE} GEL</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ text-align: center; margin-bottom: 10px; color: #333; }}
        .info {{ text-align: center; color: #666; margin-bottom: 20px; }}
        .search {{ width: 100%; padding: 15px; font-size: 16px; border: 2px solid #ddd; border-radius: 10px; margin-bottom: 20px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
        .card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); transition: transform 0.2s; }}
        .card:hover {{ transform: translateY(-5px); }}
        .card h3 {{ font-size: 14px; color: #333; margin-bottom: 10px; line-height: 1.4; height: 60px; overflow: hidden; }}
        .price {{ font-size: 24px; font-weight: bold; color: #e53935; margin-bottom: 10px; }}
        .site {{ display: inline-block; background: #e3f2fd; color: #1976d2; padding: 4px 12px; border-radius: 20px; font-size: 12px; margin-bottom: 10px; }}
        .link {{ display: block; text-align: center; background: #4CAF50; color: white; padding: 10px; border-radius: 8px; text-decoration: none; }}
        .link:hover {{ background: #43A047; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>💻 Ноутбуки >= {MIN_PRICE:,} GEL</h1>
        <p class="info">Обновлено: {timestamp} | Найдено: {len(all_products)} шт.</p>
        <input type="text" class="search" placeholder="🔍 Поиск..." onkeyup="search(this.value)">
        <div class="grid" id="products">
'''
    
    for p in all_products:
        html_content += f'''
            <div class="card" data-name="{p['name'].lower()}">
                <h3>{p['name']}</h3>
                <div class="price">{p['price_formatted']}</div>
                <span class="site">{p['site']}</span>
                <a href="{p['link']}" target="_blank" class="link">Открыть →</a>
            </div>
'''
    
    html_content += '''
        </div>
    </div>
    <script>
        function search(q) {
            q = q.toLowerCase();
            document.querySelectorAll('.card').forEach(card => {
                card.style.display = card.dataset.name.includes(q) ? 'block' : 'none';
            });
        }
    </script>
</body>
</html>'''
    
    with open('output/laptops.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ Готово! Найдено {len(all_products)} ноутбуков >= {MIN_PRICE} GEL")
    print("📁 Результаты сохранены в папке output/")

if __name__ == '__main__':
    main()
