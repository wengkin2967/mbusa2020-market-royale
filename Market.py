"""
    A market that contains the prices of the products in PRODUCTS and 
    buy/sell/get_prices methods.

    Andrew Turpin
    Sat 11 Apr 2020 17:51:25 AEST
"""
import random

    # tuples are min and max prices
PRODUCTS = ['Food', 'Electronics', 'Social', 'Hardware']
P_BOUNDS = {'Food':(80,120), 'Electronics':(200,1000), 'Social':(20,80), 'Hardware':(10,1000)} # price bounds
A_BOUNDS = {'Food':(50,100), 'Electronics':(5,30), 'Social':(10,200), 'Hardware':(1,5)} # price bounds

class Market:
    def __init__(self):
        self.prices = {k:random.randint(v[0],v[1]) for k,v in P_BOUNDS.items()}   # price of each key
        #self.amounts = {k:random.randint(v[0],v[1]) for k,v in A_BOUNDS.items()}   # amount of each key
        self.amounts = {k:7*v[1] for k,v in A_BOUNDS.items()}   # amount of each key

    def get_prices(self): return self.prices.copy()
    def get_price_amount(self): return {k:(self.prices[k],self.amounts[k]) for k in PRODUCTS}

    def sell(self, product, amount):
        """Sell amount up to as much as I have and return the product and amount sold & cost.
        """
        assert(product in PRODUCTS)
        assert(type(amount) is int)
        if amount < 0:
            return (product, 0, 0)
        a = min(amount, self.amounts[product])
        self.amounts[product] -= a
        return (product, a, self.prices[product] * a)

    def buy(self, product, amount):
        """Buy whatever - no restrictions. @return product and amount and cash.
        """
        assert(product in PRODUCTS)
        assert(type(amount) is int)
        if amount < 0:
            return (product, 0, 0)
        self.amounts[product] += amount
        return (product, amount, self.prices[product] * amount)
