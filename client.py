import os
from client import App

if __name__ == "__main__":

    a = App(os.path.dirname(os.path.realpath(__file__)))
    a.run()
