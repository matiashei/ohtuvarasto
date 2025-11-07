# pylint: disable=too-few-public-methods
import unittest

class KonsoliIO:
    def lue(self, teksti):
        return input(teksti)

    def kirjoita(self, teksti):
        print(teksti)

class Laskin:
    def __init__(self, io):
        self._io = io

    def suorita(self):
        while True:
            luku1 = int(self._io.lue("Luku 1:"))

            if luku1 == -9999:
                return

            luku2 = int(self._io.lue("Luku 2:"))

            if luku2 == -9999:
                return

            vastaus = self._laske_summa(luku1, luku2)

            self._io.kirjoita(f"Summa: {vastaus}")

    def _laske_summa(self, luku1, luku2):
        return luku1 + luku2

class StubIO:
    def __init__(self, inputs):
        self.inputs = inputs
        self.outputs = []

    def lue(self):
        return self.inputs.pop(0)

    def kirjoita(self, teksti):
        self.outputs.append(teksti)

class TestLaskin(unittest.TestCase):
    def test_yksi_summa_oikein(self):
        io = StubIO(["1", "3", "-9999"])
        laskin = Laskin(io)
        laskin.suorita()
        self.assertEqual(io.outputs[0], "Summa: 4")

def main():
    io = KonsoliIO()
    laskin = Laskin(io)
    laskin.suorita()

if __name__ == "__main__":
    unittest.main()
