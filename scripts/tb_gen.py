# pip install posit_playground

# e.g.:
#   python tb_gen.py --operation decode -n 16 -es 1

import argparse, random, datetime, enum, pathlib, math

# from posit_playground import from_bits
from hardposit import from_bits

from posit_playground.utils import get_bin, get_hex

LJUST = 25
NUM_RANDOM_TEST_CASES = 300
X = "'bX"


def clog2(x):
    return math.ceil(math.log2(x))


class Tb(enum.Enum):
    MUL = "mul"
    MUL_CORE = "mul_core"
    ADD = "add"
    DECODE = "decode"
    ENCODE = "encode"
    PPU = "ppu"

    def __str__(self):
        return self.value


parser = argparse.ArgumentParser(description="Generate test benches")
parser.add_argument(
    "--operation",
    type=Tb,
    choices=list(Tb),
    required=True,
    help="Type of test bench: adder/multiplier/etc",
)
parser.add_argument(
    "--shuffle-random", type=bool, default=False, required=False, help="Shuffle random"
)

parser.add_argument("--num-bits", "-n", type=int, required=True, help="Num posit bits")

parser.add_argument("--es-size", "-es", type=int, required=True, help="Num posit bits")

args = parser.parse_args()


N, ES = args.num_bits, args.es_size
S = clog2(N)

if args.shuffle_random == False:
    random.seed(4)


if __name__ == "__main__":

    c = f"""\t/*-------------------------------------+
    | autogenerated by tb_gen.py on       |
    | {datetime.datetime.now().strftime('%c')}            |
    +-------------------------------------*/\n"""

    ##### only positive for now
    
    positive_only = True
    if positive_only:
        _max = (1 << (N - 1)) - 1
    else:
        _max = (1 << (N)) - 1

    list_a = random.sample(range(0, _max), min(NUM_RANDOM_TEST_CASES, _max))
    list_b = random.sample(range(0, _max), min(NUM_RANDOM_TEST_CASES, _max))

    ### enforce special cases to be at the beginning
    list_a[0] = 0
    list_a[1] = 1 << (N - 1)
    list_a[2], list_b[2] = 0, 1 << (N - 1)
    # 0b10000.....001 kind of number causes errors as of 3316bd5 due to mant_len out of bound. needs more bits to be representate because it can go negative.
    list_a[3] = (1 << (N - 1)) + 1 

    if args.operation == Tb.DECODE or args.operation == Tb.ENCODE:
        for (counter, a) in enumerate(list_a):
            p = from_bits(a, N, ES)

            c += f"{'test_no ='.ljust(LJUST)} {counter+1};\n"

            if p.fields.is_some:
                regime = p.fields.unwrap().regime
                reg_s, reg_len, k = regime.reg_s, regime.reg_len, regime.k
                exp = p.fields.unwrap().exp
                mant = p.mant_repr().unwrap() # p.fields.unwrap().mant
                mant_len = p.mant_len.unwrap()
            else:
                reg_s, reg_len, k = X, X, X
                exp = X
                mant = X
                mant_len = X

            if args.operation == Tb.DECODE:
                # posit bits
                c += f"{'bits ='.ljust(LJUST)} {N}'b{p.to_bin(prefix=False)};\n"
                # sign
                c += f"{'sign_expected ='.ljust(LJUST)} {p.sign.real};\n"
                if p.fields.is_some:
                    # regime
                    c += f"{'reg_s_expected ='.ljust(LJUST)} {reg_s.real};\n"
                    c += f"{'reg_len_expected ='.ljust(LJUST)} {reg_len};\n"
                    c += f"{'k_expected ='.ljust(LJUST)} {k};\n"
                    c += f"{'k_is_pos ='.ljust(LJUST)} {(p.fields.unwrap().regime.k > 0).real};\n"
                    # exponent
                    if ES > 0:
                        c += f"{'exp_expected ='.ljust(LJUST)} {ES}'b{get_bin(exp, ES, prefix=False)};\n"
                    # mantissa
                    c += f"{'mant_expected ='.ljust(LJUST)} {N}'b{get_bin(mant, N, prefix=False)};\n"
                    c += f"{'mant_len_expected ='.ljust(LJUST)} {mant_len};\n"
                else:
                    pass
                c += f"{'is_special_expected ='.ljust(LJUST)} {(p.is_zero or p.is_nan).real};\n"
            elif args.operation == Tb.ENCODE:
                c += f"{'posit_expected ='.ljust(LJUST)} {N}'h{p.to_hex(prefix=False)};\n"
                ### sign
                c += f"{'sign ='.ljust(LJUST)} {p.sign.real};\n"
                if p.fields.is_some:
                    ### regime
                    c += f"{'reg_len ='.ljust(LJUST)} {reg_len.real};\n"
                    c += f"{'k ='.ljust(LJUST)} {k};\n"
                    ### exponent
                    if ES > 0:
                        c += f"{'exp ='.ljust(LJUST)} {ES}'b{get_bin(exp, ES, prefix=False)};\n"
                    ### mantissa
                    c += f"{'mant ='.ljust(LJUST)} {N}'b{get_bin(mant, N, prefix=False)};\n"
                c += f"{'is_zero ='.ljust(LJUST)} {p.is_zero.real};\n"
                c += f"{'is_nan ='.ljust(LJUST)} {p.is_nan.real};\n"
            c += f"#10;\n\n"

    if args.operation == Tb.MUL_CORE:
        for counter, (a, b) in enumerate(zip(list_a, list_b)):
            p1 = from_bits(a, N, ES)
            p2 = from_bits(b, N, ES)

            pout = p1 * p2

            c += f"{'test_no ='.ljust(LJUST)} {counter+1};\n\t"

            c += f"{'// p1:'.ljust(LJUST)} {p1.to_bin(prefix=False)} {p1.eval()};\n\t"
            c += f"{'p1_hex ='.ljust(LJUST)} {N}'h{get_hex(p1.bit_repr(), N//4, prefix=False)};\n\t"
            c += f"{'p1_is_zero ='.ljust(LJUST)} {p1.is_zero.real};\n\t"
            c += f"{'p1_is_nan ='.ljust(LJUST)} {p1.is_nan.real};\n\t"
            c += f"{'p1_sign ='.ljust(LJUST)} {p1.sign};\n\t"
            if pout.fields.is_some:
                c += f"{'p1_reg_len ='.ljust(LJUST)} {p1.fields.unwrap().regime.reg_len};\n\t"
                c += f"{'p1_k ='.ljust(LJUST)} {p1.fields.unwrap().regime.k};\n\t"
                if ES > 0:
                    c += f"{'p1_exp ='.ljust(LJUST)} {p1.fields.unwrap().exp};\n\t"
                c += f"{'p1_mant ='.ljust(LJUST)} {N}'b{get_bin(p1.fields.unwrap().mant, N, prefix=False)};\n\t"

            c += f"{'// p2:'.ljust(LJUST)} {get_bin(p2.bit_repr(), N, prefix=False)} {p2.eval()};\n\t"
            c += f"{'p2_hex ='.ljust(LJUST)} {N}'h{get_hex(p2.bit_repr(), N//4, prefix=False)};\n\t"
            c += f"{'p2_is_zero ='.ljust(LJUST)} {p2.is_zero.real};\n\t"
            c += f"{'p2_is_nan ='.ljust(LJUST)} {p2.is_nan.real};\n\t"
            c += f"{'p2_sign ='.ljust(LJUST)} {p2.sign};\n\t"
            if pout.fields.is_some:
                c += f"{'p2_reg_len ='.ljust(LJUST)} {p2.fields.unwrap().regime.reg_len};\n\t"
                c += f"{'p2_k ='.ljust(LJUST)} {p2.fields.unwrap().regime.k};\n\t"
                if ES > 0:
                    c += f"{'p2_exp ='.ljust(LJUST)} {p2.fields.unwrap().exp};\n\t"
                c += f"{'p2_mant ='.ljust(LJUST)} {N}'b{get_bin(p2.fields.unwrap().mant, N, prefix=False)};\n\t"

            c += f"{'// pout:'.ljust(LJUST)} {get_bin(pout.bit_repr(), N)} {pout.eval()};\n\t"
            c += f"{'pout_hex ='.ljust(LJUST)} {N}'h{get_hex(pout.bit_repr(), N//4, prefix=False)};\n\t"
            c += f"{'pout_is_zero_expected ='.ljust(LJUST)} {pout.is_zero.real};\n\t"
            c += f"{'pout_is_nan_expected ='.ljust(LJUST)} {pout.is_nan.real};\n\t"
            c += f"{'pout_sign_expected ='.ljust(LJUST)} {pout.sign};\n\t"
            if pout.fields.is_some:
                c += f"{'pout_reg_len_expected ='.ljust(LJUST)} {pout.fields.unwrap().regime.reg_len};\n\t"
                c += f"{'pout_k_expected ='.ljust(LJUST)} {pout.fields.unwrap().regime.k};\n\t"
                if ES > 0:
                    c += f"{'pout_exp_expected ='.ljust(LJUST)} {pout.fields.unwrap().exp};\n\t"
                c += f"{'pout_mant_expected ='.ljust(LJUST)} {N}'b{get_bin(pout.fields.unwrap().mant, N, prefix=False)};\n\t"

            c += f"#10;\n\n"

    elif args.operation == Tb.MUL:
        for counter, (a, b) in enumerate(zip(list_a, list_b)):
            p1 = from_bits(a, N, ES)
            p2 = from_bits(b, N, ES)

            pout = p1 * p2

            c += f"{'test_no ='.ljust(LJUST)} {counter+1};\n\t"
            c += f"{'// p1:'.ljust(LJUST)} {p1.to_bin(prefix=True)} {p1.eval()};\n\t"
            c += f"{'p1 ='.ljust(LJUST)} {N}'h{p1.to_hex(prefix=False)};\n\t"
            c += f"{'// p2:'.ljust(LJUST)} {p2.to_bin(prefix=True)} {p2.eval()};\n\t"
            c += f"{'p2 ='.ljust(LJUST)} {N}'h{p2.to_hex(prefix=False)};\n\t"
            c += f"{'// pout:'.ljust(LJUST)} {pout.to_bin(prefix=True)} {pout.eval()};\n\t"
            c += f"{'pout_expected ='.ljust(LJUST)} {N}'h{pout.to_hex(prefix=False)};\n\t"
            c += f"#10;\n\t"
            c += f'assert (pout === pout_expected) else $error("{p1.to_hex()} * {p2.to_hex()} failed");\n\n'

    elif args.operation == Tb.PPU:
        for counter, (a, b) in enumerate(zip(list_a, list_b)):
            p1 = from_bits(a, N, ES)
            p2 = from_bits(b, N, ES)

            pout = p1 + p2

            c += f"{'test_no ='.ljust(LJUST)} {counter+1};\n\t"
            c += f"{'// p1:'.ljust(LJUST)} {p1.to_bin(prefix=True)} {p1.eval()};\n\t"
            c += f"{'p1 ='.ljust(LJUST)} {N}'h{p1.to_hex(prefix=False)};\n\t"
            c += f"{'// p2:'.ljust(LJUST)} {p2.to_bin(prefix=True)} {p2.eval()};\n\t"
            c += f"{'p2 ='.ljust(LJUST)} {N}'h{p2.to_hex(prefix=False)};\n\t"
            c += f"{'// pout:'.ljust(LJUST)} {pout.to_bin(prefix=True)} {pout.eval()};\n\t"
            c += f"{'pout_expected ='.ljust(LJUST)} {N}'h{pout.to_hex(prefix=False)};\n\t"
            c += f"#10;\n\t"
            c += f'assert (pout === pout_expected) else $error("{p1.to_hex(prefix=True)} * {p2.to_hex(prefix=True)} failed");\n\n'

    filename = pathlib.Path(f"../test_vectors/tv_posit_{args.operation}_P{N}E{ES}.sv")
    with open(filename, "w") as f:
        f.write(c)
        print(f"Wrote {filename.resolve()}")
