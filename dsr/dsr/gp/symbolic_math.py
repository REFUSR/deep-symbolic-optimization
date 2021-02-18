import numpy as np
from functools import partial, wraps
import copy
import random
import operator

from dsr.program import Program,  _finish_tokens
from dsr.functions import function_map, UNARY_TOKENS, BINARY_TOKENS
from dsr.gp import base as gp_base
from dsr.gp import tokens as gp_tokens

try:
    from deap import gp
    from deap import base
    from deap import tools
    from deap import creator
    from deap import algorithms
except ImportError:
    gp          = None
    base        = None
    tools       = None
    creator     = None
    algorithms  = None


### >>> These are components to be removed...

TRIG_TOKENS = ["sin", "cos", "tan", "csc", "sec", "cot"]


# Define inverse tokens
INVERSE_TOKENS = {
    "exp" : "log",
    "neg" : "neg",
    "inv" : "inv",
    "sqrt" : "n2"
}


# Add inverse trig functions
INVERSE_TOKENS.update({
    t : "arc" + t for t in TRIG_TOKENS
    })


# Add reverse
INVERSE_TOKENS.update({
    v : k for k, v in INVERSE_TOKENS.items()
    })


def check_const(ind):
    """Returns True if children of a parent are all const tokens."""

    names = [node.name for node in ind]
    for i, name in enumerate(names):
        if name in UNARY_TOKENS and "const" in names[i+1]:
            return True
        if name in BINARY_TOKENS and "const" in names[i+1] and "const" in names[i+2]:
            return True
    return False


def check_inv(names):
    """Returns True if two sequential tokens are inverse unary operators."""

    for i, name in enumerate(names[:-1]):
        if name in INVERSE_TOKENS and names[i+1] == INVERSE_TOKENS[name]:
            return True
    return False


def check_trig(names):
    """Returns True if a descendant of a trig operator is another trig
    operator."""
        
    trig_descendant = False # True when current node is a descendant of a trig operator

    for name in names:
        if name in TRIG_TOKENS:
            if trig_descendant:
                return True
            trig_descendant = True
            trig_dangling   = 1
        elif trig_descendant:
            if name in BINARY_TOKENS:
                trig_dangling += 1
            elif name not in UNARY_TOKENS:
                trig_dangling -= 1
            if trig_dangling == 0:
                trig_descendant = False
                
    return False

### <<<

def checkConstraint(max_length, min_length, max_depth):
    """Check a varety of constraints on a memeber. These include:
        Max Length, Min Length, Max Depth, Trig Ancestors and inversion repetes. 
        
        This is a decorator function that attaches to mutate or mate functions in
        DEAP.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            keep_inds   = [copy.deepcopy(ind) for ind in args]      # The input individual(s) before the wrapped function is called 
            new_inds    = list(func(*args, **kwargs))               # Calls the wrapped function and returns results
                        
            for i, ind in enumerate(new_inds):
                
                l = len(ind)
                
                if l > max_length:
                    new_inds[i] = random.choice(keep_inds)
                elif l < min_length:
                    new_inds[i] = random.choice(keep_inds)
                elif operator.attrgetter("height")(ind) > max_depth:
                    new_inds[i] = random.choice(keep_inds)
                else:  
                    names = [node.name for node in new_inds[i]]
                    
                    if check_inv(names):
                        new_inds[i] = random.choice(keep_inds)
                    elif check_trig(names):
                        new_inds[i] = random.choice(keep_inds)
                    
            return new_inds

        return wrapper

    return decorator


def popConstraint():
    """Check a varety of constraints on a member. These include:
        
        This is a decorator function that attaches to the individual function in
        DEAP.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            while(True):
                inds    = func(*args, **kwargs)               # Calls the wrapped function and returns results
                names   = [node.name for node in inds]
                    
                if check_inv(names):
                    continue
                elif check_trig(names):
                    continue
                else:
                    break
                    
            return inds

        return wrapper

    return decorator    


# library_length = program.L. This should be folded into task
# This is going away and will be replaced with calls into prior.py
def generate_priors(tokens, max_exp_length, expr_length, max_const, max_len, min_len):
        
    priors              = np.zeros((max_exp_length, Program.library.L), dtype=np.float32)
    
    trig_descendant     = False
    const_tokens        = 0
    dangling            = 1
    offset              = 1 # Put in constraint at t+1
    
    # Never start with a terminal token
    ###priors[0, Program.library.terminal_tokens] = -np.inf
        
    for i,t in enumerate(tokens): 
        
        dangling    += Program.library.arities[t] - 1
        
        '''
            Note, actions == tokens
        '''
        '''
        if (dangling == 1) & (np.sum(np.isin(tokens, Program.library.float_tokens), axis=1) == 0):
            priors[i+offset, Program.library.float_tokens] = -np.inf
        '''
        # Something is still borken in here
        if i < len(tokens) - 1:
            
            # check trig descendants
            '''
            if t in Program.library.trig_tokens:
                trig_descendant = True
                trig_dangling   = 1
            elif trig_descendant:
                if t in Program.library.binary_tokens:
                    trig_dangling += 1
                elif t not in Program.library.unary_tokens:
                    trig_dangling -= 1
                    
                if trig_dangling == 0:
                    trig_descendant = False
            
            if trig_descendant:
                priors[i+offset, Program.library.trig_tokens] = -np.inf
            '''
            # Check inverse tokens
            '''
            if t in Program.library.inverse_tokens:
                priors[i+offset, Program.library.inverse_tokens[t]] = -np.inf    # The second token cannot be inv the first one 
            '''
            # Check const tokens        
            '''
            if i < len(tokens) - 2:
                if t in Program.binary_tokens:
                    if tokens[i+1] == Program.const_token:
                        priors[i+2, Program.const_token] = -np.inf     # The second token cannot be const if the first is        
            '''
            '''
            if t in Program.library.unary_tokens:
                priors[i+offset, Program.library.const_token] = -np.inf         # Cannot have const inside unary token

            if t == Program.library.const_token:
                const_tokens += 1
                if const_tokens >= max_const:
                    priors[i+offset:, Program.const_token] = -np.inf      # Cap the number of consts
            '''
            # Constrain terminals 
            '''
            if (i + 2) < min_len and dangling == 1:
                priors[i+offset, Program.library.terminal_tokens] = -np.inf
                
            if (i + 2) >= max_len // 2:
                remaining   = max_len - (i + 1)
                
                if dangling >= remaining - 1:
                    priors[i+offset, Program.library.binary_tokens] = -np.inf
                elif dangling == remaining:
                    priors[i+offset, Program.library.unary_tokens]  = -np.inf
             '''
    return priors


def create_primitive_set(n_input_var):
    
    pset = gp.PrimitiveSet("MAIN", n_input_var)

    # Add input variables
    rename_kwargs = {"ARG{}".format(i) : "x{}".format(i + 1) for i in range(n_input_var)}
    pset.renameArguments(**rename_kwargs)
    
    return pset


def get_top_n_programs(population, actions, config_gp_meld):
    """ Get the top n members of the population, We will also do some things like remove 
        redundant members of the population, which there tend to be a lot of.
        
        Next we compute DSR compatible parents, siblings and actions.  
    """
    
    n           = config_gp_meld["train_n"] 
    max_const   = config_gp_meld["max_const"]
    max_len     = config_gp_meld["max_len"] 
    min_len     = config_gp_meld["min_len"]
    
    max_tok     = Program.library.L

    deap_program, deap_obs, deap_action, deap_tokens, deap_expr_length  = gp_base._get_top_n_programs(population, n, actions, max_len, min_len, gp_tokens.DEAP_to_math_tokens)
    
    if config_gp_meld["compute_priors"]:
        deap_priors                     = np.empty((len(deap_tokens), actions.shape[1], max_tok), dtype=np.float32)
        
        for i in range(len(deap_tokens)):        
            deap_priors[i,]                 = generate_priors(deap_tokens[i], actions.shape[1], deap_expr_length[i], max_const, max_len, min_len)
    else:
        deap_priors                     = np.zeros((len(deap_tokens), actions.shape[1], max_tok), dtype=np.float32)
    
    return deap_program, deap_obs, deap_action, deap_priors


def convert_inverse_prim(prim, args):
    """
    Convert inverse prims according to:
    [Dd]iv(a,b) -> Mul[a, 1/b]
    [Ss]ub(a,b) -> Add[a, -b]
    We achieve this by overwriting the corresponding format method of the sub and div prim.
    """
    prim = copy.copy(prim)
    #prim.name = re.sub(r'([A-Z])', lambda pat: pat.group(1).lower(), prim.name)    # lower all capital letters

    converter = {
        'sub': lambda *args_: "Add({}, Mul(-1,{}))".format(*args_),
        'protectedDiv': lambda *args_: "Mul({}, Pow({}, -1))".format(*args_),
        'div': lambda *args_: "Mul({}, Pow({}, -1))".format(*args_),
        'mul': lambda *args_: "Mul({},{})".format(*args_),
        'add': lambda *args_: "Add({},{})".format(*args_),
        'inv': lambda *args_: "Pow(-1)".format(*args_),
        'neg': lambda *args_: "Mul(-1)".format(*args_)
    }
    prim_formatter = converter.get(prim.name, prim.format)

    return prim_formatter(*args)


def stringify_for_sympy(f):
    """Return the expression in a human readable string.
    """
    string = ""
    stack = []
    for node in f:
        stack.append((node, []))
        while len(stack[-1][1]) == stack[-1][0].arity:
            prim, args = stack.pop()
            string = convert_inverse_prim(prim, args)
            if len(stack) == 0:
                break  # If stack is empty, all nodes should have been seen
            stack[-1][1].append(string)
    return string


