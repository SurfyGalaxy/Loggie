# Loggie

A discord bot made for GeoFS Virtual Airlines to streamline the flight logging process for both pilots and admins.

## Installation

Like any discord bot, use this invite link <a href="https://discord.com/oauth2/authorize?client_id=1533829807140241690&permissions=2147551232&integration_type=0&scope=bot+applications.commands">here</a> and invite it to your discord server.

## Commands

### /log

Creates a new flight record in the database.

Params:
- departure
- arrival
- hours
- minutes
- image

#### departure

The ICAO of the departure airport

#### arrival

The ICAO of the arrival airport

#### hours

Amount of hours the flight took

#### minutes

Amount of hours the flight took

#### image

Attatchment for a screenshot of the flight


### /json

Produces a JSON dump of all logs in a server.

### /stats

Summarises the amount and total time of flights, either from the server as a whole or a single user, for a custom amount of time.

Params:
- user [optional]
- start [optional]
- end [optional]

#### user

The user to show flight records for (or everyone if left empty)

#### start

The date at the start of the range to collect flight logs (formatted as YYYY-MM-DD)

Leave empty for no limit

#### end

The date at the end of the range to collect flight logs (formatted as YYYY-MM-DD)

Leave empty for no limit

### /remove

Remove a flight log (this cannot be undone)

params:
- flight_id

#### flight_id

The flight id to remove from the database.

## AI Disclaimer

No AI was used for any part of this project.