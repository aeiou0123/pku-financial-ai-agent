import hashlib
from pathlib import Path
import pytest
from scripts.cloud_training_transfer import run_transfer
from scripts.transfer_training_data import split, join


class Response:
    def __init__(self, data):self.data=data
    def execute(self):return self.data
    def next_chunk(self, **kwargs):return None,self.data


class FakeDrive:
    def __init__(self, data, bad_checksum=False, can_download=True):
        self.data=data;self.bad_checksum=bad_checksum;self.can_download=can_download
        self.uploads={};self.folders=[]
    def files(self):return self
    def get(self,fileId,**kwargs):
        if fileId=='source':return Response({'size':str(len(self.data)),'capabilities':{'canDownload':self.can_download}})
        assert fileId=='parent'
        return Response({'mimeType':'application/vnd.google-apps.folder','capabilities':{'canAddChildren':True}})
    def get_media(self,fileId):
        assert fileId=='source';return self.data
    def create(self,body,media_body=None,**kwargs):
        if media_body is None:
            assert body['parents']==['parent'];self.folders.append(body)
            return Response({'id':'new_folder','name':body['name'],'webViewLink':'https://example.invalid/private-folder'})
        assert body['parents']==['new_folder']
        data=media_body.read_bytes();self.uploads[body['name']]=data
        return Response({'id':'id_'+body['name'],'size':str(len(data)),
            'md5Checksum':'wrong' if self.bad_checksum else hashlib.md5(data).hexdigest()})


class Downloader:
    def __init__(self,handle,request,chunksize):
        assert chunksize==8*1024*1024
        self.handle,self.data=handle,request
    def next_chunk(self,**kwargs):
        self.handle.write(self.data);return None,True


def execute(tmp_path, service, expected_sha=None):
    return run_transfer(service,split_function=split,work_parent=tmp_path,
        downloader_factory=Downloader,uploader_factory=lambda path,**kwargs:Path(path),
        train_id='source',parent_id='parent',expected_bytes=len(service.data),
        expected_sha=expected_sha or hashlib.sha256(service.data).hexdigest(),part_bytes=16)


def test_cloud_contract_verifies_parts_then_publishes_manifest(tmp_path):
    import json
    service=FakeDrive(bytes(range(51)));result=execute(tmp_path,service)
    assert result['status']=='COMPLETE' and result['parts']==4
    assert list(service.uploads)[-1]=='parts_manifest.json'
    manifest=json.loads(service.uploads['parts_manifest.json'])
    assert all(p['drive_file_id'] for p in manifest['parts'])
    received=tmp_path/'received';received.mkdir()
    for name,data in service.uploads.items():(received/name).write_bytes(data)
    join(received,tmp_path/'reassembled',expected_sha=hashlib.sha256(service.data).hexdigest())
    assert (tmp_path/'reassembled').read_bytes()==service.data


def test_bad_original_never_creates_cloud_folder(tmp_path):
    service=FakeDrive(b'wrong_original')
    with pytest.raises(ValueError,match='official original'):
        execute(tmp_path,service,expected_sha='wrong')
    assert not service.folders and not service.uploads


def test_remote_checksum_failure_has_no_completed_manifest(tmp_path):
    service=FakeDrive(bytes(range(51)),bad_checksum=True)
    with pytest.raises(ValueError,match='incomplete'):
        execute(tmp_path,service)
    assert 'parts_manifest.json' not in service.uploads


def test_missing_download_permission_fails_before_writes(tmp_path):
    service=FakeDrive(b'data',can_download=False)
    with pytest.raises(ValueError,match='permission'):
        execute(tmp_path,service)
    assert not service.folders and not service.uploads
