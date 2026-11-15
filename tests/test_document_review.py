import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from aero_psi.evidence import build_index, document_records, extract
from aero_psi.knowledge import review_records
from aero_psi.copilot import retrieve


class DocumentReviewTests(unittest.TestCase):
    def test_text_retains_real_lines_and_does_not_modify_original(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'DATA';root.mkdir();source=root/'run.txt'
            source.write_bytes(b'Time\tValue\r\n1\t-0.2\r\n\r\n2\t0.5\r\n')
            original=source.read_bytes();index=Path(temp)/'index.json'
            self.assertEqual(build_index(root,index)['extracted'],1)
            records=document_records(index,root)
            self.assertEqual([r['locator']['line'] for r in records],[1,2,4])
            self.assertEqual(records[1]['text'],'1\t-0.2')
            self.assertEqual(source.read_bytes(),original)

    def test_slides_follow_presentation_order_and_keep_speaker_notes(self):
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'talk.pptx'
            with zipfile.ZipFile(source,'w') as z:
                z.writestr('ppt/presentation.xml','<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldIdLst><p:sldId r:id="b"/><p:sldId r:id="a"/></p:sldIdLst></p:presentation>')
                z.writestr('ppt/_rels/presentation.xml.rels','<Relationships><Relationship Id="a" Target="slides/slide1.xml"/><Relationship Id="b" Target="slides/slide2.xml"/></Relationships>')
                for n in [1,2]:z.writestr(f'ppt/slides/slide{n}.xml',f'<s xmlns:a="urn:test"><a:p><a:t>Slide content {n}</a:t></a:p></s>')
                z.writestr('ppt/slides/_rels/slide2.xml.rels','<Relationships><Relationship Type="urn:test/notesSlide" Target="../notesSlides/notesSlide2.xml"/></Relationships>')
                z.writestr('ppt/notesSlides/notesSlide2.xml','<s xmlns:p="urn:p" xmlns:a="urn:a"><p:sp><p:ph type="body"/><a:p><a:t>Calibration is incomplete</a:t></a:p></p:sp><p:sp><p:ph type="sldNum"/><a:t>2</a:t></p:sp></s>')
            self.assertEqual(extract(source),[('slide',1,'Slide content 2'),('slide_notes',1,'Calibration is incomplete'),('slide',2,'Slide content 1')])

    def test_duplicate_sources_retain_paths_and_are_not_double_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'DATA';root.mkdir();(root/'a.txt').write_text('Brownian coagulation');(root/'b.txt').write_text('Brownian coagulation')
            index=Path(temp)/'index.json';build_index(root,index);records=document_records(index,root)
            self.assertEqual(len(records),2);self.assertEqual(records[1]['duplicate_of'],'a.txt')
            with patch('aero_psi.copilot._chunks',return_value=records):self.assertEqual(len(retrieve({},'Brownian coagulation')),1)

    def test_named_investigation_keeps_other_families_out(self):
        records=[{'id':g,'group':g,'kind':'document_excerpt','text':'Radiometer calibration clock timestamp'} for g in ['FLEX','BASS-II','ACME II']]
        with patch('aero_psi.copilot._chunks',return_value=records):
            self.assertEqual([r['group'] for r in retrieve({},'FLEX radiometer calibration')],['FLEX'])
            self.assertEqual([r['group'] for r in retrieve({},'BASS-II calibration')],['BASS-II'])

    def test_review_requires_matching_source_hash_and_exact_anchor(self):
        with tempfile.TemporaryDirectory() as temp:
            source={'id':'document:one','source_path':'PSI101/a.pdf','source_sha256':'abc','locator':{'page':3,'character_start':0},'text':'Radiometer was uncalibrated.'}
            note={'title':'Radiometry','source_sha256':'abc','source_range':'page 3','review_state':'Selected passage reviewed','classification':'limitation','text':'Relative only','reviewed_on':'2026-11-14','anchors':[{'kind':'page','number':3,'quote':'was uncalibrated'}]}
            path=Path(temp)/'notes.json';path.write_text(json.dumps({'notes':[note]}));web=Path(temp)/'missing.json'
            self.assertEqual(len(review_records([source],path,web)),1)
            self.assertEqual(review_records([{**source,'source_sha256':'changed'}],path,web),[])
            self.assertEqual(review_records([{**source,'text':'Instrument was calibrated.'}],path,web),[])

    def test_web_urls_must_be_consulted_and_safe(self):
        with tempfile.TemporaryDirectory() as temp:
            base={'title':'Reference','source_url':'https://www.nist.gov/example','accessed_on':'2026-11-14','status':'consulted','scope':'abstract','summary':'A bounded reference summary.'}
            file=Path(temp)/'web.json';file.write_text(json.dumps({'references':[base,{**base,'source_url':'javascript:alert(1)'},{**base,'status':'listed_not_consulted'},{**base,'source_url':'https://user:password@example.com/'}]}))
            records=review_records([],Path(temp)/'missing.json',file)
            self.assertEqual(len(records),1);self.assertEqual(records[0]['source_url'],base['source_url'])
            self.assertIn('not a live web search',records[0]['warnings'][0])

    def test_conversion_hash_is_checked_again_when_read(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);data=root/'DATA';data.mkdir();derived=root/'derived';derived.mkdir()
            source=data/'old.doc';source.write_bytes(b'old word fixture');converted=derived/'old.pdf';converted.write_bytes(b'converted fixture')
            record={'id':'document:converted','source_path':'old.doc','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                'conversion':{'converted_path':'derived/old.pdf','converted_sha256':hashlib.sha256(converted.read_bytes()).hexdigest()}}
            index=derived/'index.json';index.write_text(json.dumps({'records':[record]}))
            with patch('aero_psi.evidence.RUNTIME_ROOT',root):
                self.assertEqual(len(document_records(index,data)),1)
                converted.write_bytes(b'mutated conversion')
                self.assertEqual(document_records(index,data),[])

    def test_real_review_notes_have_live_anchors(self):
        root=Path(__file__).resolve().parents[1]
        if not (root/'derived/evidence/documents.json').is_file():self.skipTest('Local archive not installed')
        configured=json.loads((root/'mappings/scientific_review.json').read_text())['notes']
        records=review_records(document_records())
        self.assertFalse({n['title'] for n in configured}-{r['title'] for r in records})
        self.assertTrue(any(r['kind']=='consulted_web_reference' for r in records))


if __name__=='__main__':unittest.main()
