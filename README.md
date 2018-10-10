# lwPoster
### Automatically post Less Wrong meetups

`apis.py` has a function `post` that will automatically post a Less Wrong meetup to:
* lesswrong.com
* facebook
* The [SSC meetups repo](https://github.com/ssc-meetups-community/meetups)
* An email list

I've made a slight attempt to make this usable by other people, but there's still some SF stuff hardcoded in there.
It'll probably take some reading the code to be able to use this yourself.
If you do that work, and do so in a way that will make it easier for the next person, please send me a PR.

The SSC poster in particular is gnarly. It relies on having a the SSC meetups repo cloned in your working directory as `ssc-meetups`.
You also need to insert a little tag thing into the SCC meetups list so the script can find your meetup,
and need commit rights to the repo. I think they're going to replace this pretty soon anyway so maybe just don't use the SSC part.
