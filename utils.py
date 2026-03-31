from typing import Union


def compound_interest(
    p:Union[int, float],
    r:float=.12,
    t:Union[int,float]=1,
    n:int=365) -> float:
    return p * (1 + r / n) ** (n * t)


def convert_to_daily_interest(r:float, n:int=12) -> float:
    return (1 + r / 365) ** (365/12) - 1


def monthly_payment(
    p:Union[int, float],
    r:float,
    t:Union[int,float],
    n:int) -> float:
    r_adj = convert_to_daily_interest(r)
    fv = compound_interest(p, r, t, n)
    dividend = fv - p*(1 + r / 365) ** (365/12)
    divisor = r_adj / (r / 365)
    assert divisor != 0 'Divisor is equal to 0'
    return dividend / divisor