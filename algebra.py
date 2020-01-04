import collections
import math

Op = collections.namedtuple('Op', ['left', 'op', 'right'])
OPS = (('+', '-'), ('*', '/'), '^')


def paren_args(expr: str, i: int) -> (str, int):  # consider replacing '()' with ' ' and splitting to find next time
    """ Returns contents of parentheses starting at expr[i] if '(' is at expr[i], else ''. """
    if expr[i] == '(':
        paren_tracker = 1
        start = i + 1

        while True:
            i += 1
            if expr[i] == '(':
                paren_tracker += 1
            elif expr[i] == ')':
                paren_tracker -= 1

            if paren_tracker == 0 or i >= len(expr) - 1:
                break

        return expr[start: i], i
    else:
        return '', i


def _list_values(expr: str) -> [str]:  # consider just not parsing sections w/o var to begin w/, then won't need unparse
    """ Parses expr into a list, taking parentheses contents out and separating operators from operands. """
    values = []
    simple_value = ''

    i = 0
    while i < len(expr):  # and True not in [expression.startswith(key, i) for key in OPS[ops_idx]]:
        if expr[i] == '(':
            in_paren, i = paren_args(expr, i)
            values += [in_paren.strip()]
            i += 1
        elif expr[i] in ['+', '-', '*', '/', '^']:
            values += [expr[i]]
            i += 1
        else:
            while i < len(expr) and expr[i] not in ['(', '+', '-', '*', '/', '^']:
                simple_value += expr[i]
                i += 1
            values += [simple_value.strip()]
            simple_value = ''
    return values


def _parse_expr(expr: str) -> Op:
    """ Recursively creates a parsed version of expr using Op(eration) namedtuple. """
    op_vals = _list_values(expr)
    while len(op_vals) == 1 and True in [key in op_vals[0] for key in ['(', '+', '-', '*', '/', '^']]:
        op_vals = _list_values(op_vals[0])

    for ops in ['^', ('*', '/'), ('+', '-')]:
        # exponents go <<right to left<< first, but everything else goes >>left to right>> first
        if ops == '^':
            i = len(op_vals) - 1
            compare_idx = '0 <= i'
            step = -1
        else:
            i = 0
            compare_idx = 'i < len(op_vals)'
            step = 1

        while eval(compare_idx):
            unary_minus = i == 0 and op_vals[0] == '-' and ops == ('+', '-')
            if i + 1 < len(op_vals) and (type(op_vals[i + 1]) == str and op_vals[i + 1] in ops or unary_minus):
                if unary_minus:
                    l_val = '0'
                    r_val = op_vals[1]
                    op = '-'
                    len_operation = 2
                else:
                    l_val = op_vals[i]
                    r_val = op_vals[i + 2]
                    op = op_vals[i + 1]
                    len_operation = 3

                if type(l_val) == str and True in [key in l_val for key in ['(', '+', '-', '*', '/', '^']]:
                    l_val = _parse_expr(l_val)

                if type(r_val) == str and True in [key in r_val for key in ['(', '+', '-', '*', '/', '^']]:
                    r_val = _parse_expr(r_val)

                op_vals[i: i + len_operation] = [Op(l_val, op, r_val)]
                i -= step
            i += step
    return op_vals[0]


def _unparse_expr(parsed_expr: str or Op) -> str:
    """ Unparses an expression that was parsed using parse_expr() back to a str. """
    if type(parsed_expr) == str:
        return parsed_expr
    return f'({_unparse_expr(parsed_expr.left)}{parsed_expr.op}{_unparse_expr(parsed_expr.right)})'


def _solving(solution: str, parsed_var_side: str or Op, var: str):
    """
    Uses parsed expression (parsed_var_side) and string
    expression (solution) to find the solution to var recursively.
    """
    if type(parsed_var_side) == str:  # or maybe, parsed_var_side == var, both may be wrong if using this recursively
        return solution
    else:
        if var in _unparse_expr(parsed_var_side.left):  # '+', '-', '*', '/', '^'
            if parsed_var_side.op == '+':
                solution += f'-{_unparse_expr(parsed_var_side.right)}'

            elif parsed_var_side.op == '-':
                solution += f'+{_unparse_expr(parsed_var_side.right)}'

            elif parsed_var_side.op == '*':
                solution = f'({solution})/{_unparse_expr(parsed_var_side.right)}'

            elif parsed_var_side.op == '/':  # consider adding a division by 0 error
                solution = f'({solution})*{_unparse_expr(parsed_var_side.right)}'

            else:  # if parsed_var_side.op == '^':
                solution = f'math.pow(({solution}), (1/{_unparse_expr(parsed_var_side.right)}))'

            return _solving(solution, parsed_var_side.left, var)

        else:  # if parsed_var_side.right.has_var:
            if parsed_var_side.op == '+':
                solution += f'-{_unparse_expr(parsed_var_side.left)}'

            elif parsed_var_side.op == '-':
                solution = f'-({solution}-{_unparse_expr(parsed_var_side.left)})'

            elif parsed_var_side.op == '*':
                solution = f'({solution})/{_unparse_expr(parsed_var_side.left)}'

            elif parsed_var_side.op == '/':  # consider adding a division by 0 error
                solution = f'{_unparse_expr(parsed_var_side.left)}/({solution})'

            else:  # if parsed_var_side.op == '^':
                solution = f'math.log({solution}, {_unparse_expr(parsed_var_side.left)})'

            return _solving(solution, parsed_var_side.right, var)


def solve_for(equation: str, var: str) -> str or None:
    """
    Solves for var in equation in a way python can read using builtin
    math library, assuming equation has one occurrence of
    var (as well as one '='). If var not present, returns None.
    """
    if var not in equation:
        return None  # consider throwing exception (and catching were called)

    # assume one '=' and one var
    sides_of_equation = equation.split('=')
    if var in sides_of_equation[0]:
        var_side = sides_of_equation[0]
        solution = sides_of_equation[1]
    else:
        var_side = sides_of_equation[1]
        solution = sides_of_equation[0]

    parsed_var_side = _parse_expr(var_side)

    solution = _solving(solution, parsed_var_side, var)
    return solution.replace('^', '**')


class Equation:
    def __init__(self, equation: str) -> None:
        self.equ = equation

        self.x = solve_for(equation, 'x')  # equation in terms of x
        self.y = solve_for(equation, 'y')  # equation in terms of y
        self.z = solve_for(equation, 'z')  # equation in terms of z

        self.xy = solve_for(equation.replace('z', '0'), 'y')  # equation for intersection with xy plane in terms of y
        self.xz = solve_for(equation.replace('y', '0'), 'z')  # equation for intersection with xz plane in terms of z
        self.yz = solve_for(equation.replace('x', '0'), 'y')  # equation for intersection with yz plane in terms of y

    def xy_intercept(self, z: str):
        """ Less-than-3D equation of self.equ where z variable, if present, is set to z param. """
        return solve_for(self.equ.replace('z', f'({z})'), 'y')

    def xz_intercept(self, y: str):
        """ Less-than-3D equation of self.equ where y variable, if present, is set to z param. """
        return solve_for(self.equ.replace('y', f'({y})'), 'z')

    def yz_intercept(self, x: str):
        """ Less-than-3D equation of self.equ where z variable, if present, is set to z param. """
        return solve_for(self.equ.replace('x', f'({x})'), 'y')


# for testing purposes
if __name__ == '__main__':
    x = 1
    y = 2
    z = 3
    equ = solve_for('z^2=x^2+y^2', 'x')
    equ2 = f'math.pow({equ.replace("**(1/2)", "")}, 1/2)'
    print(equ)
    print(equ2)
    try:
        print(eval(equ))  # ** and pow() give complex nums, but math.pow and sqrt give exceptions
    except:
        print('invalid operation')

    try:
        print(eval(equ2))  # ** and pow() give complex nums, but math.pow and sqrt give exceptions
    except:
        print('invalid operation')
