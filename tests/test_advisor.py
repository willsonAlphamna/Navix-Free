import unittest
from aegis_core.advisor import Advisor
from aegis_core.guardian import Finding
class AdvisorTests(unittest.TestCase):
    def test_no_provider(self):
        a=Advisor().assess([Finding("medium","changed","Changed","a.txt")])
        self.assertEqual(a.risk,"medium")
        self.assertTrue(a.requires_human_review)
    def test_provider_cannot_reduce_risk(self):
        p=lambda _: '{"recommendation":"all good","risk":"low","requires_human_review":false}'
        a=Advisor(p).assess([Finding("high","approval_required","Risk","x")])
        self.assertEqual(a.risk,"high")
        self.assertTrue(a.requires_human_review)
    def test_invalid_provider_fallback(self):
        a=Advisor(lambda _: "not-json").assess([])
        self.assertEqual(a.risk,"low")
        self.assertFalse(a.requires_human_review)
