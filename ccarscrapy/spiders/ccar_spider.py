import re
import matplotlib.pyplot as plt
import scrapy
from scrapy import Selector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


class CcarSpider(scrapy.Spider):
    name = "transactions_ccar"

    def __init__(self):
        self.dummy_url = 'http://quotes.toscrape.com'
        self.driver = webdriver.Firefox(options=self.get_options())

    def start_requests(self):
        yield scrapy.Request(url=self.dummy_url, callback=self.get_transactions)

    def get_transactions(self, response):
        url = 'https://bscscan.com/dextracker?q=0x50332bdca94673f33401776365b66cc4e81ac81d&ps=100&p=1'
        self.get_url(url)
        transactions = []
        while self.has_more_itens():
            sellings = self.find_transactions_sells(self.driver.page_source)
            transactions += self.enrich_transaction(sellings, "sell")
            purchases = self.find_transactions_purchases(self.driver.page_source)
            transactions += self.enrich_transaction(purchases, "buy")

            self.go_to_next_page()

        self.driver.quit()
        data = self.accumulate_total(transactions)
        data.update({"labels": ["BUY", "SELL"]})
        self.plot_chart(data)

    def enrich_transaction(self, bare_transaction, type):
        transactions = []
        for i in range(0, len(bare_transaction) - 1, 3):
            transactions.append(
                {"currency": bare_transaction[i + 1], "value": bare_transaction[i].strip(), "type": type})
        return transactions

    def accumulate_total(self, data):
        buys = filter(lambda transaction: transaction["type"] == "buy", data)
        sells = filter(lambda transaction: transaction["type"] == "sell", data)
        total_buys = self.get_total(buys)
        total_sells = self.get_total(sells)

        return {"total_buys": total_buys, "total_sells": total_sells}

    def plot_chart(self, data):
        fig1, ax1 = plt.subplots()
        ax1.pie([data["total_buys"], data["total_sells"]], labels=data["labels"], autopct='%1.1f%%',
                shadow=True, startangle=90)
        plt.show()

    def get_total(self, transactions):
        total = 0
        for transaction in transactions:
            value = self.convert_to_float(transaction["value"])
            total = total + round(value)
        return total

    def convert_to_float(self, value):
        value_valid = self.convert_to_a_valid_number_pattern(value)
        return float(value_valid)

    def convert_to_a_valid_number_pattern(self, value):
        if re.match("(\d*),(\d*)\.(.*)", value) is not None:
            return re.sub("(\d*),(\d*)\.(.*)", "\\1\\2.\\3", value)
        else:
            return re.sub("(\d*),", "\\1.", value)

    def get_url(self, url):
        self.driver.get(url)

    def get_options(self):
        options = webdriver.FirefoxOptions()
        options.headless = True
        return options

    def wait_for_table_loaded(self):
        wait = WebDriverWait(self.driver, 10)
        wait.until(
            EC.presence_of_element_located((By.XPATH, "//table[contains(@class,'table table-hover')]")))

    def has_more_itens(self):
        try:
            self.driver.find_element(By.XPATH, "//tbody/tr")
            return True
        except:
            return False

    def get_currency_value(self, transactions):
        for i in range(0, len(transactions) - 1, 3):
            return {"currency": transactions[i + 1], "value": transactions[i].replace("\n", "")}

    def append_output(self, transactions):
        for i in range(0, len(transactions) - 1, 3):
            return {"currency": transactions[i + 1], "value": transactions[i].replace("\n", "")}

    def go_to_next_page(self):
        self.driver.find_element(By.XPATH, "//a[@aria-label='Next']").click()

    def find_transactions_sells(self, page_source):
        sel = Selector(text=page_source)
        return sel.xpath("//tr/td[3][contains(.,'CCAR')]//text()").getall()

    def find_transactions_purchases(self, page_source):
        sel = Selector(text=page_source)
        return sel.xpath("//tr/td[5][contains(.,'CCAR')]//text()").getall()
