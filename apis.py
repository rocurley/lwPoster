import smtplib
from getpass import getpass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup
import datetime
import pytz
import markdown
import json
import re
import string
import urllib.request, urllib.parse, urllib.error
from subprocess import Popen, PIPE


def next_meetup_date(config={}):
    return next_meetup_date_testable(config, datetime.datetime.now())

def next_meetup_date_testable(config, dt):
    d = dt.date()
    if dt.time() > datetime.time(hour=18): # if it's 6 PM or later
        d += datetime.timedelta(days=1) # then don't schedule it for today
    day_number = config.get_default("weekday_number", 0)
    return next_weekday(d, day_number)

def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead < 0:  # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)


def load_boilerplate(config):
    phone = config.get("phone")
    location_config = config.get("location")
    boilerplate_path = config.get_default("boilerplate_path", "boilerplate.md")
    if "phone" in location_config:
        phone = "%s (general meetup info at %s)" % (location_config.get("phone"),
                                                    phone)
    if "instructions" in location_config:
        instructions = location_config.get("instructions") + "\n"
    else:
        instructions = ""
    with open(boilerplate_path) as f:
        boilerplate = string.Template(instructions + f.read())
    return boilerplate.substitute(phone=phone)

def gen_body(topic, config):
    boilerplate = load_boilerplate(config)
    with open("meetups/body/%s.md" % topic) as f:
        topic_text = f.read()
    return "%s\n%s" % (topic_text, boilerplate)

def gen_title(topic, meetup_name):
    with open("meetups/title/%s.md" % topic) as f:
        topic_title = f.read().strip()
    return "%s: %s" % (meetup_name, topic_title)

def gen_title_with_date(topic, meetup_name, date_str):
    return "%s: %s: %s" % (meetup_name, date_str, topic)




def lw2_title(topic, config):
    return gen_title(topic, config.get("meetup_name"))

def lw2_body(topic, config):
    return gen_body(topic, config)

def lw2_post_meetup(topic, config, public):
    location = config.get_default("location", {"str": ""})
    group_id = config.get("group_id")
    maps_key = config.get("maps_key")
    lw_key = config.get("lw_key")

    date = next_meetup_date(config)
    startTime = datetime.time(18, 15)
    endTime = datetime.time(21, 00)
    with open("meetups/%s.md" % topic) as f:
        topic_text = f.read()
    return lw2_post_meetup_raw(
        lw_key,
        maps_key,
        lw2_title(topic, config),
        lw2_body(topic, config),
        location.get_default("str", ""),
        date,
        startTime,
        endTime,
        group_id,
        public,
    )

def lw2_post_meetup_raw(lw_key, maps_key, title, body, location, date,
                        startTime, endTime, groupId, public):
    with open("./lib/lw2_query.graphql") as query_file:
        query = query_file.read()

    def format_time(time):
        dt = datetime.datetime.combine(date, time)
        tz = pytz.timezone("America/Los_Angeles")
        dtz = tz.localize(dt).astimezone(pytz.utc)
        return dtz.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    startTimeStr = format_time(startTime)
    endTimeStr = format_time(endTime)
    geocoding_resp = requests.get_default(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={
            "address": location,
            "key": maps_key,
        })
    googleLocation = geocoding_resp.json()["results"][0]
    mongoLocation = {
        "type":
        "Point",
        "coordinates": [
            googleLocation["geometry"]["location"]["lng"],
            googleLocation["geometry"]["location"]["lat"],
        ]
    }
    variables = {
        "document": {
            "isEvent": "true",
            "meta": False,
            "groupId": groupId,
            "location": googleLocation["formatted_address"],
            "googleLocation": googleLocation,
            "mongoLocation": mongoLocation,
            "types": ["LW", "SSC"],
            "draft": not public,
            "title": title,
            "startTime": startTimeStr,
            "endTime": endTimeStr,
            "body": body
        }
    }
    request = {
        "query": query,
        "variables": variables,
        "operationName": "createPost"
    }
    resp = requests.post(
        "https://www.lesswrong.com/graphql",
        json=request,
        headers={"authorization": lw_key},
    )
    try:
        post_id = resp.json()["data"]["createPost"]["data"]["_id"]
    except (KeyError, TypeError):
        print("Unexpected response")
        print(resp.json())
        raise
    post_url = "https://www.lesswrong.com/events/%s" % post_id
    return post_url


def delete_lw2_post(postId, lw_key):
    unPost = string.Template("""
mutation {
    PostsRemove(documentId: "$_id"){
        _id
    }
}
""")
    resp = requests.post(
        "https://www.lesserwrong.com/graphql",
        json={'query': unPost.substitute(_id=postId)},
        headers={"authorization": lw_key},
    )
    j = resp.json()
    print(j)


def lw_login(username, password=None):
    url = "http://lesswrong.com/post/login"

    password = password or getpass("LW password: ")

    payload = {
        "rem": "on",
        "user_login": username,
        "op": "login-main",
        "passwd_login": password,
    }

    response = requests.request(
        "POST", url, data=payload, allow_redirects=False)

    if "reddit_session" not in response.cookies:
        raise LookupError("Login Failed")

    return response.cookies


def lw_get_uh(cookies):
    url = "http://lesswrong.com/meetups/new/"

    response = requests.request("Get", url, cookies=cookies)
    response_html = BeautifulSoup(response.text, "html.parser")
    return response_html.find("input", attrs={"name": "uh"})["value"]




def fb_login(email, password=None):
    url = "https://m.facebook.com/login.php"

    password = password or getpass("FB password: ")

    payload = {
        "email": email,
        "pass": password,
    }

    response = requests.request(
        "POST", url, data=payload, allow_redirects=False)

    if "c_user" not in response.cookies:
        raise LookupError("Login Failed")

    return response.cookies


def fb_get_dstg(cookies):
    url = "https://m.facebook.com/events/create/basic"
    response = requests.request("Get", url, cookies=cookies)
    response_html = BeautifulSoup(response.text, "html.parser")
    return response_html.find("input", attrs={"name": "fb_dtsg"})["value"]


def fb_post(fb_cookies,
            fb_dstg,
            title,
            description,
            location,
            date,
            time,
            public=False):
    url = "https://www.facebook.com/ajax/create/event/submit"

    url_encoded_payload = {
        "title": title,
        "description": description,
        "location": location,
        "location_id": "null_%s" % location,
        "cover_focus[x]": "0.5",
        "cover_focus[y]": "0.5",
        "only_admins_can_post": "false",
        "post_approval_required": "false",
        "start_date": date.strftime("%D"),
        "start_time": time.hour * 3600 + time.minute * 60 + time.second,
        #"end_date": "3/28/2017",
        #"end_time": "72000",
        "timezone": "America/Los_Angeles",
        #"acontext": r'{"sid_create":"1763740711","action_history":"[{\"surface\":\"create_dialog\",\"mechanism\":\"user_create_dialog\",\"extra_data\":[]}]","has_source":true}',
        "acontext": "{}",
        "event_ent_type": 1 + public,
        "guests_can_invite_friends": "true",
        "guest_list_enabled": "true",
        "save_as_draft": "false",
        "friend_birthday_prompt_xout_id": "",
        "is_multi_instance": "false",
        "dpr": "1",
    }
    form_data_payload = {
        "fb_dtsg": fb_dstg,
    }

    return requests.request(
        "POST",
        url,
        params=url_encoded_payload,
        data=form_data_payload,
        cookies=fb_cookies,
        allow_redirects=False)

def fb_title(topic, config):
    meetup_name = config.get_default("fb_meetup_name", "")
    if meetup_name == "":
        meetup_name = config.get("meetup_name")
    return gen_title(topic, meetup_name)

def fb_email(config):
    fb_login_email = config.get_default("fb_login_email", "")
    if fb_login_email == "":
        fb_login_email = config.get("email")
    return fb_login_email

def fb_body(topic, config):
    return gen_body(topic, config)

def fb_meetup_attrs(topic, config):
    date = next_meetup_date(config)
    time = datetime.time(18, 15)
    location = config.get("location")
    return (
        fb_email(config), fb_title(topic, config), fb_body(topic, config),
        location, date, time
    )

def fb_post_meetup(topic, config, public=False):
    fb_email, title, description, location, date, time = fb_meetup_attrs(topic, config)
    fb_cookies = fb_login(fb_email)
    fb_dstg = fb_get_dstg(fb_cookies)
    res = fb_post(
        fb_cookies,
        fb_dstg,
        title=title,
        description=description,
        location=location.get("str"),
        date=date,
        time=time,
        public=public)
    if not res.ok:
        raise requests.HTTPError(res)




def email_pieces(topic, config):
    boilerplate = load_boilerplate(config)
    with open("meetups/title/%s.md" % topic) as f:
        topic_title = f.read()
    with open("meetups/body/%s.md" % topic) as f:
        topic_text = f.read()
    date = next_meetup_date(config)
    location = config.get("location")
    when_str = date.strftime("%d %B %Y, 6:15 PM")
    plain_email = _email_plaintext(when_str, location.get("str"), topic_text, boilerplate)
    html_email = _email_html(when_str, location.get("str"), topic_text, boilerplate)
    email_title = _email_title(topic_title, config, date)
    return (email_title, plain_email, html_email)

def _email_plaintext(time_str, loc_str, topic_text, boilerplate):
    return """WHEN: %s
WHERE: %s

%s
%s
    """ % (time_str, loc_str, topic_text, boilerplate)

def _email_html(time_str, loc_str, topic_text, boilerplate):
    return markdown.markdown("""**WHEN:** %s

**WHERE:** %s

%s
%s
    """ % (time_str, loc_str, topic_text, boilerplate))

def _email_title(topic, config, date_obj):
    return gen_title_with_date(topic, config.get("meetup_name"), date_obj.isoformat())

def send_meetup_email(topic, config, gmail_username, toaddr):
    email_title, plaintext_email, html_email = email_pieces(topic, config)
    msg = MIMEMultipart("alternative")

    fromaddr = "%s@gmail.com" % gmail_username
    msg["Subject"] = email_title
    msg["From"] = fromaddr
    msg["To"] = toaddr

    part1 = MIMEText(plaintext_email, "plain")
    msg.attach(part1)
    part2 = MIMEText(html_email, "html")
    msg.attach(part2)

    gmail = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    pwd = config.get("gmail_app_password")
    if not pwd:
        pwd = getpass("Gmail application-specific password: ")
    gmail.login(gmail_username, pwd)
    gmail.sendmail(fromaddr, toaddr, msg.as_string())




def ssc_meetup_text(title,
                    location,
                    date,
                    time,
                    header,
                    footer,
                    email,
                    phone,
                    lw_url=None):
    if lw_url:
        lw_line = "    * More Info: [Lesswrong Meetup Post](%s)" % lw_url
    else:
        lw_line = ""
    meetup_text = """{header}
* San Francisco [LW]

    * Meetup scheduled: {date}, {time}
    * Topic: {topic}
    * Location: [{address}](https://www.google.com/maps/place/{address_url})
    * Contact: [{email}](mailto:{email}), {phone}
{lw_line}

{footer}""".format(
        time=time.strftime("%I:%M %p"),
        date=date.strftime("%B %d, %Y"),
        address=location.get("str"),
        address_url=urllib.parse.quote_plus(location.get("str")),
        topic=title,
        header=header,
        footer=footer,
        email=email,
        phone=phone,
        lw_line=lw_line)
    return meetup_text


def update_ssc_meetup(title, config, public, lw_url=None):
    location = config.get("location")
    email = config.get("email")
    phone = config.get("phone")
    date = next_meetup_date()
    time = datetime.time(18, 15)
    print_command(["git", "pull"], cwd="ssc-meetups")
    r = re.compile(
        r"\n.*BEGIN_SAN_FRANCISCO_LW.*?\n(.*\n)*?.*?END_SAN_FRANCISCO_LW.*\n")
    with open("ssc-meetups/index.md", "r+") as f:
        old = f.read()
        match = r.search(old)
        if not match:
            raise ValueError("Could not find anchors")
        lines = match.group().split('\n')
        header = "\n".join(lines[:2])
        footer = "\n".join(lines[-2:])
        new = r.sub(
            ssc_meetup_text(title, location, date, time, header, footer, email,
                            phone, lw_url), old)
        f.seek(0)
        f.write(new)
        f.truncate()
    print_command(["git", "add", "index.md"], cwd="ssc-meetups")
    print_command(
        ["git", "commit", "-m",
         date.strftime("San Francisco Meetup %F")],
        cwd="ssc-meetups")
    if public:
        print_command(["git", "push"], cwd="ssc-meetups")




def print_command(command, **kwargs):
    print(" ".join(command))
    p = Popen(command, stdout=PIPE, stderr=PIPE, **kwargs)
    output, err = p.communicate()
    print(output, end=' ')
    if err:
        print(err, end=' ')
    if p.returncode != 0:
        raise IOError("Return Status %i" % p.returncode)


class PostingConfig:
    public = {}
    secret = {}

    def __init__(self, file="config.json", secrets="secrets.json"):
        self.public = json.load(open(file))
        self.secret = json.load(open(secrets))

    def get(self, *args):
        if len(args) < 1:
            raise KeyError
        if len(args) == 1:
            return self.secret.get(args[0], self.public.get(args[0]))
        tmp_p = self.public
        tmp_s = self.secret
        for key in args:
            tmp_s = tmp_s.get(key, {})
            tmp_p = tmp_p.get(key, {})
        if tmp_s and tmp_s != {}:
            return tmp_s
        if tmp_p and tmp_p != {}:
            return tmp_p
        raise KeyError

    def set(self, *args):
        if len(args) < 2:
            raise KeyError
        if len(args) == 2:
            self.public[args[0]] = args[1]
        k = {}
        v = {}
        for key in args:
            k = v
            v = key
        self.public[k] = v

    def get_default(self, *args):
        if len(args) < 2:
            raise KeyError
        default = args[-1]
        args = args[:-1]
        try:
            v = self.get(*args)
            if v != None:
                return v
        except KeyError:
            pass
        v = default
        self.set(*args, v)
        return v

def config(file="config.json", secrets="secrets.json"):
    return PostingConfig(file, secrets)

def post(config, topic, host, public=True, skip=None, lw_url=None):
    if skip is None:
        skip = {}
    config.set("location", config.get("locations").get(host))
    if "fb" not in skip:
        fb_post_meetup(topic, config, public)
        print("Posted to Facebook")
    if "lw" not in skip:
        lw_url = lw2_post_meetup(topic, config, public)
        print(lw_url)
    if "ssc" not in skip:
        update_ssc_meetup(topic, config, public, lw_url)
        print("Posted to SSC Meetups List")
    if "email" not in skip:
        gmail_username = config.get("gmail_username")
        if public:
            email_group = config.get("email_group")
            toaddr = email_group
        else:
            toaddr = "%s@gmail.com" % gmail_username
        send_meetup_email(topic, config, gmail_username, toaddr)
        print("Email Sent")

if __name__ == "__main__":
    cfg = config()
    topic = input("enter topic name: ")
    host = input("enter short name for location: ")
    post(cfg, topic, host, skip={"fb": True, "lw": True, "ssc": True})
