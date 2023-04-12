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


def load_boilerplate(config):
    phone = config["phone"]
    location_config = config["location"]
    if "phone" in location_config:
        phone = "%s (general meetup info at %s)" % (location_config["phone"],
                                                    phone)
    if "instructions" in location_config:
        instructions = location_config["instructions"] + "\n"
    else:
        instructions = ""
    with open("boilerplate") as f:
        boilerplate = string.Template(instructions + f.read())
    return boilerplate.substitute(phone=phone)

def next_meetup_date(config={}):
    dt = datetime.datetime.now()
    d = dt.date()
    if dt.time() > datetime.time(hour=20):
        day_number = config["weekday_number"]
        d += datetime.timedelta(days=day_number)
    return next_weekday(d, 0)


def lw2_post_meetup(topic, config, public):
    location = config["location"]
    group_id = config["group_id"]
    maps_key = config["maps_key"]
    lw_key = config["lw_key"]
    meetup_name = config["meetup_name"]

    date = next_meetup_date(config)
    startTime = datetime.time(18, 15)
    endTime = datetime.time(21, 00)
    boilerplate = load_boilerplate(config)
    with open("meetups/%s" % topic) as f:
        topic_text = f.read()
    title = "%s: %s" % (meetup_name, topic)
    body = "%s\n%s" % (topic_text, boilerplate)
    return lw2_post_meetup_raw(
        lw_key,
        maps_key,
        title,
        body,
        location["str"],
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
    geocoding_resp = requests.get(
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

    password = password or getpass("LW password")

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

    password = password or getpass("FB password")

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


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead < 0:  # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)


def send_meetup_email(topic, config, gmail_username, toaddr):
    date = next_meetup_date(config)
    meetup_name = config["meetup_name"]
    location = config["location"]
    boilerplate = load_boilerplate(config)
    with open("meetups/%s" % topic) as f:
        topic_text = f.read()
    email_title = "%s: %s: %s" % (meetup_name, date.isoformat(), topic)
    when_str = date.strftime("%d %B %Y, 6:15 PM")
    plaintext_email = """WHEN: %s 
WHERE: %s

%s
%s
    """ % (when_str, location["str"], topic_text, boilerplate)
    html_email = markdown.markdown("""**WHEN:** %s

**WHERE:** %s

%s
%s
    """ % (when_str, location["str"], topic_text, boilerplate))

    fromaddr = "%s@gmail.com" % gmail_username

    part1 = MIMEText(plaintext_email, "plain")
    part2 = MIMEText(html_email, "html")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = email_title
    msg["From"] = fromaddr
    msg["To"] = toaddr
    msg.attach(part1)
    msg.attach(part2)

    gmail = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    gmail.login("palmtree3000", getpass("Gmail password"))
    gmail.sendmail(fromaddr, toaddr, msg.as_string())


def fb_post_meetup(topic, config, public=False):
    date = next_meetup_date(config)
    time = datetime.time(18, 15)
    meetup_name = config["fb_meetup_name"]
    if meetup_name == "":
        meetup_name = config["meetup_name"]
    location = config["location"]
    email = config["email"]
    fb_login_email = config["fb_login_email"]
    boilerplate = load_boilerplate(config)
    with open("meetups/%s" % topic) as f:
        topic_text = f.read()
    title = "%s: %s" % (meetup_name, topic)
    description = "%s\n%s" % (topic_text, boilerplate)
    fb_cookies = fb_login(fb_login_email)
    fb_dstg = fb_get_dstg(fb_cookies)
    res = fb_post(
        fb_cookies,
        fb_dstg,
        title=title,
        description=description,
        location=location["str"],
        date=date,
        time=time,
        public=public)
    if not res.ok:
        raise requests.HTTPError(res)


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
        address=location["str"],
        address_url=urllib.parse.quote_plus(location["str"]),
        topic=title,
        header=header,
        footer=footer,
        email=email,
        phone=phone,
        lw_line=lw_line)
    return meetup_text


def print_command(command, **kwargs):
    print(" ".join(command))
    p = Popen(command, stdout=PIPE, stderr=PIPE, **kwargs)
    output, err = p.communicate()
    print(output, end=' ')
    if err:
        print(err, end=' ')
    if p.returncode != 0:
        raise IOError("Return Status %i" % p.returncode)


def update_ssc_meetup(title, config, public, lw_url=None):
    location = config["location"]
    email = config["email"]
    phone = config["phone"]
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


def post(topic, host, public=True, skip=None, lw_url=None):
    if skip is None:
        skip = {}
    config = json.load(open("config.json"))
    config["location"] = config["locations"][host]
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
        gmail_username = config["gmail_username"]
        if public:
            email_group = config["email_group"]
            toaddr = email_group
        else:
            toaddr = "%s@gmail.com" % gmail_username
        send_meetup_email(topic, config, gmail_username, toaddr)
        print("Email Sent")
