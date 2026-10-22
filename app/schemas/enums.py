from enum import StrEnum


class Size(StrEnum):
    small = "small"
    medium = "medium"
    large = "large"


class Topping(StrEnum):
    """The allowed toppings. Pineapple is deliberately missing. 🍍"""

    mozzarella = "mozzarella"
    tomato = "tomato"
    pepperoni = "pepperoni"
    sucuk = "sucuk"
    mushroom = "mushroom"
    olive = "olive"
    pepper = "pepper"
    basil = "basil"


MEAT_TOPPINGS = {Topping.pepperoni, Topping.sucuk}


class OrderStatus(StrEnum):
    preparing = "preparing"
    baking = "baking"
    on_the_way = "on_the_way"
    delivered = "delivered"
