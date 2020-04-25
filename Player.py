# Player class for assignment
from BasePlayer import BasePlayer
import Command


class Player(BasePlayer):

    def __init__(self):
        pass
    
    def take_turn(self, loc, this_market, info, black_markets, grey_markets):
        goals = self.goal
        gold = self.gold
        amount_to_buy = 0
        print("GOALS " + str(goals))
        print ("this_market" + str(this_market))
        products_to_consider = {} #contains products and total cost (amount_to_buy * price)
        amount_to_buy = 0 
        
        if (len(this_market) > 0) and (len(goals) > 0): #only consider buying if research is done and goal is incomplete
            for p,v in goals.items(): #loop through goal to match with market's inventory and calculate total cost for each 
                if p in this_market:
                    amount_to_buy = min(this_market[p][1], v)
                    products_to_consider[p] = amount_to_buy * this_market[p][0]
            
            product_to_buy = min(products_to_consider, key=products_to_consider.get) #picking product with lowest cost to fulfil a goal
            final_cost = products_to_consider[product_to_buy]
            amount_to_buy = min(this_market[product_to_buy][1], goals[product_to_buy])        
            
                    if goals[product_to_buy] == amount_to_buy: #goal fulfilled, remove product from goal
                        print("GOALS_before_fulfil_one_product: " + str(goals))
                        goals.pop(product_to_buy)
                        print("GOALS_after_fulfil_one_product: " + str(goals))
                    else: #goal partially fulfilled, update number left to buy
                        goals[product_to_buy] -= amount_to_buy 
                        print("GOALS_after_buying_some: " + str(goals))
                        
                    return(Command.BUY,(product_to_buy, amount_to_buy)) # pass the command to buy
           
            
        return (Command.RESEARCH, None)