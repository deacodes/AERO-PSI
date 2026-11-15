import copy
import unittest
from unittest.mock import patch
from aero_psi.browser_work import execute
from aero_psi.runtime_data import allowed

class BrowserWorkTests(unittest.TestCase):
    def create(self):return execute('create',{'content':{'title':'Private study','question':'Does size change?','kind':'simulation','steps':[]}}, {})
    def test_request_scoped_save_never_writes_shared_storage(self):
        with patch('aero_psi.studio._write') as write:
            record=self.create()
            changed=execute('save',{'id':record['id'],'revision':record['revision'],'browser_record':record,'content':dict(record['content'],notes='private note')},{})
            self.assertEqual(changed['content']['notes'],'private note');write.assert_not_called()
        with self.assertRaises(ValueError):execute('save',{'id':record['id'],'revision':1,'content':record['content']},{})
    def test_other_record_cannot_be_substituted(self):
        a=self.create();b=self.create()
        with self.assertRaises(ValueError):execute('save',{'id':a['id'],'revision':1,'browser_record':b,'content':a['content']},{})
    def test_client_dataset_is_not_promoted_to_verified_measurement(self):
        a=self.create();a['datasets']=[{'id':'a'*32,'name':'test','reference':'claimed NASA data','columns':[{'name':'t','unit':'s'},{'name':'N','unit':'m-3'}],'rows':[[0,1],[1,2]],'classification':'NASA verified','stale':False}]
        r=execute('save',{'id':a['id'],'revision':1,'browser_record':a,'content':a['content']},{})
        self.assertEqual(r['datasets'][0]['classification'],'browser_supplied_unverified')
    def test_runtime_allowlist_excludes_work_and_credentials(self):
        for name in ('../.env','/DATA/a','DATA/../../.env','derived/studio/a.json','exports/a.json','.env','.venv/a'):
            self.assertFalse(allowed(name),name)
        for name in ('DATA/test.xls','aero_psi_catalog.json','derived/evidence/documents.json'):
            self.assertTrue(allowed(name),name)
