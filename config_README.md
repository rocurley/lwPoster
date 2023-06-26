The poster reads from two files to configure itself: config.json and secrets.json.
Both files are read as JSON objects, and if both contain the same key, secrets takes precedence.
The files configEXAMPLE.json and secretsEXAMPLE.json show the keys which are used, with descriptions
of purpose in many cases.

```{```
```    "email_group": "bayarealesswrong@googlegroups.com",```
Optional. Public email group to send email notifications to.
```    "email": "Used by SSC poster for contact info.",```
TODO
```    "group_id":"Looks like <qQkgmEeEreY6gjd7>, you can get it from the url of your group on lesswrong.",```
This URL looks like `https://www.lesswrong.com/groups/v7dn9rTWLcK5Tcy9f`
```    "fb_meetup_name": "San Francisco Less Wrong Meetup",```
Name to use for the meetup on FB. Optional, defaults to `meetup_name`
```    "meetup_name": "San Francisco Meetup",```
Name to use for the meetup everywhere but FB. And on FB is it isn't overridden.
```    "weekday_number": 1,```
Most confusing parameter. 1 means Monday, 2 means Tuesday, 7 means Sunday.
```    "locations": {```
```        "SF Van Ness":{```
```            "lat":37.771621,```
```            "lon":-122.418445,```
```            "str":"140 S Van Ness Ave, San Francisco, CA 94103-2519, United States"```
```        },```
A geolocator and address, labeled by the short name used to identify it when calling the script.
Multiple entries are possible for meetups which move regularly.
```        "Mecatol": {```
```            "lat": 37,```
```            "lon": -122,```
```            "str": "540 Alcatraz Ave, Oakland, CA 94609, United States"```
```        }```
```    },```
```    "location": {```
```        "instructions": "A front door code or directions or similar instructions for getting into the building",```
Optional. If directions are needed to get into the building or find the meeting location, add them here.
```        "phone": "phone number specifically for accessing site"```
Optional. This phone number, if present, appears next to the organizer's main phone (usually in secrets.json).
```    }```
```}```


Secrets:
```{```
```    "gmail_username": "Used to log in.",```
Should be 'jrandom', not 'jrandom@gmail.com'
```    "fb_login_email": "Used to log in.",```
Full email address associated with your Facebook account
```    "phone":"Phone number, used for contacting the organizer",```
Not used for any logins, but usually you don't want this visible in an open-source repository. Can be partially overridden by location-specific phone numbers.
```    "maps_key":"API key for google maps. Needed to post to LW since they need some fancy geoencoding done clientside",```
TODO
```    "lw_username": "Used to log in.",```
Exactly what it looks like. May not always been the same as the displayed name.
```    "lw_key":"You can get this from your cookies on lesswrong.com . Super annoying, but I haven't managed to automate login there. You'll need to refresh this every few months."```
TODO. LW adamantly refuses to document any part of their API, so this is subject to change without notice until such time as they decide to conduct themselves like professionals.
```}
