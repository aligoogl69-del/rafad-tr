import unittest, os, json, threading
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from server import identify, analyze, times, ApiError, Handler, ThreadingHTTPServer

class Tests(unittest.TestCase):
    def test_hosts(self):
        for url in ['https://youtube.com.attacker.org/watch?v=12345678901','http://youtu.be/12345678901','https://user@youtube.com/watch?v=12345678901','https://127.0.0.1/video','https://youtube.com:80/watch?v=12345678901']:
            with self.subTest(url=url), self.assertRaises(ApiError): identify(url)
    def test_platforms(self):
        for host,platform in [('youtu.be','youtube'),('instagram.com','instagram'),('fb.watch','facebook'),('vm.tiktok.com','tiktok')]:
            self.assertEqual(identify(f'https://{host}/video')[0],platform)
    @patch.dict(os.environ,{},clear=True)
    def test_missing_config_honest(self):
        report=analyze({'url':'https://youtu.be/abcdefghijk'})
        self.assertEqual(report['status'],'needs_connection'); self.assertEqual(report['statistics'],{})
        self.assertIsNone(report['ai_analysis'])
    @patch.dict(os.environ,{'YOUTUBE_API_KEY':'fake'},clear=True)
    @patch('server.fetch_json')
    def test_youtube(self,fetch):
        fetch.return_value={'items':[{'snippet':{'title':'عنوان #مطاعم','description':'#مطاعم #عراق','tags':['food']},'statistics':{'viewCount':'1000','likeCount':'50','commentCount':'10'}}]}
        report=analyze({'url':'https://youtube.com/shorts/abcdefghijk'})
        self.assertEqual(report['hashtags'],['#مطاعم','#عراق']);self.assertEqual(report['tags'],['food'])
        self.assertEqual(report['status'],'live');self.assertIn('6.00%',report['observations'][1])
    def test_insufficient(self): self.assertEqual(times({'posts':[]})['hours'],[])
    def test_timezone_and_ranking(self):
        rows=[{'published_at':f'2026-11-{day:02}T15:00:00Z','views':1000,'engagements':100} for day in range(1,22)]
        report=times({'posts':rows})
        self.assertEqual(report['hours'][0]['hour'],18);self.assertEqual(report['hours'][0]['rate'],10)
    def test_bad_performance(self):
        for row in [{'published_at':'2026-11-01T12:00:00','views':1,'engagements':0},{'published_at':'2026-11-01T12:00:00Z','views':0,'engagements':1}]:
            with self.assertRaises(ApiError): times({'posts':[row]})
    @patch.dict(os.environ,{'APP_API_TOKEN':'secret'},clear=True)
    def test_http_auth(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        endpoint=f'http://127.0.0.1:{server.server_port}'
        try:
            with self.assertRaises(HTTPError) as e: urlopen(Request(endpoint+'/v1/analyze',data=b'{}'))
            self.assertEqual(e.exception.code,401)
            req=Request(endpoint+'/v1/analyze',data=json.dumps({'url':'https://instagram.com/reel/abc'}).encode(),headers={'Authorization':'Bearer secret'})
            with urlopen(req) as r:self.assertEqual(json.load(r)['status'],'needs_connection')
        finally: server.shutdown();server.server_close()
if __name__=='__main__': unittest.main()
