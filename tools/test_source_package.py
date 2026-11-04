"""Run against an unpacked source-only release, without Power BI or raw data."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from setup_powerbi import configure

ROOT = Path(__file__).resolve().parents[1]


class SourcePackage(unittest.TestCase):
    def test_export_inventory_and_relative_references(self):
        inventory = json.loads((ROOT / 'PUBLICATION.json').read_text(encoding='utf-8'))['files_sha256']
        for name, expected in inventory.items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected, name)
        report = ROOT / 'powerbi/portfolio-final'
        project = json.loads((report / 'ChargeScope.pbip').read_text(encoding='utf-8'))
        self.assertEqual(project['artifacts'][0]['report']['path'], 'ChargeScope.Report')
        definition = json.loads((report / 'ChargeScope.Report/definition.pbir').read_text(encoding='utf-8'))
        self.assertEqual(definition['datasetReference']['byPath']['path'], '../ChargeScope.SemanticModel')
        model = json.loads((report / 'ChargeScope.SemanticModel/model.bim').read_text(encoding='utf-8'))['model']
        self.assertEqual(len(model['tables']), 8)
        self.assertEqual(len(model['relationships']), 4)
        self.assertEqual(model['dataAccessOptions'], {'legacyRedirects': False, 'returnErrorValuesAsNull': False})
        expression = next(item for item in model['expressions'] if item['name'] == 'BundlePath')
        self.assertTrue(expression['expression'].startswith('"" meta'))
        self.assertFalse(any('.pbi' in path.parts for path in ROOT.rglob('*')))

    def test_setup_requires_all_pinned_files_and_only_changes_path(self):
        source = ROOT / 'powerbi/portfolio-final'
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            (target / 'ChargeScope.SemanticModel').mkdir()
            model = json.loads((source / 'ChargeScope.SemanticModel/model.bim').read_text(encoding='utf-8'))
            model_path = target / 'ChargeScope.SemanticModel/model.bim'
            model_path.write_text(json.dumps(model), encoding='utf-8')
            data = target / 'data'
            data.mkdir()
            (data / 'sample.csv').write_text('sample')
            expected = hashlib.sha256((data / 'sample.csv').read_bytes()).hexdigest()
            metadata = {'required_csv_sha256': {'sample.csv': expected}}
            (target / 'SOURCE_PACKAGE.json').write_text(json.dumps(metadata), encoding='utf-8')
            project = target / 'ChargeScope.pbip'
            project.write_bytes((source / 'ChargeScope.pbip').read_bytes())
            configure(project, data)
            changed = json.loads(model_path.read_text(encoding='utf-8'))
            original_expression = next(item for item in model['model']['expressions'] if item['name'] == 'BundlePath')
            next(item for item in changed['model']['expressions'] if item['name'] == 'BundlePath')['expression'] = original_expression['expression']
            self.assertEqual(changed, model)
            (data / 'sample.csv').write_text('different')
            before = model_path.read_bytes()
            with self.assertRaises(ValueError):
                configure(project, data)
            self.assertEqual(before, model_path.read_bytes())
        with self.assertRaises(ValueError):
            configure(Path(folder) / 'unmarked/ChargeScope.pbip', data)


if __name__ == '__main__':
    unittest.main()
