# std
from sys import argv

# custom
from export import export
from redeem import redeem
from transact import collect, dispatch
from util import gen_wallet, get_all_balacnce


def transact():
    export(True)


if __name__ == '__main__':
    args = argv
    if len(args) == 2:
        {
            '--collect': collect,
            '--export': export,
            '--redeem': redeem,
            '--transact': transact,
            '--balance': get_all_balacnce
        }[args[1]]()
    else:
        {
            '--dispatch': dispatch,
            '--gen-wallet': gen_wallet
        }[args[1]](float(args[2]))
