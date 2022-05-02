#!/usr/bin/env python3
from datetime import datetime

from tests import test_e2e
from socid_extractor.schemes import schemes

def collect_pytest_annotations():
	annotations = {}
	with open('pytest.ini') as f:
		lines = f.read().splitlines()
		markers = False
		for line in lines:
			if line.startswith('markers ='):
				markers = True
				continue
			if not markers:
				continue
			if not line.startswith('   '):
				break
			name, descr = line.strip().split(': ')
			annotations[name] = descr

	return annotations


def is_test_for(mname: str, tname: str):
	return mname.lower().replace(' ', '_').replace('.', '_') == tname


def revision():
	test_url_search = 'https://github.com/soxoj/socid-extractor/search?q=test_{}'

	annotations = collect_pytest_annotations()
	tests = [test_e2e.__dict__[name]
			 for name in dir(test_e2e)
			 if name.startswith('test_')]

	methods = list(schemes.keys())
	methods_from_tests = {m: [] for m in methods}

	for t in tests:
		tname = str(t).split()[1][5:]

		notes = []
		if 'pytestmark' in t.__dict__:
			for m in t.pytestmark:
				if m.name in annotations:
					notes.append(annotations[m.name])
				elif m.name == 'skip':
					notes.append(m.kwargs['reason'])
				else:
					print(f'Unknown annotation {m} in test {t}!')

		doc_str = (t.__doc__ or '').strip().split('\n')
		added_from_doc = False

		for d in doc_str:
			if not d:
				continue
			d = d.strip()
			if d not in methods:
				print(f'Wrong method {d} in doc of test {t}!')
			methods_from_tests[d].append({
				'test': tname,
				'notes': notes,
			})
			added_from_doc = True

		if added_from_doc:
			continue

		for m in methods:
			if is_test_for(m, tname):
				# print(f'{t} is test for {m}!')
				methods_from_tests[m].append({
					'test': tname,
					'notes': notes,
				})

	methods_without_tests = []

	with open('METHODS.md', 'w') as f:
		f.write("""# Supported sites and methods

| № | Method | Test data | Notes |
| --- | --- | --- | --- |
""")

		for i, m in enumerate(methods):
			tests = methods_from_tests[m]
			tests_links = [
				f'[{t["test"]}]({test_url_search.format(t["test"])})'
				for t in tests
			]
			notes = [", ".join(t['notes']) for t in tests if t['notes']]
			if not tests:
				methods_without_tests.append(m)

			f.write(f'{i} | {m} | {", ".join(tests_links)} | {", ".join(notes)} |\n')

		f.write(f'\nThe table has been updated at {datetime.utcnow()} UTC\n')

	print(f'Total {len(m)} methods, {len(methods_without_tests)} without tests: ')
	print(methods_without_tests)

if __name__ == "__main__":
	revision()