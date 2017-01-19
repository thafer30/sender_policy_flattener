import unittest
import json
import random
import re
from string import printable
import sender_policy_flattener as spf


class FlattenerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open('fixtures.json') as f:
            cls.fixtures = json.load(f)
        cls.dns_answer = re.compile(r'ANSWER\n(?P<answers>[^;]+)')
        cls.ip_address = re.compile(r'(?<=ip[46]:)\S+')
        cls.a_record = re.compile(r'((?:\d{1,3}\.){3}\d{1,3})')
        cls.spf_include = re.compile(r'(?P<type>include|a|mx(?: \d+)? ?|ptr|cname ?)[:](?P<hostname>[^\s\'\"]+\w)', flags=re.IGNORECASE)
        cls.response = cls.fixtures['dns_regex']['response']
        cls.answer = cls.fixtures['dns_regex']['answer_section']

    def test_hashseq_produces_consistent_hash(self):
        jumbled = random.sample(printable, len(printable))
        self.assertTrue(spf.hashed_sequence(jumbled) == spf.hashed_sequence(printable))

    def test_answer_section_is_extracted_from_dns_response(self):
        expected = self.fixtures['dns_regex']['answer_section']
        match = self.dns_answer.search(self.response).group()
        self.assertEqual(match, expected)

    def test_ipaddresses_are_extracted_from_regex_search(self):
        expected = self.fixtures['dns_regex']['ips']
        match = self.ip_address.findall(self.answer)
        self.assertEqual(match, expected)

    def test_a_records_are_extracted_from_regex_search(self):
        expected = self.fixtures['dns_regex']['a_record']
        match = self.a_record.findall(self.answer)
        self.assertEqual(match, expected)

    # def test_cname_records_are_extracted_from_regex_search(self):
    #     pass

    def test_includes_are_extracted_from_regex_search(self):
        expected = self.fixtures['dns_regex']['includes']
        match = self.spf_include.findall(self.answer)  # Tuple(Tuple(Str, Str), ...)
        match = [list(l) for l in match]
        self.assertListEqual(match, expected)

    def test_ipaddresses_are_separated_correctly(self):
        ips = self.fixtures['flattening']['ips']
        ipblocks, lastrec = spf.separate_into_450bytes(ips)
        ipblocks = [list(x) for x in ipblocks]
        ipblocks = spf.hashed_sequence(repr(ipblocks))
        
        expected_ipblocks = self.fixtures['flattening']['separated']
        expected_ipblocks = spf.hashed_sequence(repr(expected_ipblocks))
        expected_lastrec = self.fixtures['flattening']['lastrec']
        
        self.assertEqual(ipblocks, expected_ipblocks)        
        self.assertEqual(lastrec, expected_lastrec)
        
    def test_bind_compatible_format_doesnt_dupe_parens(self):
        ips = self.fixtures['flattening']['ips']
        ipblocks, lastrec = spf.separate_into_450bytes(ips)
        ipblocks = [list(x) for x in ipblocks]
        for x in spf.bind_compatible_string(ipblocks):
            print(x)


class SettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open('settings.json') as f:
            cls.settings = json.load(f)

    def test_settings_contains_min_details(self):
        min_keys = ['sending domains', 'email', 'output']
        for key in min_keys:
            self.assertIn(key, self.settings.keys())

    def test_email_settings_contains_min_details(self):
        min_keys = ['to', 'from', 'subject', 'server']
        for key in min_keys:
            self.assertIn(key, self.settings['email'].keys())
