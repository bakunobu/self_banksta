from typing import Union


def compound_interest(
    p:Union[int, float],
    r:float=.12,
    t:Union[int,float]=1,
    n:int=365):
    return p * (1 + r / n) ** (n * t)