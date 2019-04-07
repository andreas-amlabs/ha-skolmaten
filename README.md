A Home assistant sensor for displaying
the rss feed from "skolmaten"


Use like
<code>
sensor:
  - platform: skolmaten
    name: Skolmaten
    feed_url: 'https://skolmaten.se/i-ur-och-skur-skabersjoskolan/rss/'
    date_format: '%a, %b %d %I:%M %p'
    monitored_conditions:
      - monday
      - tuesday
      - wednesday
      - thursday
      - friday
    inclusions:
      - published
      - title
      - summary

</code>

The project is based on code from
https://github.com/custom-components/sensor.feedparser

The project is just a hack
