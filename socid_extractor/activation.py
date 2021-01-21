import requests

def get_twitter_headers(cookies):
    headers = {
      "sec-ch-ua": "Google Chrome\";v=\"87\", \" Not;A Brand\";v=\"99\", \"Chromium\";v=\"87\"",
      "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
      "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    }

    r = requests.post("https://api.twitter.com/1.1/guest/activate.json", headers=headers)
    guest_token = r.json()['guest_token']
    headers['x-guest-token'] = guest_token

    return cookies, headers

def get_vimeo_headers(cookies):
    headers = {
      "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    }

    r = requests.get('https://vimeo.com/_rv/viewer', headers=headers)
    jwt_token = r.json()['jwt']
    headers['Authorization'] = 'jwt ' + jwt_token

    return cookies, headers
