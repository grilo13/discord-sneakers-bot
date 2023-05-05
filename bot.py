import sys

import requests
from bs4 import BeautifulSoup


class NotificationBot:
    def __init__(self, website, reference, model, size):
        self.website = website

        self.reference = reference
        self.model = model
        self.size = size

        self.available_websites = {
            'New Balance': 'https://www.newbalance.pt/pt/'
        }

        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}

    def validate_website(self) -> bool:
        if self.available_websites.get(self.website):
            return True
        return False

    def execute_bot(self) -> bool:
        if not self.validate_website():
            sys.exit(0)

        response = requests.get(self.available_websites.get(self.website) + self.model, headers=self.headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            products = soup.find_all("div", {"class": 'product-tile w-100'})
            for product in products:
                title_body = product.findNext("div", {"class": 'image-container'})
                product_href = title_body.findNext("a").get('href')
                product_reference = title_body.findNext("div", {"class": 'product-id d-none'}).text

                if self.reference == product_reference:
                    has_size = self.check_sizes(product_href)

                    if has_size:
                        return True
                    else:
                        return False

    def check_sizes(self, product_url) -> bool:
        response = requests.get(self.available_websites.get(self.website) + product_url, headers=self.headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            sizes_table = soup.find("div", {"class", "select-attribute-grid attribute-grid-5"})
            products = sizes_table.find_all("span")
            for product in products:
                product_size = product.text.strip()
                if product_size == self.size:
                    span_class_value = product.attrs['class']
                    if 'selectable' in span_class_value:
                        return True
                    else:
                        return False
            return True

        return False


if __name__ == '__main__':
    bot = NotificationBot('New Balance', 'BB480LV1-36569', '480', '40')
    bot.execute_bot()
