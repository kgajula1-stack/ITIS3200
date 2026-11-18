import unittest

from seed_demo import derive_seed


class DemoSeedTests(unittest.TestCase):
    def test_seed_is_sum_of_four_two_digit_suffixes_modulo_eleven(self):
        self.assertEqual(derive_seed(['12', '34', '56', '78']), 4)

    def test_seed_rejects_missing_or_malformed_suffixes(self):
        for suffixes in (['12', '34', '56'], ['1', '34', '56', '78'], ['aa', '34', '56', '78']):
            with self.subTest(suffixes=suffixes):
                with self.assertRaises(ValueError):
                    derive_seed(suffixes)


if __name__ == '__main__':
    unittest.main()
