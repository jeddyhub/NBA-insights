
import txgraffiti 
import pandas as pd

from types import MethodDescriptorType
from txgraffiti.playground import ConjecturePlayground
from txgraffiti.generators import convex_hull, linear_programming
from txgraffiti.heuristics import morgan_accept, dalmatian_accept
from txgraffiti.processing import remove_duplicates, sort_by_touch_count

def generate_conjectures(df: pd.DataFrame, feats: list, targ: str, hyps: list) -> list[txgraffiti.Conjecture]:
    
    pg = ConjecturePlayground(df, object_symbol="game")
    
    conjs = pg.discover(
    methods         = [linear_programming],
    features        = feats,
    target          = targ,
    hypothesis      = hyps,
    heuristics      = [morgan_accept, dalmatian_accept],
    post_processors = [remove_duplicates, sort_by_touch_count],
    )

    return conjs
